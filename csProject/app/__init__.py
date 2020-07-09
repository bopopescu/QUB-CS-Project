from flask import Flask, flash
from app.extensions import bootstrap, db, login_manager
from app.main.routes import bp as main
from app.main.auth_routes import bp as auth
from app.main.jinja_templates import bp as jinja_templates
from app.main.errors import bp as errors
from app.models import User, OAuth
from config import Config

from flask_login import login_user, current_user
from flask_dance.contrib.github import make_github_blueprint
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend
from sqlalchemy.orm.exc import NoResultFound

def create_app():
	''' Initialise the application with necessary extensions '''
	app = Flask(__name__)
	app.config.from_object(Config)
	app.app_context().push()

	bootstrap.init_app(app)

	db.init_app(app)

	login_manager.init_app(app)

	app.register_blueprint(main)
	app.register_blueprint(auth)
	app.register_blueprint(jinja_templates)
	app.register_blueprint(errors)

	github_blueprint = make_github_blueprint(client_id=Config.client_id, client_secret=Config.client_secret)
	github_blueprint.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user, user_required=False)
	app.register_blueprint(github_blueprint, url_prefix='/login')

	@login_manager.user_loader
	def load_user(user_id):
		return User.query.get(int(user_id))

	@oauth_authorized.connect_via(github_blueprint)
	def github_logged_in(blueprint, token):
		account_info = blueprint.session.get('/user')

		if account_info.ok:
			account_info_json = account_info.json()
			username = account_info_json['login']

			query = User.query.filter_by(username=username)

			try:
				user = query.one()
			except NoResultFound:
				user = User(username=username)
				db.session.add(user)
				db.session.commit()
			
			login_user(user)
			flash("Successfully signed in with GitHub.", 'success')

	return app
