from __future__ import annotations

from typing import Optional, cast

import sqlalchemy as sa
import sqlalchemy.orm as so
from db.base import Base, PrimaryKeyMixin


class ChallengeQuery(so.Query):
    def get_by_name(self, *, name: str) -> Optional[Challenge]:
        with self.session.no_autoflush:
            return cast(Optional[Challenge], self.session.query(Challenge).filter(Challenge.name == name).one_or_none())

    def get_actual(self) -> Optional[Challenge]:
        with self.session.no_autoflush:
            return cast(
                Optional[Challenge],
                self.session.query(Challenge)
                .filter(Challenge.finished_at.is_(None))
                .order_by(Challenge.id.asc())
                .first(),
            )


class Challenge(PrimaryKeyMixin, Base):
    __tablename__ = 'challenges'  # type: ignore
    __query_cls__ = ChallengeQuery

    name = sa.Column(sa.String, nullable=False, unique=True)
    finished_at = sa.Column(sa.DateTime(timezone=True))

    def __init__(self, name: str) -> None:
        self.name = name
