from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class LoginForm(FlaskForm):
    email = StringField(
        "メールアドレス",
        validators=[
            DataRequired(message="メールアドレスは必須入力です"),
            Email(message="正しいメールアドレスの形式で入力してください"),
        ],
    )
    password = PasswordField(
        "パスワード", validators=[DataRequired(message="パスワードは必須入力です")]
    )
    submit = SubmitField("ログイン")
