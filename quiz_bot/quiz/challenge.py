import logging
from typing import List, Optional

import telebot
from quiz_bot.entity import (
    ChallengeEvaluation,
    ChallengeSettings,
    ContextChallenge,
    ContextUser,
    ExtendedChallenge,
    QuizState,
    WinnerResult,
)
from quiz_bot.entity.errors import UnexpectedChallengeAmountError
from quiz_bot.quiz.checkers import IResultChecker
from quiz_bot.quiz.errors import ChallengeNotFoundError, UserIsNotWinnerError
from quiz_bot.storage import IChallengeStorage, NoResultFoundError, StopChallengeIteration

logger = logging.getLogger(__name__)


class ChallengeMaster:
    def __init__(
        self, challenge_storage: IChallengeStorage, settings: ChallengeSettings, result_checker: IResultChecker,
    ) -> None:
        self._challenge_storage = challenge_storage
        self._settings = settings
        self._result_checker = result_checker
        self._current_challenge: Optional[ExtendedChallenge] = None

        self._ensure_challenges_exist()
        if self._settings.autostart:
            self.start_next_challenge()

    def _ensure_challenges_exist(self) -> None:
        for challenge in self._settings.challenges:
            self._challenge_storage.ensure_challenge_exists(
                name=challenge.name, phase_amount=len(challenge.questions), winner_amount=challenge.max_winners
            )

    def _make_extended_model(self, challenge: ContextChallenge) -> ExtendedChallenge:
        return ExtendedChallenge(
            info=self._settings.get_challenge_info_by_name(challenge.name), data=challenge, number=challenge.id
        )

    def _set_current_state(self, challenge: Optional[ContextChallenge]) -> None:
        if challenge is None:
            self._current_challenge = None
            return
        self._current_challenge = self._make_extended_model(challenge)

    def get_quiz_state(self) -> QuizState:
        if self._current_challenge is None:
            actual_challenge = self._challenge_storage.get_actual_challenge()
            if actual_challenge is not None:
                logger.info("Found actual challenge with ID %s", actual_challenge.id)
                self._set_current_state(challenge=actual_challenge)
                return QuizState.IN_PROGRESS

            finished_challenge_ids = self._challenge_storage.get_finished_challenge_ids()
            if not finished_challenge_ids or len(finished_challenge_ids) < len(self._settings.challenges):
                logger.info("Quiz is not running now. Finished challenges: %s", finished_challenge_ids)
                return QuizState.PREPARED

            if len(finished_challenge_ids) >= len(self._settings.challenges):
                raise UnexpectedChallengeAmountError(
                    f"Not equal challenge amount: expected {len(self._settings.challenges)}, "
                    f"got {len(finished_challenge_ids)} finished challenges!"
                )
            logger.info("All challenges finished, so quiz is finished also.")
            return QuizState.FINISHED
        return QuizState.IN_PROGRESS

    def start_next_challenge(self) -> QuizState:
        try:
            self._set_current_state(challenge=self._challenge_storage.start_next_challenge())
            return self.get_quiz_state()
        except StopChallengeIteration:
            logger.warning("Quiz is finished - active challenge was not found!")
            self._current_challenge = None
            return QuizState.FINISHED

    def start_challenge_for_user(self, user: ContextUser) -> ChallengeEvaluation:
        if self._current_challenge is None:
            logger.warning("Try to start challenge for User @%s result when challenge is not running!", user.nick_name)
            return ChallengeEvaluation()
        result = self._result_checker.prepare_user_result(user=user, challenge=self._current_challenge.data)
        logger.warning("Started challenge for user @%s", user.nick_name)
        return ChallengeEvaluation(
            correct=True,
            replies=[
                self._start_info,
                self._settings.get_next_answer_notification(
                    question=self._current_challenge.info.get_question(result.phase), question_num=result.phase,
                ),
            ],
        )

    def _get_winner_result(self, user: ContextUser, challenge: ContextChallenge) -> WinnerResult:
        winner_results = self._result_checker.get_winners(challenge)
        for result in winner_results:
            if user.id != result.user.id:
                continue
            return result
        raise UserIsNotWinnerError("User @%s is not a winner!", user.nick_name)

    def get_evaluation_result(  # noqa: C901
        self, user: ContextUser, message: telebot.types.Message
    ) -> ChallengeEvaluation:
        if self._current_challenge is not None and self._current_challenge.out_of_date:
            self.start_next_challenge()
        if self._current_challenge is None:
            logger.warning("Try to get evaluation when challenge is not running!")
            return ChallengeEvaluation(
                replies=[self._settings.out_of_date_answer_notification, self._settings.post_end_info]
            )

        try:
            checked_result = self._result_checker.check_answer(
                user=user, current_challenge=self._current_challenge, message=message
            )
        except NoResultFoundError:
            logger.info(
                "Not found any Result for User @%s with challenge ID %s!",
                self._current_challenge.data.id,
                user.nick_name,
            )
            replies: List[str] = [self._settings.out_of_date_answer_notification]
            next_challenge_question = self.start_challenge_for_user(user)
            if next_challenge_question.correct:
                replies.extend(next_challenge_question.replies)
            return ChallengeEvaluation(correct=True, replies=replies)

        if not checked_result.correct:
            return ChallengeEvaluation(replies=[self._settings.random_incorrect_answer_notification])

        if not checked_result.finished_for_user:
            if checked_result.next_phase is None:
                raise RuntimeError("Next phase should be specified for not last but correct result!")
            return ChallengeEvaluation(
                correct=True,
                replies=[
                    self._settings.random_correct_answer_notification,
                    self._settings.get_next_answer_notification(
                        question=self._current_challenge.info.get_question(checked_result.next_phase),
                        question_num=checked_result.next_phase,
                    ),
                ],
            )

        winner_result = self._get_winner_result(user=user, challenge=self._current_challenge.data)
        replies: List[str] = [  # type: ignore
            self._settings.get_winner_notification(
                challenge_name=self._current_challenge.info.name, winner_pos=winner_result.position
            )
        ]
        if not checked_result.finish_condition_reached:
            return ChallengeEvaluation(correct=True, replies=replies)

        logger.info(
            "Challenge #%s '%s' finished with all winners resolution!",
            self._current_challenge.number,
            self._current_challenge.info.name,
        )
        self.start_next_challenge()
        next_challenge_question = self.start_challenge_for_user(user)
        if next_challenge_question.correct:
            replies.extend(next_challenge_question.replies)
        return ChallengeEvaluation(correct=True, replies=replies)

    @property
    def _start_info(self) -> str:
        if self._current_challenge is None:
            return self._settings.post_end_info
        return self._settings.get_start_notification(
            challenge_num=self._current_challenge.number,
            challenge_name=self._current_challenge.info.name,
            description=f"{self._current_challenge.info.description}",
        )

    def get_challenge_info(self, challenge_id: int) -> str:
        context_challenge = self._challenge_storage.get_challenge(challenge_id)
        if context_challenge is None:
            raise ChallengeNotFoundError("Challenge with ID '%s' was not found!", challenge_id)
        challenge = self._make_extended_model(context_challenge)
        winner_results = self._result_checker.get_winners(challenge.data)
        return self._settings.get_challenge_info(challenge=challenge, winner_results=winner_results)
