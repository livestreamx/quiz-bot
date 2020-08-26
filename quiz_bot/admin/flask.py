import jinja2
from flask import Flask


def get_flask_app(template_folder: str) -> Flask:
    app = Flask('T-Quiz Bot', template_folder=template_folder)
    app.secret_key = 'quizbot cool secret key'

    template_loader = jinja2.FileSystemLoader([template_folder])
    app.jinja_loader = jinja2.ChoiceLoader([app.jinja_loader, template_loader])  # type: ignore
    return app
