from telegram import Bot
import asyncio

TOKEN = "8036212595:AAGqc1rVh4RA7nLkPw-psowqskY0ldPVS7c"
TELEGRAM_CHAT_IDS = 1243745632  # например, 123456789


def send_alert(message):
    """
    Асинхронно отправляет сообщение в Telegram.
    """
    # Используем asyncio.run для запуска асинхронной отправки
    asyncio.run(Bot(TOKEN).send_message(chat_id=CHAT_ID, text=message))