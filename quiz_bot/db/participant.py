from __future__ import annotations

from typing import Optional, Sequence, cast

import sqlalchemy as sa
import sqlalchemy.orm as so
import sqlalchemy_utils as su
from quiz_bot.db.base import Base, PrimaryKeyMixin
from quiz_bot.db.challenge import Challenge
from quiz_bot.db.user import User


class ParticipantQuery(so.Query):
    def get_by_challenge(self, user_id: int, challenge_id: int) -> Optional[Participant]:
        return cast(
            Optional[Participant],
            self.session.query(Participant)
            .filter(Participant.user_id == user_id, Participant.challenge_id == challenge_id)
            .one_or_none(),
        )

    def get_sorted_pretenders(self, challenge_id: int, limit: Optional[int] = None) -> Sequence[Participant]:
        query = (
            self.session.query(Participant)
            .filter(Participant.challenge_id == challenge_id, Participant.finished_at.isnot(None))
            .order_by(Participant.scores.desc(), Participant.finished_at.asc())
        )
        if limit is not None:
            query = query.limit(limit)
        return cast(Sequence[Participant], query.all())


@su.generic_repr('user', 'challenge_id', 'scores')
class Participant(PrimaryKeyMixin, Base):
    __tablename__ = 'participants'  # type: ignore
    __query_cls__ = ParticipantQuery

    user_id = sa.Column(sa.Integer, sa.ForeignKey(User.id), nullable=False)
    challenge_id = sa.Column(sa.Integer, sa.ForeignKey(Challenge.id), nullable=False)
    finished_at = sa.Column(sa.DateTime(timezone=True))
    scores = sa.Column(sa.Integer, nullable=False)

    user = so.relationship(User, backref=so.backref("result", cascade="all, delete-orphan"))
    challenge = so.relationship(Challenge, backref=so.backref("result", cascade="all, delete-orphan"))

    def __init__(self, user_id: int, challenge_id: int,) -> None:
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.scores = 0
