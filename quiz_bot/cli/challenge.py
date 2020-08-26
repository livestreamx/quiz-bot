import io
from typing import Optional

import click
from quiz_bot.admin import set_basic_settings
from quiz_bot.cli.group import app
from quiz_bot.cli.utils import get_settings
from quiz_bot.entity import ChallengeSettings, ChitchatSettings
from quiz_bot.factory import QuizManagerFactory


def _get_management_factory(challenge_settings_file: Optional[io.StringIO]) -> QuizManagerFactory:
    set_basic_settings()
    challenge_settings: ChallengeSettings = get_settings(  # type: ignore
        file=challenge_settings_file, settings_type=ChallengeSettings
    )
    return QuizManagerFactory(challenge_settings=challenge_settings, chitchat_settings=ChitchatSettings())


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

    previous_challenge = factory.challenge_master.current_challenge
    factory.manager.next()
    next_challenge = factory.challenge_master.current_challenge

    if next_challenge is None:
        raise RuntimeError("Next challenge could not be nullable!")

    click.echo(f"Next challenge with ID {next_challenge.number} started.")

    if previous_challenge is not None:
        click.echo(f"Previous challenge with ID {previous_challenge.number} exists, so need to notify players.")
        factory.notifier.notify(previous_challenge.number)
        click.echo('Notification finished.')

    click.echo(f"Notify players about next challenge with ID {next_challenge.number}...")
    factory.notifier.notify(next_challenge.number, is_start=True)
    click.echo('Notification finished.')
