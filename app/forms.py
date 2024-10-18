from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
import sqlalchemy as sa
from app import db
from app.models import User


class LoginForm(FlaskForm):
    email = StringField(
        "メールアドレス",
        validators=[
            DataRequired(message="メールアドレスは必須入力です"),
            Email(message="正しいメールアドレスの形式で入力してください"),
        ],
        render_kw={"placeholder": "name@example.com"},
    )
    password = PasswordField(
        "パスワード",
        validators=[DataRequired(message="パスワードは必須入力です")],
        render_kw={"placeholder": "Password"},
    )
    submit = SubmitField("ログイン")


class RegisterForm(FlaskForm):
    username = StringField(
        "ユーザー名",
        validators=[DataRequired(message="ユーザー名は必須入力です"), Length(max=64)],
        render_kw={"placeholder": "username"},
    )
    email = StringField(
        "メールアドレス",
        validators=[
            DataRequired(message="メールアドレスは必須入力です"),
            Length(max=120),
            Email(message="正しいメールアドレスの形式で入力してください"),
        ],
        render_kw={"placeholder": "name@example.com"},
    )
    password = PasswordField(
        "パスワード",
        validators=[DataRequired(message="パスワードは必須入力です"), Length(max=60)],
        render_kw={"placeholder": "Password"},
    )
    password2 = PasswordField(
        "パスワード(確認用)",
        validators=[
            DataRequired(message="パスワード(確認用)は必須入力です"),
            EqualTo("password", "パスワードが一致しません"),
            Length(max=60),
        ],
        render_kw={"placeholder": "Password2"},
    )
    submit = SubmitField("新規登録")

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError(
                "既に登録済みのメールアドレスです 違うアドレスを入力してください"
            )


class EditUsernameForm(FlaskForm):
    username = StringField(
        "ユーザー名",
        validators=[
            DataRequired(message="新しいユーザー名を入力してください"),
            Length(max=64),
        ],
    )
    submit = SubmitField("変更")


class DeleteAccountForm(FlaskForm):
    submit = SubmitField("削除する")
