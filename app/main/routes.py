from flask import render_template
from app import db
from flask_login import current_user, login_required
import sqlalchemy as sa
from app.models import Medicine, DailyLog
from flask_babel import _, get_locale
from flask import g
from app.main import bp


@bp.before_app_request
def before_request():
    # 場所と選択された言語を取得
    g.locale = str(get_locale())


@bp.route("/")
@bp.route("/index")
@login_required
def index():
    title = _("ホーム")
    # 現在のユーザーの服用中の薬の種類を取得
    medicine_query = sa.select(sa.func.count(Medicine.id)).where(
        Medicine.user == current_user, Medicine.is_active == True
    )
    medicine_kinds = db.session.scalar(medicine_query)

    # 現在のユーザーの日々の記録数を取得
    daily_log_query = sa.select(sa.func.count(DailyLog.id)).where(
        DailyLog.user == current_user
    )
    days = db.session.scalar(daily_log_query)

    return render_template(
        "index.html", title=title, medicine_kinds=medicine_kinds, days=days
    )
