from pathlib import Path
from typing import Optional

from flask import Flask, render_template
from quiz_bot import db
from quiz_bot.admin.flask import get_flask_app


def quizbot_app() -> Flask:
    template_folder = Path(__file__).parent / "templates"
    flask_app = get_flask_app(template_folder.as_posix())

    @flask_app.teardown_request
    def remove_session(exception: Optional[Exception]) -> None:
        db.current_session.remove()

    @flask_app.route('/')
    def index() -> str:
        return render_template("index.html", name="T-Quiz Bot Overview")

    return flask_app  # noqa: R504
