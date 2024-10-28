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
from app.models import User, TakingUnit
import re


# FloatFieldのデフォルトエラーメッセージを上書き、全角数字判定
class MyFloatField(FloatField):
    def process_formdata(self, valuelist):
        # 入力が空の場合は何もしない
        if not valuelist or not valuelist[0].strip():
            self.data = None
            return

        input_value = valuelist[0]

        # 全角数字を含むかどうかチェック
        if re.search(r"[０-９．]", input_value):
            self.data = None
            raise ValidationError(self.gettext("半角数字で入力してください"))

        # 半角数字のチェック
        try:
            self.data = float(input_value)
        except ValueError:
            self.data = None
            raise ValidationError(self.gettext("半角数字で入力してください"))


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
    dose_per_day = MyFloatField(
        "1日に服用する量",
        render_kw={"placeholder": "例:1　(2.5のように小数点の記入も可能です)"},
    )
    taking_unit = SelectField(
        "服用単位",
        choices=[(unit.name, unit.value) for unit in TakingUnit],
        validators=[DataRequired(message="服用単位は必須入力です")],
    )
    taking_timing = StringField(
        "服用するタイミング",
        validators=[Length(max=100)],
        render_kw={"placeholder": "例:毎食後、就寝前、症状が出た時等"},
    )
    memo = TextAreaField(
        "診察メモ",
        render_kw={
            "placeholder": "このお薬がなぜ処方されたかや、医師からのアドバイス、注意点などを書いてみましょう",
            "rows": "4",
        },
    )
    rating = HiddenField("お薬の評価", render_kw={"value": 0})
    is_active = BooleanField(
        "現在服用中(服用中ならオンにしてください)",
        render_kw={"role": "switch"},
    )
    submit = SubmitField("登録")
