from __future__ import annotations

import sqlalchemy as sa
import sqlalchemy.orm as so
import sqlalchemy_utils as su
from quiz_bot.db.base import Base, PrimaryKeyMixin
from quiz_bot.db.user import User


@su.generic_repr('user_id', 'text')
class Message(PrimaryKeyMixin, Base):
    __tablename__ = 'messages'  # type: ignore

    user_id = sa.Column(sa.Integer, sa.ForeignKey(User.id), nullable=False)
    text = sa.Column(sa.String, nullable=False)

    user = so.relationship(User, backref=so.backref("result", cascade="all, delete-orphan"))

    def __init__(self, user_id: int, text: str,) -> None:
        self.user_id = user_id
        self.text = text
