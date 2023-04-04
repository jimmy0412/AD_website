FROM python:3.10-buster

RUN apt-get update
RUN pip install --upgrade pip
RUN pip install -U flask flask-sqlalchemy

ENV FLASK_APP=app
WORKDIR /app
COPY ./app /app
CMD python3 app2.py
