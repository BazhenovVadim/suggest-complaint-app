FROM python:3.12-slim

WORKDIR /bot

COPY vk_bot.py /bot/vk_bot.py
COPY requirements.txt /bot/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "vk_bot.py"]