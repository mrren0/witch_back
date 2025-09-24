FROM python:3.12-slim

RUN apt-get update

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/logs

RUN chmod -R 755 /app/logs
