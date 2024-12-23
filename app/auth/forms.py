from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
import sqlalchemy as sa
from app import db
from app.models import User


class LoginForm(FlaskForm):
    email = StringField(
        _l("メールアドレス"),
        validators=[
            DataRequired(message=_l("メールアドレスは必須入力です")),
            Email(message=_l("正しいメールアドレスの形式で入力してください")),
        ],
        render_kw={"placeholder": "name@example.com"},
    )
    password = PasswordField(
        _l("パスワード"),
        validators=[DataRequired(message=_l("パスワードは必須入力です"))],
        render_kw={"placeholder": "Password"},
    )
    submit = SubmitField(_l("ログイン"))


class RegisterForm(FlaskForm):
    username = StringField(
        _l("ユーザー名"),
        validators=[
            DataRequired(message=_l("ユーザー名は必須入力です")),
            Length(max=64),
        ],
        render_kw={"placeholder": "username"},
    )
    email = StringField(
        _l("メールアドレス"),
        validators=[
            DataRequired(message=_l("メールアドレスは必須入力です")),
            Length(max=120),
            Email(message=_l("正しいメールアドレスの形式で入力してください")),
        ],
        render_kw={"placeholder": "name@example.com"},
    )
    password = PasswordField(
        _l("パスワード"),
        validators=[
            DataRequired(message=_l("パスワードは必須入力です")),
            Length(max=60),
        ],
        render_kw={"placeholder": "Password"},
    )
    password2 = PasswordField(
        _l("パスワード(確認用)"),
        validators=[
            DataRequired(message=_l("パスワード(確認用)は必須入力です")),
            EqualTo("password", _l("パスワードが一致しません")),
            Length(max=60),
        ],
        render_kw={"placeholder": "Password2"},
    )
    submit = SubmitField(_l("新規登録"))

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError(
                _l("既に登録済みのメールアドレスです 違うアドレスを入力してください")
            )
