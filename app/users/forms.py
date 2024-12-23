from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_babel import lazy_gettext as _l


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
