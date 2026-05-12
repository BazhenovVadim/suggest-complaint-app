FROM python:3.12-slim

WORKDIR /bot

COPY tg_bot.py /bot/tg_bot.py
COPY requirements.txt /bot/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "tg_bot.py"]