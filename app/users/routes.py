from flask import render_template, redirect, url_for, flash, request
from flask_login import logout_user, current_user, login_required
from flask_babel import _
from app import db
from app.users import bp
from app.users.forms import EditUsernameForm, DeleteAccountForm


@bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    title = _("ユーザー名の変更")
    form = EditUsernameForm()

    if form.validate_on_submit():
        current_user.username = form.username.data
        db.session.commit()
        flash(_("ユーザー名を変更しました"))
        return redirect(url_for("users.edit"))
    elif request.method == "GET":
        form.username.data = current_user.username

    return render_template("users/edit.html", form=form, title=title)


@bp.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    title = _("アカウント削除")
    form = DeleteAccountForm()

    if form.validate_on_submit():
        user = current_user
        db.session.delete(user)
        db.session.commit()
        logout_user()
        flash(_("アカウントが削除されました。ご利用ありがとうございました。"))
        return redirect(url_for("auth.login"))

    return render_template("users/delete.html", form=form, title=title)
