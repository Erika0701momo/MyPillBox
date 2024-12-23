from flask_wtf import FlaskForm
from wtforms import (
    SubmitField,
    HiddenField,
    DateField,
    FloatField,
    FieldList,
    FormField,
    Form,
)
from wtforms.validators import DataRequired, ValidationError
import sqlalchemy as sa
from app import db
from app.models import DailyLog
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
