FROM python:3.8.1-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY ./requirements.txt /app

RUN apt-get -y update && \
  apt-get install -y --no-install-recommends \
  build-essential \
  libffi-dev \
  libpq-dev \
  libmagic1

RUN pip3 install --upgrade pip setuptools --no-cache-dir
RUN pip3 install wheel --no-cache-dir
RUN pip3 install -r /app/requirements.txt --no-cache-dir

RUN rm -rf /root/.cache/pip3


COPY . /app
