"""
Messages module for Telegram bot UI.
Contains message templates and formatters.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from ...models import Order, User, Product, OrderItem
from .styles import Emojis, TextStyles

class MessageTemplates:
    """Message templates for different scenarios."""
    
    @staticmethod
    def welcome(user: User, is_admin: bool = False) -> str:
        """Welcome message template."""
        name = user.first_name or user.username or "Гость"
        
        message = (
            f"{Emojis.SPARKLES} {TextStyles.bold('Добро пожаловать')}, {name}!\n\n"
        )
        
        if is_admin:
            message += (
                f"{Emojis.ADMIN} Вы администратор системы\n\n"
                f"{TextStyles.bold('Доступные команды:')}\n"
                f"{Emojis.MANAGE} /admin - Панель управления\n"
                f"{Emojis.ORDER} /orders - Управление заказами\n"
                f"{Emojis.STATS} /stats - Статистика\n"
                f"{Emojis.SETTINGS} /settings - Настройки\n"
            )
        else:
            message += (
                f"{TextStyles.bold('Доступные команды:')}\n"
                f"{Emojis.ORDER} /myorders - Мои заказы\n"
                f"{Emojis.CART} /cart - Корзина\n"
                f"{Emojis.HEART} /wishlist - Избранное\n"
                f"{Emojis.HELP} /help - Помощь\n"
            )
            
        return message
    
    @staticmethod
    def error(message: str, admin_info: Optional[str] = None) -> str:
        """Error message template."""
        error_msg = f"{Emojis.ERROR} {message}"
        
        if admin_info:
            error_msg += (
                f"\n\n{TextStyles.italic('Техническая информация:')}\n"
                f"{TextStyles.code(admin_info)}"
            )
            
        return error_msg
    
    @staticmethod
    def success(message: str) -> str:
        """Success message template."""
        return f"{Emojis.SUCCESS} {message}"
    
    @staticmethod
    def warning(message: str) -> str:
        """Warning message template."""
        return f"{Emojis.WARNING} {message}"
    
    @staticmethod
    def info(message: str) -> str:
        """Info message template."""
        return f"{Emojis.INFO} {message}"

    @staticmethod
    def welcome_message(user_name: str) -> str:
        return (
            f"{Emojis.WELCOME} {TextStyles.header('Добро пожаловать в Unicflo')}\n"
            f"Здравствуйте, {TextStyles.bold(user_name)}!\n\n"
            f"{TextStyles.italic('Теперь вы будете получать уведомления о своих заказах в Telegram.')}\n\n"
            f"{Emojis.SHOPPING} Приятных покупок!"
        )
    
    @staticmethod
    def order_status_update(order) -> str:
        status_emoji = {
            'pending': Emojis.PENDING,
            'processing': Emojis.PROCESSING,
            'ready_for_pickup': Emojis.READY,
            'shipped': Emojis.SHIPPED,
            'delivered': Emojis.DELIVERED,
            'canceled': Emojis.CANCELED,
            'returned': Emojis.RETURNED,
        }.get(order.status, Emojis.INFO)
        
        message = (
            f"{Emojis.NOTIFICATION} {TextStyles.header(f'Обновление заказа #{order.id}')}\n"
            f"{Emojis.STATUS} Статус: {status_emoji} {TextStyles.bold(order.get_status_display())}\n"
            f"{Emojis.PRICE} Сумма: {TextStyles.bold(f'{order.final_amount:,} сум')}\n"
        )
        
        # Add delivery information
        if order.shipping_method:
            if order.shipping_method.delivery_type == 'branch_pickup':
                branch = order.pickup_branch
                if branch:
                    message += (
                        f"\n{Emojis.BRANCH} {TextStyles.subheader('Филиал для самовывоза')}"
                        f"{TextStyles.list_item(f'Название: {branch.name}')}\n"
                        f"{TextStyles.list_item(f'Адрес: {branch.street}, {branch.district}')}\n"
                        f"{TextStyles.list_item(f'Часы работы: {branch.working_hours}')}\n"
                    )
                    if branch.location_link:
                        message += f"{TextStyles.list_item(f'Локация: {branch.location_link}')}\n"
            else:  # home_delivery
                address = order.delivery_address
                if address:
                    message += (
                        f"\n{Emojis.HOME} {TextStyles.subheader('Адрес доставки')}"
                        f"{TextStyles.list_item(f'Адрес: {address.street}, {address.district}')}\n"
                        f"{TextStyles.list_item(f'Телефон: {order.phone_number}')}\n"
                    )
        
        # Add status-specific messages
        status_messages = {
            'pending': "Ваш заказ получен и ожидает обработки.",
            'processing': "Ваш заказ находится в обработке.",
            'ready_for_pickup': "Ваш заказ готов к получению в выбранном филиале!",
            'shipped': "Ваш заказ отправлен!",
            'delivered': "Ваш заказ доставлен. Спасибо за покупку!",
            'canceled': "Ваш заказ отменен.",
            'returned': "Возврат товара получен."
        }
        
        if order.status in status_messages:
            message += f"\n{TextStyles.italic(status_messages[order.status])}\n"
            
        if order.status == 'shipped' and order.tracking_number:
            message += f"\n{Emojis.TRACKING} Номер отслеживания: {TextStyles.code(order.tracking_number)}\n"
        
        # Add order items
        message += f"\n{TextStyles.subheader('Товары в заказе')}"
        for item in order.items.select_related('product', 'variant').all():
            variant_info = f" ({item.variant.color.name}, {item.variant.size.name})" if item.variant else ""
            message += TextStyles.list_item(
                f"{item.quantity}x {item.product.name}{variant_info} "
                f"({item.price:,} сум)"
            ) + "\n"
        
        return message

class OrderMessages:
    """Message templates for orders."""
    
    @staticmethod
    def format_order_details(order: Order, show_items: bool = True) -> str:
        """Format detailed order information."""
        status_emoji = {
            'pending': Emojis.PENDING,
            'processing': Emojis.PROCESSING,
            'shipped': Emojis.SHIPPING,
            'delivered': Emojis.SUCCESS,
            'canceled': Emojis.ERROR,
            'returned': Emojis.RETURN
        }.get(order.status, Emojis.ORDER)
        
        message = (
            f"{Emojis.ORDER} *Заказ #{order.id}*\n\n"
            f"{Emojis.STATUS} Статус: {status_emoji} {order.get_status_display()}\n"
            f"{Emojis.MONEY} Сумма: {order.final_amount:,} сум\n"
        )
        
        if order.shipping_method:
            message += f"{Emojis.SHIPPING} Доставка: {order.shipping_method.name}\n"
            
        if order.branch:
            message += f"\n{Emojis.LOCATION} *Филиал:*\n"
            message += f"{order.branch.name}\n"
            message += f"{order.branch.street}, {order.branch.district}\n"
            if order.branch.working_hours:
                message += f"Часы работы: {order.branch.working_hours}\n"
        
        if show_items and order.items.exists():
            message += f"\n{Emojis.PACKAGE} *Товары:*\n"
            for item in order.items.all():
                variant_info = ""
                if item.variant:
                    variant_info = f" ({item.variant.color.name}, {item.variant.size.name})"
                message += f"• {item.quantity}x {item.product.name}{variant_info}\n"
        
        return message
    
    @staticmethod
    def format_order_list(orders: List[Order]) -> str:
        """Format list of orders."""
        if not orders:
            return f"{Emojis.INFO} У вас пока нет заказов"
            
        message = f"{Emojis.ORDER} *Ваши заказы:*\n\n"
        
        for order in orders:
            status_emoji = {
                'pending': Emojis.PENDING,
                'processing': Emojis.PROCESSING,
                'shipped': Emojis.SHIPPING,
                'delivered': Emojis.SUCCESS,
                'canceled': Emojis.ERROR,
                'returned': Emojis.RETURN
            }.get(order.status, Emojis.ORDER)
            
            message += (
                f"#{order.id} - {status_emoji} {order.get_status_display()}\n"
                f"Сумма: {order.final_amount:,} сум\n"
                f"Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
            
        return message
    
    @staticmethod
    def format_order_status_update(order: Order) -> str:
        """Format order status update message."""
        status_emoji = {
            'pending': Emojis.PENDING,
            'processing': Emojis.PROCESSING,
            'shipped': Emojis.SHIPPING,
            'delivered': Emojis.SUCCESS,
            'canceled': Emojis.ERROR,
            'returned': Emojis.RETURN
        }.get(order.status, Emojis.ORDER)
        
        message = (
            f"{Emojis.NOTIFICATION} *Обновление заказа #{order.id}*\n\n"
            f"{Emojis.STATUS} Новый статус: {status_emoji} {order.get_status_display()}\n"
        )
        
        if order.status == 'shipped' and order.tracking_number:
            message += f"\n{Emojis.TRACKING} Номер отслеживания: {order.tracking_number}\n"
            
        return message 