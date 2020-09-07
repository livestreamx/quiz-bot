import logging
from typing import List, Optional, Sequence

import telebot
from quiz_bot.entity import (
    AnswerEvaluation,
    AnyChallengeInfo,
    BotPicture,
    ChallengeSettings,
    CheckedResult,
    ContextChallenge,
    ContextParticipant,
    ContextUser,
    EvaluationStatus,
    PictureLocation,
    QuizState,
    RegularChallengeInfo,
    UnexpectedChallengeAmountError,
)
from quiz_bot.quiz.errors import ChallengeNotFoundError, NullableParticipantError
from quiz_bot.quiz.keeper import ChallengeKeeper
from quiz_bot.quiz.registrar import Registrar
from quiz_bot.storage import IChallengeStorage

logger = logging.getLogger(__name__)


class ChallengeMaster:
    def __init__(
        self, storage: IChallengeStorage, settings: ChallengeSettings, registrar: Registrar, keeper: ChallengeKeeper,
    ) -> None:
        self._storage = storage
        self._settings = settings
        self._registrar = registrar
        self._keeper = keeper

        self._sync_challenge()
        if all((self._settings.autostart, not self._keeper.has_data or self._keeper.finished,)):
            self.start_next_challenge()

    @property
    def keeper(self) -> ChallengeKeeper:
        return self._keeper

    @property
    def _is_last_challenge(self) -> bool:
        return self._keeper.has_data and self._keeper.number == self._settings.challenge_amount

    def _save_challenge_data(self, challenge: ContextChallenge) -> None:
        self._keeper.set(data=challenge, info=self._settings.get_challenge_model(challenge.id))

    def _sync_challenge(self) -> None:
        actual_challenge = self._storage.get_actual_challenge()
        if actual_challenge is not None:
            logger.info("Actual challenge with ID %s", actual_challenge.id)
            self._save_challenge_data(actual_challenge)
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
        self._save_challenge_data(challenge)

    def resolve_quiz_state(self) -> QuizState:
        self._sync_challenge()
        if not self._keeper.has_data:
            return QuizState.NEW
        if self._keeper.finished:
            if self._is_last_challenge:
                return QuizState.FINISHED
            return QuizState.WAIT_NEXT
        return QuizState.IN_PROGRESS

    def _get_next_challenge_info(self) -> AnyChallengeInfo:
        if not self._keeper.has_data:
            return self._settings.get_challenge_model(1)
        return self._settings.get_challenge_model(self._keeper.number + 1)

    def start_next_challenge(self) -> None:
        next_challenge_info = self._get_next_challenge_info()
        next_challenge = self._storage.create_challenge(
            name=next_challenge_info.name,
            phase_amount=next_challenge_info.phase_amount,
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
        participant = self._registrar.get_participation_for_user(user=user, challenge=self._keeper.data)
        if participant is None:
            participant = self._registrar.create_participation_for_user(user=user, challenge=self._keeper.data)
            result = self._keeper.checker.create_initial_phase(participant=participant)
            logger.warning("Started challenge ID %s for user @%s", self._keeper.number, user.nick_name)

            replies = list(additional_replies) + [
                self._settings.get_start_notification(
                    challenge_num=self._keeper.number,
                    challenge_name=self._keeper.info.name,
                    description=f"{self._keeper.info.description}",
                ),
            ]
            if isinstance(self._keeper.info, RegularChallengeInfo):
                replies.append(
                    self._settings.get_next_answer_notification(
                        question=self._keeper.info.get_question(result.phase), question_num=result.phase,
                    )
                )

            return self._get_evaluation(
                status=status,
                replies=replies,
                picture=BotPicture(file=self._keeper.info.picture, location=PictureLocation.ABOVE),
            )
        return self._get_evaluation(
            status=status,
            replies=[self._settings.get_already_started_notification(challenge_name=self._keeper.info.name)],
        )

    def _resolve_next_event(self, participant: ContextParticipant, result: CheckedResult) -> AnswerEvaluation:
        status = EvaluationStatus.CORRECT

        if result.next_phase is not None:
            replies: List[str] = []
            if isinstance(self._keeper.info, RegularChallengeInfo):
                replies.append(
                    self._settings.get_next_answer_notification(
                        question=self._keeper.info.get_question(result.next_phase), question_num=result.next_phase,
                    )
                )
            return self._get_evaluation(status=status, replies=replies)

        self._registrar.finish_participation(participant)
        pretender_replies = [
            self._settings.get_pretender_notification(
                challenge_name=self._keeper.info.name, scores=participant.scores, finished_at=participant.finished_at,
            )
        ]

        has_all_winners = self._registrar.all_winners_exist(challenge=self._keeper.data)
        if not has_all_winners:
            return self._get_evaluation(status=status, replies=pretender_replies)

        self._storage.finish_actual_challenge()
        logger.info(
            "Challenge #%s '%s' finished with all winners resolution!", self._keeper.number, self._keeper.info.name,
        )
        if not self._is_last_challenge and self._settings.autostart:
            self.start_next_challenge()
            return self.start_challenge_for_user(
                user=participant.user, status=status, additional_replies=pretender_replies
            )
        return self._get_evaluation(status=status, replies=pretender_replies)

    def evaluate(self, user: ContextUser, message: telebot.types.Message) -> AnswerEvaluation:  # noqa: C901
        if self._keeper.out_of_date:
            self._storage.finish_actual_challenge()

        participant = self._registrar.get_participation_for_user(user=user, challenge=self._keeper.data)
        if participant is None:
            logger.info(
                "User @%s is not a Participant for challenge with ID %s!", user.nick_name, self._keeper.data.id,
            )
            return self._get_evaluation(status=EvaluationStatus.NOT_CHECKED)
        if participant.completed_challenge:
            logger.info(
                "User @%s has already completed challenge with ID %s!", user.nick_name, self._keeper.data.id,
            )
            return self._get_evaluation(status=EvaluationStatus.NOT_CHECKED)

        if self._keeper.finished:
            return self._get_evaluation(status=EvaluationStatus.INCORRECT)

        checked_result = self._keeper.checker.check_answer(
            participant=participant, data=self._keeper.data, info=self._keeper.info, message=message  # type: ignore
        )
        if not checked_result.correct:
            return self._get_evaluation(status=EvaluationStatus.INCORRECT)

        self._registrar.add_correct_answer(participant)
        return self._resolve_next_event(participant=participant, result=checked_result)

    def skip_evaluation(self, user: ContextUser) -> AnswerEvaluation:
        participant = self._registrar.get_participation_for_user(user=user, challenge=self._keeper.data)
        if participant is None:
            raise NullableParticipantError
        unchecked_result = self._keeper.checker.skip_question(participant=participant, data=self._keeper.data)
        return self._resolve_next_event(participant=participant, result=unchecked_result)

    def get_challenge_info(self, challenge_id: Optional[int] = None) -> str:
        if not isinstance(challenge_id, int):
            logger.info("Challenge ID was not specified, so use current challenge information.")
            challenge_id = self._keeper.number

        context_challenge = self._storage.get_challenge(challenge_id)
        if context_challenge is None:
            raise ChallengeNotFoundError(f"Challenge with ID {challenge_id} was not found!")

        winner_results = self._registrar.get_winners(self._keeper.data)

        if not self._keeper.finished:
            results = self._settings.get_time_left_info(self._keeper.finish_after)
        else:
            results = (
                "\n".join(self._settings.get_results_info(winner_results))
                + "\n\n"
                + self._settings.get_time_over_info(self._keeper.data)
            )
        return self._settings.get_challenge_info(number=self._keeper.number, info=self._keeper.info, results=results)
