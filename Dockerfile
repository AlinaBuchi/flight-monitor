# base image
# more from https://hub.docker.com/search?q=
FROM python:3.10

# initialize project dir
RUN mkdir /src
WORKDIR /src

# install and config poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false

# install project dependencies
COPY poetry.lock pyproject.toml /src/
RUN poetry install -n --no-root

# final preparations
EXPOSE 5000
ENTRYPOINT ["python3", "/src/main.py"]