import abc
import logging
from datetime import datetime
from typing import Sequence, cast

from quiz_bot import db
from quiz_bot.storage.context_models import ContextChallenge, ContextResult, ContextUser
from quiz_bot.storage.errors import NoResultFoundError

logger = logging.getLogger(__name__)


class IResultStorage(abc.ABC):
    @abc.abstractmethod
    def create_result(self, user: ContextUser, challenge: ContextChallenge, phase: int) -> None:
        pass

    @abc.abstractmethod
    def prepare_next_result(self, result: ContextResult, next_phase: int) -> None:
        pass

    @abc.abstractmethod
    def finish_phase(self, result: ContextResult, finish_time: datetime) -> None:
        pass

    @abc.abstractmethod
    def get_last_result(self, user: ContextUser) -> ContextResult:
        pass

    @abc.abstractmethod
    def get_equal_results(self, result: ContextResult) -> Sequence[ContextResult]:
        pass


class ResultStorage(IResultStorage):
    def create_result(self, user: ContextUser, challenge: ContextChallenge, phase: int) -> None:
        with db.create_session() as session:
            session.add(db.Result(user_id=user.id, challenge_id=challenge.id, phase=phase))

    def prepare_next_result(self, result: ContextResult, next_phase: int) -> None:
        self.create_result(user=result.user, challenge=result.challenge, phase=next_phase)

    def finish_phase(self, result: ContextResult, finish_time: datetime) -> None:
        with db.create_session() as session:
            db_result = session.query(db.Result).filter(db.Result.id == result.id).one()
            db_result.finished_at = finish_time

    def get_last_result(self, user: ContextUser) -> ContextResult:
        with db.create_session() as session:
            result = session.query(db.Result).last_for_user(user_id=user.id)
            if result is None:
                raise NoResultFoundError(f"Not found any Result for User={user}")
            return cast(ContextResult, ContextResult.from_orm(result))

    def get_equal_results(self, result: ContextResult) -> Sequence[ContextResult]:
        with db.create_session() as session:
            return cast(
                Sequence[ContextResult],
                session.query(db.Result).get_equal_results(
                    challenge_id=result.challenge.id, phase=result.phase, finished=bool(result.finished_at is not None)
                ),
            )
