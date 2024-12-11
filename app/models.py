from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from flask_babel import lazy_gettext as _l


# # お薬服用単位をenum(定数)で定義
# class TakingUnit(enum.Enum):
#     tablet = "錠"
#     capsule = "カプセル"
#     package = "包"
#     mg = "mg"
#     drop = "滴"
#     ml = "ml"

#     # 翻訳を追加
#     @classmethod
#     def get_translated(cls, value):
#         translation_map = {
#             cls.tablet: _l("tablet"),
#             cls.capsule: _l("capsule"),
#             cls.package: _l("package"),
#             cls.mg: _l("mg"),
#             cls.drop: _l("drop"),
#             cls.ml: _l("ml"),
#         }
#         return translation_map.get(value, value)  # 翻訳が見つからない場合はそのまま返す


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64))
    email: so.Mapped[str] = so.mapped_column(sa.String(120), unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    medicines: so.Mapped[list["Medicine"]] = so.relationship(
        cascade="all, delete-orphan", back_populates="user"
    )
    daily_logs: so.Mapped[list["DailyLog"]] = so.relationship(
        cascade="all, delete-orphan", back_populates="user"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}"

    # デバッグ用にクラスのオブジェクトをプリント
    def __repr__(self):
        return f"<User {self.id}, {self.username}>"


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Medicine(db.Model):
    __tablename__ = "medicines"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100))
    taking_start_date: so.Mapped[datetime.date] = so.mapped_column(sa.Date)
    dose_per_day: so.Mapped[Optional[float]]
    taking_timing: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    memo: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
    rating: so.Mapped[Optional[int]] = so.mapped_column(default=0)
    is_active: so.Mapped[bool] = so.mapped_column(sa.Boolean)
    taking_unit: so.Mapped[str] = so.mapped_column(sa.String(10))

    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id))

    user: so.Mapped[User] = so.relationship(back_populates="medicines")
    daily_log_details: so.Mapped[list["DailyLogDetail"]] = so.relationship(
        cascade="all, delete-orphan", back_populates="medicine"
    )

    # デバッグ用にクラスのオブジェクトをプリント
    def __repr__(self):
        return f"<Medicine {self.id}, {self.name}>"


class DailyLog(db.Model):
    __tablename__ = "daily_logs"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    date: so.Mapped[datetime.date] = so.mapped_column(sa.Date)
    mood: so.Mapped[int]
    condition: so.Mapped[int]

    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id))

    user: so.Mapped[User] = so.relationship(back_populates="daily_logs")
    daily_log_details: so.Mapped[list["DailyLogDetail"]] = so.relationship(
        cascade="all, delete-orphan", back_populates="daily_log"
    )

    # デバッグ用にクラスのオブジェクトをプリント
    def __repr__(self):
        return f"<DailyLog {self.id}, {self.date}, user_id:{self.user_id}>"


class DailyLogDetail(db.Model):
    __tablename__ = "daily_log_details"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    dose: so.Mapped[float]

    medicine_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Medicine.id))
    daily_log_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(DailyLog.id))

    medicine: so.Mapped[Medicine] = so.relationship(back_populates="daily_log_details")
    daily_log: so.Mapped[DailyLog] = so.relationship(back_populates="daily_log_details")

    # 複合ユニーク制約
    __table_args__ = (
        sa.UniqueConstraint(
            "medicine_id", "daily_log_id", name="uq_medicine_daily_log"
        ),
    )

    # デバッグ用にクラスのオブジェクトをプリント
    def __repr__(self):
        return f"<DailyLogDetail id:{self.id}, daily_log_id:{self.daily_log_id}, medicine_id:{self.medicine_id}, dose:{self.dose}>"
