import logging
import asyncio
from django.conf import settings
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

class TelegramService:
    @staticmethod
    async def send_message(chat_id, message):
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN not set. Skipping notification.")
            return
            
        try:
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            await bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Telegram message sent to {chat_id}")
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while sending Telegram message: {str(e)}")

    @staticmethod
    def notify_order_status(order):
        if not hasattr(order.user, 'profile') or not order.user.profile.telegram_chat_id:
            logger.info(f"User {order.user.username} has no Telegram chat ID. Skipping notification.")
            return
            
        chat_id = order.user.profile.telegram_chat_id
        
        # Create a detailed message
        message = f"📦 Order #{order.id} Update 📦\n\n"
        message += f"Status: {order.get_status_display()}\n"
        message += f"Total: ${order.final_amount}\n\n"
        
        if order.status == 'pending':
            message += "Your order has been received and is being processed.\n"
        elif order.status == 'processing':
            message += "Your order is being prepared for shipping.\n"
        elif order.status == 'shipped':
            message += f"Your order has been shipped! "
            if order.tracking_number:
                message += f"Tracking number: {order.tracking_number}\n"
        elif order.status == 'delivered':
            message += "Your order has been delivered. Thank you for shopping with us!\n"
        elif order.status == 'canceled':
            message += "Your order has been canceled.\n"
        elif order.status == 'returned':
            message += "Your returned items have been received.\n"
        
        # Add order items
        message += "\nOrder Items:\n"
        for item in order.items.all():
            message += f"- {item.quantity}x {item.product.name} (${item.price})\n"
        
        # Execute the async function
        try:
            asyncio.run(TelegramService.send_message(chat_id, message))
        except Exception as e:
            logger.error(f"Failed to send order notification: {str(e)}")
            
    @staticmethod
    def send_welcome_message(user_profile):
        if not user_profile.telegram_chat_id:
            logger.info(f"User has no Telegram chat ID. Skipping welcome message.")
            return
            
        chat_id = user_profile.telegram_chat_id
        message = f"👋 Welcome to Unicflo, {user_profile.user.username}! 👋\n\n"
        message += "Thank you for connecting your Telegram account. You will receive updates about your orders here.\n\n"
        message += "Happy shopping! 🛍️"
        
        try:
            asyncio.run(TelegramService.send_message(chat_id, message))
        except Exception as e:
            logger.error(f"Failed to send welcome message: {str(e)}")