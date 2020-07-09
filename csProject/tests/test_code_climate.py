import unittest
from flask import current_app as app
from base import BaseTestCase
from app.extensions import db
from app.models import Code_Climate
from app.main.code_climate import *

class TestCodeClimate(BaseTestCase):

	''' Ensure that the the get_data method returns an empty dict if code climate data 
	cannot be found due to a null repo id being passed as a parameter'''
	def test_get_data_no_repo_id_valid_timestamp(self):
		expected = {}
		timestamp = '2019-01-01'
		result = get_data(None, timestamp)
		self.assertEqual(result, expected)

	''' Ensure that the the get_data method returns an empty dict if code climate data 
	cannot be found due to a non-existent repo id'''
	def test_get_data_valid_parameters_repo_doesnt_exist(self):
		expected = {}
		repo_id = 'non-existent_id'
		timestamp = '2019-01-01'
		result = get_data(repo_id, timestamp)
		self.assertEqual(result, expected)

	''' Ensure that the the get_data method returns an non-empty dict for a repo_id and
	timestamp that exist on code climate'''
	def test_get_data_valid_parameters_repo_exists(self):
		repo_id = '5cb0b7df0af4a20263007ae8'
		timestamp = '2016-08-01'
		result = get_data(repo_id, timestamp)
		self.assertTrue(result) # non-empty dictionaries evaluate to true

	''' Ensure that the the get_issues_data method returns an empty dict for valid parameters
	but when the repo does not have any issues.	Note: function is unreachable if repo id is None'''
	def test_get_issues_data_valid_parameters_but_no_issues(self):
		repo_id = '5cb0b7df0af4a20263007ae8'
		snapshot_id = '5cb0b7e165d9f10001010325'
		language = 'java'
		result = get_issues_data(repo_id, snapshot_id, language)
		self.assertFalse(result) # non-empty dictionaries evaluate to true

	''' Ensure that the the get_issues_data method returns an non-empty dict for valid parameters.'''
	def test_get_issues_data_valid_parameters(self):
		repo_id = '5cb0bd9bce00a3470d001a30'
		snapshot_id = '5cb0bd9c65d9f10001010b19'
		language = 'java'
		result = get_issues_data(repo_id, snapshot_id, language)
		self.assertTrue(result) # non-empty dictionaries evaluate to true

	''' Ensure that the the get_issues_data method returns an empty dict for non-existent repo id'''
	def test_get_issues_data_non_existent_id(self):
		repo_id = 'non-existent_id'
		snapshot_id = '5cb0b7e165d9f10001010325'
		language = 'java'
		result = get_issues_data(repo_id, snapshot_id, language)
		self.assertFalse(result) # empty dictionaries evaluate to false

	''' Ensure that the the get_issues_data method returns an empty dict for invalid snapshot id'''
	def test_get_issues_data_no_snapshot_id(self):
		repo_id = '5cb0b7df0af4a20263007ae8'
		snapshot_id = None
		language = 'java'
		result = get_issues_data(repo_id, snapshot_id, language)
		self.assertFalse(result) # empty dictionaries evaluate to false

	''' Ensure that the the get_issues_data method returns an empty dict for invalid language'''
	def test_get_issues_data_no_langauge(self):
		repo_id = '5cb0b7df0af4a20263007ae8'
		snapshot_id = '5cb0b7e165d9f10001010325'
		language = 'java'
		result = get_issues_data(repo_id, snapshot_id, language)
		self.assertFalse(result) # non-empty dictionaries evaluate to true

	''' Ensure that the the get_issues_data method returns an empty dict for unsupported langauge'''
	def test_get_issues_data_language_not_supported(self):
		repo_id = '5cb0b7df0af4a20263007ae8'
		snapshot_id = '5cb0b7e165d9f10001010325'
		language = 'unsupported language'
		result = get_issues_data(repo_id, snapshot_id, language)
		self.assertFalse(result) # non-empty dictionaries evaluate to true

	''' Ensure that the the get_issue_overview method returns the expected dict if no data is provided'''
	def test_get_issue_overview_no_data(self):
		data = {}
		expected = {'files_with_issues': 0, 'category': {}, 'type': {}, 'severity': {}}
		result = get_issue_overview(data)
		self.assertEqual(result, expected)

	''' Ensure that the the get_issue_overview method returns the expected dict if valid data is provided'''
	def test_get_issue_overview_valid_data(self):
		repo_id = '5cb0bd9bce00a3470d001a30'
		snapshot_id = '5cb0bd9c65d9f10001010b19'
		language = 'java'
		data = get_issues_data(repo_id, snapshot_id, language)
		
		result = get_issue_overview(data)
		self.assertTrue(result['files_with_issues'] > 0)
		self.assertTrue(result['category'] is not {})
		self.assertTrue(result['type'] is not {})
		self.assertTrue(result['severity'] is not {})

	''' Ensure that the the database can be updated with valid data.
	Note: this method can only be called with valid data'''
	def test_store_cc_analysis_data_valid(self):
		repo_id = '5cb0bd9bce00a3470d001a30'
		snapshot_id = '5cb0bd9c65d9f10001010b19'
		language = 'java'
		data = {'lines_of_code': 200}

		bare_record = Code_Climate(id=repo_id, snapshot=snapshot_id)
		db.session.add(bare_record)
		store_cc_analysis_data(repo_id, data)
		row = db.session.query(Code_Climate).filter(Code_Climate.id==repo_id).first()
		self.assertTrue(row) # true if exists
		self.assertTrue(row.lines_of_code == 200)
 	
	''' Test that get_paginated_data method returns a single page if the data is not paginated'''
	def test_get_paginated_data_single_page(self):
		url = 'https://api.codeclimate.com/v1/repos/5cb0b7df0af4a20263007ae8/snapshots/5cb0b7e165d9f10001010325/issues'
		result = list(get_paginated_data(url))
		self.assertEqual(len(result), 1) 		

	''' Test that get_paginated_data method returns multiple pages if the data is paginated'''
	def test_get_paginated_data_paginated_data(self):
		url = 'https://api.codeclimate.com/v1/repos/5cb0bd9bce00a3470d001a30/snapshots/5cb0bd9c65d9f10001010b19/issues'
		result = list(get_paginated_data(url))
		self.assertTrue(len(result) > 1) 

	''' Test that a snapshot id is returned when a repo id is passed which exists '''
	def test_get_snapshot_valid_repo_id(self):
		repo_id = '5cb0bd9bce00a3470d001a30'
		result = get_snapshot(repo_id)
		self.assertTrue(result)

	''' Test that None is returned when a repo id is passed which exists '''
	def test_get_snapshot_invalid_repo_id(self):
		repo_id = 'invalid-repo-id'
		result = get_snapshot(repo_id)
		self.assertIsNone(result)

	''' Test that a number for loc is returned with valid repo id '''
	def test_get_loc_valid_repo_id(self):
		repo_id = '5cb0bd9bce00a3470d001a30'
		result = get_loc(repo_id)
		self.assertTrue(result >= 0)

	''' Test that None is returned with valid repo id '''
	def test_get_loc_invalid_repo_id(self):
		repo_id = 'invalid-repo-id'
		result = get_loc(repo_id)
		self.assertIsNone(result)

if __name__ == '__main__':	
	unittest.main()