"""
Decorators module for Telegram bot.
Contains decorators for error handling and user validation.
"""

import logging
from functools import wraps
from telegram import Update
from telegram.constants import ParseMode
from ..ui.messages import MessageTemplates
from ..services.user_service import UserService

logger = logging.getLogger(__name__)

def handle_errors(func):
    """Error handling decorator for bot handlers."""
    @wraps(func)
    async def wrapper(update: Update, context, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            
            # Get the appropriate message object
            message = update.callback_query.message if update.callback_query else update.message
            
            # Send error message
            await message.reply_text(
                MessageTemplates.error(
                    "Произошла ошибка. Пожалуйста, попробуйте позже.",
                    str(e) if context.user_data.get('is_admin') else None
                ),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Re-raise for logging
            raise
            
    return wrapper

def user_required(func):
    """User validation decorator for bot handlers."""
    @wraps(func)
    async def wrapper(update: Update, context, *args, **kwargs):
        try:
            # Get user data
            user_data = update.effective_user
            if not user_data:
                message = update.callback_query.message if update.callback_query else update.message
                await message.reply_text(
                    MessageTemplates.error("Пользователь не найден"),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Get or create user in database
            user, created = await UserService.get_or_create_user(
                telegram_id=user_data.id,
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                language_code=user_data.language_code
            )
            
            if not user:
                message = update.callback_query.message if update.callback_query else update.message
                await message.reply_text(
                    MessageTemplates.error("Ошибка при получении данных пользователя"),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Check if user is blocked
            if not user.is_active:
                message = update.callback_query.message if update.callback_query else update.message
                await message.reply_text(
                    MessageTemplates.error("Ваш аккаунт заблокирован"),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Store user data in context
            context.user_data['user'] = user
            context.user_data['is_admin'] = user.is_telegram_admin
            
            return await func(update, context, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in user_required decorator: {str(e)}")
            message = update.callback_query.message if update.callback_query else update.message
            await message.reply_text(
                MessageTemplates.error("Произошла ошибка при проверке пользователя"),
                parse_mode=ParseMode.MARKDOWN
            )
            raise
            
    return wrapper

def admin_required(func):
    """Admin validation decorator for bot handlers."""
    @wraps(func)
    async def wrapper(update: Update, context, *args, **kwargs):
        try:
            # Get user data
            user_data = update.effective_user
            if not user_data:
                message = update.callback_query.message if update.callback_query else update.message
                await message.reply_text(
                    MessageTemplates.error("Пользователь не найден"),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Get user from database
            user = await UserService.get_user(user_data.id)
            if not user:
                message = update.callback_query.message if update.callback_query else update.message
                await message.reply_text(
                    MessageTemplates.error("Пользователь не найден в базе данных"),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Check if user is admin
            if not user.is_telegram_admin:
                message = update.callback_query.message if update.callback_query else update.message
                await message.reply_text(
                    MessageTemplates.error("У вас нет прав для этого действия"),
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Store user data in context
            context.user_data['user'] = user
            context.user_data['is_admin'] = True
            
            return await func(update, context, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in admin_required decorator: {str(e)}")
            message = update.callback_query.message if update.callback_query else update.message
            await message.reply_text(
                MessageTemplates.error("Произошла ошибка при проверке прав администратора"),
                parse_mode=ParseMode.MARKDOWN
            )
            raise
            
    return wrapper

def rate_limit(limit: int = 1, window: int = 60):
    """Rate limiting decorator for bot handlers."""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context, *args, **kwargs):
            try:
                # Get user ID
                user_id = update.effective_user.id
                
                # Get rate limit data from context
                rate_limits = context.bot_data.setdefault('rate_limits', {})
                user_limits = rate_limits.setdefault(user_id, {'count': 0, 'reset_time': 0})
                
                # Get current time
                current_time = int(time.time())
                
                # Reset counter if window has passed
                if current_time > user_limits['reset_time']:
                    user_limits['count'] = 0
                    user_limits['reset_time'] = current_time + window
                
                # Check rate limit
                if user_limits['count'] >= limit:
                    message = update.callback_query.message if update.callback_query else update.message
                    await message.reply_text(
                        MessageTemplates.warning(
                            f"Слишком много запросов. Пожалуйста, подождите {window} секунд."
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                
                # Increment counter
                user_limits['count'] += 1
                
                return await func(update, context, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in rate_limit decorator: {str(e)}")
                raise
                
        return wrapper
    return decorator 