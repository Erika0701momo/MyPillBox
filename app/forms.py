from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    TextAreaField,
    BooleanField,
    HiddenField,
    DateField,
    FloatField,
    SelectField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
import sqlalchemy as sa
from app import db
from app.models import User


class MyFloatField(FloatField):
    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = float(valuelist[0])
            except ValueError:
                self.data = None
                raise ValueError(self.gettext("半角数字で入力してください"))


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


class CreateMedicineFrom(FlaskForm):
    name = StringField(
        "お薬の名前",
        validators=[DataRequired(message="お薬の名前は必須入力です"), Length(max=100)],
        render_kw={"placeholder": "例:デパス0.5mg"},
    )
    taking_start_date = DateField(
        "服用開始日",
        format="%Y-%m-%d",
        validators=[DataRequired(message="服用開始日は必須入力です")],
    )
    dose_per_day = MyFloatField("1日に服用する量", render_kw={"placeholder": "例:1 "})
    # taking_unit = SelectField(
    #     "服用単位", validators=[DataRequired(message="服用単位は必須入力です")]
    # )
    # memo = TextAreaField(
    #     "診察メモ",
    #     render_kw={
    #         "placeholder": "このお薬がなぜ処方されたかや、医師からのアドバイスなどを書いてください"
    #     },
    # )
    # rating = HiddenField("お薬の評価")
    # is_active = BooleanField("現在服用中(服用中ならチェックを付けてください)")
    submit = SubmitField("登録")

    def validate_dose_per_day(self, dose_per_day):
        try:
            float(dose_per_day.data)
        except:
            raise ValidationError("半角数字で入力してください")
