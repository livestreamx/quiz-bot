from __future__ import annotations

from typing import Sequence, cast

import sqlalchemy as sa
import sqlalchemy.orm as so
import sqlalchemy_utils as su
from quiz_bot.db.base import Base, PrimaryKeyMixin


class MessageQuery(so.Query):
    def get_message_ids(self, limit: int) -> Sequence[int]:
        return cast(Sequence[int], self.session.query(Message).with_entities(Message.id).limit(limit).all())


@su.generic_repr('user_id', 'text')
class Message(PrimaryKeyMixin, Base):
    __tablename__ = 'messages'  # type: ignore
    __query_cls__ = MessageQuery

    text = sa.Column(sa.String, nullable=False)

    def __init__(self, text: str,) -> None:
        self.text = text
