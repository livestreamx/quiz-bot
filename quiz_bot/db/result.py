from __future__ import annotations

from typing import Any, Optional, Sequence, cast

import sqlalchemy as sa
import sqlalchemy.orm as so
from quiz_bot.db.base import Base, PrimaryKeyMixin
from quiz_bot.db.challenge import Challenge
from quiz_bot.db.user import User


def _get_finish_condition(finished: bool) -> Any:
    if finished:
        return Result.finished_at.isnot(None)
    return Result.finished_at.is_(None)


class ResultQuery(so.Query):
    def get_by_ids(self, user_id: int, challenge_id: int, phase: int) -> Result:
        return cast(
            Result,
            self.session.query(Result)
            .filter(Result.user_id == user_id, Result.challenge_id == challenge_id, Result.phase == phase)
            .one(),
        )

    def last_for_user(self, user_id: int) -> Optional[Result]:
        return cast(
            Optional[Result],
            self.session.query(Result)
            .filter(Result.user_id == user_id)
            .order_by(Result.challenge_id.desc(), Result.phase.desc())
            .first(),
        )

    def get_equal_results(self, challenge_id: int, phase: int, finished: bool) -> Sequence[Result]:
        return cast(
            Sequence[Result],
            self.session.query(Result)
            .filter(Result.challenge_id == challenge_id, Result.phase == phase, _get_finish_condition(finished))
            .all(),
        )


class Result(PrimaryKeyMixin, Base):
    __tablename__ = 'results'  # type: ignore
    __query_cls__ = ResultQuery

    user_id = sa.Column(sa.Integer, sa.ForeignKey(User.id), nullable=False)
    challenge_id = sa.Column(sa.Integer, sa.ForeignKey(Challenge.id), nullable=False)
    phase = sa.Column(sa.Integer, nullable=False)
    finished_at = sa.Column(sa.DateTime(timezone=True))

    user = so.relationship(User, backref=so.backref("result", cascade="all, delete-orphan"))
    challenge = so.relationship(Challenge, backref=so.backref("result", cascade="all, delete-orphan"))

    def __init__(self, user_id: int, challenge_id: int, phase: int) -> None:
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.phase = phase
