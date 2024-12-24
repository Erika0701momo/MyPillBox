from flask import render_template, abort
from app import db
from app.errors import bp
from werkzeug.exceptions import default_exceptions


# エラーコードをurlに打ち込むとそのエラーページを表示
@bp.get("/<int:code>")
def error_page(code):
    if code not in default_exceptions.keys():
        code = 500
    abort(code)


@bp.app_errorhandler(400)
def bad_request_error(error):
    return render_template("errors/400.html"), 400


@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@bp.app_errorhandler(405)
def method_not_allowed_error(error):
    return render_template("errors/405.html"), 405


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("errors/500.html"), 500
