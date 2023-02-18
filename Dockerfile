FROM python:3.8.14-slim

COPY requirements.txt .
RUN /usr/local/bin/python -m pip install --upgrade pip && pip install -r requirements.txt

WORKDIR /opt/4-A7
COPY main.py .
COPY bot bot

ENTRYPOINT ["python3", "main.py"]

