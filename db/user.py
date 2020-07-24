from typing import Optional

import sqlalchemy as sa
import sqlalchemy_utils as su
from db.base import Base, PrimaryKeyMixin


@su.generic_repr('id', 'first_name', 'last_name', 'external_id', 'nick_name')
class User(PrimaryKeyMixin, Base):
    __tablename__ = 'users'  # type: ignore

    external_id = sa.Column(sa.Integer, nullable=False)
    chitchat_id = sa.Column(sa.String, nullable=False)
    first_name = sa.Column(sa.String)
    last_name = sa.Column(sa.String)
    nick_name = sa.Column(sa.String)

    def __init__(
        self,
        external_id: int,
        chitchat_id: str,
        first_name: Optional[str],
        last_name: Optional[str],
        nick_name: Optional[str],
    ) -> None:
        self.external_id = external_id
        self.chitchat_id = chitchat_id
        self.first_name = first_name
        self.last_name = last_name
        self.nick_name = nick_name
