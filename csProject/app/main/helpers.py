import sys, json, os, requests, re, time, stat
from flask import current_app as app, abort
from flask_login import current_user
from ..models import OAuth, Code_Climate, Archive
from ..extensions import db
from dateutil.relativedelta import relativedelta
from datetime import date
from ..constants import github_api_url_base, subordinate_username

def get_user_token():
	''' Returns the GitHub OAuth token of the current authenticated user '''
	token = db.session.query(OAuth).filter(OAuth.user_id==current_user.id).first().token['access_token']
	if token:
		return token
	return None

def format_repo_stats(repo_stats):
	''' Returns provided statistics in format suitable for google chart rendering 
	by removing non-numerical stats '''
	for repo,stat in repo_stats.items():
		del stat['description']
		del stat['owner']
	
	return repo_stats

def chart_format_repo_stats(repo_stats):
	''' Removes statistical values that would skew the chart used to draw them '''
	formatted = ['Statistic']
	for repo, stats in repo_stats.iteritems():
		formatted.append(repo)
	ChartFormatted = [formatted]

	# stats = ['stargazers', 'watchers', 'subscribers', 'size (KB)', 'open issues', 'forks']
	stats = ['stargazers', 'subscribers',  'open issues', 'forks']
	for s in stats:
		stat = [s]
		for repo, values in repo_stats.iteritems():
			for k,v in values.iteritems():
				if k == s:
					stat.append(v)
		ChartFormatted.append(stat)
		
	return ChartFormatted

def get_chart_data(all_data):
	''' Returns a dict correctly formatted for google bar chart '''
	all_charts = {}

	for metric in ['cbo', 'wmc', 'dit', 'rfc', 'lcom']:

		chart_data = [['Class', metric.upper(), 'Average']]
		avg = all_data['ck_metrics'][metric]

		for _class, class_data in all_data['class_data'].iteritems():
			bar = [_class, class_data[metric], avg]
			chart_data.append(bar)
			
		all_charts[metric] = chart_data

	return all_charts

def create_archive(url):
	''' Creates an empty directory for the given repositry to be downloaded into. Returns the file path '''
	repo_name = os.path.basename(os.path.normpath(url)).strip().replace('_','-')
	owner = url.rsplit('/', 2)[-2]
	cwd = os.path.dirname(os.getcwd())
	utc_now = str(int(time.time()))

	path = os.path.join(cwd, 'archive', owner + '_' + repo_name.replace('.git','').strip(), utc_now)

	if not os.path.exists(path):
		os.makedirs(path)

	return path

def get_repo_dir(repository, timestamp):
	''' Returns the full file path for a given repository or None if not found '''
	path = db.session.query(Archive).filter(Archive.name==repository).filter(Archive.timestamp==timestamp).first()
	if not path:
		return None

	repo_dir = os.path.join(os.path.dirname(os.getcwd()), path.archive_folder)
	return repo_dir

def get_repo_language(slug, token):
	''' Returns the language of a given repository or None if not found'''
	api_url = '{}repos/{}'.format(github_api_url_base, slug.lower())

	headers = {'Authorization': 'token %s' % token}
	response = requests.get(api_url, headers=headers)

	if response.status_code == 200:
		data = json.loads(response.text or response.content)
		return data['language']
	else:
		return None

def create_json_file(url):
	''' Creates file required to add a repository to code climate '''
	data = {
		"data": {
			"type": "repos",
			"attributes": {
				"url": "" + url + ""
			}
		}
	}

	with open('code_climate_add_repo.json', 'w') as outfile:
		json.dump(data, outfile)

	return 'code_climate_add_repo.json'

def delete_file(path):
	''' Deletes file at given path, if exists '''
	if os.path.exists(path):
		os.remove(path)

# def get_time_intervals(time_series):
def get_time_intervals(start, end):
	''' Returns a list of dates at similar intervals between (and including) the start and end dates provided '''
	intervals = []
	num_intervals = 5
	
	delta = end - start
	difference = delta.days
	
	if difference < 4:
		return [start, end]

	days_between_intervals = int(round(difference/float(num_intervals-1)))

	intervals.append(start)
	for i in range(1,num_intervals-1):
		days_after = i * days_between_intervals
		intervals.append(start + relativedelta(days=days_after))
	intervals.append(end)

	return intervals

def get_sha(github_slug, timestamp, user_token):
	''' Returns the sha hash of the commit of a repository closest to the timestamp provided '''
	headers = {'Authorization': 'token %s' % user_token}
	api_url = '{}repos/{}/commits?until={}T23:59:59Z'.format(github_api_url_base, github_slug, timestamp.isoformat())

	response = requests.get(api_url, headers=headers)
	resp_data = json.loads(response.text or response.content)

	if response.status_code == 200:
		try:
			return resp_data[0]['sha']
		except:
			return None
	
	return None

def walklevel(some_dir, level):
	''' Returns each directory path exactly x directories below the provided directory (where x = level). 
	Ref: https://stackoverflow.com/questions/229186/os-walk-without-digging-into-directories-below '''
	low_level_dirs = []
	some_dir = some_dir.rstrip(os.path.sep)
	num_sep = some_dir.count(os.path.sep)

	for root, dirs, files in os.walk(some_dir):
		num_sep_this = root.count(os.path.sep)
	
		if num_sep + level <= num_sep_this:
			yield root
			del dirs[:]

def parse_search_data(data):
	''' Returns a dict in the format "slug" : "url" for each result of github search query data '''
	repositories = {}

	for repository in data['items']:
		url = repository['clone_url']
		github_slug = repository['full_name']
		repositories[github_slug] = url
	
	return repositories

def get_failed_registry():
	return [u'f8658681-6eee-46c3-a197-fe49202369f3', u'c3f935f0-ddc1-400c-86ac-b8edb14f2a05', u'874bf02b-c7c4-4f7b-b4ca-65031919c68d', u'47341bb9-996a-4dd5-9277-12168c3df00f', u'1a6686a4-2f0c-467a-81eb-2c2113784520', u'e58447bd-c2cb-4c91-bb21-9fc281c75c81', u'c9857e19-f096-498c-9ee5-1be1e5372ab4']
