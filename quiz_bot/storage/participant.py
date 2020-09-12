import abc
import datetime
import logging
from typing import Optional, Sequence, cast

import sqlalchemy.orm as so
from quiz_bot import db
from quiz_bot.entity import ContextParticipant
from quiz_bot.storage.errors import NoParticipantFoundError

logger = logging.getLogger(__name__)


class IParticipantStorage(abc.ABC):
    @abc.abstractmethod
    def create_participant(self, user_id: int, challenge_id: int) -> ContextParticipant:
        pass

    @abc.abstractmethod
    def get_participation(self, user_id: int, challenge_id: int) -> Optional[ContextParticipant]:
        pass

    @abc.abstractmethod
    def increment_score(self, participant_id: int) -> None:
        pass

    @abc.abstractmethod
    def finish_participation(self, participant_id: int, finished_at: datetime.datetime) -> None:
        pass

    @abc.abstractmethod
    def get_pretenders(self, challenge_id: int) -> Sequence[ContextParticipant]:
        pass

    @abc.abstractmethod
    def has_all_winners(self, challenge_id: int, winner_amount: int) -> bool:
        pass

    @abc.abstractmethod
    def get_participants_amount(self, session: so.Session, challenge_id: int) -> int:
        pass

    @abc.abstractmethod
    def get_pretenders_amount(self, session: so.Session, challenge_id: int) -> int:
        pass

    @abc.abstractmethod
    def get_max_scores(self, session: so.Session, challenge_id: int) -> Optional[int]:
        pass


class ParticipantStorage(IParticipantStorage):
    @staticmethod
    def _get_existing_participant(session: so.Session, user_id: int, challenge_id: int) -> db.Participant:
        db_participant = session.query(db.Participant).get_by_challenge(user_id=user_id, challenge_id=challenge_id)
        if db_participant is None:
            raise NoParticipantFoundError(
                f"No one participant found for user_id {user_id} and challenge_id {challenge_id}"
            )
        return cast(db.Participant, db_participant)

    def create_participant(self, user_id: int, challenge_id: int) -> ContextParticipant:
        with db.create_session() as session:
            session.add(db.Participant(user_id=user_id, challenge_id=challenge_id))
            session.flush()
            return cast(
                ContextParticipant,
                ContextParticipant.from_orm(
                    self._get_existing_participant(session, user_id=user_id, challenge_id=challenge_id)
                ),
            )

    def get_participation(self, user_id: int, challenge_id: int) -> Optional[ContextParticipant]:
        with db.create_session() as session:
            participant = session.query(db.Participant).get_by_challenge(user_id=user_id, challenge_id=challenge_id)
            if participant is not None:
                return cast(ContextParticipant, ContextParticipant.from_orm(participant))
            return None

    def increment_score(self, participant_id: int) -> None:
        with db.create_session() as session:
            db_participant = session.query(db.Participant).get(participant_id)
            db_participant.scores += 1

    def finish_participation(self, participant_id: int, finished_at: datetime.datetime) -> None:
        with db.create_session() as session:
            db_participant = session.query(db.Participant).get(participant_id)
            db_participant.finished_at = finished_at

    def get_pretenders(self, challenge_id: int) -> Sequence[ContextParticipant]:
        with db.create_session() as session:
            db_pretenders = session.query(db.Participant).get_sorted_pretenders(challenge_id=challenge_id)
            return [ContextParticipant.from_orm(pretender) for pretender in db_pretenders]

    def has_all_winners(self, challenge_id: int, winner_amount: int) -> bool:
        with db.create_session() as session:
            db_pretenders: Sequence[db.Participant] = session.query(db.Participant).get_sorted_pretenders(
                challenge_id=challenge_id, limit=winner_amount
            )
            return len(db_pretenders) == winner_amount

    def get_participants_amount(self, session: so.Session, challenge_id: int) -> int:
        return cast(int, session.query(db.Participant).get_participant_amount(challenge_id=challenge_id))

    def get_pretenders_amount(self, session: so.Session, challenge_id: int) -> int:
        return cast(int, session.query(db.Participant).get_pretenders_amount(challenge_id=challenge_id))

    def get_max_scores(self, session: so.Session, challenge_id: int) -> Optional[int]:
        participant = session.query(db.Participant).get_max_scores(challenge_id=challenge_id)
        if participant is not None:
            return cast(int, participant.scores)
        return None
