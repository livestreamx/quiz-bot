import logging

import requests
import telebot
from quiz_bot.clients import BotResponse, ShoutboxClient, ShoutboxPrewrittenDetectedError, ShoutboxRequest
from quiz_bot.entity import ChallengeType, ContextUser, EvaluationStatus, InfoSettings, QuizState
from quiz_bot.quiz.challenge import ChallengeMaster
from quiz_bot.quiz.errors import UnexpectedQuizStateError, UnreachableMessageProcessingError
from quiz_bot.quiz.markup import UserMarkupMaker
from quiz_bot.quiz.objects import ApiCommand, SkipApprovalCommand
from quiz_bot.storage import IAttemptsStorage, IUserStorage

logger = logging.getLogger(__name__)


class QuizManager:
    def __init__(
        self,
        settings: InfoSettings,
        shoutbox_client: ShoutboxClient,
        user_storage: IUserStorage,
        attempts_storage: IAttemptsStorage,
        markup_maker: UserMarkupMaker,
        challenge_master: ChallengeMaster,
    ) -> None:
        self._settings = settings
        self._shoutbox_client = shoutbox_client
        self._user_storage = user_storage
        self._attempts_storage = attempts_storage
        self._markup_maker = markup_maker
        self._challenge_master = challenge_master

        self._state: QuizState = QuizState.NEW
        self._sync_state()

    def _sync_state(self) -> None:
        self._state = self._challenge_master.resolve_quiz_state()

    def next(self) -> None:
        if self._state.prepared:
            self._challenge_master.start_next_challenge()
            self._sync_state()
            if self._state is QuizState.IN_PROGRESS:
                return
            raise UnexpectedQuizStateError(f"Quiz has state '{self._state}' after next challenge starting!")
        raise UnexpectedQuizStateError(f"Could not start next challenge - current state is '{self._state}'!")

    def _get_shoutbox_answer(self, user: ContextUser, text: str) -> str:
        if self._shoutbox_client.enabled:
            try:
                response = self._shoutbox_client.make_request(data=ShoutboxRequest(text=text, user_id=user.chitchat_id))
                return response.text
            except requests.RequestException:
                logger.exception("Error while making request to shoutbox!")
            except ShoutboxPrewrittenDetectedError as e:
                logger.debug(e)  # noqa: G200
        return self._settings.random_empty_message

    def _get_simple_response(self, message: telebot.types.Message, attach_unknown_info: bool = False) -> BotResponse:
        user = self._user_storage.make_unknown_context_user(message)
        replies = [self._get_shoutbox_answer(user=user, text=message.text)]
        markup = None
        if attach_unknown_info:
            replies.append(self._settings.unknown_info)
            markup = self._markup_maker.help_markup
        return BotResponse(user=user, user_message=message.text, replies=replies, markup=markup,)

    def get_help_response(self, message: telebot.types.Message) -> BotResponse:
        internal_user = self._user_storage.get_or_create_user(message)
        if self._state is QuizState.IN_PROGRESS:
            return BotResponse(
                user=internal_user,
                user_message=message.text,
                replies=[self._settings.greetings, self._settings.wait_for_user_info],
                markup=self._markup_maker.start_with_status_markup,
                split=True,
            )
        return BotResponse(
            user=internal_user,
            user_message=message.text,
            reply=self._settings.greetings,
            markup=self._markup_maker.status_markup,
            split=True,
        )

    def get_start_response(self, message: telebot.types.Message) -> BotResponse:
        internal_user = self._user_storage.get_or_create_user(message)
        if self._state.prepared:
            self._sync_state()

        if self._state.prepared:
            return BotResponse(user=internal_user, user_message=message.text, reply=self._settings.not_started_info,)
        if self._state is QuizState.FINISHED:
            return BotResponse(
                user=internal_user,
                user_message=message.text,
                reply=self._settings.post_end_info,
                markup=self._markup_maker.status_markup,
            )
        start_info = self._challenge_master.start_challenge_for_user(internal_user)
        return BotResponse(
            user=internal_user,
            user_message=message.text,
            replies=start_info.replies,
            split=True,
            picture=start_info.picture,
        )

    def get_status_response(self, message: telebot.types.Message) -> BotResponse:
        internal_user = self._user_storage.get_or_create_user(message)
        if self._state.prepared:
            self._sync_state()

        if self._state is QuizState.NEW:
            return BotResponse(user=internal_user, user_message=message.text, reply=self._settings.not_started_info,)
        if self._state is QuizState.IN_PROGRESS:
            return BotResponse(
                user=internal_user, user_message=message.text, reply=self._challenge_master.get_challenge_info(),
            )
        if self._state is QuizState.WAIT_NEXT:
            return BotResponse(
                user=internal_user,
                user_message=message.text,
                replies=[self._challenge_master.get_challenge_info(), self._settings.not_started_info],
                split=True,
            )
        return BotResponse(
            user=internal_user,
            user_message=message.text,
            replies=[self._challenge_master.get_challenge_info(), self._settings.post_end_info],
            split=True,
        )

    def get_skip_response(self, message: telebot.types.Message) -> BotResponse:
        internal_user = self._user_storage.get_or_create_user(message)
        if self._attempts_storage.ensure_skip_for_user(internal_user.id):
            if message.text.endswith(ApiCommand.SKIP):
                return BotResponse(
                    user=internal_user,
                    user_message=message.text,
                    markup=self._markup_maker.skip_approval_markup,
                    reply=self._settings.skip_question_approval,
                )
            if message.text.endswith(SkipApprovalCommand.YES):
                self._attempts_storage.clear(internal_user.id)
                replies = [self._settings.skip_question_success]
                fake_evaluation = self._challenge_master.skip_evaluation(internal_user)
                replies.extend(fake_evaluation.replies)
                return BotResponse(user=internal_user, user_message=message.text, replies=replies, split=True)
            if message.text.endswith(SkipApprovalCommand.NO):
                return BotResponse(
                    user=internal_user, user_message=message.text, reply=self._settings.skip_question_refuse
                )
        return BotResponse(user=internal_user, user_message=message.text, reply=self._settings.skip_question_prohibited)

    def _evaluate(self, user: ContextUser, message: telebot.types.Message) -> BotResponse:  # noqa: C901
        evaluation = self._challenge_master.evaluate(user=user, message=message)
        self._state = evaluation.quiz_state
        replies = evaluation.replies

        if evaluation.status is EvaluationStatus.CORRECT:
            self._attempts_storage.clear(user.id)
            replies.insert(0, self._settings.random_correct_answer_notification)
            return BotResponse(user=user, user_message=message.text, replies=replies, split=True)

        if evaluation.status is EvaluationStatus.INCORRECT:
            if self._state is QuizState.IN_PROGRESS:
                replies.extend(
                    [
                        self._get_shoutbox_answer(user=user, text=message.text),
                        self._settings.random_incorrect_answer_notification,
                    ]
                )
                markup = None
                if (
                    self._challenge_master.keeper.info.type is ChallengeType.REGULAR
                    and self._attempts_storage.need_to_skip_notify(user.id)
                ):
                    replies.append(self._settings.random_skip_question_notification)
                    markup = self._markup_maker.skip_markup
                return BotResponse(user=user, user_message=message.text, replies=replies, markup=markup)
            if self._state.delivered:
                replies.insert(0, self._settings.out_of_date_info)
                return BotResponse(
                    user=user, user_message=message.text, replies=replies, markup=self._markup_maker.status_markup
                )

        if evaluation.status is EvaluationStatus.NOT_CHECKED:
            if self._state.delivered:
                return self._get_simple_response(message)
            if self._state is QuizState.IN_PROGRESS:
                replies.extend(
                    [self._get_shoutbox_answer(user=user, text=message.text), self._settings.wait_for_user_info]
                )
                return BotResponse(
                    user=user,
                    user_message=message.text,
                    replies=replies,
                    markup=self._markup_maker.start_with_help_markup,
                )
        if evaluation.status is EvaluationStatus.ALREADY_COMPLETED:
            return self._get_simple_response(message)
        raise UnreachableMessageProcessingError("Should not be there!")

    def respond(self, message: telebot.types.Message) -> BotResponse:
        internal_user = self._user_storage.get_or_create_user(message)
        if internal_user is None:
            logger.warning("Gotten message '%s' from unknown user: %s!", message.text, message.from_user)
            return self._get_simple_response(message, attach_unknown_info=True)
        if self._state is QuizState.NEW:
            return self._get_simple_response(message)
        return self._evaluate(user=internal_user, message=message)
