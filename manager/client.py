import collections
import logging
import threading

import requests
import telebot
import tenacity

logger = logging.getLogger(__name__)


def get_full_name(user: telebot.types.User) -> str:
    """
    Get full name of the Telegram user in the form `<First Name> <Last Name> @<Username>`

    Args:
        user: Telegram user object

    Returns:
        String with a full name
    """
    name = user.first_name or ''
    if user.last_name:
        name += f' {user.last_name}'
    if user.username:
        name += f' @{user.username}'
    return name


def run_bot(token: str, chitchat_url: str, log_level: str):
    locks = collections.defaultdict(threading.Lock)
    bot = telebot.TeleBot(token)

    def _send(message: telebot.types.Message, response: str):
        """
        Save original response to MongoDB and send normalized response to chat
        """
        bot.send_message(chat_id=message.chat.id, text=response, parse_mode='html')

        logger.info(f'Chat {message.chat.id} with {get_full_name(message.from_user)}: {message.text} -> {response}')

    @bot.message_handler(commands=['start'])
    def _start(message: telebot.types.Message):
        """
        Send response to a Telegram user `/start` command
        """
        with locks[message.chat.id]:
            _send(message, response='Задавайте ваши вопросы')

    @tenacity.retry(
        reraise=True,
        retry=tenacity.retry_if_exception_type(requests.RequestException),
        stop=tenacity.stop_after_attempt(3),
        before_sleep=tenacity.before_sleep_log(logger, log_level),
        after=tenacity.after_log(logger, log_level),
    )
    def _get_response(text: str, user_id: str, force_full_mode: bool = True) -> str:
        context = {'text': text, 'user_id': user_id, 'force_full_mode': force_full_mode}
        return requests.post(chitchat_url, json=context).json()['text']

    def _send_response(message: telebot.types.Message):
        """
        Send response to a Telegram user chat message
        """
        chat_id = message.chat.id
        user_id = str(message.from_user.id) if message.from_user else '<unknown>'

        with locks[chat_id]:
            try:
                response = _get_response(message.text, user_id)
            except Exception as e:
                logger.exception(e)
                response = 'Произошла ошибка'

            if response is None:
                response = 'Ответа нет'

            _send(message, response=response)

    @bot.message_handler()
    def send_response(message: telebot.types.Message):
        try:
            _send_response(message)
        except Exception as e:
            logger.exception(e)

    logger.info('Telegram bot started')
    bot.polling(none_stop=True)


def main():
    config = {}
    if not config.telegram.chitchat_host or not config.telegram.chitchat_port:
        raise EnvironmentError('CHITCHAT_HOST and CHITCHAT_PORT must be defined')

    log_level = logging.getLevelName(config.log_level)
    chitchat_url = f'http://{config.telegram.chitchat_host}:{config.telegram.chitchat_port}/'

    run_bot(config.telegram.key, chitchat_url, log_level)


if __name__ == "__main__":
    while True:
        try:
            main()
        except requests.RequestException as e:
            logger.exception(e)
