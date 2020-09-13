import abc

import telebot


class IInterface(abc.ABC):
    @abc.abstractmethod
    def run(self) -> None:
        pass

    @abc.abstractmethod
    def _register_handlers(self, bot: telebot.TeleBot) -> None:
        pass
