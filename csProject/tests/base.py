from flask_testing import TestCase
from app import create_app
from app.extensions import db
from app.config import TestConfig
from testdata import TestUser
from flask import current_app

class BaseTestCase(TestCase):

	def create_app(self):
		self.app = create_app()
		self.app.config.from_object(TestConfig)
		self.app.login_manager.init_app(current_app)
		return self.app

	def setUp(self):
		db.create_all()
		self.test_user = TestUser()
		

	def tearDown(self):
		db.session.remove()
		db.drop_all()

	def test_app_exists(self):
		self.assertFalse(current_app is None)

	def test_app_is_testing(self):
		self.assertTrue(current_app.config['TESTING'])

	def test_login_disabled(self):
		self.assertTrue(current_app.config['LOGIN_DISABLED'])
	
