"""
Main bot module for Telegram bot.
Contains bot setup and handlers registration.
"""

import logging
import asyncio
from pathlib import Path
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from django.conf import settings

from .commands.start import start_command
from .commands.admin import (
    admin_command,
    manage_orders,
    show_stats,
    settings as admin_settings,
    process_order_action,
    process_navigation
)
from .commands.orders import (
    my_orders_command,
    view_order,
    refresh_order,
    search_orders
)

logger = logging.getLogger(__name__)

class UnicfloBot:
    """Main bot class that handles initialization and setup."""
    
    def __init__(self):
        """Initialize bot with configuration."""
        if not settings.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
            
        self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Set up command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("admin", admin_command))
        self.application.add_handler(CommandHandler("myorders", my_orders_command))
        self.application.add_handler(CommandHandler("search", search_orders))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(
            manage_orders,
            pattern="^manage_orders$"
        ))
        self.application.add_handler(CallbackQueryHandler(
            show_stats,
            pattern="^show_stats$"
        ))
        self.application.add_handler(CallbackQueryHandler(
            admin_settings,
            pattern="^settings$"
        ))
        self.application.add_handler(CallbackQueryHandler(
            view_order,
            pattern="^view_order_[0-9]+$"
        ))
        self.application.add_handler(CallbackQueryHandler(
            refresh_order,
            pattern="^refresh_order_[0-9]+$"
        ))
        self.application.add_handler(CallbackQueryHandler(
            process_order_action,
            pattern="^(accept|process|ship|deliver|cancel|return)_order_[0-9]+$"
        ))
        self.application.add_handler(CallbackQueryHandler(
            process_navigation,
            pattern="^(page_[0-9]+|filter_(all|active|pending|processing|shipped))$"
        ))
        
        # Log errors
        self.application.add_error_handler(self._error_handler)
        
    async def _error_handler(self, update, context):
        """Log errors caused by updates."""
        logger.error(f"Update {update} caused error {context.error}")
        
    def run(self):
        """Run the bot."""
        logger.info("Starting bot...")
        self.application.run_polling()

def run_bot():
    """Run the bot."""
    try:
        bot = UnicfloBot()
        bot.run()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        raise
