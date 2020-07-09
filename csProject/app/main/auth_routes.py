from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, logout_user, current_user
from flask_dance.contrib.github import github
import json


bp = Blueprint('auth', __name__)

@bp.route('/login')
def login():
	if not current_user.is_authenticated:
		return redirect(url_for('github.login'))

	account_info = github.get('/user')
	account_info_json = account_info.json()

	return redirect(url_for('main.index'))

@bp.route('/logout')
@login_required
def logout():
	logout_user()

	return render_template('logout.html')