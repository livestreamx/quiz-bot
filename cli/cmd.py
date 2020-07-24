import logging

from storage import UserStorage

from cli.group import app
from manager import (
    Bot,
    ChitchatClient,
    ChitchatClientSettings,
    DataBaseSettings,
    InfoSettings,
    LoggingSettings,
    RemoteClientSettings,
)
from manager.interface import InterfaceMaker

logger = logging.getLogger(__name__)


@app.command()
def start() -> None:
    logging_settings = LoggingSettings()
    logging_settings.setup_logging()
    DataBaseSettings().setup_db()
    bot = Bot(
        user_storage=UserStorage(),
        chitchat_client=ChitchatClient(ChitchatClientSettings()),
        logging_settings=logging_settings,
        remote_client_settings=RemoteClientSettings(),
        dialog_settings=InfoSettings(),
        interface_maker=InterfaceMaker(),
    )
    bot.run()
