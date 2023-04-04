FROM python:3.10-buster
RUN mkdir /app
WORKDIR /app
COPY ./app /app
RUN apt-get update
RUN pip install --upgrade pip
RUN pip install -U flask flask-sqlalchemy

ENV FLASK_APP=app

CMD python3 app2.py
