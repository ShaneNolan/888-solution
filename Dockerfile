FROM python:3.8
WORKDIR /app

ENV POETRY_VERSION=1.0.10 \
    PATH="/root/.poetry/bin:$PATH"
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/${POETRY_VERSION}/get-poetry.py | python && \
    poetry config virtualenvs.create false
COPY ./pyproject.toml ./poetry.lock /app/
COPY ./app /app/app/


RUN poetry install --no-root --no-dev --no-interaction