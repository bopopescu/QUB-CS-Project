from flask import flash
from .helpers import create_json_file, delete_file#, update_codeclimate_table
from ..models import Code_Climate, Archive
from ..extensions import db
from ..constants import codeclimate_token, subordinate_username
from .data_dict import file_ext_dict
from datetime import timedelta, date
from collections import defaultdict
import requests, json, humanize

def get_data(repo_id, timestamp):
	'''' Fetches and commits to db the results of code climate analysis. 
	Returns empty dict if code climate have not finished analysis yet '''
	response = requests.get('https://api.codeclimate.com/v1/repos/'+str(repo_id))
	data = {}

	if response.status_code == 200:
		resp_data = json.loads(response.text or response.content)
		try:
			snapshot_id = resp_data['data']['relationships']['latest_default_branch_snapshot']['data']['id']
			badge_token = resp_data['data']['attributes']['badge_token']
		except TypeError:
			flash('Analysis incomplete. Please try again later', 'warning')
			return 'data'

		if snapshot_id and badge_token:
			response = requests.get('https://api.codeclimate.com/v1/repos/{}/snapshots/{}'.format(repo_id,snapshot_id))
			resp_data = json.loads(response.text or response.content)
			data['id'] = repo_id
			data['lines_of_code'] = resp_data['data']['attributes']['lines_of_code']
			data['issues_count'] = resp_data['data']['meta']['issues_count']
			data['issues_remediation'] = humanize.naturaltime(timedelta(minutes=resp_data['data']['meta']['measures']['remediation']['value'])).replace(' ago','')
			data['tech_debt_ratio'] = str(resp_data['data']['meta']['measures']['technical_debt_ratio']['value']) + '%'
			data['tech_debt_ratio'] = "%.2f%%" % resp_data['data']['meta']['measures']['technical_debt_ratio']['value']
			data['tech_debt_remediation'] = humanize.naturaltime(timedelta(minutes=resp_data['data']['meta']['measures']['technical_debt_ratio']['meta']['remediation_time']['value'])).replace(' ago','')
			data['tech_debt_implementation'] = humanize.naturaltime(timedelta(minutes=resp_data['data']['meta']['measures']['technical_debt_ratio']['meta']['implementation_time']['value'])).replace(' ago','')
			data['snapshot'] = snapshot_id
			data['badge_token'] = badge_token
			data['timestamp'] = timestamp

			store_cc_analysis_data(repo_id, data)

	return data

def get_issues_data(repo_id, snapshot_id, language):
	''' Returns a dict containing code smells identified by code climate for each file 
	(if the file matches the target language). Returns empty dict if language is not supported '''
	data = defaultdict(list)
	try:
		file_extensions = file_ext_dict[language.lower()]
	except:
		flash('Language not supported', 'danger')
		return data

	url = 'https://api.codeclimate.com/v1/repos/{}/snapshots/{}/issues'.format(repo_id, snapshot_id)
	for resp_data in get_paginated_data(url):
		
		if 'errors' in resp_data.keys():
			return data
		
		for issue in resp_data['data']:
			file = issue['attributes']['constant_name']
			fingerprint = issue['attributes']['fingerprint']

			if file.endswith(tuple(file_extensions)):
				issue_data = {
				'fingerprint': issue['attributes']['fingerprint'],
				'category': issue['attributes']['categories'][0],
				'description': issue['attributes']['description'],
				'type' : issue['attributes']['engine_name'],
				'start_line' : issue['attributes']['location']['start_line'],
				'end_line' : issue['attributes']['location']['end_line'],
				'severity' : issue['attributes']['severity']
				}
				data[file].append(issue_data)

	return data

def get_issue_overview(data):
	''' Reutns a summary of code smells identified by code climate to populate the jumbotron on 
	the /quality_issues route. Groups the number of issues by category, type and severity.'''
	summary_data = {}
	files_with_issues = len(data.keys())
	summary_data['files_with_issues'] = files_with_issues

	# count issues for each category
	for metric in ('category', 'type', 'severity'):
		totals = {}
		
		for file in data:
			for issue in data[file]:
				metric_name = metric
				totals.setdefault(issue[metric_name].lower(), 0)
				totals[issue[metric].lower()] += 1
		
		summary_data[metric] = totals

	return summary_data

def store_cc_analysis_data(repo_id, data):
	''' Stores the results of code climate analysis '''
	exists = db.session.query(Code_Climate).filter(Code_Climate.id == repo_id).first()

	if exists:
		db.session.query(Code_Climate).filter(Code_Climate.id == repo_id).update(data)
		db.session.commit()

def get_paginated_data(url):
	''' Helper function that returns each page for paginated API responses from code climate API '''
	session = requests.Session()

	try:
		first_page = session.get(url).json()
	except requests.ConnectionError:
		flash('Failed to obtain issue data.', 'danger')
		return

	yield first_page
	num_pages = first_page['meta']['total_pages']

	for page_num in range(2, num_pages + 1):
		next_page = session.get(url,  data={'page[number]':page_num}).json()
		yield next_page

def get_snapshot(repo_id):
	''' Returns the snapshot ID of the latest snapshot for a repo from code climate. The snapshot ID 
	identifies the most recent quality analysis. Reutns none if analysis is incomplete '''
	headers = {
		'Authorization': 'Token token={}'.format(codeclimate_token)
	}
	response = requests.get('https://api.codeclimate.com/v1/repos/'+repo_id, headers=headers)

	if response.status_code == 200:
		resp_data = json.loads(response.text or response.content)
		try:
			snapshot_id = resp_data['data']['relationships']['latest_default_branch_snapshot']['data']['id']
		except:
			return None
	else:
		return None

	return snapshot_id

def get_loc(repo_id):
	''' Helper function that returns the number of lines of code for repos that have been added to code climate'''
	headers = {
		'Authorization': 'Token token={}'.format(codeclimate_token)
	}
	snapshot_id = get_snapshot(repo_id)

	if not snapshot_id:
		return None

	response = requests.get('https://api.codeclimate.com/v1/repos/{}/snapshots/{}'.format(repo_id,snapshot_id), headers=headers)
	resp_data = json.loads(response.text or response.content)
	loc = resp_data['data']['attributes']['lines_of_code']

	return loc