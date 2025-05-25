"""
Orders command module for Telegram bot.
Contains order management commands and related functionality.
"""

import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from ..ui.messages import MessageTemplates
from ..ui.keyboards import Keyboards
from ..ui.styles import Emojis, TextStyles
from ..services.order_service import OrderService
from ..utils.decorators import handle_errors, user_required

logger = logging.getLogger(__name__)

@handle_errors
@user_required
async def my_orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /myorders command."""
    try:
        # Get user from context
        user = context.user_data['user']
        
        # Get user's orders
        orders = await OrderService.get_user_orders(user)
        
        # Format orders list
        orders_text = await OrderService.format_order_list(orders)
        
        # Send message
        await update.message.reply_text(
            orders_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.main_menu(user.is_telegram_admin)
        )
        
        logger.info(f"User {user.telegram_id} viewed their orders")
        
    except Exception as e:
        logger.error(f"Error in my_orders command: {str(e)}")
        raise

@handle_errors
@user_required
async def view_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle view_order callback."""
    try:
        # Get user from context
        user = context.user_data['user']
        
        # Get order ID from callback data
        callback_data = update.callback_query.data
        order_id = int(callback_data.split('_')[-1])
        
        # Get order
        order = await OrderService.get_order_by_id(order_id)
        if not order:
            await update.callback_query.answer("Заказ не найден")
            return
        
        # Check if user has access to this order
        if not user.is_telegram_admin and order.user != user:
            await update.callback_query.answer("У вас нет доступа к этому заказу")
            return
        
        # Format order details
        order_text = await OrderService.format_order_message(order)
        
        # Send message with appropriate keyboard
        keyboard = (
            Keyboards.order_actions(order)
            if user.is_telegram_admin
            else Keyboards.back_keyboard("my_orders")
        )
        
        await update.callback_query.message.edit_text(
            order_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        logger.info(f"User {user.telegram_id} viewed order {order_id}")
        
    except Exception as e:
        logger.error(f"Error in view_order: {str(e)}")
        raise

@handle_errors
@user_required
async def refresh_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle refresh_order callback."""
    try:
        # Get user from context
        user = context.user_data['user']
        
        # Get order ID from callback data
        callback_data = update.callback_query.data
        order_id = int(callback_data.split('_')[-1])
        
        # Get order
        order = await OrderService.get_order_by_id(order_id)
        if not order:
            await update.callback_query.answer("Заказ не найден")
            return
        
        # Check if user has access to this order
        if not user.is_telegram_admin and order.user != user:
            await update.callback_query.answer("У вас нет доступа к этому заказу")
            return
        
        # Format order details
        order_text = await OrderService.format_order_message(order)
        
        # Send message with appropriate keyboard
        keyboard = (
            Keyboards.order_actions(order)
            if user.is_telegram_admin
            else Keyboards.back_keyboard("my_orders")
        )
        
        await update.callback_query.message.edit_text(
            order_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        await update.callback_query.answer("Информация обновлена")
        
        logger.info(f"User {user.telegram_id} refreshed order {order_id}")
        
    except Exception as e:
        logger.error(f"Error in refresh_order: {str(e)}")
        raise

@handle_errors
@user_required
async def search_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle search_orders command."""
    try:
        # Get user from context
        user = context.user_data['user']
        
        # Check if user is admin
        if not user.is_telegram_admin:
            await update.message.reply_text(
                MessageTemplates.error("У вас нет прав для этого действия"),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Get search query
        query = ' '.join(context.args)
        if not query:
            await update.message.reply_text(
                f"{Emojis.SEARCH} Введите поисковый запрос после команды:\n"
                f"/search <запрос>",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Search orders
        orders = await OrderService.search_orders(query)
        
        if not orders:
            await update.message.reply_text(
                f"{Emojis.SEARCH} По запросу «{query}» ничего не найдено",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Format orders list
        orders_text = await OrderService.format_order_list(orders)
        
        # Send results
        await update.message.reply_text(
            f"{Emojis.SEARCH} Результаты поиска по запросу «{query}»:\n\n"
            f"{orders_text}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"Admin {user.telegram_id} searched orders with query: {query}")
        
    except Exception as e:
        logger.error(f"Error in search_orders: {str(e)}")
        raise 