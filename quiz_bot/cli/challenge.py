import io
from typing import Optional

import click
from quiz_bot.cli.group import app
from quiz_bot.cli.utils import get_settings, set_basic_settings
from quiz_bot.entity import ChallengeSettings, ChitchatSettings
from quiz_bot.factory import QuizManagerFactory, QuizNotifierFactory


@app.group()
@click.pass_context
@click.option('-c', '--challenge-settings-file', type=click.File('r'), help='Challenge settings JSON file')
def challenge(ctx: click.Context, challenge_settings_file: Optional[io.StringIO]) -> None:
    set_basic_settings()
    ctx.obj = get_settings(file=challenge_settings_file, settings_type=ChallengeSettings)


@challenge.command()
@click.pass_obj
@click.option('-i', '--challenge-id', type=click.INT, help='Database challenge ID for notification')
def notification(obj: ChallengeSettings, challenge_id: int) -> None:
    click.echo(f"Prepare notification for challenge ID {challenge_id}...")
    factory = QuizNotifierFactory(challenge_settings=obj)
    factory.notifier.notify(challenge_id)
    click.echo('Notification finished.')


@challenge.command()
@click.pass_obj
def start_next(obj: ChallengeSettings) -> None:
    click.echo("Prepare to start next challenge...")
    factory = QuizManagerFactory(challenge_settings=obj, chitchat_settings=ChitchatSettings())
    factory.manager.next()
    click.echo('Next challenge started.')
