import io
from typing import Optional

import click
from quiz_bot.admin import set_basic_settings
from quiz_bot.cli.group import app
from quiz_bot.cli.utils import get_settings
from quiz_bot.entity import ChallengeSettings, ShoutboxSettings
from quiz_bot.factory import ChatFactory, QuizInterfaceFactory


@app.command()
@click.option('-challenges', '--challenge-settings-file', type=click.File('r'), help='Challenge settings JSON file')
@click.option('-shoutbox', '--shoutbox-settings-file', type=click.File('r'), help='Shoutbox settings JSON file')
def run(challenge_settings_file: Optional[io.StringIO], shoutbox_settings_file: Optional[io.StringIO]) -> None:
    click.echo('Starting up QuizBot...')
    set_basic_settings()
    challenge_settings: ChallengeSettings = get_settings(
        file=challenge_settings_file, settings_type=ChallengeSettings  # type: ignore
    )
    shoutbox_settings: ShoutboxSettings = get_settings(
        file=shoutbox_settings_file, settings_type=ShoutboxSettings  # type: ignore
    )
    factory = QuizInterfaceFactory(challenge_settings=challenge_settings, shoutbox_settings=shoutbox_settings)
    factory.interface.run()


@app.command()
@click.option('-u', '--with-user', help="Chosen user nick_name for chat")
def chat(with_user: str) -> None:
    click.echo('Starting up ChatBot...')
    set_basic_settings()
    factory = ChatFactory(with_user)
    factory.interface.message()
    factory.interface.run()
