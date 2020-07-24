import logging

from quiz_bot.cli.group import app
from quiz_bot.manager import Bot, ChallengeMaster, ChitchatClient, InterfaceMaker
from quiz_bot.settings import (
    ChallengeSettings,
    ChitchatClientSettings,
    DataBaseSettings,
    InfoSettings,
    LoggingSettings,
    RemoteClientSettings,
)
from quiz_bot.storage import ChallengeStorage, ResultStorage, UserStorage

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
        info_settings=InfoSettings(),
        interface_maker=InterfaceMaker(),
        challenge_master=ChallengeMaster(
            challenge_storage=ChallengeStorage(), result_storage=ResultStorage(), settings=ChallengeSettings()
        ),
    )
    bot.run()
