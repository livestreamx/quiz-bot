import abc
import logging
from typing import Optional, Sequence, cast

import sqlalchemy.orm as so
from quiz_bot import db
from quiz_bot.entity import ContextParticipant
from quiz_bot.storage.errors import NoParticipantFoundError
from quiz_bot.utils import get_now

logger = logging.getLogger(__name__)


class IParticipantStorage(abc.ABC):
    @abc.abstractmethod
    def create_participant(self, user_id: int, challenge_id: int) -> None:
        pass

    @abc.abstractmethod
    def get_participation(self, user_id: int, challenge_id: int) -> Optional[db.Participant]:
        pass

    @abc.abstractmethod
    def increment_score(self, user_id: int, challenge_id: int) -> None:
        pass

    @abc.abstractmethod
    def finish_participation(self, user_id: int, challenge_id: int) -> None:
        pass

    @abc.abstractmethod
    def get_pretenders(self, challenge_id: int) -> Sequence[ContextParticipant]:
        pass


class ParticipantStorage(IParticipantStorage):
    def create_participant(self, user_id: int, challenge_id: int) -> None:
        with db.create_session() as session:
            session.add(db.Participant(user_id=user_id, challenge_id=challenge_id))

    def get_participation(self, user_id: int, challenge_id: int) -> Optional[ContextParticipant]:
        with db.create_session() as session:
            participant = session.query(db.Participant).get_by_challenge(user_id=user_id, challenge_id=challenge_id)
            if participant is not None:
                return cast(ContextParticipant, ContextParticipant.from_orm(participant))
            return None

    @staticmethod
    def _get_existing_participant(session: so.Session, user_id: int, challenge_id: int) -> db.Participant:
        db_participant = session.query(db.Participant).get_by_challenge(user_id=user_id, challenge_id=challenge_id)
        if db_participant is None:
            raise NoParticipantFoundError(
                f"No one participant found for user_id {user_id} and challenge_id {challenge_id}"
            )
        return cast(db.Participant, db_participant)

    def increment_score(self, user_id: int, challenge_id: int) -> None:
        with db.create_session() as session:
            db_participant = self._get_existing_participant(session=session, user_id=user_id, challenge_id=challenge_id)
            db_participant.scores += 1

    def finish_participation(self, user_id: int, challenge_id: int) -> None:
        with db.create_session() as session:
            db_participant = self._get_existing_participant(session=session, user_id=user_id, challenge_id=challenge_id)
            db_participant.finished_at = get_now()

    def get_pretenders(self, challenge_id: int) -> Sequence[ContextParticipant]:
        with db.create_session() as session:
            db_pretenders = session.query(db.Participant).get_sorted_pretenders(challenge_id=challenge_id)
            return [ContextParticipant.from_orm(pretender) for pretender in db_pretenders]
