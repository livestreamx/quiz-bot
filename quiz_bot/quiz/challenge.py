import logging
from typing import Optional, Sequence

import telebot
from quiz_bot.entity import (
    AnswerEvaluation,
    BotPicture,
    ChallengeInfo,
    ChallengeSettings,
    CheckedResult,
    ContextChallenge,
    ContextParticipant,
    ContextUser,
    EvaluationStatus,
    ExtendedChallenge,
    PictureLocation,
    QuizState,
)
from quiz_bot.entity.errors import UnexpectedChallengeAmountError
from quiz_bot.quiz.checkers import IResultChecker
from quiz_bot.quiz.errors import ChallengeNotFoundError, NullableCurrentChallengeError, NullableParticipantError
from quiz_bot.quiz.registrar import Registrar
from quiz_bot.storage import IChallengeStorage

logger = logging.getLogger(__name__)


class ChallengeMaster:
    def __init__(
        self,
        storage: IChallengeStorage,
        settings: ChallengeSettings,
        result_checker: IResultChecker,
        registrar: Registrar,
    ) -> None:
        self._storage = storage
        self._settings = settings
        self._result_checker = result_checker
        self._registrar = registrar

        self._current_challenge: Optional[ExtendedChallenge] = None

        self._sync_challenge()
        if all(
            [
                self._settings.autostart,
                self._current_challenge is None
                or (self._current_challenge is not None and self._current_challenge.finished),
            ]
        ):
            self.start_next_challenge()

    @property
    def current_challenge(self) -> Optional[ExtendedChallenge]:
        return self._current_challenge

    @property
    def _is_last_challenge(self) -> bool:
        return self._current_challenge is not None and self._current_challenge.number == self._settings.challenge_amount

    def _make_extended_model(self, challenge: ContextChallenge) -> ExtendedChallenge:
        return ExtendedChallenge(
            info=self._settings.get_challenge_model(challenge.id), data=challenge, number=challenge.id
        )

    def _set_current_challenge(self, challenge: ContextChallenge) -> None:
        self._current_challenge = self._make_extended_model(challenge)

    def _sync_challenge(self) -> None:
        actual_challenge = self._storage.get_actual_challenge()
        if actual_challenge is not None:
            logger.info("Actual challenge with ID %s", actual_challenge.id)
            self._set_current_challenge(actual_challenge)
            return

        finished_challenge_ids = self._storage.get_finished_challenge_ids()
        if not finished_challenge_ids:
            logger.info("Quiz has not been running yet.")
            return

        if len(finished_challenge_ids) > self._settings.challenge_amount:
            raise UnexpectedChallengeAmountError(
                f"Not equal challenge amount: expected {self._settings.challenge_amount}, "
                f"got {len(finished_challenge_ids)} finished challenges!"
            )
        logger.info("Quiz is not running now. Finished challenges: %s", finished_challenge_ids)
        challenge = self._storage.get_challenge(finished_challenge_ids[-1])
        if challenge is None:
            raise ChallengeNotFoundError("Could not found finished challenge - WTF?")
        self._set_current_challenge(challenge)

    def resolve_quiz_state(self) -> QuizState:
        self._sync_challenge()
        if self._current_challenge is None:
            return QuizState.NEW
        if self._current_challenge.finished:
            if self._is_last_challenge:
                return QuizState.FINISHED
            return QuizState.WAIT_NEXT
        return QuizState.IN_PROGRESS

    def _get_next_challenge_info(self) -> ChallengeInfo:
        if self._current_challenge is None:
            return self._settings.get_challenge_model(1)
        return self._settings.get_challenge_model(self._current_challenge.number + 1)

    def start_next_challenge(self) -> None:
        next_challenge_info = self._get_next_challenge_info()
        next_challenge = self._storage.create_challenge(
            name=next_challenge_info.name,
            phase_amount=len(next_challenge_info.questions),
            winner_amount=next_challenge_info.max_winners,
        )
        logger.info("Next challenge: %s", next_challenge)
        self._sync_challenge()

    def _get_evaluation(
        self, status: EvaluationStatus, replies: Optional[Sequence[str]] = (), picture: Optional[BotPicture] = None
    ) -> AnswerEvaluation:
        return AnswerEvaluation(status=status, replies=replies, quiz_state=self.resolve_quiz_state(), picture=picture)

    def start_challenge_for_user(
        self,
        user: ContextUser,
        status: EvaluationStatus = EvaluationStatus.NOT_CHECKED,
        additional_replies: Sequence[str] = (),
    ) -> AnswerEvaluation:
        if self._current_challenge is None:
            raise NullableCurrentChallengeError(
                "Try to start challenge for User @%s result when challenge is not running!", user.nick_name
            )

        participant = self._registrar.get_participation_for_user(user=user, challenge=self._current_challenge.data)
        if participant is None:
            participant = self._registrar.create_participation_for_user(
                user=user, challenge=self._current_challenge.data
            )
            result = self._result_checker.create_initial_phase(participant=participant)
            logger.warning("Started challenge ID %s for user @%s", self._current_challenge.number, user.nick_name)
            return self._get_evaluation(
                status=status,
                replies=list(additional_replies)
                + [
                    self._settings.get_start_notification(
                        challenge_num=self._current_challenge.number,
                        challenge_name=self._current_challenge.info.name,
                        description=f"{self._current_challenge.info.description}",
                    ),
                    self._settings.get_next_answer_notification(
                        question=self._current_challenge.info.get_question(result.phase), question_num=result.phase,
                    ),
                ],
                picture=BotPicture(file=self._current_challenge.info.picture, location=PictureLocation.ABOVE),
            )
        return self._get_evaluation(
            status=status,
            replies=[self._settings.get_already_started_notification(challenge_name=self._current_challenge.info.name)],
        )

    def _resolve_next_event(self, participant: ContextParticipant, result: CheckedResult) -> AnswerEvaluation:
        if self._current_challenge is None:
            raise NullableCurrentChallengeError
        status = EvaluationStatus.CORRECT

        if result.next_phase is not None:
            return self._get_evaluation(
                status=status,
                replies=[
                    self._settings.get_next_answer_notification(
                        question=self._current_challenge.info.get_question(result.next_phase),
                        question_num=result.next_phase,
                    ),
                ],
            )

        self._registrar.finish_participation(participant)
        pretender_replies = [
            self._settings.get_pretender_notification(
                challenge_name=self._current_challenge.info.name,
                scores=participant.scores,
                finished_at=participant.finished_at,
            )
        ]

        has_all_winners = self._registrar.all_winners_exist(challenge=self._current_challenge.data)
        if not has_all_winners:
            return self._get_evaluation(status=status, replies=pretender_replies)

        self._storage.finish_actual_challenge()
        logger.info(
            "Challenge #%s '%s' finished with all winners resolution!",
            self._current_challenge.number,
            self._current_challenge.info.name,
        )
        if not self._is_last_challenge and self._settings.autostart:
            self.start_next_challenge()
            return self.start_challenge_for_user(
                user=participant.user, status=status, additional_replies=pretender_replies
            )
        return self._get_evaluation(status=status, replies=pretender_replies)

    def evaluate(self, user: ContextUser, message: telebot.types.Message) -> AnswerEvaluation:  # noqa: C901
        if self._current_challenge is None:
            raise NullableCurrentChallengeError(
                "Try to evaluate answer for User @%s result when challenge is not running!", user.nick_name
            )
        if self._current_challenge.out_of_date:
            self._storage.finish_actual_challenge()

        participant = self._registrar.get_participation_for_user(user=user, challenge=self._current_challenge.data)
        if participant is None:
            logger.info(
                "User @%s is not a Participant for challenge with ID %s!",
                user.nick_name,
                self._current_challenge.data.id,
            )
            return self._get_evaluation(status=EvaluationStatus.NOT_CHECKED)
        if participant.completed_challenge:
            logger.info(
                "User @%s has already completed challenge with ID %s!", user.nick_name, self._current_challenge.data.id,
            )
            return self._get_evaluation(status=EvaluationStatus.NOT_CHECKED)

        if self._current_challenge.finished:
            return self._get_evaluation(status=EvaluationStatus.INCORRECT)

        checked_result = self._result_checker.check_answer(
            participant=participant, current_challenge=self._current_challenge, message=message
        )
        if not checked_result.correct:
            return self._get_evaluation(status=EvaluationStatus.INCORRECT)

        self._registrar.add_correct_answer(participant)
        return self._resolve_next_event(participant=participant, result=checked_result)

    def skip_evaluation(self, user: ContextUser) -> AnswerEvaluation:
        if self._current_challenge is None:
            raise NullableCurrentChallengeError
        participant = self._registrar.get_participation_for_user(user=user, challenge=self._current_challenge.data)
        if participant is None:
            raise NullableParticipantError
        unchecked_result = self._result_checker.skip_question(
            participant=participant, current_challenge=self._current_challenge
        )
        return self._resolve_next_event(participant=participant, result=unchecked_result)

    def get_challenge_info(self, challenge_id: Optional[int] = None) -> str:
        if not isinstance(challenge_id, int):
            logger.info("Challenge ID was not specified, so use current challenge information.")
            if self._current_challenge is None:
                raise NullableCurrentChallengeError
            challenge_id = self._current_challenge.number

        context_challenge = self._storage.get_challenge(challenge_id)
        if context_challenge is None:
            raise ChallengeNotFoundError(f"Challenge with ID {challenge_id} was not found!")

        challenge = self._make_extended_model(context_challenge)
        winner_results = self._registrar.get_winners(challenge.data)
        return self._settings.get_challenge_info(challenge=challenge, winner_results=winner_results)
