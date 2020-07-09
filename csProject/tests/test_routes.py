import unittest
from base import BaseTestCase
from flask import current_app as app
from app.extensions import db
from app.models import Archive, Code_Climate
from urlparse import urlparse
from testdata import TestUser

class TestRoutes(BaseTestCase):

	def set_up(self):
		''' Authenticate a user for testing '''
		with app.test_request_context():
			@app.login_manager.request_loader
			def load_user_from_request(request):
				return self.test_user

	def populate_db(self):
		# add an archived repository
		repo = Archive(url='http://github.com/owner/name', name='name', owner='owner', github_slug='owner/repo', \
			language='java', timestamp='2019-01-01', archive_folder='path/to/folder')
		db.session.add(repo)

		archive_record = db.session.query(Archive).filter(Archive.url=='http://github.com/owner/name').first()
		self.assertIsNotNone(archive_record)
		
		# add code climate record for archived repository
		cc = Code_Climate(id='123456789', archive_id=archive_record.id, github_slug=archive_record.github_slug, \
			timestamp=archive_record.timestamp)
		db.session.add(cc)

	# Ensure that unauthorized request returns unauthorized error and 401 page loads
	def test_index_unauthorized(self):
		self.app.config['LOGIN_DISABLED'] = False
		self.app.login_manager.init_app(app)
		response = self.client.get('/', content_type='html/text')
		self.assertEqual(response.status_code, 401)
		self.assertIn(b'You must be logged in', response.data)

	# Ensure that unauthorized user is redirected to GitHub to login
	def test_redirect_github_login(self):
		self.app.config['LOGIN_DISABLED'] = False
		self.app.login_manager.init_app(app)
		response = self.client.get('/login', follow_redirects=False)
		expectedPath = '/login/github'
		self.assertEqual(response.status_code, 302)
		self.assertEqual(urlparse(response.location).path, expectedPath)

	""" Log in with existing user - github handles login so bypass 
	'@login_required' decorator and ensure that index page loads with 200 status
	"""
	def test_login_authorized(self):
		response = self.client.get('/', follow_redirects=False)
		self.assertIn(b'Welcome', response.data)
		self.assertEqual(response.status_code, 200)

	# Ensure that user can logout and logout page loads
	def test_logout(self):
		response = self.client.get('/logout', content_type='html/text')
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'You have been logged out', response.data)

	# Ensure that statistics page loads
	def test_stats_page(self):
		response = self.client.get('/stats', content_type='html/text')
		self.assertIn(b'Statistics', response.data)
		self.assertEqual(response.status_code, 200)

	# Ensure that repositories page loads
	def test_repositories_page(self):
		self.set_up()
		response = self.client.get('/repositories', content_type='html/text')
		self.assertIn(b'Repositories', response.data)
		self.assertEqual(response.status_code, 200)

	# Ensure that browse page loads
	def test_browse_page(self):
		response = self.client.get('/trending', content_type='html/text')
		self.assertIn(b'Trending', response.data)
		self.assertEqual(response.status_code, 200)

	# Ensure that downloads page loads
	def test_downloads_page(self):
		response = self.client.get('/downloads', content_type='html/text')
		self.assertIn(b'Downloads', response.data)
		self.assertEqual(response.status_code, 200)

	# Ensure that analysis page loads
	def test_analysis_page(self):
		response = self.client.get('/analyse', content_type='html/text')
		self.assertIn(b'Redirecting', response.data)
		self.assertEqual(response.status_code, 302)

	# Ensure that user is redirected to home page if change language page is accessed with no args
	def test_change_language_page_no_args(self):
		response = self.client.get('/change_language', content_type='html/text')
		self.assertIn(b'Redirecting', response.data)
		self.assertEqual(response.status_code, 302)

	# Ensure that user is redirected to home page if change language page is accessed with a repo that is not archived
	def test_change_language_page_invalid_args(self):
		response = self.client.get('/change_language?repo=doesnt_exist&timestamp=2019-04-15', content_type='html/text')
		self.assertIn(b'Redirecting', response.data)
		self.assertEqual(response.status_code, 302)

	# Ensure that change language page loads with valid args
	def test_change_language_page_valid_args(self):
		self.populate_db()
		response = self.client.get('/change_language?repo=name&timestamp=2019-01-01', content_type='html/text')
		self.assertIn(b'Change Language', response.data)
		self.assertEqual(response.status_code, 200)

	# Ensure that user is redirected to home page if quality issues page is accessed with no args
	def test_quality_issues_page(self):
		response = self.client.get('/quality_issues', content_type='html/text')
		self.assertIn(b'Redirecting', response.data)
		self.assertEqual(response.status_code, 302)

	# Ensure that user is redirected to home page if quality issues page is accessed with a repo that is not archived
	def test_quality_issues_page(self):
		response = self.client.get('/quality_issues?repo=non-existent', content_type='html/text')
		self.assertIn(b'Redirecting', response.data)
		self.assertEqual(response.status_code, 302)

	# Ensure that quality issues page loads with valid args
	def test_quality_issues_page_valid_args(self):
		self.populate_db()
		response = self.client.get('/quality_issues?id={}'.format('123456789'), content_type='html/text')
		self.assertIn(b'Quality Issues', response.data)
		self.assertEqual(response.status_code, 200)

	# Ensure that archive all route returns 404 if no repo is provided
	def test_archive_all_page(self):
		response = self.client.get('/analyse_all', content_type='html/text')
		self.assertIn(b'Page Not Found', response.data)
		self.assertEqual(response.status_code, 404)

	# Ensure that archive all route returns 404 if no repo is provided
	def test_archive_all_page_2(self):
		response = self.client.get('/analyse_all/', content_type='html/text')
		self.assertIn(b'Page Not Found', response.data)
		self.assertEqual(response.status_code, 404)

	# Ensure that archive all route redirects to home page if invalid repo
	def test_archive_all_page_non_existent_repo(self):
		response = self.client.get('/analyse_all/non-existent-repo', content_type='html/text')
		self.assertIn(b'Redirecting', response.data)
		self.assertEqual(response.status_code, 302)
			
	# Ensure that compare route redirects to downloads page on get request
	def test_compare_page_get(self):
		response = self.client.get('/compare', content_type='html/text')
		self.assertIn(b'Redirecting', response.data)
		self.assertEqual(response.status_code, 302)

	# Ensure that compare route load with valid form data (csv repositories)
	def test_compare_page_post_valid(self):
		post_data = dict(selected="http://github.com/owner/name,http://github.com/owner/name2")
		response = self.client.post('/compare', data=post_data)
		self.assertIn(b'Compare', response.data)
		self.assertEqual(response.status_code, 200)

	# Ensure that compare route load with valid form data (single repositories)
	def test_compare_page_post_valid_2(self):
		post_data = dict(selected="http://github.com/owner/name")
		response = self.client.post('/compare', data=post_data)
		self.assertIn(b'Compare', response.data)
		self.assertEqual(response.status_code, 200)

	''' Ensure that compare route redirects to downloads page on invalid post request
	(form is invalid) '''
	def test_compare_page_post_invalid(self):
		post_data = dict(selected='')
		response = self.client.post('/compare', data=post_data)
		self.assertIn(b'Redirecting', response.data)
		self.assertEqual(response.status_code, 302)

	# Ensure that discover filters page loads 
	def test_discover_filters_page(self):
		response = self.client.get('/discover_filters', content_type='html/text')
		self.assertIn(b'Set Filters', response.data)
		self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
	unittest.main()