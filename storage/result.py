import abc
import logging
from typing import Sequence, cast

import db
import sqlalchemy.orm as so
from storage.models import ContextChallenge, ContextUser, ContextResult

logger = logging.getLogger(__name__)


class IResultStorage(abc.ABC):
    @abc.abstractmethod
    def set_phase(self, user: ContextUser, challenge: ContextChallenge) -> None:
        pass

    @abc.abstractmethod
    def get_phase(self, user: ContextUser) -> Sequence[ContextWinner]:
        pass


class ResultStorage(IResultStorage):
    @staticmethod
    def _get_db_user(session: so.Session, internal_id: int) -> db.User:
        return cast(db.User, session.query(db.User).filter(db.User.id == internal_id).one())

    @staticmethod
    def _get_winners(session: so.Session, challenge_id: int) -> Sequence[db.Winner]:
        return cast(Sequence[db.Winner], session.query(db.Winner).filter(db.Winner.challenge_id == challenge_id).all())

    def set_winner(self, challenge: ContextChallenge, user: ContextUser) -> None:
        with db.create_session() as session:
            internal_user = self._get_db_user(session, internal_id=user.id)
            winner: db.Winner = db.Winner(challenge_id=challenge.id, user_id=internal_user.id)
            session.add(winner)

    def get_winners_by_challenge_id(self, challenge_id: int) -> Sequence[ContextWinner]:
        with db.create_session() as session:
            winners = self._get_winners(session, challenge_id=challenge_id)
            return tuple(ContextWinner.from_orm(winner) for winner in winners)
