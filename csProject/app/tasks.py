from main.helpers import create_archive, get_time_intervals, get_sha, get_user_token, delete_file, get_repo_language, create_json_file
from constants import github_api_url_base, codeclimate_token, subordinate_token as s_token, subordinate_username as s_user
from main.data_dict import ck_thresholds
import pygit2
import git
import requests, os, shutil, json
from datetime import timedelta, date
from app import create_app, db
from models import Archive, CK, CK_Class, Code_Climate, Github_Stats
import os, subprocess, re
import pandas as pd
import dateutil.parser
from numpy import mean

app = create_app()
app.app_context().push()

def store_archive_info(url, timestamp, archive_folder, token):
	''' Stores details about an archived repository into the archive table if not exists.
	Returns None if invalid github slug '''
	slug = re.sub(r"http(s)?://github\.com/",'', url).replace('.git','').strip()

	try:
		owner, name = slug.split('/')
	except ValueError:
		return None

	language = get_repo_language(slug, token)

	relative_folder = os.path.join(*archive_folder.rsplit(os.path.sep, 3)[-3:]) # last 3 parts of archive path
	relative_folder = os.path.join(relative_folder, str(timestamp)) # last 3 parts of archive path

	exists = db.session.query(Archive).filter_by(archive_folder=archive_folder).first()
	if not exists:
		archive = Archive(url=url, name=name, owner=owner, github_slug=slug, \
			language=language, timestamp=str(timestamp), archive_folder=relative_folder)
		db.session.add(archive)

	db.session.commit()
	return slug

def archive_repository(download_folder, url, github_slug, timestamp, token):
	''' Download previous versions of the chosen repository at the specified
	intervals and commit these to subordinate account for future analysis '''
	sha = get_sha(github_slug, timestamp, token)

	if sha:
		oid = pygit2.Oid(hex=sha)
		try:
			repo = pygit2.clone_repository(url, download_folder, bare=False)
			init_repo(oid, download_folder)
			u_name = github_slug.split('/')[1] + str(timestamp).replace('-','')
			bare_url = create_bare_repo(u_name)
			if bare_url:
				commit_files(bare_url, download_folder)
		except Exception as ex:
			os.rmdir(download_folder)
			return False
	else:
		return False

	return True # Successfully archived

def add_repo_to_cc(github_slug, timestamp):
	''' Returns the code climate generated identifier after adding a project to code climate.
	Returns None if project cannot be added to code climate '''
	repo_url = 'https://github.com/' + github_slug
	api_url = 'https://api.codeclimate.com/v1/github/repos'

	headers = {
		'Accept': 'application/vnd.api+json', 
		'Content-Type': 'application/vnd.api+json', 
		'Authorization': 'Token token={}'.format(codeclimate_token)
	}

	filename = create_json_file(repo_url)

	with open(filename, 'rb') as f:
		response = requests.post(api_url, headers=headers, data=f.read())

 	delete_file(filename)

	resp_data = json.loads(response.text or response.content)
	if response.status_code == 201:
		codeclimate_id = resp_data['data']['id']
	else:
		print resp_data['errors'][0]['detail']
		return
	
	store_cc_details(codeclimate_id, github_slug, timestamp)

	return codeclimate_id

def store_cc_details(cc_id, github_slug, timestamp):
	''' Stores the initial code climate details for a repository. Full details are added later when 
	code climate has completed analysis. '''
	exists = db.session.query(Code_Climate).filter(Code_Climate.id == cc_id).first()
	
	if not exists:
		# get archive_id for link to archive table
		repo_name = github_slug.replace(s_user + '/','')[:-8] # cut off owner and last 8 digits (timestamp)
		archive_id = db.session.query(Archive).filter(Archive.name == repo_name).filter(Archive.timestamp == timestamp).first().id

		code_climate_details = Code_Climate(id=cc_id, archive_id=archive_id, github_slug=github_slug, timestamp=timestamp)
		db.session.add(code_climate_details)
		db.session.commit()

def calculate_ck_class_metrics(repo_folder, timestamp):
	''' Runs the CK metrics calulcator and stores the results for each class in the project before calling
	function which calculates overall quality '''
	archive_folder = os.path.join(repo_folder.replace(os.path.dirname(os.getcwd()), ''), str(timestamp))[1:]
	project_dir = os.path.join(repo_folder, str(timestamp))
	subprocess.call(['java', '-jar', 'calculate_ck_metrics.jar', project_dir])

	data = pd.read_csv('class.csv')
	metrics = ['cbo', 'wmc', 'dit', 'rfc', 'lcom']
	archive_id = db.session.query(Archive).filter_by(archive_folder=archive_folder).first().id
	ck = {'archive_id': archive_id, 'classes':None, 'cbo':None, 'wmc':None, 'rfc':None, 'dit':None, 'lcom':None, 'quality_score': None}

	ck = CK(**ck)
	db.session.add(ck)
	db.session.flush()

	for index, row in data.iterrows():
		ck_class = CK_Class(ck_id=ck.id, name=row['class'], cbo=row['cbo'], wmc=row['wmc'], \
			dit=row['dit'], rfc=row['rfc'], lcom=row['lcom'])
		db.session.add(ck_class)
	
	delete_file('class.csv')
	calculate_quality(ck)

	db.session.commit()

def calculate_quality(record):
	''' Calculates project-level metric scores and overall quality score based on class-level scores. Returns 
	None if the project does not have enough classes for accurate analysis (less than 5) '''
	classes = db.session.query(CK_Class).filter(CK_Class.ck_id==record.id).all()
	num_classes = len(classes)
	record.classes = num_classes

	# ensure project is large enough to analyse
	if num_classes < 5:
		db.session.rollback()
		return

	for metric, threshold in ck_thresholds.items():
		total_deviance = 0

		for _class in classes:
			class_metric_value = getattr(_class, metric)
			if class_metric_value > threshold:
				total_deviance += class_metric_value - threshold

		metric_score = -1 * ((float(num_classes)*total_deviance) / (total_deviance + num_classes + 1))
		setattr(record, metric, metric_score)

	weighting = 1./9
	record.quality_score = (num_classes 
		+ 4*weighting*record.cbo 
		+ 2*weighting*record.wmc 
		+ 2*weighting*record.rfc 
		+ weighting*record.lcom) \
		/ num_classes

	db.session.commit()

def count_contributors(github_slug, from_, to, token):
	''' Stores statistics obtained from the github API for a repository between 2 specified dates.
	Counts number of commits and unique contributors to a repository between the dates '''
	headers = {'Authorization': 'token %s' % token}

	session = requests.Session()

	contributors = {} # use dict to avoid counting duplicates

	api_url = '{}repos/{}/commits?since={}&until={}&per_page=100'\
	.format(github_api_url_base, github_slug, from_.isoformat(), (to + timedelta(days=1)).isoformat())  # inclusive of last interval

	response = session.get(api_url, headers=headers) # dont catch potential error - let job fail and it will be picked up by run_archive_task

	response_data = json.loads(response.text or response.content)

	for commit in response_data:
		username = commit['commit']['author']['email']
		contributors[username] = None # assign dummy value to newly created key

	# access paginated response data
	if response.links:
		num_pages = int(response.links["last"]['url'].split('&page=')[1])
		for page_num in range(2, num_pages+1):
			next_page = session.get(api_url + '&page=' + str(page_num), headers=headers).json()

			for commit in next_page:
				username =  commit['commit']['author']['email']
				contributors[username] = None

	num_contributors = len(contributors.keys())
	print github_slug, num_contributors
	return num_contributors
	# store_github_statistics(github_slug, from_, to, num_contributors)

def store_github_statistics(slug, from_, to, contributors, change_freq):
	''' Stores data extracted from GitHub API if not exists and if the project is archived. Average monthly commits is stored later
	once the average has been calculated for all versions of the repository '''
	from_ = from_.strftime("%Y-%m-%d")
	to = to.strftime("%Y-%m-%d")

	exists = db.session.query(Github_Stats).filter(Github_Stats.slug == slug)\
	.filter(Github_Stats.from_ == from_)\
	.filter(Github_Stats.to == to)\
	.first()

	if not exists:
		archived = db.session.query(Archive)\
		.filter(Archive.github_slug==slug)\
		.first()

		if archived:
			record = Github_Stats(archive_id=archived.id, slug=slug, from_=from_, to=to, contributors=contributors, avg_monthly_commits=change_freq)
			db.session.add(record)
			db.session.commit()

def calculate_change_frequency(slug, first_interval, last_interval, token):
	headers = {'Authorization': 'token %s' % token}
	session = requests.Session()

	commits_per_month = []

	until = first_interval
	end_date = last_interval + timedelta(days=31)

	while (until <= end_date):
		from_ = until
		until = date(until.year, until.month, until.day) + timedelta(days=31)

		api_url='https://api.github.com/repos/{}/commits?since={}T00:00:00&until={}T00:00:00&per_page=100'.format(slug, from_, until)
		response = session.get(api_url, headers=headers) # dont catch potential error - let job fail and it will be picked up by run_archive_task

		if response.status_code != 200:
			return 'error' # commits_per_month += 0?

		response_data = json.loads(response.text or response.content)

		commits_this_month = len(response_data)

		if response.links:
			num_pages = int(response.links["last"]['url'].split('&page=')[1])

			for page_num in range(2, num_pages+1):
				next_page = session.get(api_url + '&page=' + str(page_num), headers=headers).json()	
				commits_this_month += len(next_page)

		commits_per_month.append(commits_this_month)
	
	mean_commits_per_month = mean(commits_per_month)
	
	return mean_commits_per_month
	

def init_repo(oid, download_path):
	''' Revert repo to the state it was in at the specified timestamp (oid) and 
	remove connection to src repository before committing for analysis '''
	repo = pygit2.init_repository(download_path, bare=False)
	repo.reset(oid, pygit2.GIT_RESET_HARD)
	shutil.rmtree(os.path.join(download_path, '.git'))

def create_bare_repo(repo_name):
	''' Create empty repository with descriptive name on subordinate github account.
	Returns url of new repostiory or None if unsuccessful '''
	api_url = '{}user/repos'.format(github_api_url_base)
	headers = {'Authorization': 'token %s' % s_token}
	data = {"name": repo_name, "private": False}
	response = requests.post(api_url, headers=headers, json=data)

	if response.status_code == 201:
		print 'Created new repository {}'.format(repo_name)
		return json.loads(response.text or response.content)['ssh_url']
	else:
		print response.text

def commit_files(bare_url, download_path):
	''' Commit and push files to repository on subordinate account for future analysis '''
	file_list = []
	for (dirpath, dirnames, filenames) in os.walk(download_path):
		if '.git' not in dirpath:
			file_list += [os.path.join(dirpath, file) for file in filenames]
	
	try:
		repo = git.Repo.init(download_path)
		repo.index.add(file_list)
		repo.index.commit(message='Initial commit')
		repo.git.push(bare_url, 'HEAD:main')
	except:
		print 'Failed to commit to {}'.format(bare_url)
	print 'Committed successfully to {}'.format(bare_url)