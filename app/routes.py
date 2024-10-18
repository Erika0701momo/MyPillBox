from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegisterForm, EditUsernameForm, DeleteAccountForm
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
        .where(Medicine.user_id == current_user.id, Medicine.is_active == True)
    )
    medicine_kinds = db.session.scalar(query)
    return render_template("index.html", title="ホーム", medicine_kinds=medicine_kinds)


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
