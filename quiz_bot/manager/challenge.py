import abc
import logging
from typing import Optional

import telebot
from quiz_bot.settings import ChallengeSettings
from quiz_bot.storage import (
    BaseAnswerResult,
    ContextChallenge,
    ContextUser,
    CorrectAnswerResult,
    CurrentChallenge,
    IChallengeStorage,
    IResultStorage,
    StopChallengeIteration,
)

logger = logging.getLogger(__name__)


class IChallengeMaster(abc.ABC):
    @abc.abstractmethod
    def start_next_challenge(self) -> None:
        pass

    @abc.abstractmethod
    def get_answer_result(self, user: ContextUser, message: telebot.types.Message) -> BaseAnswerResult:
        pass

    @property
    @abc.abstractmethod
    def start_info(self) -> str:
        pass


class ChallengeMaster(IChallengeMaster):
    def __init__(
        self, challenge_storage: IChallengeStorage, result_storage: IResultStorage, settings: ChallengeSettings
    ) -> None:
        self._challenge_storage = challenge_storage
        self._result_storage = result_storage
        self._settings = settings

        self._current_challenge: Optional[CurrentChallenge]
        self._quiz_finished: bool = False
        self._resolve()

    def _resolve(self) -> None:
        for challenge in self._settings.challenges:
            self._challenge_storage.create_challenge(name=challenge.name, phase_amount=len(challenge.questions))
        self._synchronize_current_challenge_if_neccessary()

    def _resolve_current_state(self, challenge: Optional[ContextChallenge]) -> None:
        if challenge is None:
            self._current_challenge = None
            return
        self._current_challenge = CurrentChallenge(
            info=self._settings.get_challenge_by_name(challenge.name), data=challenge, number=challenge.id
        )

    def _synchronize_current_challenge_if_neccessary(self) -> None:
        if self._current_challenge is None:
            actual_challenge = self._challenge_storage.get_actual_challenge()
            if actual_challenge is not None:
                self._resolve_current_state(challenge=actual_challenge)

    def start_next_challenge(self) -> None:
        try:
            self._resolve_current_state(challenge=self._challenge_storage.start_next_challenge())
        except StopChallengeIteration:
            logger.warning("Quiz is finished - active challenge was not found!")
            self._quiz_finished = True

    def _move_to_next_phase(self, user: ContextUser) -> None:
        pass

    def get_answer_result(self, user: ContextUser, message: telebot.types.Message) -> BaseAnswerResult:
        if self._current_challenge is None:
            logger.error("Try to get answer result when challenge is not running!")
            return BaseAnswerResult()

        is_answer_correct = (
            True  # TODO: здесь должен быть менеджер, куда передается ChallengeInfo и определяется правильность ответа
        )
        if not is_answer_correct:
            return BaseAnswerResult()

        current_phase = 5  # TODO: здесь должно быть взаимодействие с ResultStorage
        if current_phase < self._current_challenge.number:
            self._move_to_next_phase(user)
        else:
            self.start_next_challenge()
        return CorrectAnswerResult(reply=self._settings.correct_answer_notification)

    @property
    def start_info(self) -> str:
        self._synchronize_current_challenge_if_neccessary()
        if self._current_challenge is None:
            return self._settings.post_end_info
        return self._settings.get_start_notification(
            challenge_num=self._current_challenge.number,
            challenge_name=self._current_challenge.info.name,
            description=self._current_challenge.info.description,
        )
