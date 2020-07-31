import io
from typing import Optional

import click
from quiz_bot.cli.group import app
from quiz_bot.cli.utils import get_settings, set_basic_settings
from quiz_bot.clients import RemoteBotClient
from quiz_bot.entity import ChallengeSettings, RemoteClientSettings
from quiz_bot.manager import ChallengeMaster, ClassicResultChecker, QuizNotifier
from quiz_bot.storage import ChallengeStorage, ResultStorage, UserStorage


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
    notifier = QuizNotifier(
        user_storage=UserStorage(),
        remote_client=RemoteBotClient(RemoteClientSettings()),
        challenge_master=ChallengeMaster(
            challenge_storage=ChallengeStorage(),
            settings=challenge_settings,
            result_checker=ClassicResultChecker(result_storage=ResultStorage(), challenge_settings=challenge_settings),
        ),
    )
    notifier.notify(challenge_id)
