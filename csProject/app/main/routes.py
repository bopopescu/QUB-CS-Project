from flask import Blueprint, render_template, request, flash, current_app, g, jsonify, url_for, redirect
from flask_login import login_required, current_user
from rq import push_connection, pop_connection, Queue
from rq.registry import StartedJobRegistry
from helpers import (get_user_token, chart_format_repo_stats, get_chart_data, format_repo_stats, get_repo_language,
	get_repo_dir, create_archive, walklevel, get_time_intervals, parse_search_data, get_failed_registry)
import forms
import code_climate
import analysis_functions
from github import Github
from ..constants import github_api_url_base, github_headers, slave_username
from data_dict import supported_languages
from ..extensions import db
from ..models import Code_Climate, Archive, CK, CK_Class, Github_Stats
import redis
import git, pygit2
import requests, json, urllib, os, time, re
from datetime import datetime, date, timedelta
from scipy.stats.stats import pearsonr, spearmanr

bp = Blueprint('main', __name__)

def get_redis_connection():
	redis_connection = getattr(g, '_redis_connection', None)
	if redis_connection is None:
		redis_url = current_app.config['REDIS_URL']
		redis_connection = g._redis_connection = redis.from_url(redis_url)
	return redis_connection

@bp.route('/rq/current_jobs')
def get_current_rq_jobs():
	registry = StartedJobRegistry('default', connection=get_redis_connection())
	running_job_ids = registry.get_job_ids()
	failed_registry = get_failed_registry()
	running_job_ids = [job for job in running_job_ids if job not in failed_registry]
	return jsonify(len(running_job_ids))

@bp.before_request
def push_rq_connection():
	push_connection(get_redis_connection())

@bp.teardown_request
def pop_rq_connection(exception=None):
	pop_connection()

@bp.route('/status/<job_id>')
def job_status(job_id):
	q = Queue()
	job = q.fetch_job(job_id)
	if job is None:
		response = {'status': 'unknown'}
	else:
		response = {
			'status': job.get_status(),
			'result': job.result,
		}
		if job.is_failed:
			response['message'] = job.exc_info.strip().split('\n')[-1]
	return jsonify(response)

@bp.route('/run_archive_task', methods=['POST'])
def run_archive_task():
	''' Adds each of the following methods to the execution queue for each version of each repository url:
		1. download source code
		2. caluculate quality
		3. add to code climate
		4. extract github stats
	'''
	# determine method of user input
	if request.form['view'] == 'single':
		form = forms.RepoURLArchiveForm(request.form)
		urls = request.form.to_dict(flat=False)['url']
	else:
		form = forms.RepoURLArchiveFormCSV(request.form)
		urls = form.get_csv_urls()

	if form.validate_on_submit() and forms.valid_urls(urls):
		url_list = filter(None, urls) # filter out empty fields
		url_list = list(dict.fromkeys(url_list)) # remove duplicates

		start_date = datetime.strptime(request.form['start_date'], '%d/%m/%Y').date()
		end_date = datetime.strptime(request.form['end_date'], '%d/%m/%Y').date()

		if start_date == end_date:
			time_intervals = [start_date]
		else:
			time_intervals = get_time_intervals(start_date, end_date)

		token = get_user_token()
		q = Queue()
		success = True
		total_downloads = len(url_list)*len(time_intervals)
		num_failures = 0

		for url in url_list:
			archive_folder = create_archive(url)	

			for idx in range(len(time_intervals)):
				timestamp = time_intervals[idx]

				# skip if already archived
				exists = db.session.query(Archive).filter(Archive.url==url).filter(Archive.timestamp==timestamp).first()
				if exists:
					continue

				# write details to db
				store_job = q.enqueue('app.tasks.store_archive_info', url, timestamp, archive_folder, token, timeout=999999)
				# wait for job to finish successfully before moving to the next stage of analysis
				while(store_job.status != 'finished' and store_job.status != 'failed'):
					pass

				if store_job.is_failed or store_job.result is None:
					num_failures += len(time_intervals) # failed for all versions
					continue

				# download source code
				github_slug = store_job.result
				download_folder = os.path.join(archive_folder, str(timestamp))
				archive_job = q.enqueue('app.tasks.archive_repository', download_folder, url, github_slug, timestamp, token, timeout=999999)

				# wait for job to finish successfully before moving to the next stage of analysis
				while(archive_job.status != 'finished' and archive_job.status != 'failed'):
					pass

				if archive_job.is_failed or archive_job.result is False:
					num_failures += 1
					continue

				# add to code climate
				name = db.session.query(Archive).filter_by(github_slug=github_slug).first().name
				cc_slug = slave_username + '/' + name + str(timestamp).replace('-','')
				cc_job = q.enqueue('app.tasks.add_repo_to_cc', cc_slug, timestamp, timeout=999999)

				# wait for job to finish successfully before moving to the next stage of analysis
				while(cc_job.status != 'finished' and cc_job.status != 'failed'):
					pass
				cc_id = cc_job.result

				language = db.session.query(Archive).filter_by(github_slug=github_slug).first().language
				if cc_job.is_failed or cc_job.result is False:
					num_failures += 1
					continue

				# perform analysis (if java project)
				if language.lower() != 'java':
					continue

				analyse_job = q.enqueue('app.tasks.calculate_ck_class_metrics', archive_folder, timestamp, timeout=999999)
				while(analyse_job.status != 'finished' and analyse_job.status != 'failed'):
					pass

				if analyse_job.is_failed: 
					num_failures += 1
					continue

			# extract github statistics
			from_ = time_intervals[0]
			to = time_intervals[-1]

			# count contributors
			count_contributors_job = q.enqueue('app.tasks.count_contributors', github_slug, from_, to, token, timeout=999999)

			while (count_contributors_job.status != 'finished' and count_contributors_job.status != 'failed'):
				pass
		
			if count_contributors_job.is_failed:
				num_failures += len(time_intervals) # failed for all versions
				continue

			num_contributors = count_contributors_job.result

			# calculate average monthly commits for the repository	
			change_freq_job = q.enqueue('app.tasks.calculate_change_frequency', github_slug, from_, to, token, timeout=999999)

			while (change_freq_job.status != 'finished' and change_freq_job.status != 'failed'):
				pass

			if change_freq_job.is_failed: 
				num_failures += len(time_intervals) # failed for all versions
				continue

			change_freq = change_freq_job.result

			q.enqueue('app.tasks.store_github_statistics', github_slug, from_, to, num_contributors, change_freq, timeout=999999)

		if num_failures == total_downloads:
			return jsonify('Failed to archive all repositories. Please check the URLs and dates provided.'), 400

		return jsonify('Archived {}/{} repositories...'.format(total_downloads-num_failures, total_downloads)), 202
	else:
		if form.errors:
			return jsonify(form.errors.itervalues().next()), 400
		return jsonify('Invalid URL'), 400


#####################
	# ROUTES #
#####################

@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
	form = forms.RepoURLArchiveForm()
	csv_form = forms.RepoURLArchiveFormCSV()

	archive_directory = os.path.join(os.path.dirname(os.getcwd()),'archive')
	archived_repos = {}

	repos = db.session.query(Archive).all()
	
	for repo in repos:
		archived_repos.setdefault(repo.name, list()).append(repo.timestamp)

	return render_template('archive.html', form=form, csv_form=csv_form, archived_repos=archived_repos)

@bp.route('/stats', methods=['GET', 'POST'])
@login_required
def stats():
	form = forms.RepoURLForm()

	if request.method == 'POST' and form.validate_on_submit():
		urls = request.form.to_dict(flat=False)
		url_list = filter(None, urls.itervalues().next())

		token = get_user_token()

		if not token:
			return 'Unauthorised'
	
		g = Github(token)
		repo_stats={}

		for r in url_list:
			repo_name='/'.join(r.rsplit('/', 2)[1:]).replace('.git','').replace(" ", "")
			try:
				repo = g.get_repo(repo_name)
				repo_stats[repo.name] = {}
				metrics = ['stargazers_count', 'watchers', 'subscribers_count', 'size', 'owner', 'open_issues_count', 'forks_count', 'description']
				
				for metric in metrics:
					descriptor = metric.replace('count','').replace('_',' ').rstrip()
					repo_stats[repo.name][descriptor] = getattr(repo, metric, 0)
				repo_stats[repo.name]['branches'] = repo.get_branches().totalCount
			except:
				flash("Failed to extract statistics for repository '{}' ({})".format(repo_name.capitalize(), r), 'danger')

		chart_stats = chart_format_repo_stats(repo_stats)
		repo_stats = format_repo_stats(repo_stats)
		
		return render_template('stats.html', form=form, stats=repo_stats, chart_stats=chart_stats)
	else:
		if form.errors:
			flash(form.errors['url'][0], 'danger')
	
	return render_template('stats.html', form=form)

@bp.route('/repositories')
@login_required
def repositories():
	repositories={}

	api_url = '{}users/{}/repos'.format(github_api_url_base, current_user.username)
	headers = {'Authorization': 'token %s' % get_user_token()}
	response = requests.get(api_url, headers=headers)

	if response.status_code == 200:
		repository_data = json.loads(response.text or response.content)

		for r in repository_data:
			repositories[r['name']]= r['html_url']
	else:
		flash('Could not access your repositories', 'danger')
		return render_template('repositories.html')

	return render_template('repositories.html', repositories=repositories)

@bp.route('/trending', methods=['GET', 'POST'])
@login_required
def trending():
	url = 'https://github-trending-api.now.sh/repositories'

	language = request.args.get('language')
	since = request.args.get('since')

	if language:
		url += '?language='+urllib.quote(language.encode("utf-8"))

		if since:
			url += '&since='+since
	elif since:
			url += '?since='+since

	response = requests.get(url, headers=github_headers)
	data = response.text.encode("utf-8")
	json_data = json.loads(data)

	trending_repos = {}

	for repo in json_data:
		try:
			name = repo['name']
			trending_repos[name] = {}
			trending_repos[name]['description'] = repo['description']
			trending_repos[name]['url'] = repo['url']
			trending_repos[name]['language'] = repo['language']
		except KeyError:
			pass

	return render_template('browse.html', trending_repos=trending_repos)

@bp.route('/downloads')
@login_required
def downloads():
	repositories = []
	from sqlalchemy import func 
	query = db.session.query(Archive)\
	.filter(Archive.language.ilike("java"))\
	.distinct(Archive.github_slug)\
	.group_by(Archive.github_slug).having(func.count(Archive.github_slug) >= 5)
	
	for repo in query.all():
		repositories.append(repo)

	return render_template('downloads.html', repositories=repositories)

@bp.route('/analyse', methods=['GET', 'POST'])
@login_required
def analyse():
	repository = request.args.get('repo')
	timestamp = request.args.get('timestamp')
	all_data = { 'ck_metrics': {}, 'class_data': {}, 'chart_data': {} }

	if not (repository and timestamp):
		flash('You must provide a repository and valid time', 'danger')
		return redirect(url_for('main.index'))
	
	archived_repo = db.session.query(Archive).filter(Archive.name==repository).filter(Archive.timestamp==timestamp).first()
	repo_dir = get_repo_dir(repository, timestamp)

	if not (archived_repo and repo_dir):
		flash('You must archive this repository before analysis', 'danger')
		return redirect(url_for('main.index'))

	# get ck data
	ck_record = db.session.query(Archive, CK)\
		.filter(Archive.archive_folder==archived_repo.archive_folder)\
		.filter(Archive.id==CK.archive_id)\
		.filter(CK.quality_score != None)\
		.first()

	if ck_record:
		all_data['ck_metrics'] = ck_record.CK.__repr__()

		classes = db.session.query(CK, CK_Class).filter(ck_record.CK.id==CK_Class.ck_id).all()
		for _class in classes:
			all_data['class_data'][_class.CK_Class.name] = _class.CK_Class.__repr__()

		# get chart data
		all_data['chart_data'] = get_chart_data(all_data)

	# get code climate data
	cc_record = db.session.query(Archive, Code_Climate).filter(archived_repo.id==Code_Climate.archive_id).first()
	cc_data = {}

	if not cc_record:
		flash('Could not obtain code climate data. Permissions may be required.', 'danger')
	else:
		cc_data = code_climate.get_data(cc_record.Code_Climate.id, timestamp)
		all_data['cc_data'] = cc_data

	if request.method == 'POST':
		return jsonify(all_data)
	else:
		return render_template('results.html', language=archived_repo.language, data=all_data)

@bp.route('/analyse_all/<repo_name>', methods=['GET'])
@login_required
def analyse_all(repo_name):
	''' Analyse all versions of an archived repository '''
	repos = db.session.query(Archive).filter(Archive.name == repo_name).all()

	if not repos:
		flash('You must archive this repository before analysis', 'danger')
		return redirect(url_for('main.index'))

	headers = {'Cookie': 'session=' + request.cookies['session']}
	cc_data = []
	ck_data = []

	for repo in repos:
		url = 'http://127.0.0.1:5000/analyse?repo=' + repo.name + '&timestamp=' + repo.timestamp
		response = requests.post(url, headers=headers)
		data = json.loads(response.content)
		
		if not data:
			flash('Could not analyse {} for {}'.format(repo.name, repo.timestamp), 'danger')
			continue
		timestamp = ''

		if 'cc_data' in data.keys():
			cc_data.append(data['cc_data'])
			timestamp = data['cc_data']['timestamp']

		if 'ck_metrics' in data.keys():
			temp = data['ck_metrics']
			temp['timestamp'] = timestamp
			ck_data.append(temp)

	return render_template('analyse_all.html', repo_name=repo_name, cc_data=cc_data, ck_data=ck_data)

@bp.route('/change_language', methods=['GET', 'POST'])
@login_required
def change_language():
	form = forms.ChangeLanguageForm()
	repo = request.args.get('repo')
	timestamp = request.args.get('timestamp')
	record = db.session.query(Archive).filter(Archive.name==repo).filter(Archive.timestamp==timestamp).first()

	if not (repo and timestamp and record):
		flash('You must provide a repository and valid time', 'danger')
		return redirect(url_for('main.index'))

	old_language = record.language

	if request.method =='POST':
		new_language = request.form.get('new_language').lower()
		
		if not new_language in supported_languages:
			flash('Language not supported.', 'danger')
			return render_template('change_language.html', form=form, old_language=old_language)

		github_slug = db.session.query(Archive).filter(Archive.name == repo).filter(Archive.timestamp == timestamp).first().github_slug
		archive_folder = db.session.query(Archive).filter(Archive.name == repo).filter(Archive.timestamp == timestamp).first().archive_folder
		gitattributes = os.path.join(os.path.dirname(os.getcwd()), archive_folder, '.gitattributes')

		# create or update the gitattributes file
		try:
			f = open(gitattributes, 'a')
			f.write("*.* linguist-language=" + new_language.capitalize())
			f.close()
		except IOError:
			flash('You must archive this repository before making changes', 'danger')
			return render_template('change_language.html', form=form, old_language=old_language)

		# commit to github
		repository = git.Repo(os.path.join(os.path.dirname(os.getcwd()), archive_folder))
		repository.index.add([gitattributes])
		repository.index.commit(message='Adding gitattributes file.')
		url = 'git@github.com:' + slave_username + '/' + repo + timestamp.replace('-','') + '.git'
		repository.git.push(url, 'HEAD:master')

		# update db
		row = db.session.query(Archive).filter_by(archive_folder=archive_folder).all()
		row.language = new_language
		db.session.commit()

		flash('Language updated', 'success')
		return redirect(url_for('main.index'))

	return render_template('change_language.html', form=form, old_language=old_language)

@bp.route('/quality_issues')
@login_required
def quality_issues():
	''' Code smells identified by code climate '''
	id = request.args.get('id')

	record = db.session.query(Archive, Code_Climate)\
	.filter(Code_Climate.id==id)\
	.filter(Archive.id==Code_Climate.archive_id)\
	.first()

	if not record:
		flash('Invalid ID', 'danger')
		return redirect(url_for('main.index'))

	github_slug = record.Archive.github_slug
	language = record.Archive.language
	repository = record.Archive.name

	try:
		snapshot_id = Code_Climate.query.filter_by(id=id).first().snapshot
		badge_token = Code_Climate.query.filter_by(id=id).first().badge_token
	except:
		snapshot_id = badge_token = None

	data = code_climate.get_issues_data(id, snapshot_id, language)

	cc_data = {'github_slug': github_slug, 'badge_token': badge_token}
	summary_data = code_climate.get_issue_overview(data)

	return render_template('quality_issues.html', issue_data=data, summary_data=summary_data, cc_data=cc_data)

@bp.route('/compare', methods=['GET', 'POST'])
@login_required
def compare():

	if request.method == 'POST':
		selected_repositories = []
		for repo in request.form['selected'].split(','):
			selected_repositories.append(repo)

		# quality over time
		quality_scores = analysis_functions.get_quality_scores(selected_repositories)
		quality_change_per_version = analysis_functions.caluculate_quality_over_time(quality_scores)
		
		versions=[]
		change_in_quality_score_per_version=[]
		for _, quality_change in quality_change_per_version.items():
			for idx in range(len(quality_change)):
				versions.append(idx)
				change_in_quality_score_per_version.append(quality_change[idx])

		quality_over_time_correlation = analysis_functions.correlate(versions, change_in_quality_score_per_version)

		# quality vs code size
		quality_vs_code_size = analysis_functions.calculate_quality_vs_code_size(selected_repositories)

		code_size_per_repo_version = analysis_functions.get_code_size_per_version(selected_repositories)
		loc_change_between_versions_per_repo = analysis_functions.calculate_change_in_code_size_between_versions(code_size_per_repo_version)
		
		code_sizes=[]
		for _, version_sizes in loc_change_between_versions_per_repo.items():
			for idx in range(len(version_sizes)):
				code_sizes.append(version_sizes[idx])

		quality_vs_code_size_correlation = analysis_functions.correlate(code_sizes, change_in_quality_score_per_version)

		# quality vs contributors
		total_contributors, median_quality_score  = analysis_functions.caluculate_quality_vs_contributors(selected_repositories)
		quality_vs_contributors_correlation = analysis_functions.correlate(total_contributors, median_quality_score)
		
		# quality vs change-frequency
		median_quality_per_repo = analysis_functions.calculate_median_quality_per_repo(quality_scores)
		avg_monthly_commits_per_repo = analysis_functions.calculate_avg_monthly_commits_per_repo(selected_repositories)		

		change_freq = [stat[1] for stat in sorted(avg_monthly_commits_per_repo)]
		quality_change = [stat[1] for stat in sorted(median_quality_per_repo)]
		
		quality_vs_change_freq_correlation = analysis_functions.correlate(change_freq, quality_change)

		return render_template('compare.html', \
			quality_change_over_time=quality_change_per_version, quality_over_time_correlation=quality_over_time_correlation, \
			code_sizes=code_sizes, quality_vs_code_size_correlation=quality_vs_code_size_correlation, \
			quality_vs_contributors=[total_contributors, median_quality_score], quality_vs_contributors_correlation=quality_vs_contributors_correlation, \
			quality_vs_change_freq=[change_freq, quality_change], quality_vs_change_freq_correlation=quality_vs_change_freq_correlation, \
			quality_scores=quality_scores\
			)

	return redirect(url_for('main.downloads'))

@bp.route('/discover_filters', methods=['GET', 'POST'])
@login_required
def discover_filters():
	form = forms.FiltersForm()
	return render_template('change_filters.html', form=form)

@bp.route('/discover', methods=['GET', 'POST'])
@login_required
def discover():
	form = forms.FiltersForm()

	if request.method == 'POST' and form.validate_on_submit():
		filters = request.form.to_dict(flat=True)
	elif form.errors:
		flash(form.errors.itervalues().next(), 'danger')
		return redirect(url_for('main.discover_filters'))
	else:
		filters = {
		'language' : 'java',
		'created_before' : (date.today() - timedelta(days=3*365)).isoformat(),		# created at least 3 years ago
		'updated_after' : (date.today() - timedelta(days=31)).isoformat(),		# updated in the last 31 days
		'min_size' : '1000',
		'max_size' : '5000'
		}

	api_url = '{}search/repositories?q=+language:{}+is:public+size:{}..{}+created:<={}+pushed:>={}&per_page=50&sort:updated'\
	.format(github_api_url_base, filters['language'], filters['min_size'], filters['max_size'], \
		filters['created_before'], filters['updated_after'])

	headers = {'Authorization': 'token %s' % get_user_token()}

	response = requests.get(api_url, headers=headers)
	session = requests.Session()

	repositories = {}

	if response.status_code == 200:
		if response.links:
			# results are paginated
			num_pages = int(response.links["last"]['url'].split('&page=')[1])
			page_limit = 3 # 150 max results

			if page_limit < num_pages:
				limit = page_limit
			else:
				limit = num_pages
		else:
			limit = 1

		for page_num in range(1, limit+1):
			data = session.get(api_url + '&page=' + str(page_num)).json()
			data = parse_search_data(data)
			repositories.update(data)

	else:
		flash(response.text, 'danger')
		return redirect(url_for('main.index'))

	return render_template('discover.html', repositories=repositories, filters=filters)
