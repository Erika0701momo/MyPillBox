from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    TextAreaField,
    BooleanField,
    HiddenField,
    DateField,
    FloatField,
    SelectField,
    MonthField,
)
from wtforms.validators import DataRequired, Length, ValidationError
import re
from flask_babel import lazy_gettext as _l


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


class SelectMonthForm(FlaskForm):
    month = MonthField(format="%Y-%m")
    submit = SubmitField(_l("決定"))
