from __future__ import annotations

from typing import Sequence, cast

import sqlalchemy as sa
import sqlalchemy.orm as so
import sqlalchemy_utils as su
from quiz_bot.db.base import Base, PrimaryKeyMixin
from quiz_bot.db.user import User


class MessageQuery(so.Query):
    def get_all_message_ids(self) -> Sequence[int]:
        return cast(Sequence[int], self.session.query(Message).with_entities(Message.id).all())


@su.generic_repr('user_id', 'text')
class Message(PrimaryKeyMixin, Base):
    __tablename__ = 'messages'  # type: ignore
    __query_cls__ = MessageQuery

    user_id = sa.Column(sa.Integer, sa.ForeignKey(User.id), nullable=False)
    text = sa.Column(sa.String, nullable=False)

    user = so.relationship(User, backref=so.backref("user", cascade="all, delete-orphan"))

    def __init__(self, user_id: int, text: str,) -> None:
        self.user_id = user_id
        self.text = text
