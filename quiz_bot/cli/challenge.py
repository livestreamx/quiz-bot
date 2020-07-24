from quiz_bot.cli.group import app


@app.group()
def challenge() -> None:
    pass


@challenge.command()
def go_to_next() -> None:
    pass
