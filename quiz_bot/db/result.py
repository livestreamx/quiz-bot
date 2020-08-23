from __future__ import annotations

from typing import Optional, cast

import sqlalchemy as sa
import sqlalchemy.orm as so
from quiz_bot.db import Participant
from quiz_bot.db.base import Base, PrimaryKeyMixin
from quiz_bot.db.challenge import Challenge


class ResultQuery(so.Query):
    def last_for_participant(self, participant_id: int) -> Optional[Result]:
        return cast(
            Optional[Result],
            self.session.query(Result)
            .filter(Result.participant_id == participant_id)
            .order_by(Result.phase.desc())
            .first(),
        )


class Result(PrimaryKeyMixin, Base):
    __tablename__ = 'results'  # type: ignore
    __query_cls__ = ResultQuery

    participant_id = sa.Column(sa.Integer, sa.ForeignKey(Participant.id), nullable=False)
    phase = sa.Column(sa.Integer, nullable=False)
    finished_at = sa.Column(sa.DateTime(timezone=True))

    participant = so.relationship(Participant, backref=so.backref("result", cascade="all, delete-orphan"))
    challenge = so.relationship(Challenge, backref=so.backref("result", cascade="all, delete-orphan"))

    def __init__(self, participant_id: int, phase: int) -> None:
        self.participant_id = participant_id
        self.phase = phase
