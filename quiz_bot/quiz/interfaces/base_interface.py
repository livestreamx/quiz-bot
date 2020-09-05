import abc
import logging

from quiz_bot.clients import RemoteBotClient
from quiz_bot.quiz.interfaces.abstract_interface import IInterface

logger = logging.getLogger(__name__)


class BaseInterface(IInterface, abc.ABC):
    def __init__(self, client: RemoteBotClient) -> None:
        self._client = client
        self._register_handlers(client.bot)

    def run(self) -> None:
        logger.info('Bot is started.')
        self._client.run_loop()
