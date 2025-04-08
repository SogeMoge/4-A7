FROM python:3.13.2-slim

COPY requirements.txt .
RUN apt-get update && apt-get install -y python3-dev build-essential
RUN /usr/local/bin/python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

WORKDIR /opt/4-A7
COPY main.py .
COPY bot bot
ENTRYPOINT ["python3", "main.py"]

