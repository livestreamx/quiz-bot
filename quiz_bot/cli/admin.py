import click
from quiz_bot.cli.group import app


@app.command(short_help='Run application admin panel')
@click.option('--port', default=8076)
def admin(port: int) -> None:
    """ Run T-Quiz Bot admin panel. """
    from quiz_bot.admin import quizbot_app, set_basic_settings

    set_basic_settings()
    quizbot_app().run(host='0.0.0.0', port=port, debug=True)
