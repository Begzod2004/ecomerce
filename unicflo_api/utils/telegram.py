import logging
import asyncio
from django.conf import settings
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

# Emoji constants
EMOJIS = {
    'pending': '⏳',
    'processing': '🔄',
    'ready_for_pickup': '✨',
    'shipped': '📦',
    'delivered': '✅',
    'canceled': '❌',
    'returned': '↩️',
    'notification': '🔔',
    'status': '📍',
    'price': '💰',
    'branch': '🏪',
    'home': '🏠',
}

class TelegramService:
    @staticmethod
    async def send_message(chat_id, message):
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN not set. Skipping notification.")
            return
            
        try:
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
            logger.info(f"Telegram message sent to {chat_id}")
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while sending Telegram message: {str(e)}")

    @staticmethod
    def notify_order_status(order):
        if not order.user.telegram_id:
            logger.info(f"User {order.user.username} has no Telegram chat ID. Skipping notification.")
            return
            
        status_emoji = EMOJIS.get(order.status, EMOJIS['notification'])
        
        # Create a detailed message
        message = (
            f"{EMOJIS['notification']} *Обновление заказа #{order.id}*\n\n"
            f"{EMOJIS['status']} Статус: {status_emoji} {order.get_status_display()}\n"
            f"{EMOJIS['price']} Сумма: {order.final_amount:,} сум\n"
        )

        # Add delivery information based on shipping method
        if order.shipping_method:
            if order.shipping_method.delivery_type == 'branch_pickup':
                branch = order.pickup_branch
                if branch:
                    message += f"\n{EMOJIS['branch']} *Филиал для самовывоза:*\n"
                    message += f"Название: {branch.name}\n"
                    message += f"Адрес: {branch.street}, {branch.district}\n"
                    message += f"Часы работы: {branch.working_hours}\n"
                    if branch.location_link:
                        message += f"Локация: {branch.location_link}\n"
            else:  # home_delivery
                address = order.delivery_address
                if address:
                    message += f"\n{EMOJIS['home']} *Адрес доставки:*\n"
                    message += f"Адрес: {address.street}, {address.district}\n"
                    message += f"Телефон: {order.phone_number}\n"
        
        # Add status-specific messages
        if order.status == 'pending':
            message += "\nВаш заказ получен и ожидает обработки.\n"
        elif order.status == 'processing':
            message += "\nВаш заказ находится в обработке.\n"
        elif order.status == 'ready_for_pickup':
            message += "\nВаш заказ готов к получению в выбранном филиале!\n"
        elif order.status == 'shipped':
            message += "\nВаш заказ отправлен!\n"
            if order.tracking_number:
                message += f"Номер отслеживания: {order.tracking_number}\n"
        elif order.status == 'delivered':
            message += "\nВаш заказ доставлен. Спасибо за покупку!\n"
        elif order.status == 'canceled':
            message += "\nВаш заказ отменен.\n"
        elif order.status == 'returned':
            message += "\nВозврат товара получен.\n"
        
        # Add order items
        message += "\nТовары в заказе:\n"
        for item in order.items.select_related('product').all():
            message += f"• {item.quantity}x {item.product.name} ({item.price:,} сум)\n"
        
        try:
            asyncio.run(TelegramService.send_message(order.user.telegram_id, message))
        except Exception as e:
            logger.error(f"Failed to send order notification: {str(e)}")
            
    @staticmethod
    def send_welcome_message(user):
        if not user.telegram_id:
            logger.info(f"User has no Telegram chat ID. Skipping welcome message.")
            return
            
        message = (
            f"👋 Добро пожаловать в Unicflo, {user.get_full_name() or user.username}!\n\n"
            "Спасибо за подключение Telegram аккаунта. "
            "Теперь вы будете получать уведомления о статусе ваших заказов здесь.\n\n"
            "Приятных покупок! 🛍️"
        )
        
        try:
            asyncio.run(TelegramService.send_message(user.telegram_id, message))
        except Exception as e:
            logger.error(f"Failed to send welcome message: {str(e)}")