import logging
from typing import Optional

import telebot
from quiz_bot.manager.checker import ResultChecker
from quiz_bot.settings import ChallengeSettings
from quiz_bot.storage import (
    BaseAnswerResult,
    ContextChallenge,
    ContextUser,
    CorrectAnswerResult,
    CurrentChallenge,
    IChallengeStorage,
    StopChallengeIteration,
)

logger = logging.getLogger(__name__)


class ChallengeMaster:
    def __init__(
        self, challenge_storage: IChallengeStorage, settings: ChallengeSettings, result_checker: ResultChecker,
    ) -> None:
        self._challenge_storage = challenge_storage
        self._settings = settings
        self._result_checker = result_checker

        self._current_challenge: Optional[CurrentChallenge] = None
        self._quiz_finished: bool = False
        self._resolve()

    def _resolve(self) -> None:
        for challenge in self._settings.challenges:
            self._challenge_storage.ensure_challenge_exists(
                name=challenge.name, phase_amount=len(challenge.questions), winner_amount=challenge.max_winners
            )
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

    def get_answer_result(self, user: ContextUser, message: telebot.types.Message) -> BaseAnswerResult:
        if self._current_challenge is None:
            logger.error("Try to get answer result when challenge is not running!")
            return BaseAnswerResult()

        checked_result = self._result_checker.check_answer(
            user=user, current_challenge=self._current_challenge, message=message
        )
        if not checked_result.correct:
            return BaseAnswerResult()

        if checked_result.challenge_finished:
            self.start_next_challenge()
            return CorrectAnswerResult(
                reply=self._settings.correct_answer_notification,
                post_reply=self._settings.get_finish_notification(
                    challenge_name=self._current_challenge.info.name, challenge_num=self._current_challenge.number
                ),
            )

        if checked_result.next_phase is None:
            raise ValueError("Correct result without challenge finish should have next phase!")
        return CorrectAnswerResult(
            reply=self._settings.correct_answer_notification,
            post_reply=self._settings.get_next_answer_notification(
                question=self._current_challenge.info.questions[checked_result.next_phase],
                question_num=checked_result.next_phase,
            ),
        )

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

    @property
    def first_answer(self) -> str:
        if self._current_challenge is None:
            raise RuntimeError("Challenge should be started before getting the first answer!")
        return self._settings.get_next_answer_notification(
            question=self._current_challenge.info.questions[0], question_num=1,
        )
