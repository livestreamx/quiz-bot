import abc
import logging
from typing import Optional, Sequence, cast

import sqlalchemy.orm as so
from quiz_bot import db
from quiz_bot.entity import ContextChallenge
from quiz_bot.storage.errors import NoActualChallengeError
from quiz_bot.utils import get_now

logger = logging.getLogger(__name__)


class IChallengeStorage(abc.ABC):
    @abc.abstractmethod
    def create_challenge(self, name: str, phase_amount: int, winner_amount: int) -> ContextChallenge:
        pass

    @staticmethod
    @abc.abstractmethod
    def get_actual_challenge() -> Optional[ContextChallenge]:
        pass

    @staticmethod
    @abc.abstractmethod
    def finish_actual_challenge() -> ContextChallenge:
        pass

    @abc.abstractmethod
    def get_challenge(self, challenge_id: int) -> Optional[ContextChallenge]:
        pass

    @abc.abstractmethod
    def get_finished_challenge_ids(self) -> Sequence[int]:
        pass

    @abc.abstractmethod
    def get_challenge_ids(self, session: so.Session) -> Sequence[int]:
        pass


class ChallengeStorage(IChallengeStorage):
    def create_challenge(self, name: str, phase_amount: int, winner_amount: int) -> ContextChallenge:
        with db.create_session() as session:
            challenge = db.Challenge(name=name, phase_amount=phase_amount, winner_amount=winner_amount)
            session.add(challenge)
            session.flush()
            return cast(ContextChallenge, ContextChallenge.from_orm(challenge))

    @staticmethod
    def get_actual_challenge() -> Optional[ContextChallenge]:
        with db.create_session() as session:
            challenge: Optional[db.Challenge] = session.query(db.Challenge).get_actual()
            if challenge is None:
                return None
            return cast(ContextChallenge, ContextChallenge.from_orm(challenge))

    @staticmethod
    def finish_actual_challenge() -> ContextChallenge:
        with db.create_session(expire_on_commit=False) as session:
            challenge: Optional[db.Challenge] = session.query(db.Challenge).get_actual()
            if challenge is None:
                raise NoActualChallengeError("Has not got any actual challenge!")
            challenge.finished_at = get_now()
            return cast(ContextChallenge, ContextChallenge.from_orm(challenge))

    def get_challenge(self, challenge_id: int) -> Optional[ContextChallenge]:
        with db.create_session() as session:
            challenge = session.query(db.Challenge).get(challenge_id)
            if challenge is None:
                return None
            return cast(ContextChallenge, ContextChallenge.from_orm(challenge))

    def get_finished_challenge_ids(self) -> Sequence[int]:
        with db.create_session() as session:
            return cast(Sequence[int], session.query(db.Challenge).get_finished_ids())

    def get_challenge_ids(self, session: so.Session) -> Sequence[int]:
        return cast(Sequence[int], session.query(db.Challenge.id).distinct())
