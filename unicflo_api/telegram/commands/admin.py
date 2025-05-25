"""
Admin command module for Telegram bot.
Contains admin command handlers and related functionality.
"""

import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from ..ui.messages import MessageTemplates
from ..ui.keyboards import Keyboards
from ..ui.styles import Emojis, TextStyles
from ..services.order_service import OrderService
from ..services.user_service import UserService
from ..utils.decorators import handle_errors, admin_required

logger = logging.getLogger(__name__)

@handle_errors
@admin_required
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin command."""
    try:
        # Get user from context
        user = context.user_data['user']
        
        # Send admin panel
        await update.message.reply_text(
            f"{Emojis.ADMIN} {TextStyles.bold('Панель управления')}\n\n"
            f"Выберите действие:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.admin_panel()
        )
        
        logger.info(f"Admin {user.telegram_id} opened admin panel")
        
    except Exception as e:
        logger.error(f"Error in admin command: {str(e)}")
        raise

@handle_errors
@admin_required
async def manage_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle manage_orders callback."""
    try:
        # Get user from context
        user = context.user_data['user']
        
        # Get current page and filter from context or set defaults
        page = context.user_data.get('orders_page', 1)
        filter_type = context.user_data.get('orders_filter', 'active')
        
        # Get filtered orders
        orders, total_pages = await OrderService.get_filtered_orders(
            filter_type=filter_type,
            page=page
        )
        
        # Format orders list
        orders_text = await OrderService.format_order_list(orders)
        
        # Send message with navigation
        message = update.callback_query.message if update.callback_query else update.message
        await message.reply_text(
            orders_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.orders_navigation(page, total_pages, filter_type)
        )
        
        logger.info(f"Admin {user.telegram_id} viewing orders (page {page}, filter: {filter_type})")
        
    except Exception as e:
        logger.error(f"Error in manage_orders: {str(e)}")
        raise

@handle_errors
@admin_required
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle show_stats callback."""
    try:
        # Get user from context
        user = context.user_data['user']
        
        # Get statistics
        order_stats = await OrderService.get_order_stats()
        user_stats = await UserService.get_user_stats()
        
        # Format statistics message
        stats_message = (
            f"{TextStyles.section_title('Статистика', Emojis.STATS)}\n"
            f"\n{TextStyles.section_title('Заказы', Emojis.ORDER)}"
            f"{TextStyles.key_value('Всего заказов', str(order_stats['total']), Emojis.CHART)}"
            f"{TextStyles.key_value('Активные', str(order_stats['active']) + f' ({order_stats['active_percent']}%)', Emojis.FIRE)}"
            f"{TextStyles.key_value('Ожидают', str(order_stats['pending']) + f' ({order_stats['pending_percent']}%)', Emojis.PENDING)}"
            f"{TextStyles.key_value('В обработке', str(order_stats['processing']) + f' ({order_stats['processing_percent']}%)', Emojis.PROCESSING)}"
            f"{TextStyles.key_value('Отправлены', str(order_stats['shipped']) + f' ({order_stats['shipped_percent']}%)', Emojis.SHIPPED)}"
            f"{TextStyles.key_value('Доставлены', str(order_stats['delivered']) + f' ({order_stats['delivered_percent']}%)', Emojis.SUCCESS)}"
            f"{TextStyles.key_value('Отменены', str(order_stats['canceled']) + f' ({order_stats['canceled_percent']}%)', Emojis.ERROR)}"
            f"{TextStyles.key_value('Возвраты', str(order_stats['returned']) + f' ({order_stats['returned_percent']}%)', Emojis.RETURNED)}"
            f"{TextStyles.key_value('За сегодня', str(order_stats['today']), Emojis.CALENDAR)}"
            f"\n{TextStyles.section_title('Пользователи', Emojis.USER)}"
            f"{TextStyles.key_value('Всего пользователей', str(user_stats['total']), Emojis.CHART)}"
            f"{TextStyles.key_value('Администраторы', str(user_stats['admins']) + f' ({user_stats['admins_percent']}%)', Emojis.ADMIN)}"
            f"{TextStyles.key_value('Активные', str(user_stats['active']) + f' ({user_stats['active_percent']}%)', Emojis.SUCCESS)}"
            f"{TextStyles.key_value('Заблокированные', str(user_stats['blocked']) + f' ({user_stats['blocked_percent']}%)', Emojis.ERROR)}"
            f"{TextStyles.key_value('С заказами', str(user_stats['with_orders']) + f' ({user_stats['with_orders_percent']}%)', Emojis.ORDER)}"
            f"{TextStyles.key_value('За сегодня', str(user_stats['today']), Emojis.CALENDAR)}"
        )
        
        # Send statistics
        message = update.callback_query.message if update.callback_query else update.message
        await message.reply_text(
            stats_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.back_keyboard("admin_panel")
        )
        
        logger.info(f"Admin {user.telegram_id} viewed statistics")
        
    except Exception as e:
        logger.error(f"Error in show_stats: {str(e)}")
        raise

@handle_errors
@admin_required
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle settings callback."""
    try:
        # Get user from context
        user = context.user_data['user']
        
        # Send settings menu
        message = update.callback_query.message if update.callback_query else update.message
        await message.reply_text(
            f"{TextStyles.section_title('Настройки', Emojis.SETTINGS)}\n"
            f"Выберите раздел:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.settings_keyboard()
        )
        
        logger.info(f"Admin {user.telegram_id} opened settings")
        
    except Exception as e:
        logger.error(f"Error in settings: {str(e)}")
        raise

@handle_errors
@admin_required
async def process_order_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle order action callbacks."""
    try:
        # Get user from context
        user = context.user_data['user']
        
        # Get callback data
        callback_data = update.callback_query.data
        action, order_id = callback_data.split('_')[0], int(callback_data.split('_')[-1])
        
        # Validate action
        is_valid, message = await OrderService.validate_order_action(order_id, action, user)
        if not is_valid:
            await update.callback_query.answer(message)
            return
        
        # Process action
        order = await OrderService.update_order_status(order_id, action)
        if not order:
            await update.callback_query.answer("Ошибка при обновлении заказа")
            return
        
        # Send status update
        status_message = await OrderService.format_order_status_update(order)
        await update.callback_query.message.reply_text(
            status_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Update order details
        order_message = await OrderService.format_order_message(order)
        await update.callback_query.message.edit_text(
            order_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=Keyboards.order_actions(order)
        )
        
        logger.info(f"Admin {user.telegram_id} performed action {action} on order {order_id}")
        
    except Exception as e:
        logger.error(f"Error in process_order_action: {str(e)}")
        raise

@handle_errors
@admin_required
async def process_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle navigation callbacks."""
    try:
        # Get user from context
        user = context.user_data['user']
        
        # Get callback data
        callback_data = update.callback_query.data
        
        if callback_data.startswith('page_'):
            # Handle page navigation
            page = int(callback_data.split('_')[1])
            context.user_data['orders_page'] = page
            await manage_orders(update, context)
            
        elif callback_data.startswith('filter_'):
            # Handle filter change
            filter_type = callback_data.split('_')[1]
            context.user_data['orders_filter'] = filter_type
            context.user_data['orders_page'] = 1
            await manage_orders(update, context)
            
        logger.info(f"Admin {user.telegram_id} navigated to {callback_data}")
        
    except Exception as e:
        logger.error(f"Error in process_navigation: {str(e)}")
        raise 