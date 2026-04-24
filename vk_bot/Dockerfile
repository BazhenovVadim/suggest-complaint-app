FROM python:3.12-slim

WORKDIR /bot

COPY vk_bot.py /bot/vk_bot.py

RUN pip install --no-cache-dir \
    vkbottle==4.6.2 \
    aiohttp==3.13.5 \
    python-dotenv==1.2.2

CMD ["python", "vk_bot.py"]