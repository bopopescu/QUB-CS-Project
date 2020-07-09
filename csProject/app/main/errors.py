from flask import Blueprint, render_template

bp = Blueprint('error_handlers', __name__, template_folder='templates')

@bp.app_errorhandler(401)
def unauthorized(error):
    return render_template('401.html'), 401

@bp.app_errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@bp.app_errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@bp.app_errorhandler(410)
def gone(error):
    return render_template('410.html'), 410

@bp.app_errorhandler(500)
def internal_server_error(error):
    return render_template('500.html'), 500

@bp.app_errorhandler(Exception)
def exceptions(error):
    print error
    return render_template('500.html'), 500
