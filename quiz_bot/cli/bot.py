import io
import logging
from typing import Optional

import click
from quiz_bot.cli.group import app
from quiz_bot.cli.utils import get_settings, set_basic_settings
from quiz_bot.clients import ChitchatClient, RemoteBotClient
from quiz_bot.entity import ChallengeSettings, ChitchatSettings, InfoSettings, RemoteClientSettings
from quiz_bot.manager import ChallengeMaster, ClassicResultChecker, InterfaceMaker, QuizBot
from quiz_bot.storage import ChallengeStorage, ResultStorage, UserStorage

logger = logging.getLogger(__name__)


@app.command()
@click.option('-challenges', '--challenge-settings-file', type=click.File('r'), help='Challenge settings JSON file')
@click.option('-chitchat', '--chitchat-settings-file', type=click.File('r'), help='Chitchat settings JSON file')
def start(challenge_settings_file: Optional[io.StringIO], chitchat_settings_file: Optional[io.StringIO]) -> None:
    set_basic_settings()
    challenge_settings: ChallengeSettings = get_settings(
        file=challenge_settings_file, settings_type=ChallengeSettings  # type: ignore
    )
    chitchat_settings: ChitchatSettings = get_settings(
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
