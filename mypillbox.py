import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db
from app.models import User, Medicine, DailyLog, DailyLogDetail


app = create_app()


# flask shellで使うためのシェルコンテキストを設定
@app.shell_context_processor
def make_shell_context():
    return {
        "sa": sa,
        "so": so,
        "db": db,
        "User": User,
        "Medicine": Medicine,
        "DailyLog": DailyLog,
        "DailyLogDetail": DailyLogDetail,
    }
