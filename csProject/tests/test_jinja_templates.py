import unittest
from flask import current_app as app
from base import BaseTestCase
from app.main.jinja_templates import *

class TestJinjaTemplates(BaseTestCase):

	''' Test to_json method with char input '''
	def test_to_json_char(self):
		args = 'a'
		expected = '"a"'
		result = to_json(args)
		self.assertEqual(result, expected)

	''' Test to_json method with string input '''
	def test_to_json_string(self):
		args = 'a string'
		expected = '"a string"'
		result = to_json(args)
		self.assertEqual(result, expected)

	''' Test to_json method with number input '''
	def test_to_json_number(self):
		args = 5
		expected = '5'
		result = to_json(args)
		self.assertEqual(result, expected)

	''' Test to_json method with dict input '''
	def test_to_json_dicy(self):
		args = {'key': 'value'}
		expected = '{"key": "value"}'
		result = to_json(args)
		self.assertEqual(result, expected)

	''' Test get_repo_name method with expected input '''
	def test_get_repo_name_single_underscore(self):
		args = 'owner_reponame'
		expected = 'reponame'
		result = get_repo_name(args)
		self.assertEqual(result, expected)

	''' Test get_repo_name method with expected input '''
	def test_get_repo_name_mixed_case(self):
		args = 'Owner_Reponame'
		expected = 'Reponame'
		result = get_repo_name(args)
		self.assertEqual(result, expected)

	''' Test get_repo_name method with expected input '''
	def test_get_repo_name_with_hyphens(self):
		args = 'Owner_Repo-name'
		expected = 'Repo-name'
		result = get_repo_name(args)
		self.assertEqual(result, expected)

	''' Test get_repo_name method with expected input '''
	def test_get_repo_name_multiple_underscores(self):
		args = 'Owner_repo_sitory-name'
		expected = 'repo_sitory-name'
		result = get_repo_name(args)
		self.assertEqual(result, expected)

	''' Test sort_by_severity method with expected input '''
	def test_sort_by_severity(self):
		args = [
		{
		"category": "Complexity", 
		"description": "Method `transformRequest` has 29 lines of code (exceeds 25 allowed). Consider refactoring.", 
		"end_line": 81, 
		"fingerprint": "96a08d02d1fbfbe373087ddc870ff503", 
		"severity": "minor", 
		"start_line": 37, 
		"type": "structure"
		}, 
		{
		"category": "Complexity", 
		"description": "Method `transformRequest` has a Cognitive Complexity of 9 (exceeds 5 allowed). Consider refactoring.", 
		"end_line": 81, 
		"fingerprint": "5d79f602b5fb8a7558458b17e0ed6a99", 
		"severity": "major", 
		"start_line": 37, 
		"type": "structure"
		}, 
		{
		"category": "Complexity", 
		"description": "Method `transformRequest` has a Cognitive Complexity of 9 (exceeds 5 allowed). Consider refactoring.", 
		"end_line": 81, 
		"fingerprint": "5d79f602b5fb8a7558458b17e0ed6a99", 
		"severity": "critical", 
		"start_line": 37, 
		"type": "structure"
		}, 
		{
		"category": "Complexity", 
		"description": "Method `transformRequest` has a Cognitive Complexity of 9 (exceeds 5 allowed). Consider refactoring.", 
		"end_line": 81, 
		"fingerprint": "5d79f602b5fb8a7558458b17e0ed6a99", 
		"severity": "info", 
		"start_line": 37, 
		"type": "structure"
		}, 
		{
		"category": "Complexity", 
		"description": "Method `transformRequest` has a Cognitive Complexity of 9 (exceeds 5 allowed). Consider refactoring.", 
		"end_line": 81, 
		"fingerprint": "5d79f602b5fb8a7558458b17e0ed6a99", 
		"severity": "blocker", 
		"start_line": 37, 
		"type": "structure"
		}
		]
		result = sort_by_severity(args)
		self.assertTrue(result[0]['severity'] == 'blocker')
		self.assertTrue(result[1]['severity'] == 'critical')
		self.assertTrue(result[2]['severity'] == 'major')
		self.assertTrue(result[3]['severity'] == 'minor')
		self.assertTrue(result[4]['severity'] == 'info')


if __name__ == '__main__':	
	unittest.main()