import logging

import requests
import telebot
from quiz_bot.clients import BotResponse, ChitchatClient, ChitchatPrewrittenDetectedError, ChitChatRequest
from quiz_bot.entity import ContextUser, EvaluationStatus, InfoSettings, QuizState
from quiz_bot.quiz.challenge import ChallengeMaster
from quiz_bot.quiz.errors import UnexpectedQuizStateError, UnreachableMessageProcessingError
from quiz_bot.quiz.markup import UserMarkupMaker
from quiz_bot.storage import IUserStorage

logger = logging.getLogger(__name__)


class QuizManager:
    def __init__(
        self,
        settings: InfoSettings,
        chitchat_client: ChitchatClient,
        user_storage: IUserStorage,
        markup_maker: UserMarkupMaker,
        challenge_master: ChallengeMaster,
    ) -> None:
        self._settings = settings
        self._chitchat_client = chitchat_client
        self._user_storage = user_storage
        self._markup_maker = markup_maker
        self._challenge_master = challenge_master

        self._state: QuizState = QuizState.NEW
        self._sync_state()

    def _sync_state(self) -> None:
        self._state = self._challenge_master.quiz_state

    def next(self) -> None:
        if self._state.prepared:
            self._challenge_master.start_next_challenge()
            self._sync_state()
            if self._state is QuizState.IN_PROGRESS:
                return
            raise UnexpectedQuizStateError(f"Quiz has state '{self._state}' after next challenge starting!")
        raise UnexpectedQuizStateError(f"Could not start next challenge - current state is '{self._state}'!")

    def _get_chitchat_answer(self, user: ContextUser, text: str) -> str:
        if self._chitchat_client.enabled:
            try:
                response = self._chitchat_client.make_request(data=ChitChatRequest(text=text, user_id=user.chitchat_id))
                return response.text
            except requests.RequestException:
                logger.exception("Error while making request to chitchat!")
            except ChitchatPrewrittenDetectedError as e:
                logger.info(e)  # noqa: G200
        return self._settings.random_empty_message

    def _get_simple_response(self, message: telebot.types.Message, attach_unknown_info: bool = False) -> BotResponse:
        user = self._user_storage.make_unknown_context_user(message)
        replies = [self._get_chitchat_answer(user=user, text=message.text)]
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
        if self._state is QuizState.FINISHED:
            return BotResponse(
                user=internal_user,
                user_message=message.text,
                replies=[self._settings.greetings, self._settings.post_end_info],
                markup=self._markup_maker.status_markup,
                split=True,
            )
        return BotResponse(
            user=internal_user,
            user_message=message.text,
            replies=[self._settings.greetings, self._settings.not_started_info],
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
        return BotResponse(user=internal_user, user_message=message.text, replies=start_info.replies, split=True)

    def get_status_response(self, message: telebot.types.Message) -> BotResponse:
        internal_user = self._user_storage.get_or_create_user(message)
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

    def _evaluate(self, user: ContextUser, message: telebot.types.Message) -> BotResponse:
        evaluation = self._challenge_master.evaluate(user=user, message=message)
        self._state = evaluation.quiz_state
        replies = evaluation.replies

        if evaluation.status is EvaluationStatus.CORRECT:
            replies.insert(0, self._settings.random_correct_answer_notification)
            return BotResponse(user=user, user_message=message.text, replies=replies, split=True)

        if evaluation.status is EvaluationStatus.INCORRECT:
            if self._state is QuizState.IN_PROGRESS:
                replies.extend(
                    [
                        self._get_chitchat_answer(user=user, text=message.text),
                        self._settings.random_incorrect_answer_notification,
                    ]
                )
                return BotResponse(user=user, user_message=message.text, replies=replies)
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
                    [self._get_chitchat_answer(user=user, text=message.text), self._settings.wait_for_user_info]
                )
                return BotResponse(
                    user=user,
                    user_message=message.text,
                    replies=replies,
                    markup=self._markup_maker.start_with_help_markup,
                )
        raise UnreachableMessageProcessingError("Should not be there!")

    def respond(self, message: telebot.types.Message) -> BotResponse:
        internal_user = self._user_storage.get_or_create_user(message)
        if internal_user is None:
            logger.warning("Gotten message '%s' from unknown user: %s!", message.text, message.from_user)
            return self._get_simple_response(message, attach_unknown_info=True)
        if self._state is QuizState.NEW:
            return self._get_simple_response(message)
        return self._evaluate(user=internal_user, message=message)
