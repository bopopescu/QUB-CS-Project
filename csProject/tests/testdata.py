from app.models import User, OAuth
from flask_login import login_user
from base import db
from datetime import datetime
# class TestUser():

# 	def __init__(self):
# 		self.username = 'GaryMcPolin'
# 		# self.github_token = {"access_token": "a6637954e866f7510cd52b79e52d2d98222e568d", "token_type": "bearer", "scope": [""]}
# 		self.user = User(username=self.username)
# 		db.session.add(self.user)
# 		db.session.commit()

# 	def get_user(self):
# 		return self.user

# 	def get_token(self):
# 		return self.github_token['access_token']

class TestUser():

	def __init__(self):
		self.id = 1
		self.username = 'subordinateuser'
		self.provider = 'github'
		self.created_at = datetime.now()
		self.token = {"access_token": "91a43d39637f8d3f566411d834044a6f39b58037", "token_type": "bearer", "scope": [""]}
		self.user_id = 1

		self.user = User(id=self.id, username=self.username)
		self.oauth = OAuth(id=self.id,provider=self.provider, created_at=self.created_at, token=self.token, user_id=self.user_id)

		db.session.add(self.user)
		db.session.add(self.oauth)
		db.session.commit()

