FROM python:3.8-slim

RUN groupadd -r app && useradd -r -g app app

WORKDIR /code

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        gcc \
        htop \
        nano \
        locales \
        procps \
        make \
        g++ \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock /code/

RUN pip install --no-compile --upgrade pip \
 && pip install --no-compile poetry \
 && poetry config virtualenvs.create false \
 && mkdir -p /code/quiz_bot && touch /code/quiz_bot/__init__.py \
 && poetry install --no-dev --no-interaction --no-ansi \
 && pip uninstall --yes poetry \
 && rm -r /code/quiz_bot

ENTRYPOINT ["bash"]
CMD []
