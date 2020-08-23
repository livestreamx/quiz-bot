import abc
import logging
from datetime import datetime
from typing import cast

from quiz_bot import db
from quiz_bot.entity import ContextResult
from quiz_bot.storage.errors import NoResultFoundError

logger = logging.getLogger(__name__)


class IResultStorage(abc.ABC):
    @abc.abstractmethod
    def create_result(self, participant_id: int, phase: int) -> None:
        pass

    @abc.abstractmethod
    def finish_phase(self, result: ContextResult, finish_time: datetime) -> None:
        pass

    @abc.abstractmethod
    def get_last_result(self, participant_id: int) -> ContextResult:
        pass


class ResultStorage(IResultStorage):
    def create_result(self, participant_id: int, phase: int) -> None:
        with db.create_session() as session:
            session.add(db.Result(participant_id=participant_id, phase=phase))

    def finish_phase(self, result: ContextResult, finish_time: datetime) -> None:
        with db.create_session() as session:
            db_result = session.query(db.Result).filter(db.Result.id == result.id).one()
            db_result.finished_at = finish_time

    def get_last_result(self, participant_id: int) -> ContextResult:
        with db.create_session() as session:
            result = session.query(db.Result).last_for_participant(participant_id=participant_id)
            if result is None:
                raise NoResultFoundError(f"Not found any Result for Participant with ID {participant_id}")
            return cast(ContextResult, ContextResult.from_orm(result))
