import os
from pathlib import Path
from typing import Optional, cast

from flask import Flask, Response, render_template, send_from_directory
from quiz_bot import db
from quiz_bot.admin.cloud import CloudMaker
from quiz_bot.admin.flask import get_flask_app
from quiz_bot.admin.statistics import StatisticsCollector


def quizbot_app(cloud_maker: CloudMaker, statistics_collector: StatisticsCollector) -> Flask:
    admin_folder = Path(__file__).parent
    template_folder = admin_folder / "templates"
    static_folder = admin_folder / "files"

    if not static_folder.exists():
        os.makedirs(static_folder.as_posix())

    flask_app = get_flask_app(template_folder.as_posix())

    @flask_app.teardown_request
    def remove_session(exception: Optional[Exception]) -> None:
        db.current_session.remove()

    @flask_app.route('/')
    def index() -> str:
        picture_name = cloud_maker.save_cloud(static_folder)
        return render_template(
            "index.html",
            page_name="T-Quiz Bot Overview",
            picture_name=picture_name,
            statistics=statistics_collector.statistics,
        )

    @flask_app.route('/files/<path:file>')
    def get_file(file: str) -> Response:
        return cast(Response, send_from_directory(static_folder.as_posix(), file))

    return flask_app  # noqa: R504
