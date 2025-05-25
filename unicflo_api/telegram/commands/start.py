"""
Start command module for Telegram bot.
Contains initial greeting and setup functionality.
"""

import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from django.contrib.auth import get_user_model
from ..ui.messages import MessageTemplates
from ..ui.keyboards import Keyboards
from ..utils.decorators import handle_errors, user_required

logger = logging.getLogger(__name__)

User = get_user_model()

@handle_errors
@user_required
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    # Get user info from Telegram
    telegram_user = update.effective_user
    telegram_id = str(telegram_user.id)
    
    # Try to get or create user
    try:
        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'username': telegram_user.username or f"user_{telegram_id}",
                'first_name': telegram_user.first_name,
                'last_name': telegram_user.last_name,
                'is_telegram_user': True,
            }
        )
        
        if not created:
            # Update user info
            user.username = telegram_user.username or f"user_{telegram_id}"
            user.first_name = telegram_user.first_name
            user.last_name = telegram_user.last_name
            user.save()
        
        # Send welcome message with main menu
        await update.message.reply_text(
            MessageTemplates.welcome_message(user.get_full_name()),
            reply_markup=Keyboards.main_menu()
        )
        
        logger.info(f"User {user.telegram_id} started the bot")
        
    except Exception as e:
        # Log error and send generic message
        logger.error(f"Error in start command: {str(e)}")
        await update.message.reply_text(
            "Извините, произошла ошибка при обработке команды. "
            "Пожалуйста, попробуйте позже."
        ) 