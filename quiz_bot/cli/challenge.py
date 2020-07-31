import click
from quiz_bot.cli.group import app


@app.group()
def challenge() -> None:
    pass


@challenge.command()
@click.option('-i', '--id', help='Database challenge ID for notification')
def notification() -> None:
    pass
