ARG IMAGE_BASE
ARG BUILD_NUMBER
ARG POETRY_CONTENT_HASH

FROM ${IMAGE_BASE}chatbot/quiz-bot:${POETRY_CONTENT_HASH}

RUN mkdir /code/quiz_bot && touch /code/quiz_bot/__init__.py

COPY ./quiz_bot /code/quiz_bot
COPY ./makefile /code/makefile

CMD ["app", "start"]