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
    FieldList,
    FormField,
    Form,
    MonthField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
import sqlalchemy as sa
from app import db
from app.models import User, DailyLog
import re
from flask_login import current_user
from flask_babel import lazy_gettext as _l


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
            self.data = input_value  # 入力値を保持
            raise ValidationError(self.gettext(_l("半角数字で入力してください")))

        # 半角数字のチェック
        try:
            self.data = float(input_value)
        except ValueError:
            self.data = input_value  # 入力値を保持
            raise ValidationError(self.gettext(_l("半角数字で入力してください")))


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


class EditUsernameForm(FlaskForm):
    username = StringField(
        _l("ユーザー名"),
        validators=[
            DataRequired(message=_l("新しいユーザー名を入力してください")),
            Length(max=64),
        ],
    )
    submit = SubmitField(_l("変更"))


class DeleteAccountForm(FlaskForm):
    submit = SubmitField(_l("削除する"))


class CreateMedicineFrom(FlaskForm):
    name = StringField(
        _l("お薬の名前"),
        validators=[
            DataRequired(message=_l("お薬の名前は必須入力です")),
            Length(max=100),
        ],
        render_kw={"placeholder": _l("例:デパス0.5mg")},
    )
    taking_start_date = DateField(
        _l("服用開始日"),
        format="%Y-%m-%d",
        validators=[DataRequired(message=_l("服用開始日は必須入力です"))],
    )
    dose_per_day = MyFloatField(
        _l("1日に服用する量"),
        render_kw={"placeholder": _l("例:1　(2.5のように小数点の記入も可能です)")},
    )
    taking_unit = SelectField(
        _l("服用単位"),
        choices=[
            ("tablet", _l("錠")),
            ("capsule", _l("カプセル")),
            ("packet", _l("包")),
            ("mg", _l("mg")),
            ("drop", _l("滴")),
            ("ml", _l("ml")),
        ],
        validators=[DataRequired(message=_l("服用単位は必須入力です"))],
    )
    taking_timing = StringField(
        _l("服用するタイミング"),
        validators=[Length(max=100)],
        render_kw={"placeholder": _l("例:毎食後、就寝前、症状が出た時等")},
    )
    memo = TextAreaField(
        _l("診察メモ"),
        render_kw={
            "placeholder": _l(
                "このお薬がなぜ処方されたかや、医師からのアドバイス、注意点などを書いてみましょう"
            ),
            "rows": "4",
        },
    )
    rating = HiddenField(_l("あなたのこのお薬への評価"), default=0)
    is_active = BooleanField(
        _l("現在服用中(服用中ならオンにしてください)"),
        render_kw={"role": "switch"},
    )
    submit = SubmitField(_l("登録"))


class MedicineSortForm(FlaskForm):
    active_sort = SelectField(
        _l("並び替え"),
        choices=[("registerorder", _l("登録順")), ("ratingorder", _l("星評価順"))],
    )
    not_active_sort = SelectField(
        _l("並び替え"),
        choices=[("registerorder", _l("登録順")), ("ratingorder", _l("星評価順"))],
    )


class EditMedicineForm(FlaskForm):
    name = StringField(
        _l("お薬の名前"),
        validators=[
            DataRequired(message=_l("お薬の名前は必須入力です")),
            Length(max=100),
        ],
        render_kw={"placeholder": _l("例:デパス0.5mg")},
    )
    taking_start_date = DateField(
        _l("服用開始日"),
        format="%Y-%m-%d",
        validators=[DataRequired(message=_l("服用開始日は必須入力です"))],
    )
    dose_per_day = MyFloatField(
        _l("1日に服用する量"),
        render_kw={"placeholder": _l("例:1　(2.5のように小数点の記入も可能です)")},
    )
    taking_timing = StringField(
        _l("服用するタイミング"),
        validators=[Length(max=100)],
        render_kw={"placeholder": _l("例:毎食後、就寝前、症状が出た時等")},
    )
    memo = TextAreaField(
        _l("診察メモ"),
        render_kw={
            "placeholder": _l(
                "このお薬がなぜ処方されたかや、医師からのアドバイス、注意点などを書いてみましょう"
            ),
            "rows": "4",
        },
    )
    rating = HiddenField(_l("あなたのこのお薬への評価"))
    is_active = BooleanField(
        _l("現在服用中(オフにすると、服用中でないお薬に移動します)"),
        render_kw={"role": "switch"},
    )
    local_month = HiddenField()
    submit = SubmitField(_l("更新"))


# 削除モーダル用　POSTで送信してデータベースに変更を加えるのでCSRF対策のためwtformsで削除ボタンを作る
class EmptyForm(FlaskForm):
    submit = SubmitField(_l("削除する"))


# DailyLogFormとEditDailyLogFormのサブフォーム
class DailyLogDetailForm(Form):
    dose = MyFloatField(_l("服用量"))


class DailyLogForm(FlaskForm):
    date = DateField(
        _l("日付を選んでください"),
        format="%Y-%m-%d",
        validators=[DataRequired(message=_l("日付は必須入力です"))],
    )
    mood = HiddenField(
        _l("その日の気分を教えてください"),
        validators=[DataRequired(message=_l("気分は必須入力です"))],
    )

    condition = HiddenField(
        _l("その日の体調を教えてください"),
        validators=[DataRequired(message=_l("体調は必須入力です"))],
    )
    # detailsに、複数のDailyLogDetailFormを持たせる
    details = FieldList(FormField(DailyLogDetailForm))
    submit = SubmitField(_l("登録"))

    # 既に登録されている日付を入力したらバリデーションエラーを表示
    def validate_date(self, date):
        registerd_date = db.session.scalar(
            sa.select(DailyLog)
            .join(DailyLog.user)
            .where(DailyLog.user == current_user, DailyLog.date == date.data)
        )
        if registerd_date is not None:
            raise ValidationError(
                _l(
                    "既に登録済みの日付です 違う日付を選択するか、日々の記録一覧からその日付の記録を編集してださい"
                )
            )


class EditDailyLogForm(FlaskForm):
    mood = HiddenField(
        _l("その日の気分を教えてください"),
        validators=[DataRequired(message=_l("気分は必須入力です"))],
    )

    condition = HiddenField(
        _l("その日の体調を教えてください"),
        validators=[DataRequired(message=_l("体調は必須入力です"))],
    )
    # daily_log_detailsとadded_meds_detailsに、複数のDailyLogDetailFormを持たせる
    daily_log_details = FieldList(FormField(DailyLogDetailForm))
    added_meds_details = FieldList(FormField(DailyLogDetailForm))
    submit = SubmitField(_l("更新"))


class SelectMonthForm(FlaskForm):
    month = MonthField(format="%Y-%m")
    submit = SubmitField(_l("決定"))
