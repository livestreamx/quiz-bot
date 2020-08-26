import logging
from pathlib import Path
from typing import Optional, cast
from uuid import uuid4

import matplotlib.pyplot as plt
from flask import Flask, Response, render_template, send_from_directory
from quiz_bot import db
from quiz_bot.admin.flask import get_flask_app
from quiz_bot.storage import MessageStorage
from wordcloud import WordCloud

logger = logging.getLogger(__name__)


def quizbot_app() -> Flask:
    admin_folder = Path(__file__).parent
    template_folder = admin_folder / "templates"
    static_folder = admin_folder / "files"

    flask_app = get_flask_app(template_folder.as_posix())
    wordcloud_factory = WordCloud(background_color="white", width=1280, height=640)
    message_storage = MessageStorage()

    @flask_app.teardown_request
    def remove_session(exception: Optional[Exception]) -> None:
        db.current_session.remove()

    @flask_app.route('/')
    def index() -> str:
        texts = [message.text for message in message_storage.messages]
        picture_name = f"f{str(uuid4())}.jpg"

        try:
            cloud = wordcloud_factory.generate(" ".join(texts))

            plt.imshow(cloud, interpolation='bilinear')
            plt.axis("off")
            plt.savefig((static_folder / picture_name).as_posix(), format="jpg", dpi=115)
        except ValueError:
            logger.exception("Troubles when creating wordcloud!")

        return render_template("index.html", page_name="T-Quiz Bot Overview", picture_name=picture_name)

    @flask_app.route('/files/<path:file>')
    def get_file(file: str) -> Response:
        return cast(Response, send_from_directory(static_folder.as_posix(), file))

    return flask_app  # noqa: R504
