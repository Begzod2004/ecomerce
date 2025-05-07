from telegram import Bot
from telegram.ext import Updater
from django import conf
import asyncio

class TelegramService:
    def __init__(self):
        self.bot = Bot(token=conf('TELEGRAM_BOT_TOKEN'))

    async def send_message(self, chat_id, message):
        await self.bot.send_message(chat_id=chat_id, text=message)

    @staticmethod
    def notify_order_status(order):
        message = f"Order #{order.id} status updated to: {order.status}\n"
        message += f"Total: ${order.total_amount}\n"
        message += f"Shipping Address: {order.shipping_address}"
        # Foydalanuvchi Telegram ID’si saqlanadigan joydan olinadi
        chat_id = order.user.profile.telegram_chat_id if hasattr(order.user, 'profile') else None
        if chat_id:
            service = TelegramService()
            asyncio.run(service.send_message(chat_id, message))