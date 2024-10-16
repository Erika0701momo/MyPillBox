from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
import datetime
import enum
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# お薬服用単位をenum(定数)で定義
class TakingUnit(enum.Enum):
    tablet = "錠"
    package = "包"
    mg = "mg"
    drop = "滴"
    ml = "ml"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64))
    email: so.Mapped[str] = so.mapped_column(sa.String(120), unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    medicines: so.Mapped[list["Medicine"]] = so.relationship(
        cascade="all, delete-orphan", back_populates="user"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    memo: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
    rating: so.Mapped[Optional[int]] = so.mapped_column(default=0)
    is_active: so.Mapped[bool] = so.mapped_column(sa.Boolean)
    taking_unit: so.Mapped[TakingUnit] = so.mapped_column(sa.Enum(TakingUnit))

    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id))

    user: so.Mapped[User] = so.relationship(back_populates="medicines")

    # デバッグ用にクラスのオブジェクトをプリント
    def __repr__(self):
        return f"<Medicine {self.id}, {self.name}>"
