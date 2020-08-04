import logging
from typing import List

import requests
import telebot
from quiz_bot.clients import BotResponse, ChitchatClient, ChitchatPrewrittenDetectedError, ChitChatRequest
from quiz_bot.entity import ContextUser, InfoSettings, QuizState
from quiz_bot.quiz.challenge import ChallengeMaster
from quiz_bot.quiz.errors import UnexpectedQuizStateError
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

        self._state: QuizState = self._challenge_master.get_quiz_state()

    def next(self) -> None:
        if self._state is QuizState.PREPARED:
            next_state = self._challenge_master.start_next_challenge()
            if next_state is not QuizState.IN_PROGRESS:
                raise UnexpectedQuizStateError(f"Quiz has state '{next_state}' after next challenge starting!")
            self._state = next_state
            return
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

    def _get_unknown_user_response(self, message: telebot.types.Message) -> BotResponse:
        unknown_user = self._user_storage.make_unknown_context_user(message)
        chitchat_answer = self._get_chitchat_answer(user=unknown_user, text=message.text)
        return BotResponse(
            user=unknown_user,
            user_message=message.text,
            replies=[chitchat_answer, self._settings.unknown_info],
            markup=self._markup_maker.help_markup,
        )

    def _evaluate(self, user: ContextUser, message: telebot.types.Message) -> BotResponse:
        evaluation = self._challenge_master.get_evaluation_result(user=user, message=message)
        if not evaluation.correct:
            evaluation.replies.insert(0, self._get_chitchat_answer(user=user, text=message.text))
        return BotResponse(user=user, user_message=message.text, replies=evaluation.replies, split=evaluation.correct)

    def get_help_response(self, message: telebot.types.Message) -> BotResponse:
        internal_user = self._user_storage.get_or_create_user(message)
        return BotResponse(
            user=internal_user,
            user_message=message.text,
            reply=self._settings.greetings,
            markup=self._markup_maker.start_markup,
        )

    def get_start_response(self, message: telebot.types.Message) -> BotResponse:
        internal_user = self._user_storage.get_or_create_user(message)

        replies: List[str] = []
        if self._state is QuizState.PREPARED:
            replies.append(self._settings.not_started_info)
        if self._state is QuizState.IN_PROGRESS:
            start_info = self._challenge_master.start_challenge_for_user(internal_user)
            if start_info.replies:
                replies.extend(start_info.replies)
            else:
                replies.append(self._get_chitchat_answer(user=internal_user, text=message.text))
        if self._state is QuizState.FINISHED:
            replies.append(self._settings.post_end_info)
        return BotResponse(
            user=internal_user,
            user_message=message.text,
            replies=replies,
            split=replies,
            markup=self._markup_maker.start_markup,
        )

    def respond(self, message: telebot.types.Message) -> BotResponse:
        internal_user = self._user_storage.get_user(message.from_user)
        if internal_user is None:
            logger.warning("Gotten message '%s' from unknown user: %s!", message.text, message.from_user)
            return self._get_unknown_user_response(message)
        return self._evaluate(user=internal_user, message=message)
