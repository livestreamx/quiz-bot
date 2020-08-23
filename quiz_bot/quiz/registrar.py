from collections import Sequence
from typing import List, Optional

from quiz_bot.entity import ContextChallenge, ContextParticipant, ContextUser, WinnerResult
from quiz_bot.storage import IParticipantStorage
from quiz_bot.utils import get_now


class Registrar:
    def __init__(self, storage: IParticipantStorage):
        self._storage = storage

    def get_participation_for_user(
        self, user: ContextUser, challenge: ContextChallenge
    ) -> Optional[ContextParticipant]:
        return self._storage.get_participation(user_id=user.id, challenge_id=challenge.id)

    def create_participation_for_user(self, user: ContextUser, challenge: ContextChallenge) -> ContextParticipant:
        return self._storage.create_participant(user_id=user.id, challenge_id=challenge.id)

    def set_answer_correct(self, participant: ContextParticipant) -> None:
        self._storage.increment_score(participant_id=participant.id)

    def finish_participation(self, participant: ContextParticipant) -> None:
        participant.finished_at = get_now()
        self._storage.finish_participation(participant_id=participant.id, finished_at=participant.finished_at)

    def all_winners_exist(self, challenge: ContextChallenge) -> bool:
        return self._storage.has_all_winners(challenge_id=challenge.id, winner_amount=challenge.winner_amount)

    def get_winners(self, challenge: ContextChallenge) -> Sequence[WinnerResult]:
        pretenders = self._storage.get_pretenders(challenge_id=challenge.id)
        winner_list: List[WinnerResult] = []
        position = 0
        for participant in pretenders:
            position += 1
            winner_list.append(
                WinnerResult(
                    user=participant.user,
                    position=position,
                    scores=participant.scores,
                    finished_at=participant.finished_at,
                )
            )
        return winner_list
