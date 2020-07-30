import logging
from typing import List, Optional

import telebot
from quiz_bot.manager.checkers import IResultChecker
from quiz_bot.settings import ChallengeSettings
from quiz_bot.storage import (
    AnswerResult,
    ContextChallenge,
    ContextUser,
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

    def start_challenge_for_user(self, user: ContextUser) -> AnswerResult:
        if self._current_challenge is None:
            logger.warning("Try to start challenge for User @%s result when challenge is not running!", user.nick_name)
            return AnswerResult()
        result = self._result_checker.prepare_user_result(user=user, challenge=self._current_challenge.data)
        logger.warning("Started challenge for user @%s", user.nick_name)
        return AnswerResult(
            correct=True,
            replies=[
                self.start_info,
                self._settings.get_next_answer_notification(
                    question=self._current_challenge.info.get_question(result.phase), question_num=result.phase,
                ),
            ],
        )

    def get_answer_result(self, user: ContextUser, message: telebot.types.Message) -> AnswerResult:  # noqa: C901
        if self._current_challenge is None:
            logger.warning("Try to get answer result when challenge is not running!")
            return AnswerResult()

        try:
            checked_result = self._result_checker.check_answer(
                user=user, current_challenge=self._current_challenge, message=message
            )
        except NoResultFoundError:
            logger.info("Not found any Result for User @%s. Maybe, challenge not started yet for him?", user.nick_name)
            return AnswerResult()
        if not checked_result.correct:
            return AnswerResult(replies=[self._settings.random_incorrect_answer_notification])

        if not checked_result.finished_for_user:
            if checked_result.next_phase is None:
                raise RuntimeError("Next phase should be specified for not last but correct result!")
            return AnswerResult(
                correct=True,
                replies=[
                    self._settings.random_correct_answer_notification,
                    self._settings.get_next_answer_notification(
                        question=self._current_challenge.info.get_question(checked_result.next_phase),
                        question_num=checked_result.next_phase,
                    ),
                ],
            )

        replies: List[str] = [self._settings.get_winner_notification(challenge_name=self._current_challenge.info.name)]
        if not checked_result.challenge_finished:
            return AnswerResult(correct=True, replies=replies)

        logger.info(
            "Challenge #%s '%s' finished with all winners resolution!",
            self._current_challenge.number,
            self._current_challenge.info.name,
        )
        self.start_next_challenge()
        next_challenge_question = self.start_challenge_for_user(user)
        if next_challenge_question.correct:
            replies.extend(next_challenge_question.replies)
        return AnswerResult(correct=True, replies=replies)

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
