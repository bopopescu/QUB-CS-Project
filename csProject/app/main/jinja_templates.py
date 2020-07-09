from flask import Blueprint
import json


bp = Blueprint('jinja', __name__, template_folder='templates')

# custom jinja template for converting dict to json in front end
@bp.app_template_filter()
def to_json(value):
	return json.dumps(value)

# custom jinja template for text replacement in strings
@bp.app_template_filter()
def get_repo_name(str):
	return str.split('_', 1)[-1]

# custom jinja template for sorting code climate issues by severity
@bp.app_template_filter()
def sort_by_severity(lst):
	severities = ['blocker', 'critical', 'major', 'minor', 'info']
	order = {key: i for i, key in enumerate(severities)}
	return sorted(lst, key=lambda d: order[d['severity']])
