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
