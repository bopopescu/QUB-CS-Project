import unittest
from flask import current_app as app
from base import BaseTestCase
from app.extensions import db
from app.models import Archive, User, OAuth
from app.constants import subordinate_username
from app.main.helpers import *
from datetime import datetime, date, timedelta
import os
import shutil
from testdata import TestUser

class TestHelpers(BaseTestCase):

	def set_up(self):
		''' Authenticate a user for testing '''
		with app.test_request_context():
			@app.login_manager.request_loader
			def load_user_from_request(request):
				return self.test_user

	''' Ensure that the correct token is returned for an authenticated user.
	Note: this method is unreachable for an unauthenticated user '''
	def test_get_user_token_user_logged_in(self):
		self.set_up()
		expected = self.test_user.token['access_token']
		result = get_user_token()
		self.assertEqual(result, expected)

	''' Ensure that data returned is in the expected format i.e. numerical stats only'''
	def test_format_repo_stats(self):
		before_formatting = { 'example_repo':  { \
			'stargazers' : 1, \
			'watchers' : 2, \
			'subscribers' : 3, \
			'size' : 4, \
			'owner' : 'jbloggs', \
			'open issues' : 5, \
			'forks' : 6, \
			'description' : 'thisisatestrepo', \
			'branches' : 7 \
		}}
		expected = { 'example_repo': { \
			'stargazers' : 1, \
			'watchers' : 2, \
			'subscribers' : 3, \
			'size' : 4, \
			'open issues' : 5, \
			'forks' : 6, \
			'branches' : 7 \
		}}
		result = format_repo_stats(before_formatting)
		self.assertEqual(result, expected)
	
	''' Ensure that data returned only contains the metrics we want to display on the chart'''
	def test_chart_format_repo_stats(self):
		before_formatting = { 'example_repo':  { \
			'stargazers' : 1, \
			'watchers' : 2, \
			'subscribers' : 3, \
			'size' : 4, \
			'owner' : 'jbloggs', \
			'open issues' : 5, \
			'forks' : 6, \
			'description' : 'thisisatestrepo', \
			'branches' : 7 \
		}}
		expected = [['Statistic', 'example_repo'], \
		['stargazers', 1], ['subscribers', 3], \
		['open issues', 5], ['forks', 6]]
		result = chart_format_repo_stats(before_formatting)
		self.assertEqual(result, expected)

	''' Ensure that 5 entries are added to the database when url uses http protocol '''
	# def test_store_archive_info_http_url(self):
	# 	url = 'http://github.com/mytestrepo/httptestrepo.git'
	# 	start = date.today()
	# 	end = start + timedelta(days=10)
	# 	time_intervals = get_time_intervals(start, end)
	# 	archive_folder = os.path.join('mytestrepo', 'httptestrepo', 'folder')

	# 	store_archive_info(url, time_intervals, archive_folder)

	# 	rows_added = db.session.query(Archive).filter_by(url=url).all()
	# 	self.assertEqual(len(rows_added), 5)

	# 	for timestamp in time_intervals:
	# 		expected_archive_folder = os.path.join(archive_folder, str(timestamp))
	# 		exists = db.session.query(Archive).filter_by(archive_folder=expected_archive_folder).first()
	# 		self.assertIsNotNone(exists)

	# 		expected_slug = 'mytestrepo/httptestrepo'
	# 		self.assertEqual(exists.github_slug, expected_slug)
	
	# ''' Ensure that 5 entries are added to the database when url uses https protocol '''
	# def test_store_archive_info_https_url(self):
	# 	url = 'https://github.com/mytestrepo/httpstestrepo.git'
	# 	start = date.today()
	# 	end = start + timedelta(days=10)
	# 	time_intervals = get_time_intervals(start, end)
	# 	archive_folder = os.path.join('mytestrepo', 'httpstestrepo', 'folder')

	# 	store_archive_info(url, time_intervals, archive_folder)

	# 	rows_added = db.session.query(Archive).filter_by(url=url).all()
	# 	self.assertEqual(len(rows_added), 5)
		
	# 	for timestamp in time_intervals:
	# 		expected_archive_folder = os.path.join(archive_folder, str(timestamp))
	# 		exists = db.session.query(Archive).filter_by(archive_folder=expected_archive_folder).first()
	# 		self.assertIsNotNone(exists)

	# 		expected_slug = 'mytestrepo/httpstestrepo'
	# 		self.assertEqual(exists.github_slug, expected_slug)

	# ''' Ensure that 5 entries are added to the database when url contains whitespace '''
	# def test_store_archive_info_url_with_whitespace(self):
	# 	url = 'https://github.com/mytestrepo/withwhitespace.git  '
	# 	start = date.today()
	# 	end = start + timedelta(days=10)
	# 	time_intervals = get_time_intervals(start, end)
	# 	archive_folder = os.path.join('mytestrepo', 'withwhitespace', 'folder')

	# 	store_archive_info(url, time_intervals, archive_folder)

	# 	rows_added = db.session.query(Archive).filter_by(url=url).all()
	# 	self.assertEqual(len(rows_added), 5)
		
	# 	for timestamp in time_intervals:
	# 		expected_archive_folder = os.path.join(archive_folder, str(timestamp))
	# 		exists = db.session.query(Archive).filter_by(archive_folder=expected_archive_folder).first()
	# 		self.assertIsNotNone(exists)

	# 		expected_slug = 'mytestrepo/withwhitespace'
	# 		self.assertEqual(exists.github_slug, expected_slug)
	
	# ''' Ensure that no addditional entries are made to the database if they already exist '''
	# def test_store_archive_info_already_exists(self):
	# 	url = 'https://github.com/mytestrepo/withwhitespace.git  '
	# 	start = date.today()
	# 	end = start + timedelta(days=10)
	# 	time_intervals = get_time_intervals(start, end)
	# 	archive_folder = os.path.join('mytestrepo', 'withwhitespace', 'folder')

	# 	store_archive_info(url, time_intervals, archive_folder)

	# 	rows_added = db.session.query(Archive).filter_by(url=url).all()
	# 	self.assertEqual(len(rows_added), 5)
		
	# 	for timestamp in time_intervals:
	# 		expected_archive_folder = os.path.join(archive_folder, str(timestamp))
	# 		exists = db.session.query(Archive).filter_by(archive_folder=expected_archive_folder).first()
	# 		self.assertIsNotNone(exists)

	# 		expected_slug = 'mytestrepo/withwhitespace'
	# 		self.assertEqual(exists.github_slug, expected_slug)	

	# ''' Ensure that no entries are made to the database if the url is invalid '''
	# def test_store_archive_info_already_exists(self):
	# 	url = 'https://github.com/mytestrepo/invalid/url.git  '
	# 	start = date.today()
	# 	end = start + timedelta(days=10)
	# 	time_intervals = get_time_intervals(start, end)
	# 	archive_folder = os.path.join('mytestrepo', 'invalid', 'url', 'folder')

	# 	store_archive_info(url, time_intervals, archive_folder)

	# 	rows_added = db.session.query(Archive).filter_by(url=url).all()
	# 	self.assertEqual(len(rows_added), 0)

	''' Ensure that archive directory is created if url contains whitespace. '''
	def test_create_archive_with_whitespace(self):
		url = 'https://github.com/mytestrepo/testrepowithwhitespace '
		result = create_archive(url)
		self.assertTrue(os.path.isdir(result))

		root_created = os.path.dirname(result)
		# ensure files aren't deleted from the actual application archive
		self.assertFalse(root_created.endswith('CSC3002-Project{}archive'.format(os.path.sep)))
		shutil.rmtree(root_created)
		self.assertFalse(os.path.isdir(root_created))

	''' Ensure that archive directory is created if url contains .git extension. '''
	def test_create_archive_with_git_ext(self):
		url = 'https://github.com/mytestrepo/testrepowithgitext.git'
		result = create_archive(url)
		self.assertTrue(os.path.isdir(result))

		root_created = os.path.dirname(result)
		# ensure files aren't deleted from the actual application archive
		self.assertFalse(root_created.endswith('CSC3002-Project{}archive'.format(os.path.sep)))
		shutil.rmtree(root_created)
		self.assertFalse(os.path.isdir(root_created))

	''' Ensure that archive directory is created with valid url '''
	def test_create_archive_without_git_ext(self):
		url = 'https://github.com/mytestrepo/testrepowithoutgitext'
		result = create_archive(url)
		self.assertTrue(os.path.isdir(result))
		
		root_created = os.path.dirname(result)
		# ensure files aren't deleted from the actual application archive
		self.assertFalse(root_created.endswith('CSC3002-Project{}archive'.format(os.path.sep)))
		shutil.rmtree(root_created)
		self.assertFalse(os.path.isdir(root_created))

	''' Ensure that archive directory is created when url contains an underscore. 
	Repo names may contain underscores but these should be replaced with hyphens as underscore 
	char is used to separate owner from repo name in the directory name'''
	def test_create_archive_with_underscore(self):
		url = 'https://github.com/mytestrepo/test_repo_with_underscore'
		result = create_archive(url)
		self.assertTrue(os.path.isdir(result))

		num_underscores_in_path = result.count('_')
		archive_root_dir = os.path.join(os.path.dirname(os.getcwd()), 'archive')
		num_underscores_in_archive_root_dir = archive_root_dir.count('_')
		expected_num_underscores = num_underscores_in_path - num_underscores_in_archive_root_dir
		self.assertEqual(num_underscores_in_path, expected_num_underscores)
		
		root_created = os.path.dirname(result)
		# ensure files aren't deleted from the actual application archive
		self.assertFalse(root_created.endswith('CSC3002-Project{}archive'.format(os.path.sep)))
		shutil.rmtree(root_created)
		self.assertFalse(os.path.isdir(root_created))

	''' Ensure that path to archive directory is returned when the directory already exists '''
	def test_create_archive_already_exists(self):
		url = 'https://github.com/GaryMcPolin/ChurchillMouldingsLtd.git'
		result = create_archive(url)
		self.assertTrue(os.path.isdir(result))
		result = create_archive(url)
		self.assertTrue(os.path.isdir(result))
		
	''' Ensure correct repository archive folder path is returned with valid repo name and timestamp. 
	Note: Method can never be reached if either argument is none '''
	def test_get_repo_dir_found(self):
		repo = 'myrepo'
		timestamp = '1973-01-01'
		archive_folder = 'archive/jbloggs_myrepo/1551184837/1973-01-01'

		archive_details = Archive(url='https://github.com/myrepo.git' , owner='jbloggs', name=repo, github_slug='jbloggs/myrepo', timestamp=timestamp, archive_folder=archive_folder)
		db.session.add(archive_details)
		db.session.commit()

		result = get_repo_dir(repo, timestamp)
		expected = os.path.join(os.path.dirname(os.getcwd()), archive_folder)
		self.assertEqual(result, expected)

	''' Ensure nothing is returned with invalid repo name and valid timestamp. 
	Note: Method can never be reached if either argument is none '''
	def test_get_repo_dir_repo_name_not_found(self):
		repo = 'myotherrepo'
		timestamp = '1973-01-01'

		result = get_repo_dir(repo, timestamp)
		expected = None
		self.assertEqual(result, expected)

	''' Ensure nothing is returned with valid repo name and invalid timestamp. 
	Note: Method can never be reached if either argument is none '''
	def test_get_repo_dir_timestamp_not_found(self):
		repo = 'myrepo'
		timestamp = '2019-01-01'

		result = get_repo_dir(repo, timestamp)
		expected = None
		self.assertEqual(result, expected)

	''' Ensure nothing is returned with invalid repo name and invalid timestamp. 
	Note: Method can never be reached if either argument is none '''
	def test_get_repo_dir_neither_found(self):
		repo = 'myotherrepo'
		timestamp = '2019-01-01'

		result = get_repo_dir(repo, timestamp)
		expected = None
		self.assertEqual(result, expected)

	''' Ensure nothing is returned when using SQL injection. 
	Note: Method can never be reached if either argument is none '''
	def test_get_repo_dir_sql_injection(self):
		repo = '%'
		timestamp = '%'

		result = get_repo_dir(repo, timestamp)
		expected = None
		self.assertEqual(result, expected)

	''' Ensure that the language returned is correct for a known repository when valid 
	arguments are passed. Note: This test relies on the repository being present on code climate'''
	def test_get_repo_language_valid_arguments(self):
		self.set_up()
		result = get_repo_language('bootstrap', '2019-02-28')
		expected = 'JavaScript'
		self.assertEqual(result, expected)

	''' Ensure that the language returned is correct for a known repository (uppercase name) when valid 
	arguments are passed. Note: This test relies on the repository being present on code climate'''
	def test_get_repo_language_valid_arguments(self):
		self.set_up()
		result = get_repo_language('Motrix', '2019-02-05')
		expected = 'JavaScript'
		self.assertEqual(result, expected)

	''' Ensure that the language returned is None for an unknown repository when incorrect 
	timestamp is passed. Note: This test relies on the repository not being present on code climate'''
	def test_get_repo_language_incorrect_repo_and_timestamp(self):
		self.set_up()
		result = get_repo_language('non-existent-repo', '2999-02-28')
		self.assertIsNone(result)

	''' Ensure that the language returned is None for an unknown repository when incorrect 
	timestamp is passed. Note: This test relies on the repository not being present on code climate'''
	def test_get_repo_language_no_args(self):
		self.set_up()
		result = get_repo_language('', '')
		self.assertIsNone(result)

	''' Ensure that the language returned is None for an unknown repository when incorrect 
	timestamp is passed. Note: This test relies on the repository not being present on code climate'''
	def test_get_repo_language_no_repo(self):
		self.set_up()
		result = get_repo_language('', '2019-02-28')
		self.assertIsNone(result)

	''' Ensure that the language returned is None for an unknown repository when incorrect 
	timestamp is passed. Note: This test relies on the repository not being present on code climate'''
	def test_get_repo_language_no_timestamp(self):
		self.set_up()
		result = get_repo_language('bootstrap', '')
		self.assertIsNone(result)

	''' Ensure that the language returned is None for an unknown repository when valid 
	timestamp is passed. Note: This test relies on the repository not being present on code climate'''
	def test_get_repo_language_incorrect_repo(self):
		self.set_up()
		result = get_repo_language('non-existent-repo', '2019-02-28')
		self.assertIsNone(result)

	''' Ensure that the language returned is None for a known repository when incorrect 
	timestamp is passed. Note: This test relies on the repository not being present on code climate'''
	def test_get_repo_language_incorrect_timestamp(self):
		self.set_up()
		result = get_repo_language('bootstrap', '2999-02-28')
		self.assertIsNone(result)

	''' Ensure that the language returned is None when a repository name is passed to attempt to interfere 
	with the url for api call when correct timestamp is passed. i.e. Contains url reserved chars (/)'''
	def test_get_repo_language_repo_with_url_reserved_chars(self):
		self.set_up()
		result = get_repo_language('/bootstrap/', '2019-02-28')
		self.assertIsNone(result)

	''' Ensure that json file is created after method is called and that the file contains the url passed.
	Note: This method is unreachable with url = empty string. Ensure that the delet_file method also 
	deletes the file '''
	def test_create_and_delete_json_file_valid(self):
		url= 'http://this.is.a.url.git'
		fname = create_json_file(url)
		fpath = os.path.join(os.getcwd(), fname)

		self.assertTrue(os.path.isfile(fpath))
		with open(fpath) as file:
			self.assertTrue(url in file.read())

		# delete file & test delete method works
		delete_file(fpath)
		self.assertFalse(os.path.isfile(fpath))

	''' Ensure that a list of 5 dates is returned when valid arguments are passed.
	Ensure that the first date in the returned list is the first argument passed.
	Ensure that the last date in the returned list is the last argument passed.
	Note: This method is unreachable when end date is < start date, or when either arg is none '''
	def test_get_time_intervals_returns_correct_data(self):
		start = date.today()
		end = start + timedelta(days=10)
		result = get_time_intervals(start, end)
		self.assertEqual(type(result), list)
		self.assertEqual(len(result), 5)
		self.assertEqual(start, result[0])
		self.assertEqual(end, result[4])

	''' Ensure that a list of 5 dates is returned when valid arguments are passed.
	Ensure that the first date in the returned list is the first argument passed.
	Ensure that the last date in the returned list is the last argument passed. '''
	def test_get_time_intervals_10_day_difference(self):
		start = date.today()
		end = start + timedelta(days=10)
		result = get_time_intervals(start, end)
		self.assertEqual(type(result), list)
		self.assertEqual(len(result), 5)
		self.assertEqual(start, result[0])
		self.assertEqual(end, result[4])

	''' Ensure that a list of just 2 dates is returned when start and end dates less than 
	4 days apart are passed. The list should contain the start and end dates that were passed.'''
	def test_get_time_intervals_4_day_difference(self):
		start = date.today()
		end = start + timedelta(days=4)
		result = get_time_intervals(start, end)

		self.assertEqual(type(result), list)
		self.assertEqual(len(result), 5)
		self.assertEqual(start, result[0])
		self.assertEqual(end, result[4])

	''' Ensure that a list of just 2 dates is returned when start and end dates less than 
	4 days apart are passed. The list should contain the start and end dates that were passed.'''
	def test_get_time_intervals_less_than_four_day_difference(self):
		start = date.today()
		end = start + timedelta(days=3)
		result = get_time_intervals(start, end)

		self.assertEqual(type(result), list)
		self.assertEqual(len(result), 2)
		self.assertEqual(start, result[0])
		self.assertEqual(end, result[1])

	''' Ensure that a sha hash is returned when valid arguments are passed.
	Note: This method is unreachable if any arguments are None'''
	def test_get_sha_valid_arguments(self):
		self.set_up()
		github_slug = 'twbs/bootstrap'
		timestamp = date(2019,2,28)
		user_token = get_user_token()
		self.assertIsNotNone(user_token)

		result = get_sha(github_slug, timestamp, user_token)
		self.assertIsNotNone(result)

	''' Ensure that None is returned when github_slug is empty.
	Note: This method is unreachable if any arguments are None'''
	def test_get_sha_empty_slug(self):
		self.set_up()
		github_slug = ''
		timestamp = date(2019,2,28)
		user_token = get_user_token()
		self.assertIsNotNone(user_token)

		result = get_sha(github_slug, timestamp, user_token)
		self.assertIsNone(result)

	''' Ensure that None is returned when github_slug is empty.
	Note: This method is unreachable if any arguments are None'''
	def test_get_sha_no_token(self):
		self.set_up()
		github_slug = 'twbs/bootstrap'
		timestamp = date(2019,2,28)
		user_token = None

		result = get_sha(github_slug, timestamp, user_token)
		self.assertIsNone(result)

	''' Ensure that the 2 directories below the project directory are returned. '''
	def test_walklevel(self):
		project_dir = os.path.dirname(os.getcwd())
		expected_sub_dirs = [ os.path.join(project_dir, 'app'),os.path.join(project_dir, 'tests') ]

		for sub_dir in walklevel(project_dir, 1):
			self.assertTrue(os.path.isdir(sub_dir))
			self.assertTrue(sub_dir in expected_sub_dirs)

	''' Ensure that the 2 directories below the project directory are returned. '''
	def test_walklevel(self):
		project_dir = os.path.dirname(os.getcwd())
		expected_sub_dirs = [ os.path.join(os.getcwd(), 'app'),os.path.join(os.getcwd(), 'tests') ]
		returned_dirs = []

		for sub_dir in walklevel(project_dir, 2):
			self.assertTrue(os.path.isdir(sub_dir))
			returned_dirs.append(sub_dir)
		
		self.assertTrue(expected_dir in returned_dirs for expected_dir in expected_sub_dirs)

if __name__ == '__main__':	
	unittest.main()