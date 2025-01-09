from flask import render_template, flash, redirect, url_for, request, abort, current_app
from app import db
from app.logs import bp
from app.logs.forms import EmptyForm, DailyLogForm, EditDailyLogForm
from flask_login import current_user, login_required
import sqlalchemy as sa
from app.models import Medicine, DailyLog, DailyLogDetail
from flask_paginate import Pagination, get_page_parameter
from flask_babel import _
from flask import g
from app.helpers import format_unit, format_dose_unit


@bp.route("/")
@login_required
def list():
    title = _("日々の記録")
    # モーダル削除ボタン用
    form = EmptyForm()

    # クエリパラメータから現在のページ番号を取得
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = current_app.config["LOGS_PER_PAGE"]

    # 全体の件数を取得
    total_query = sa.select(sa.func.count(DailyLog.id)).where(
        DailyLog.user == current_user
    )
    total_count = db.session.scalar(total_query)

    # ページネーションされた日々の記録を取得
    query = (
        sa.select(DailyLog)
        .where(DailyLog.user == current_user)
        .order_by(DailyLog.date.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    daily_logs = db.session.scalars(query).all()

    # 各DailyLogに対してdoseがすべて0.0かをチェックする
    for log in daily_logs:
        log.all_doses_zero = all(detail.dose == 0.0 for detail in log.daily_log_details)
        # 英語版ならdoseに合わせて単位を複数形、日本語版ならそのままにする
        for detail in log.daily_log_details:
            detail.localized_taking_unit = format_dose_unit(
                detail.dose, detail.medicine.taking_unit
            )

    pagination = Pagination(
        page=page,
        per_page=per_page,
        total=total_count,
        display_msg=_("<b>{total}</b>件中の<b>{start} - {end}</b>件"),
        record_name=_("日々の記録"),
        css_framework="bootstrap5",
    )

    return render_template(
        "logs/list.html",
        daily_logs=daily_logs,
        form=form,
        pagination=pagination,
        title=title,
    )


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    title = _("日々の記録登録")
    form = DailyLogForm()

    # 服用中のお薬を取得
    active_query = (
        sa.select(Medicine)
        .where(Medicine.user == current_user, Medicine.is_active == True)
        .order_by(Medicine.id)
    )
    active_medicines = db.session.scalars(active_query).all()

    # フォーマット済み単位を生成
    locale = g.locale
    formatted_units = {
        med.id: format_unit(med.taking_unit, locale) for med in active_medicines
    }

    # 服用中のお薬の数だけエントリを追加し、dose_per_dayを初期値として設定
    form.details.min_entries = len(active_medicines)
    for medicine in active_medicines:
        # form.details.append_entry()でWTFormsのFieldListに新しいフォームエントリ(項目)を追加
        detail_entry = form.details.append_entry()
        # 1日に服用する量を設定 数値が整数に変換できるか判定
        detail_entry.dose.data = (
            int(medicine.dose_per_day)
            if medicine.dose_per_day and medicine.dose_per_day.is_integer()
            else medicine.dose_per_day
        )

    if form.validate_on_submit():
        # new_daily_logをデータベースに登録
        new_daily_log = DailyLog(
            date=form.date.data,
            mood=int(form.mood.data),
            condition=int(form.condition.data),
            user=current_user,
        )
        db.session.add(new_daily_log)
        db.session.commit()

        # 各daily_log_detailをデータベースに登録
        for idx, medicine in enumerate(active_medicines):
            daily_log_detail = DailyLogDetail(
                dose=form.details[idx].dose.data or 0,
                medicine=medicine,
                daily_log=new_daily_log,
            )
            db.session.add(daily_log_detail)

        db.session.commit()

        if g.locale == "ja":
            formatted_date = new_daily_log.date.strftime("%Y/%m/%d")
        else:
            formatted_date = new_daily_log.date.strftime("%m/%d/%Y")

        flash(_("%(date)sの記録を登録しました", date=formatted_date))
        return redirect(url_for("logs.list"))

    return render_template(
        "logs/create.html",
        form=form,
        medicines=active_medicines,
        title=title,
        unit_labels=formatted_units,
    )


@bp.route("/<int:daily_log_id>/edit", methods=["GET", "POST"])
@login_required
def edit(daily_log_id):
    title = _("日々の記録編集")

    daily_log = db.session.get(DailyLog, daily_log_id)
    if daily_log is None or daily_log.user_id != current_user.id:
        abort(404)

    # フォームの初期化
    form = EditDailyLogForm()

    # 服用中のお薬を取得
    active_query = (
        sa.select(Medicine)
        .where(
            Medicine.user == current_user,
            Medicine.is_active == True,
            Medicine.taking_start_date
            <= daily_log.date,  # DailyLogのdate以前に服用開始されたもの
        )
        .order_by(Medicine.id)
    )
    active_medicines = db.session.scalars(active_query).all()
    medicines_to_add = []
    # medicineがdaily_log_detailsに含まれていなければmedicines_to_addに追加
    for medicine in active_medicines:
        if not any(
            detail.medicine_id == medicine.id for detail in daily_log.daily_log_details
        ):
            medicines_to_add.append(medicine)

    # フォーマット済み単位を生成
    locale = g.locale
    formatted_units_for_log = {
        detail.id: format_unit(detail.medicine.taking_unit, locale)
        for detail in daily_log.daily_log_details
    }
    if medicines_to_add:
        formatted_units_for_meds = {
            med.id: format_unit(med.taking_unit, locale) for med in medicines_to_add
        }
    else:
        formatted_units_for_meds = {}

    if locale == "ja":
        formatted_date = daily_log.date.strftime("%Y/%m/%d")
    else:
        formatted_date = daily_log.date.strftime("%m/%d/%Y")

    if form.validate_on_submit():
        # DailyLogの更新
        daily_log.mood = form.mood.data
        daily_log.condition = form.condition.data
        # DailyLogDetailの更新
        for idx, detail in enumerate(daily_log.daily_log_details):
            detail.dose = form.daily_log_details[idx].dose.data or 0
        # medicines_to_addの分もDailyLogDetailに登録
        if medicines_to_add:
            for idx, medicine in enumerate(medicines_to_add):
                new_detail = DailyLogDetail(
                    dose=form.added_meds_details[idx].dose.data or 0,
                    medicine=medicine,
                    daily_log=daily_log,
                )
                db.session.add(new_detail)
        db.session.commit()

        flash(_("%(date)sの記録を更新しました", date=formatted_date))
        return redirect(url_for("logs.list"))
    elif request.method == "GET":
        # フォームに既存データ投入
        form.mood.data = daily_log.mood
        form.condition.data = daily_log.condition
        # daily_log_detailsのお薬の数だけエントリを追加し、doseを初期値として設定
        for detail in daily_log.daily_log_details:
            # form.details.append_entry()でWTFormsのFieldListに新しいフォームエントリ(項目)を追加
            detail_entry = form.daily_log_details.append_entry()
            # 各お薬の服用量を設定 数値が整数に変換できるか判定
            detail_entry.dose.data = (
                int(detail.dose) if detail.dose.is_integer() else detail.dose
            )
        # 服用中でdaily_logの日付より前に登録されたお薬の数だけエントリを追加
        if medicines_to_add:
            for medicine in medicines_to_add:
                # form.details.append_entry()でWTFormsのFieldListに新しいフォームエントリ(項目)を追加
                detail_entry = form.added_meds_details.append_entry({"dose": None})

    return render_template(
        "logs/edit.html",
        daily_log=daily_log,
        medicines=medicines_to_add,
        log_unit_labels=formatted_units_for_log,
        meds_unit_labels=formatted_units_for_meds,
        form=form,
        title=title,
    )


@bp.route("/<int:daily_log_id>/delete", methods=["POST"])
@login_required
def delete(daily_log_id):
    # モーダル削除ボタン用
    form = EmptyForm()

    if form.validate_on_submit():
        daily_log_to_delete = db.session.get(DailyLog, daily_log_id)
        if (
            daily_log_to_delete is None
            or daily_log_to_delete.user_id != current_user.id
        ):
            abort(404)
        db.session.delete(daily_log_to_delete)
        db.session.commit()

        if g.locale == "ja":
            formatted_date = daily_log_to_delete.date.strftime("%Y/%m/%d")
        else:
            formatted_date = daily_log_to_delete.date.strftime("%m/%d/%Y")

        flash(_("%(date)sの記録を削除しました", date=formatted_date))
        return redirect(url_for("logs.list"))
    else:
        flash(_("すみません、記録削除に失敗しました"))
        return redirect(url_for("logs.list"))
