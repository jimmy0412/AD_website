FROM python:3.10-buster

WORKDIR /app
COPY . /app
RUN apt-get update
RUN pip install -U flask flask-sqlalchemy 

CMD run python3 app.py
