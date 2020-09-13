import logging

import click
import telebot
from quiz_bot.clients import BotResponse, RemoteBotClient
from quiz_bot.entity import ContextUser
from quiz_bot.quiz.interfaces.base_interface import BaseInterface
from quiz_bot.quiz.interfaces.errors import NoUserFoundError
from quiz_bot.quiz.objects import ChatEmptyReply, ContentType
from quiz_bot.storage import IUserStorage

logger = logging.getLogger(__name__)


_YES = "Yes"
_NO = "No"


class ChatInterface(BaseInterface):
    def __init__(self, client: RemoteBotClient, user_storage: IUserStorage, target_user: str) -> None:
        super().__init__(client)
        self._user_storage = user_storage
        self._target_user = self._resolve_user(target_user)

    def _resolve_user(self, target_user: str) -> ContextUser:
        internal_user = self._user_storage.get_user_by_nick_name(target_user)
        if internal_user is not None:
            return internal_user
        raise NoUserFoundError(f"No one user found with nick_name '{target_user}'!")

    def _register_handlers(self, bot: telebot.TeleBot) -> None:  # noqa: C901
        @bot.message_handler(
            content_types=[ContentType.TEXT], func=lambda message: message.from_user.id == self._target_user.external_id
        )
        def default_handler(message: telebot.types.Message) -> None:
            with self._client.thread_lock[message.chat.id]:
                click.secho(f'{message.from_user.username}: {message.text}', fg='green')
                self.message()

    def message(self) -> None:
        reply = click.prompt('Message', type=str, default=ChatEmptyReply)
        if reply != ChatEmptyReply:
            self._client.send(BotResponse(user=self._target_user, reply=reply))
