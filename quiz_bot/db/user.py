from __future__ import annotations

from typing import Optional, Sequence, cast

import sqlalchemy as sa
import sqlalchemy.orm as so
import sqlalchemy_utils as su
from quiz_bot.db.base import Base, PrimaryKeyMixin


class UserQuery(so.Query):
    def get_by_external_id(self, value: int) -> Optional[User]:
        return cast(Optional[User], self.session.query(User).filter(User.external_id == value).one_or_none())

    def get_all_user_ids(self) -> Sequence[int]:
        return cast(Sequence[int], self.session.query(User).with_entities(User.id).all())


@su.generic_repr('id', 'first_name', 'last_name', 'external_id', 'nick_name')
class User(PrimaryKeyMixin, Base):
    __tablename__ = 'users'  # type: ignore
    __query_cls__ = UserQuery

    external_id = sa.Column(sa.Integer, nullable=False)
    remote_chat_id = sa.Column(sa.Integer, nullable=False)
    chitchat_id = sa.Column(sa.String, nullable=False)
    first_name = sa.Column(sa.String)
    last_name = sa.Column(sa.String)
    nick_name = sa.Column(sa.String)

    def __init__(
        self,
        external_id: int,
        remote_chat_id: int,
        chitchat_id: str,
        first_name: Optional[str],
        last_name: Optional[str],
        nick_name: Optional[str],
    ) -> None:
        self.external_id = external_id
        self.remote_chat_id = remote_chat_id
        self.chitchat_id = chitchat_id
        self.first_name = first_name
        self.last_name = last_name
        self.nick_name = nick_name
