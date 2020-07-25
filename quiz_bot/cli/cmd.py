import io
import logging
from typing import Optional

import click
from quiz_bot.cli.group import app
from quiz_bot.manager import Bot, ChallengeMaster, ChitchatClient, InterfaceMaker
from quiz_bot.manager.checker import ResultChecker
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


def _get_challenge_settings(challenge_settings_file: Optional[io.StringIO]) -> ChallengeSettings:
    if challenge_settings_file is not None:
        return ChallengeSettings.parse_raw(challenge_settings_file.read())
    return ChallengeSettings()


@app.command()
@click.option('-csf', '--challenge-settings-file', type=click.File('r'))
def start(challenge_settings_file: Optional[io.StringIO]) -> None:
    logging_settings = LoggingSettings()
    logging_settings.setup_logging()
    DataBaseSettings().setup_db()
    challenge_settings = _get_challenge_settings(challenge_settings_file)
    bot = Bot(
        user_storage=UserStorage(),
        chitchat_client=ChitchatClient(ChitchatClientSettings()),
        logging_settings=logging_settings,
        remote_client_settings=RemoteClientSettings(),
        info_settings=InfoSettings(),
        interface_maker=InterfaceMaker(),
        challenge_master=ChallengeMaster(
            challenge_storage=ChallengeStorage(),
            settings=challenge_settings,
            result_checker=ResultChecker(result_storage=ResultStorage(), challenge_settings=challenge_settings),
        ),
    )
    bot.run()
