import logging
from time import sleep

import click

from manager import ApplicationSettings, init_app, run_app

logger = logging.getLogger(__name__)


@click.group()
def app() -> None:
    pass


@app.command()
def start() -> None:
    app_settings = ApplicationSettings()
    app_settings.setup_logging()
    bot = init_app(app_settings)
    while True:
        try:
            run_app(bot)
        except Exception:
            logger.exception("Raised error while application running!")
            sleep(1)
