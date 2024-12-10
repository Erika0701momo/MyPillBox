import sqlalchemy as sa
import sqlalchemy.orm as so
from app import app, db, cli
from app.models import User, Medicine, TakingUnit, DailyLog, DailyLogDetail


# flask shellで使うためのシェルコンテキストを設定
@app.shell_context_processor
def make_shell_context():
    return {
        "sa": sa,
        "so": so,
        "db": db,
        "User": User,
        "Medicine": Medicine,
        "TakingUnit": TakingUnit,
        "DailyLog": DailyLog,
        "DailyLogDetail": DailyLogDetail,
    }
