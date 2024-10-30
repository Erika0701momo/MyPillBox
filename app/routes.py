from flask import render_template, flash, redirect, url_for, request, abort
from app import app, db
from app.forms import (
    LoginForm,
    RegisterForm,
    EditUsernameForm,
    DeleteAccountForm,
    CreateMedicineFrom,
    MedicineSortForm,
)
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models import User, Medicine, TakingUnit
from urllib.parse import urlsplit


@app.route("/")
@app.route("/index")
@login_required
def index():
    # 服用中の薬の種類を取得
    query = (
        sa.select(sa.func.count(Medicine.id))
        .join(Medicine.user)
        .where(Medicine.user == current_user, Medicine.is_active == True)
    )
    medicine_kinds = db.session.scalar(query)

    return render_template("index.html", title="ホーム", medicine_kinds=medicine_kinds)


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

    return render_template("edit_username.html", title="ユーザー名の変更", form=form)


@app.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    form = DeleteAccountForm()

    if form.validate_on_submit():
        user = current_user
        db.session.delete(user)
        db.session.commit()
        logout_user()
        flash("アカウントが削除されました。ご利用ありがとうございました。")
        return redirect(url_for("login"))

    return render_template("delete_account.html", form=form)


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

    return render_template("create_medicine.html", form=form)


@app.route("/medicine_detail/<int:medicine_id>")
@login_required
def medicine_detail(medicine_id):
    medicine = db.session.get(Medicine, medicine_id)
    if medicine is None or medicine.user_id != current_user.id:
        abort(404)
    return render_template("medicine_detail.html")
