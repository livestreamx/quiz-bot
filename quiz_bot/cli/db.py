import click
import sqlalchemy_utils as sau
from quiz_bot.cli.group import app
from quiz_bot.settings import DataBaseSettings
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError


def _ensure_database_exists(db_url: URL) -> None:
    try:
        if not sau.database_exists(db_url):
            sau.create_database(db_url)
    except OperationalError as e:
        click.echo(e)
        click.echo("Catched error when trying to check database existence!")


def _create_engine(context: click.Context, settings: DataBaseSettings) -> None:
    _ensure_database_exists(settings.url)
    context.obj = settings.setup_db()


@click.command()
@click.pass_obj
def create_all(engine: Engine) -> None:
    from quiz_bot.db.base import metadata

    click.echo('Creating schema...')
    metadata.create_all(engine)
    click.echo('Schema successfully created')


@click.command()
@click.pass_obj
def drop_all(engine: Engine) -> None:
    from quiz_bot.db.base import metadata

    click.echo('Dropping schema...')
    for table in metadata.tables:
        engine.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
    metadata.drop_all()
    click.echo('Schema successfully dropped!')


def db_commands(group: click.Group) -> click.Group:
    group.add_command(create_all)
    group.add_command(drop_all)
    return group


@db_commands
@app.group(short_help='Commands for simple database operations')
@click.pass_context
def db(ctx: click.Context) -> None:
    _create_engine(context=ctx, settings=DataBaseSettings())
