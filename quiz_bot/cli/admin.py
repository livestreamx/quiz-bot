import click
from quiz_bot.cli.group import app
from quiz_bot.entity import MessageCloudSettings
from quiz_bot.storage import MessageStorage
from quiz_bot.utils import CloudMaker
from wordcloud import WordCloud


@app.command(short_help='Run application admin panel')
@click.option('-p', '--port', default=8076)
@click.option('-d', '--debug', is_flag=True)
def admin(port: int, debug: bool) -> None:
    """ Run T-Quiz Bot admin panel. """
    from quiz_bot.admin import quizbot_app, set_basic_settings

    set_basic_settings()
    cloud_maker = CloudMaker(
        wordcloud=WordCloud(background_color="white", width=1280, height=640),
        storage=MessageStorage(MessageCloudSettings()),
    )
    quizbot_app(cloud_maker=cloud_maker).run(host='0.0.0.0', port=port, debug=debug)
