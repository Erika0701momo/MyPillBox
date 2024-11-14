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
    DailyLogDetailForm,
)
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models import User, Medicine, TakingUnit, DailyLog, DailyLogDetail
from urllib.parse import urlsplit


@app.route("/")
@app.route("/index")
@login_required
def index():
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
        "index.html", title="ホーム", medicine_kinds=medicine_kinds, days=days
    )


# q = sa.select(sa.func.count(Medicine.id)).join(Medicine.user).where(Medicine.user == u, Medicine.is_active==True)


@app.route("/login", methods=["GET", "POST"])
def login():
    # ログインしている場合はインデックスへリダイレクト
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
        if user is None or not user.check_password(form.password.data):
            flash("メールアドレスまたはパスワードが違います")
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
        flash("アカウントを登録しました！ログインしましょう")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/edit_username", methods=["GET", "POST"])
@login_required
def edit_username():
    form = EditUsernameForm()

    if form.validate_on_submit():
        current_user.username = form.username.data
        db.session.commit()
        flash("ユーザー名を変更しました")
        return redirect(url_for("edit_username"))
    elif request.method == "GET":
        form.username.data = current_user.username

    return render_template("edit_username.html", form=form, title="ユーザー名の変更")


@app.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    title = "アカウント削除"
    form = DeleteAccountForm()

    if form.validate_on_submit():
        user = current_user
        db.session.delete(user)
        db.session.commit()
        logout_user()
        flash("アカウントが削除されました。ご利用ありがとうございました。")
        return redirect(url_for("login"))

    return render_template("delete_account.html", form=form, title=title)


@app.route("/medicines", methods=["GET"])
@login_required
def medicines():
    title = "お薬管理"

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
    title = "お薬登録"
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
        flash(f"お薬「{medicine.name}」を登録しました")
        return redirect(url_for("medicines"))

    return render_template("create_medicine.html", form=form, title=title)


@app.route("/medicine_detail/<int:medicine_id>")
@login_required
def medicine_detail(medicine_id):
    title = "お薬詳細"
    # モーダル削除ボタン用
    form = EmptyForm()
    medicine = db.session.get(Medicine, medicine_id)

    if medicine is None or medicine.user_id != current_user.id:
        abort(404)
    return render_template(
        "medicine_detail.html", medicine=medicine, title=title, form=form
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
        form.dose_per_day.data = medicine.dose_per_day
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

    # 現在のユーザーの日々の記録を取得
    query = (
        sa.select(DailyLog)
        .where(DailyLog.user == current_user)
        .order_by(DailyLog.date.desc())
    )
    daily_logs = db.session.scalars(query).all()

    # 各DailyLogに対してdoseがすべて0.0かをチェックする
    for log in daily_logs:
        log.all_doses_zero = all(detail.dose == 0.0 for detail in log.daily_log_details)

    return render_template("daily_logs.html", daily_logs=daily_logs, title=title)


# query = sa.select(DailyLog).where(DailyLog.user == user)
# for log in dailylog2.dailylogdetails:
# print(log.medicine.name)


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
        # TODO 短い書き方に変更
        detail_entry = form.details.append_entry()
        if medicine.dose_per_day is not None:
            if str(medicine.dose_per_day).split(".")[1] == "0":
                detail_entry.dose.data = int(medicine.dose_per_day)
            else:
                detail_entry.dose.data = medicine.dose_per_day

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
    form = EditDailyLogForm(
        mood=daily_log.mood,
        condition=daily_log.condition,
    )

    # POSTリクエストでバリデーションが失敗した場合はフォームエントリの新規追加をしない
    if request.method == "POST" and not form.validate_on_submit():
        pass
    else:
        # GETリクエスト時またはバリデーション成功時のみ新規エントリを追加
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

        for detail in daily_log.daily_log_details:
            # form.details.append_entry()でWTFormsのFieldListに新しいフォームエントリ(項目)を追加
            # フォームエントリに各服用量を設定 float型の数値が整数か判定
            detail_entry = form.details.append_entry(
                {"dose": int(detail.dose) if detail.dose.is_integer() else detail.dose}
            )
            detail_entry.medicine_name = detail.medicine.name
            detail_entry.medicine_unit = detail.medicine.taking_unit.value
            detail_entry.medicine_id.data = detail.medicine.id

        for medicine in active_medicines:
            # medicineがdaily_log_detailsに含まれていなければdetail_entryを設定
            if not any(
                detail.medicine_id == medicine.id
                for detail in daily_log.daily_log_details
            ):
                detail_entry = form.details.append_entry({"dose": None})
                detail_entry.medicine_name = medicine.name
                detail_entry.medicine_unit = medicine.taking_unit.value
                detail_entry.medicine_id.data = medicine.id

    if form.validate_on_submit():
        daily_log.mood = form.mood.data
        daily_log.condition = form.condition.data

        # DailyLogDetailの更新
        for detail_form, detail in zip(
            form.details.entries, daily_log.daily_log_details
        ):
            detail.dose = detail_form.dose.data or 0

        # active_medicinesの追加分もDeilyLogDetailに登録
        for detail_form in form.details.entries[len(daily_log.daily_log_details) :]:
            new_detail = DailyLogDetail(
                dose=detail_form.dose.data or 0,
                medicine_id=detail_form.medicine_id.data,
                daily_log=daily_log,
            )
            db.session.add(new_detail)

        db.session.commit()
        flash(f"{daily_log.date.strftime('%Y/%m/%d')}の記録を更新しました")
        return redirect(url_for("daily_logs"))

    return render_template(
        "edit_daily_log.html",
        daily_log=daily_log,
        form=form,
        title=title,
    )


# for detail in dailylog.daily_log_details:
#    print(detail.medicine.taking_unit.value)
