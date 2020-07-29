import io
import logging
from typing import Optional

import click
from quiz_bot.cli.group import app
from quiz_bot.clients import ChitchatClient, RemoteBotClient
from quiz_bot.manager import ChallengeMaster, InterfaceMaker, QuizBot
from quiz_bot.manager.checkers.classic import ClassicResultChecker
from quiz_bot.settings import (
    ChallengeSettings,
    ChitchatSettings,
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
    bot = QuizBot(
        user_storage=UserStorage(),
        chitchat_client=ChitchatClient(ChitchatSettings()),
        remote_client=RemoteBotClient(RemoteClientSettings()),
        logging_settings=logging_settings,
        info_settings=InfoSettings(),
        interface_maker=InterfaceMaker(),
        challenge_master=ChallengeMaster(
            challenge_storage=ChallengeStorage(),
            settings=challenge_settings,
            result_checker=ClassicResultChecker(result_storage=ResultStorage(), challenge_settings=challenge_settings),
        ),
    )
    bot.run()
