from __future__ import annotations

import datetime
from typing import List, Optional, cast

import sqlalchemy as sa
import sqlalchemy.orm as so
from quiz_bot.db.base import Base, PrimaryKeyMixin


class ChallengeQuery(so.Query):
    def get_actual(self) -> Optional[Challenge]:
        return cast(
            Optional[Challenge],
            self.session.query(Challenge).filter(Challenge.finished_at.is_(None)).order_by(Challenge.id.asc()).first(),
        )

    def get_finished_ids(self) -> List[int]:
        return cast(
            List[int],
            self.session.query(Challenge).with_entities(Challenge.id).filter(Challenge.finished_at.isnot(None)).all(),
        )


class Challenge(PrimaryKeyMixin, Base):
    __tablename__ = 'challenges'  # type: ignore
    __query_cls__ = ChallengeQuery

    name = sa.Column(sa.String, nullable=False, unique=True)
    phase_amount = sa.Column(sa.Integer, nullable=False)
    winner_amount = sa.Column(sa.Integer, nullable=False)
    duration = sa.Column(sa.Interval, nullable=False)
    finished_at = sa.Column(sa.DateTime(timezone=True))

    def __init__(self, name: str, phase_amount: int, winner_amount: int, duration: datetime.timedelta) -> None:
        self.name = name
        self.phase_amount = phase_amount
        self.winner_amount = winner_amount
        self.duration = duration
