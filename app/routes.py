from flask import render_template, flash, redirect, url_for, request, abort
from app import app, db
from app.forms import (
    LoginForm,
    RegisterForm,
    EditUsernameForm,
    DeleteAccountForm,
    CreateMedicineFrom,
    MedicineSortForm,
    EditMedicineForm,
    EmptyForm,
    DailyLogForm,
    EditDailyLogForm,
    SelectMonthForm,
)
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.models import User, Medicine, TakingUnit, DailyLog, DailyLogDetail
from urllib.parse import urlsplit
from flask_paginate import Pagination, get_page_parameter
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from flask_babel import _


@app.route("/")
@app.route("/index")
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


@app.route("/login", methods=["GET", "POST"])
def login():
    # ログインしている場合はインデックスへリダイレクト
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
        if user is None or not user.check_password(form.password.data):
            flash(_("メールアドレスまたはパスワードが違います"))
            return redirect(url_for("login"))
        login_user(user)
        # ログイン前にアクセスしたページがあればそこへ遷移
        next_page = request.args.get("next")
        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("index")
        return redirect(next_page)

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    # ログインしている場合はインデックスへリダイレクト
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_("アカウントを登録しました！ログインしましょう"))
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/edit_username", methods=["GET", "POST"])
@login_required
def edit_username():
    title = _("ユーザー名の変更")
    form = EditUsernameForm()

    if form.validate_on_submit():
        current_user.username = form.username.data
        db.session.commit()
        flash(_("ユーザー名を変更しました"))
        return redirect(url_for("edit_username"))
    elif request.method == "GET":
        form.username.data = current_user.username

    return render_template("edit_username.html", form=form, title=title)


@app.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    title = _("アカウント削除")
    form = DeleteAccountForm()

    if form.validate_on_submit():
        user = current_user
        db.session.delete(user)
        db.session.commit()
        logout_user()
        flash(_("アカウントが削除されました。ご利用ありがとうございました。"))
        return redirect(url_for("login"))

    return render_template("delete_account.html", form=form, title=title)


@app.route("/medicines", methods=["GET"])
@login_required
def medicines():
    title = _("お薬管理")

    # フォーム設定
    form = MedicineSortForm()
    form.active_sort.data = request.args.get("active_sort", "registerorder")
    form.not_active_sort.data = request.args.get("not_active_sort", "registerorder")

    # 服用中のお薬のお薬を登録順で取得
    active_query = (
        sa.select(Medicine)
        .join(Medicine.user)
        .where(Medicine.user == current_user, Medicine.is_active == True)
        .order_by(Medicine.id)
    )
    # 服用中でないお薬を登録順で取得
    not_active_query = (
        sa.select(Medicine)
        .join(Medicine.user)
        .where(Medicine.user == current_user, Medicine.is_active == False)
        .order_by(Medicine.id)
    )
    # 服用中のお薬を星評価順で取得
    rating_active_query = (
        sa.select(Medicine)
        .join(Medicine.user)
        .where(Medicine.user == current_user, Medicine.is_active == True)
        .order_by(Medicine.rating.desc())
    )
    # 服用中でないお薬を星評価順で取得
    rating_not_active_query = (
        sa.select(Medicine)
        .join(Medicine.user)
        .where(Medicine.user == current_user, Medicine.is_active == False)
        .order_by(Medicine.rating.desc())
    )

    if form.active_sort.data == "ratingorder":
        active_medicines = db.session.scalars(rating_active_query).all()
    else:
        active_medicines = db.session.scalars(active_query).all()

    if form.not_active_sort.data == "ratingorder":
        not_active_medicines = db.session.scalars(rating_not_active_query).all()
    else:
        not_active_medicines = db.session.scalars(not_active_query).all()

    return render_template(
        "medicines.html",
        active_medicines=active_medicines,
        not_active_medicines=not_active_medicines,
        form=form,
        title=title,
    )


@app.route("/create_medicine", methods=["GET", "POST"])
@login_required
def create_medicine():
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
            taking_unit=TakingUnit[form.taking_unit.data],
            user=current_user,
        )
        db.session.add(medicine)
        db.session.commit()
        flash(_("お薬「%(medicine_name)s」を登録しました", medicine_name=medicine.name))
        return redirect(url_for("medicines"))

    return render_template("create_medicine.html", form=form, title=title)


@app.route("/medicine_detail/<int:medicine_id>", methods=["GET"])
@login_required
def medicine_detail(medicine_id):
    title = "お薬詳細"
    # モーダル削除ボタン用
    form = EmptyForm()

    selectform = SelectMonthForm()
    medicine = db.session.get(Medicine, medicine_id)

    if medicine is None or medicine.user_id != current_user.id:
        abort(404)

    # グラフ用デフォルト値
    chart_data = {"dates": [], "doses": [], "moods": [], "conditions": []}
    max_dose = 6

    selected_month = request.args.get("month") or datetime.now(
        timezone(timedelta(hours=9))
    ).strftime("%Y-%m")
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

    return render_template(
        "medicine_detail.html",
        medicine=medicine,
        title=title,
        form=form,
        selectform=selectform,
        chart_data=chart_data,
        max_dose=max_dose,
    )


@app.route("/edit_medicine/<int:medicine_id>", methods=["GET", "POST"])
@login_required
def edit_medicine(medicine_id):
    title = "お薬編集"
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
        flash(f"お薬「{medicine.name}」の情報を更新しました")
        return redirect(url_for("medicine_detail", medicine_id=medicine.id))
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

    return render_template(
        "edit_medicine.html", medicine=medicine, form=form, title=title
    )


@app.route("/delete_medicine/<int:medicine_id>", methods=["POST"])
@login_required
def delete_medicine(medicine_id):
    # モーダル削除ボタン用
    form = EmptyForm()

    if form.validate_on_submit():
        medicine_to_delete = db.session.get(Medicine, medicine_id)
        if medicine_to_delete is None or medicine_to_delete.user_id != current_user.id:
            abort(404)
        db.session.delete(medicine_to_delete)
        db.session.commit()
        flash(f"お薬「{medicine_to_delete.name}」を削除しました")
        return redirect(url_for("medicines"))
    else:
        flash("すみません、お薬削除に失敗しました")
        return redirect(url_for("medicines"))


@app.route("/daily_logs")
@login_required
def daily_logs():
    title = "日々の記録"
    # モーダル削除ボタン用
    form = EmptyForm()

    # クエリパラメータから現在のページ番号を取得
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = app.config["LOGS_PER_PAGE"]

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

    pagination = Pagination(
        page=page,
        per_page=per_page,
        total=total_count,
        display_msg="<b>{total}</b>件中の<b>{start} - {end}</b>件",
        record_name="日々の記録",
        css_framework="bootstrap5",
    )

    return render_template(
        "daily_logs.html",
        daily_logs=daily_logs,
        form=form,
        pagination=pagination,
        title=title,
    )


@app.route("/create_daily_log", methods=["GET", "POST"])
@login_required
def create_daily_log():
    title = "日々の記録登録"
    form = DailyLogForm()

    # 服用中のお薬を取得
    active_query = (
        sa.select(Medicine)
        .where(Medicine.user == current_user, Medicine.is_active == True)
        .order_by(Medicine.id)
    )
    active_medicines = db.session.scalars(active_query).all()

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
            # if form.details[idx].dose.data is None:
            #     form.details[idx].dose.data = 0
            daily_log_detail = DailyLogDetail(
                dose=form.details[idx].dose.data or 0,
                medicine=medicine,
                daily_log=new_daily_log,
            )
            db.session.add(daily_log_detail)

        db.session.commit()
        flash(f"{new_daily_log.date.strftime('%Y/%m/%d')}の記録を登録しました")
        return redirect(url_for("daily_logs"))

    return render_template(
        "create_daily_log.html", form=form, medicines=active_medicines, title=title
    )


@app.route("/edit_daily_log/<int:daily_log_id>", methods=["GET", "POST"])
@login_required
def edit_daily_log(daily_log_id):
    title = "日々の記録編集"

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
        flash(f"{daily_log.date.strftime('%Y/%m/%d')}の記録を更新しました")
        return redirect(url_for("daily_logs"))
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
        "edit_daily_log.html",
        daily_log=daily_log,
        medicines=medicines_to_add,
        form=form,
        title=title,
    )


@app.route("/delete_daily_log/<int:daily_log_id>", methods=["POST"])
@login_required
def delete_daily_log(daily_log_id):
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
        flash(f"{daily_log_to_delete.date.strftime('%Y/%m/%d')}の記録を削除しました")
        return redirect(url_for("daily_logs"))
    else:
        flash("すみません、記録削除に失敗しました")
        return redirect(url_for("daily_logs"))
