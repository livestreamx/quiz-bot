import logging
from copy import deepcopy
from typing import Optional

import telebot
from quiz_bot.manager.checkers import IResultChecker
from quiz_bot.settings import ChallengeSettings
from quiz_bot.storage import (
    BaseAnswerResult,
    ContextChallenge,
    ContextUser,
    CorrectAnswerResult,
    CurrentChallenge,
    IChallengeStorage,
    NoResultFoundError,
    StopChallengeIteration,
)

logger = logging.getLogger(__name__)


class ChallengeMaster:
    def __init__(
        self, challenge_storage: IChallengeStorage, settings: ChallengeSettings, result_checker: IResultChecker,
    ) -> None:
        self._challenge_storage = challenge_storage
        self._settings = settings
        self._result_checker = result_checker

        self._current_challenge: Optional[CurrentChallenge] = None
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
            self._current_challenge = None

    def start_challenge_for_user(self, user: ContextUser) -> BaseAnswerResult:
        if self._current_challenge is None:
            logger.warning("Try to start challenge for User @%s result when challenge is not running!", user.nick_name)
            return BaseAnswerResult()
        result = self._result_checker.prepare_user_result(user=user, challenge=self._current_challenge.data)
        logger.warning("Started challenge for user @%s", user.nick_name)
        return CorrectAnswerResult(
            reply=self._settings.get_next_answer_notification(
                question=self._current_challenge.info.get_question(result.phase), question_num=result.phase,
            )
        )

    def get_answer_result(self, user: ContextUser, message: telebot.types.Message) -> BaseAnswerResult:
        if self._current_challenge is None:
            logger.warning("Try to get answer result when challenge is not running!")
            return BaseAnswerResult()

        try:
            checked_result = self._result_checker.check_answer(
                user=user, current_challenge=self._current_challenge, message=message
            )
        except NoResultFoundError:
            logger.info("Not found any Result for User @%s. Maybe, challenge not started yet for him?", user.nick_name)
            return BaseAnswerResult()
        if not checked_result.correct:
            return BaseAnswerResult(post_reply=self._settings.random_incorrect_answer_notification)

        if checked_result.challenge_finished:
            previous_challenge = deepcopy(self._current_challenge)
            self.start_next_challenge()
            next_challenge_question = self.start_challenge_for_user(user)

            post_reply = None
            if isinstance(next_challenge_question, CorrectAnswerResult):
                post_reply = next_challenge_question.reply

            return CorrectAnswerResult(
                reply=self._settings.get_winner_notification(challenge_name=previous_challenge.info.name),
                post_reply=post_reply,
            )

        if checked_result.next_phase is None:
            raise ValueError("Correct result without challenge finish should have next phase!")
        return CorrectAnswerResult(
            reply=self._settings.random_correct_answer_notification,
            post_reply=self._settings.get_next_answer_notification(
                question=self._current_challenge.info.get_question(checked_result.next_phase),
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
            description=f"{self._current_challenge.info.description}",
        )
