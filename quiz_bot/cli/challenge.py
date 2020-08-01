import io
from typing import Optional

import click
from quiz_bot.cli.group import app
from quiz_bot.cli.utils import get_settings, set_basic_settings
from quiz_bot.entity import ChallengeSettings
from quiz_bot.factory import NotifierFactory


@app.group()
def challenge() -> None:
    pass


@challenge.command()
@click.option('-i', '--challenge-id', type=click.INT, help='Database challenge ID for notification')
@click.option('-c', '--challenge-settings-file', type=click.File('r'), help='Challenge settings JSON file')
def notification(challenge_id: int, challenge_settings_file: Optional[io.StringIO]) -> None:
    set_basic_settings()
    challenge_settings: ChallengeSettings = get_settings(
        file=challenge_settings_file, settings_type=ChallengeSettings  # type: ignore
    )
    factory = NotifierFactory(challenge_settings=challenge_settings)
    factory.notifier.notify(challenge_id)
