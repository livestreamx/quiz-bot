from typing import List

from pydantic import BaseModel
from quiz_bot import db
from quiz_bot.storage import IChallengeStorage, IParticipantStorage, IUserStorage


class ChallengeStatistics(BaseModel):
    participants: int
    pretenders: int
    max_scores: int


class QuizStatistics(BaseModel):
    users: int
    challenges: List[ChallengeStatistics]


class StatisticsCollector:
    def __init__(
        self, user_storage: IUserStorage, challenge_storage: IChallengeStorage, participant_storage: IParticipantStorage
    ):
        self._user_storage = user_storage
        self._challenge_storage = challenge_storage
        self._participant_storage = participant_storage

    @property
    def statistics(self) -> QuizStatistics:
        with db.create_session() as session:
            users = self._user_storage.get_user_ids_amount(session)
            challenges: List[ChallengeStatistics] = []
            for challenge_id in self._challenge_storage.get_challenge_ids(session):
                max_scores = self._participant_storage.get_max_scores(session, challenge_id=challenge_id) or 0
                statistics = ChallengeStatistics(
                    participants=self._participant_storage.get_participants_amount(session, challenge_id=challenge_id),
                    pretenders=self._participant_storage.get_pretenders_amount(session, challenge_id=challenge_id),
                    max_scores=max_scores,
                )
                challenges.append(statistics)
            return QuizStatistics(users=users, challenges=challenges)
