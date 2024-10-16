from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegisterForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.models import User
from urllib.parse import urlsplit


@app.route("/")
@app.route("/index")
@login_required
def index():
    return render_template("index.html", title="ホーム")


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
        flash("ログインしました！")
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
