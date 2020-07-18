import logging

import click
from storage import UserStorage

from manager import Bot, ChitchatClient, ChitchatClientSettings, DialogSettings, LoggingSettings, RemoteClientSettings

logger = logging.getLogger(__name__)


@click.group()
def app() -> None:
    pass


@app.command()
def start() -> None:
    logging_settings = LoggingSettings()
    logging_settings.setup_logging()
    bot = Bot(
        user_storage=UserStorage(),
        chitchat_client=ChitchatClient(ChitchatClientSettings()),
        logging_settings=logging_settings,
        remote_client_settings=RemoteClientSettings(),
        dialog_settings=DialogSettings(),
    )
    bot.run()
