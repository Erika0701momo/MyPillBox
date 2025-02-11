import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "").replace(
        "postgres://", "postgresql://"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT")
    # daily_logs.htmlで表示する日々の記録の数を設定
    LOGS_PER_PAGE = 10
    LANGUAGES = ["ja", "en"]
