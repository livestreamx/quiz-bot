from __future__ import annotations

import sqlalchemy as sa
import sqlalchemy.orm as so
import sqlalchemy_utils as su
from quiz_bot.db import Challenge, User
from quiz_bot.db.base import Base, PrimaryKeyMixin


class ParticipantQuery(so.Query):
    pass


@su.generic_repr('user', 'challenge_id', 'scores')
class Participant(PrimaryKeyMixin, Base):
    __tablename__ = 'participants'  # type: ignore
    __query_cls__ = ParticipantQuery

    user_id = sa.Column(sa.Integer, sa.ForeignKey(User.id), nullable=False)
    challenge_id = sa.Column(sa.Integer, sa.ForeignKey(Challenge.id), nullable=False)
    scores = sa.Column(sa.Integer, nullable=False)

    user = so.relationship(User, backref=so.backref("result", cascade="all, delete-orphan"))
    challenge = so.relationship(Challenge, backref=so.backref("result", cascade="all, delete-orphan"))

    def __init__(self, user_id: int, challenge_id: int,) -> None:
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.scores = 0
