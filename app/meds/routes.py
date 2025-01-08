from flask import render_template, redirect, url_for, flash, request, g, abort
from flask_login import current_user, login_required
from flask_babel import _
import sqlalchemy as sa
from app import db
from app.meds import bp
from app.meds.forms import (
    CreateMedicineFrom,
    MedicineSortForm,
    EditMedicineForm,
    EmptyForm,
    SelectMonthForm,
)
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.helpers import unit_labels, format_unit, format_dose_unit
from app.models import Medicine, DailyLog, DailyLogDetail


@bp.route("/", methods=["GET"])
@login_required
def list():
    title = _("お薬管理")

    # フォーム設定
    form = MedicineSortForm()
    form.active_sort.data = request.args.get("active_sort", "registerorder")
    form.not_active_sort.data = request.args.get("not_active_sort", "registerorder")

    # ソート条件を設定
    active_order_by = (
        Medicine.rating.desc()
        if form.active_sort.data == "ratingorder"
        else Medicine.id
    )
    not_active_order_by = (
        Medicine.rating.desc()
        if form.not_active_sort.data == "ratingorder"
        else Medicine.id
    )

    # 服用中のお薬のお薬を取得
    active_query = (
        sa.select(Medicine)
        .join(Medicine.user)
        .where(Medicine.user == current_user, Medicine.is_active == True)
        .order_by(active_order_by)
    )
    active_medicines = db.session.scalars(active_query).all()

    # 服用中でないお薬を取得
    not_active_query = (
        sa.select(Medicine)
        .join(Medicine.user)
        .where(Medicine.user == current_user, Medicine.is_active == False)
        .order_by(not_active_order_by)
    )
    not_active_medicines = db.session.scalars(not_active_query).all()

    return render_template(
        "meds/list.html",
        active_medicines=active_medicines,
        not_active_medicines=not_active_medicines,
        form=form,
        title=title,
    )


@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    title = _("お薬登録")
    form = CreateMedicineFrom()

    if form.validate_on_submit():
        medicine = Medicine(
            name=form.name.data,
            taking_start_date=form.taking_start_date.data,
            dose_per_day=form.dose_per_day.data,
            taking_timing=form.taking_timing.data,
            memo=form.memo.data,
            rating=int(form.rating.data),
            is_active=form.is_active.data,
            taking_unit=form.taking_unit.data,
            user=current_user,
        )
        db.session.add(medicine)
        db.session.commit()
        flash(_("お薬「%(medicine_name)s」を登録しました", medicine_name=medicine.name))
        return redirect(url_for("meds.list"))

    return render_template("meds/create.html", form=form, title=title)


@bp.route("/<int:medicine_id>", methods=["GET"])
@login_required
def detail(medicine_id):
    title = _("お薬詳細")
    # モーダル削除ボタン用
    form = EmptyForm()

    selectform = SelectMonthForm()
    medicine = db.session.get(Medicine, medicine_id)

    if medicine is None or medicine.user_id != current_user.id:
        abort(404)

    # グラフ用デフォルト値
    chart_data = {"dates": [], "doses": [], "moods": [], "conditions": []}
    max_dose = 6

    selected_month = request.args.get("month") or datetime.now().strftime(
        format="%Y-%m"
    )
    selectform.month.data = datetime.strptime(selected_month, "%Y-%m")

    # 月初と月末の日付を計算
    start_date = datetime.strptime(selected_month + "-01", "%Y-%m-%d").date()
    end_date = start_date.replace(day=1) + relativedelta(months=1) - timedelta(days=1)

    # 選択月の全日付を生成
    all_dates = [
        start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)
    ]

    # グラフに表示するデータを取得
    logs = db.session.execute(
        sa.select(DailyLog.date, DailyLogDetail.dose, DailyLog.mood, DailyLog.condition)
        .join(DailyLogDetail, DailyLog.id == DailyLogDetail.daily_log_id)
        .where(
            DailyLog.date.between(start_date, end_date),
            DailyLogDetail.medicine_id == medicine.id,
            DailyLog.user == current_user,
        )
        .order_by(DailyLog.date)
    ).all()

    # データを辞書形式に変換
    log_dict = {log[0]: log for log in logs}

    # 日付ごとにデータを補完
    default_data = ("", 0, None, None)
    chart_data = {
        "dates": [d.strftime("%m/%d") for d in all_dates],
        "doses": [
            int(dose) if dose.is_integer() else dose
            for d, dose in ((d, log_dict.get(d, default_data)[1]) for d in all_dates)
        ],
        "moods": [log_dict.get(d, default_data)[2] for d in all_dates],
        "conditions": [log_dict.get(d, default_data)[3] for d in all_dates],
    }

    if chart_data["doses"]:
        if max_dose < max(chart_data["doses"]):
            max_dose = max(chart_data["doses"])
    else:
        max_dose = 0

    chart_labels = {
        "dose_label": _("お薬の量"),
        "mood_label": _("気分"),
        "condition_label": _("体調"),
        "y_rating_title": _("気分と体調"),
    }

    # フォーマット済み単位を生成
    locale = g.locale
    taking_unit = format_dose_unit(medicine.dose_per_day, medicine.taking_unit)
    if not locale == "ja":
        taking_unit = taking_unit.title()
    graph_taking_unit = format_unit(medicine.taking_unit, locale)

    if locale == "ja":
        start_date = medicine.taking_start_date.strftime("%Y/%m/%d")
    else:
        start_date = medicine.taking_start_date.strftime("%m/%d/%Y")

    return render_template(
        "meds/detail.html",
        medicine=medicine,
        title=title,
        form=form,
        selectform=selectform,
        chart_data=chart_data,
        max_dose=max_dose,
        unit_labels=unit_labels,
        taking_unit=taking_unit,
        graph_taking_unit=graph_taking_unit,
        chart_labels=chart_labels,
        start_date=start_date,
    )


@bp.route("/<int:medicine_id>/edit", methods=["GET", "POST"])
@login_required
def edit(medicine_id):
    title = _("お薬編集")
    medicine = db.session.get(Medicine, medicine_id)
    if medicine is None or medicine.user_id != current_user.id:
        abort(404)

    form = EditMedicineForm()

    if form.validate_on_submit():
        medicine.name = form.name.data
        medicine.taking_start_date = form.taking_start_date.data
        medicine.dose_per_day = form.dose_per_day.data
        medicine.taking_timing = form.taking_timing.data
        medicine.memo = form.memo.data
        medicine.rating = form.rating.data
        medicine.is_active = form.is_active.data

        db.session.commit()
        flash(
            _(
                "お薬「%(medicine_name)s」の情報を更新しました",
                medicine_name=medicine.name,
            )
        )

        # フォームからローカル年月を取得
        selected_month = form.local_month.data
        selected_month = selected_month.replace(" ", "").replace("+", "")

        return redirect(
            url_for("meds.detail", medicine_id=medicine.id, month=selected_month)
        )
    elif request.method == "GET":
        # フォームに既存データ投入
        form.name.data = medicine.name
        form.taking_start_date.data = medicine.taking_start_date
        # 1日に服用する量を設定 数値が整数に変換できるか判定
        form.dose_per_day.data = (
            int(medicine.dose_per_day)
            if medicine.dose_per_day and medicine.dose_per_day.is_integer()
            else medicine.dose_per_day
        )
        form.taking_timing.data = medicine.taking_timing
        form.memo.data = medicine.memo
        form.rating.data = medicine.rating
        form.is_active.data = medicine.is_active

    return render_template("meds/edit.html", medicine=medicine, form=form, title=title)


@bp.route("/<int:medicine_id>/delete", methods=["POST"])
@login_required
def delete(medicine_id):
    # モーダル削除ボタン用
    form = EmptyForm()

    if form.validate_on_submit():
        medicine_to_delete = db.session.get(Medicine, medicine_id)
        if medicine_to_delete is None or medicine_to_delete.user_id != current_user.id:
            abort(404)
        db.session.delete(medicine_to_delete)
        db.session.commit()
        flash(_("お薬「%(medicine)s」を削除しました", medicine=medicine_to_delete.name))
        return redirect(url_for("meds.list"))
    else:
        flash(_("すみません、お薬削除に失敗しました"))
        return redirect(url_for("meds.list"))
