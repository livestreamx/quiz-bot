import io
import logging
from typing import Optional, Type

import click
from pydantic import BaseSettings
from quiz_bot.cli.group import app
from quiz_bot.clients import ChitchatClient, RemoteBotClient
from quiz_bot.entity import (
    ChallengeSettings,
    ChitchatSettings,
    DataBaseSettings,
    InfoSettings,
    LoggingSettings,
    RemoteClientSettings,
)
from quiz_bot.manager import ChallengeMaster, ClassicResultChecker, InterfaceMaker, QuizBot
from quiz_bot.storage import ChallengeStorage, ResultStorage, UserStorage

logger = logging.getLogger(__name__)


def _get_settings(file: Optional[io.StringIO], settings_type: Type[BaseSettings]) -> BaseSettings:
    if file is not None:
        return settings_type.parse_raw(file.read())
    return settings_type()


@app.command()
@click.option('-challenges', '--challenge-settings-file', type=click.File('r'))
@click.option('-chitchat', '--chitchat-settings-file', type=click.File('r'))
def start(challenge_settings_file: Optional[io.StringIO], chitchat_settings_file: Optional[io.StringIO]) -> None:
    LoggingSettings().setup_logging()
    DataBaseSettings().setup_db()
    challenge_settings: ChallengeSettings = _get_settings(
        file=challenge_settings_file, settings_type=ChallengeSettings  # type: ignore
    )
    chitchat_settings: ChitchatSettings = _get_settings(
        file=chitchat_settings_file, settings_type=ChitchatSettings  # type: ignore
    )
    bot = QuizBot(
        user_storage=UserStorage(),
        chitchat_client=ChitchatClient(chitchat_settings),
        remote_client=RemoteBotClient(RemoteClientSettings()),
        info_settings=InfoSettings(),
        interface_maker=InterfaceMaker(),
        challenge_master=ChallengeMaster(
            challenge_storage=ChallengeStorage(),
            settings=challenge_settings,
            result_checker=ClassicResultChecker(result_storage=ResultStorage(), challenge_settings=challenge_settings),
        ),
    )
    bot.run()
