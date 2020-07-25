import abc
import logging
from typing import Optional, cast

from quiz_bot import db
from quiz_bot.storage.context_models import ContextChallenge
from quiz_bot.storage.errors import NoActualChallengeError, StopChallengeIteration
from quiz_bot.utils import get_now

logger = logging.getLogger(__name__)


class IChallengeStorage(abc.ABC):
    @abc.abstractmethod
    def ensure_challenge_exists(self, name: str, phase_amount: int, winner_amount: int) -> None:
        pass

    @staticmethod
    @abc.abstractmethod
    def get_actual_challenge() -> Optional[ContextChallenge]:
        pass

    @abc.abstractmethod
    def start_next_challenge(self) -> ContextChallenge:
        pass


class ChallengeStorage(IChallengeStorage):
    def ensure_challenge_exists(self, name: str, phase_amount: int, winner_amount: int) -> None:
        with db.create_session() as session:
            challenge: Optional[db.Challenge] = session.query(db.Challenge).get_by_name(name)
            if challenge is None:
                session.add(db.Challenge(name=name, phase_amount=phase_amount, winner_amount=winner_amount))

    @staticmethod
    def get_actual_challenge() -> Optional[ContextChallenge]:
        with db.create_session() as session:
            challenge: Optional[db.Challenge] = session.query(db.Challenge).get_actual()
            if challenge is None:
                return None
            return cast(ContextChallenge, ContextChallenge.from_orm(challenge))

    @staticmethod
    def _finish_actual_challenge() -> ContextChallenge:
        with db.create_session(expire_on_commit=False) as session:
            challenge: Optional[db.Challenge] = session.query(db.Challenge).get_actual()
            if challenge is None:
                raise NoActualChallengeError("Has not got any actual challenge!")
            challenge.finished_at = get_now()
            return cast(ContextChallenge, ContextChallenge.from_orm(challenge))

    def start_next_challenge(self) -> ContextChallenge:
        finished_actual_challenge = self._finish_actual_challenge()
        with db.create_session() as session:
            new_challenge: Optional[db.Challenge] = session.query(db.Challenge).filter(
                db.Challenge.id > finished_actual_challenge.id
            ).order_by(db.Challenge.id.asc()).first()
            if new_challenge is None:
                raise StopChallengeIteration
            return cast(ContextChallenge, ContextChallenge.from_orm(new_challenge))
