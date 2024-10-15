from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", title="ホーム")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash("ログインしました！")
        return redirect(url_for("index"))
    return render_template("login.html", form=form)
