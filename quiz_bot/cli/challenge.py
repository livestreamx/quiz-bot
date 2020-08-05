import io
from typing import Optional

import click
from quiz_bot.cli.group import app
from quiz_bot.cli.utils import get_settings, set_basic_settings
from quiz_bot.entity import ChallengeSettings, ChitchatSettings
from quiz_bot.factory import QuizManagerFactory


@app.group()
@click.pass_context
@click.option('-c', '--challenge-settings-file', type=click.File('r'), help='Challenge settings JSON file')
def challenge(ctx: click.Context, challenge_settings_file: Optional[io.StringIO]) -> None:
    set_basic_settings()
    challenge_settings: ChallengeSettings = get_settings(  # type: ignore
        file=challenge_settings_file, settings_type=ChallengeSettings
    )
    ctx.obj = QuizManagerFactory(challenge_settings=challenge_settings, chitchat_settings=ChitchatSettings())


@challenge.command()
@click.pass_obj
@click.option('-i', '--challenge-id', type=click.INT, help='Database challenge ID for notification')
def notification(obj: QuizManagerFactory, challenge_id: int) -> None:
    click.echo(f"Prepare notification for challenge ID {challenge_id}...")
    obj.notifier.notify(challenge_id)
    click.echo('Notification finished.')


@challenge.command()
@click.pass_obj
def start_next(obj: QuizManagerFactory) -> None:
    click.echo("Prepare to start next challenge...")
    previous_challenge = obj.challenge_master.current_challenge
    obj.manager.next()
    next_challenge = obj.challenge_master.current_challenge
    click.echo(f"Next challenge with ID {next_challenge.number} started.")

    if previous_challenge is not None:
        click.echo(f"Previous challenge with ID {previous_challenge.number} exists, so need to notify players.")
        obj.notifier.notify(previous_challenge.number)
        click.echo('Notification finished.')

    click.echo(f"Notify players about next challenge with ID {next_challenge.number}...")
    obj.notifier.notify(previous_challenge.number)
    click.echo('Notification finished.')
