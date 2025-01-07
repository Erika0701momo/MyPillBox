from flask import Flask, request, current_app, g
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import RotatingFileHandler
import os
from flask_babel import Babel, lazy_gettext as _l
from flask_moment import Moment
from flask_talisman import Talisman
import secrets


# クライアントの言語を取得してマッチする言語を見つける
def get_locale():
    return request.accept_languages.best_match(current_app.config["LANGUAGES"])


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_message = _l("このページにアクセスするにはログインしてください")
login.login_view = "auth.login"
babel = Babel()
moment = Moment()
talisman = Talisman()

# 必要なリソースを許可するようにCSPを設定
csp = {
    "default-src": ["'self'"],
    "img-src": ["'self'", "https://www.gravatar.com", "data:"],
    "style-src": ["'self'", "https://fonts.googleapis.com", "'unsafe-inline'"],
    "font-src": ["'self'", "https://fonts.gstatic.com"],
    "script-src": ["'self'", "https://cdnjs.cloudflare.com"],
}


# アプリケーションファクトリーを定義
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # @app.before_request
    # def set_nonce():
    #     g.nonce = secrets.token_urlsafe(16)  # 一時的な識別子を生成

    # @app.after_request
    # def set_csp_nonce(response):
    #     csp_header = (
    #         f"script-src 'self' https://cdnjs.cloudflare.com 'nonce-{g.nonce}'; "
    #         "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
    #         "img-src 'self' https://www.gravatar.com data:; "
    #         "font-src 'self' https://fonts.gstatic.com;"
    #     )
    #     response.headers["Content-Security-Policy"] = csp_header
    #     return response

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    moment.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    talisman.init_app(
        app,
        content_security_policy=csp,
        content_security_policy_nonce_in=["script-src"],
        force_https=False,
    )

    from app.errors import bp as errors_bp

    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.users import bp as users_bp

    app.register_blueprint(users_bp, url_prefix="/users")

    from app.meds import bp as meds_bp

    app.register_blueprint(meds_bp, url_prefix="/meds")

    from app.logs import bp as logs_bp

    app.register_blueprint(logs_bp, url_prefix="/logs")

    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    from app.cli import bp as cli_bp

    app.register_blueprint(cli_bp)

    if not app.debug:
        # ログファイル作成
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/mypillbox.log", maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("MyPillBox startup")

    return app


from app import models
