import io
import logging
from typing import Optional

import click
from quiz_bot.cli.group import app
from quiz_bot.cli.utils import get_settings, set_basic_settings
from quiz_bot.entity import ChallengeSettings, ChitchatSettings
from quiz_bot.factory import QuizBotFactory

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
    factory = QuizBotFactory(challenge_settings=challenge_settings, chitchat_settings=chitchat_settings)
    factory.quiz_bot.run()
