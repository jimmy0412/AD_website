FROM --platform=$BUILDPLATFORM python:3.10-alpine AS builder

WORKDIR /app
RUN pip install pandas
COPY ./app /app
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt



ENTRYPOINT ["python3"]
CMD ["app.py"]

