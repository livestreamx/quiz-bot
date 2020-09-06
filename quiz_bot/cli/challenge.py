import io
from typing import Optional

import click
from quiz_bot.admin import set_basic_settings
from quiz_bot.cli.group import app
from quiz_bot.cli.utils import get_settings
from quiz_bot.entity import ChallengeSettings, ShoutboxSettings
from quiz_bot.factory import QuizManagerFactory


def _get_management_factory(challenge_settings_file: Optional[io.StringIO]) -> QuizManagerFactory:
    set_basic_settings()
    challenge_settings: ChallengeSettings = get_settings(  # type: ignore
        file=challenge_settings_file, settings_type=ChallengeSettings
    )
    return QuizManagerFactory(challenge_settings=challenge_settings, shoutbox_settings=ShoutboxSettings())


@app.group(short_help="Commands for challenge managment")
def challenge() -> None:
    pass


@challenge.command()
@click.option('-c', '--challenge-settings-file', type=click.File('r'), help='Challenge settings JSON file')
@click.option('-i', '--challenge-id', type=click.INT, help='Database challenge ID for notification')
def notification(challenge_settings_file: Optional[io.StringIO], challenge_id: Optional[int]) -> None:
    if isinstance(challenge_id, int):
        click.echo(f"Prepare notification for challenge ID {challenge_id}...")
    else:
        click.echo("Challenge ID not specified. Try to prepare notification for current challenge...")
    factory = _get_management_factory(challenge_settings_file)
    factory.notifier.notify(challenge_id)
    click.echo('Notification finished.')


@challenge.command()
@click.option('-c', '--challenge-settings-file', type=click.File('r'), help='Challenge settings JSON file')
def start_next(challenge_settings_file: Optional[io.StringIO]) -> None:
    click.echo("Prepare to start next challenge...")
    factory = _get_management_factory(challenge_settings_file)

    previous_number: Optional[int] = None
    if factory.challenge_master.keeper.has_data:
        previous_number = factory.challenge_master.keeper.number

    factory.manager.next()
    next_number = factory.challenge_master.keeper.number

    click.echo(f"Next challenge with ID {next_number} started.")

    if previous_number is not None:
        click.echo(f"Previous challenge with ID {previous_number} exists, so need to notify players.")
        factory.notifier.notify(previous_number)
        click.echo('Notification finished.')

    click.echo(f"Notify players about next challenge with ID {next_number}...")
    factory.notifier.notify(next_number, is_start=True)
    click.echo('Notification finished.')
