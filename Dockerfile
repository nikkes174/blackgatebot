FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Europe/Moscow

WORKDIR /usr/src/app/bot

COPY VPNTgBot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY VPNTgBot/ .

CMD ["python", "bot.py"]