import click
from quiz_bot.cli.group import app


@app.group()
def challenge() -> None:
    pass


@challenge.command()
@click.option('--challenge-id', help='Database challenge ID for finish notification')
def finish_notification() -> None:
    pass
