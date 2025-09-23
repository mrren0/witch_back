FROM python:3.12-slim

RUN apt-get update

WORKDIR /app

COPY requirements.txt .

ENV PIP_DISABLE_PYPI_PACKAGE_JSON=1
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/logs
RUN chmod -R 755 /app/logs
