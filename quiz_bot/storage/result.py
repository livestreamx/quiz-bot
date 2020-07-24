import abc
import logging
from typing import cast

from quiz_bot import db
from quiz_bot.storage.context_models import ContextChallenge, ContextResult, ContextUser
from quiz_bot.storage.errors import NoResultFoundError
from quiz_bot.utils import get_now

logger = logging.getLogger(__name__)


class IResultStorage(abc.ABC):
    @abc.abstractmethod
    def set_phase(self, user: ContextUser, challenge: ContextChallenge, phase: int) -> None:
        pass

    @abc.abstractmethod
    def finish_phase(self, user: ContextUser, challenge: ContextChallenge, phase: int) -> None:
        pass

    @abc.abstractmethod
    def get_last_phase(self, user: ContextUser) -> ContextResult:
        pass


class ResultStorage(IResultStorage):
    def set_phase(self, user: ContextUser, challenge: ContextChallenge, phase: int) -> None:
        with db.create_session() as session:
            session.add(db.Result(user_id=user.id, challenge_id=challenge.id, phase=phase))

    def finish_phase(self, user: ContextUser, challenge: ContextChallenge, phase: int) -> None:
        with db.create_session() as session:
            result = session.query(db.Result).get_by_ids(user_id=user.id, challenge_id=challenge.id, phase=phase)
            if result is None:
                raise NoResultFoundError(
                    f"Could not finish phase - not found any Result!\nUser={user}, Challenge={challenge}, phase={phase}"
                )
            result.finished_at = get_now()

    def get_last_phase(self, user: ContextUser) -> ContextResult:
        with db.create_session() as session:
            result = session.query(db.Result).last_for_user(user_id=user.id)
            if result is None:
                raise NoResultFoundError(f"Not found any Result for User={user}")
            return cast(ContextResult, ContextResult.from_orm(result))
