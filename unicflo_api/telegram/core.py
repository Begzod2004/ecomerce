"""
Core module for Telegram bot.
Contains base configuration, setup and error handling.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from telegram import Bot, Update
from telegram.ext import Application, ContextTypes
from django.conf import settings

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(Path(settings.BASE_DIR) / 'logs' / 'telegram_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class UnicfloBot:
    """Main bot class that handles initialization and core functionality."""
    
    def __init__(self):
        """Initialize bot with configuration."""
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.admin_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
        self.admin_ids = settings.TELEGRAM_ADMIN_USER_IDS
        self.webapp_url = settings.WEBAPP_URL
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        
    async def initialize(self) -> None:
        """Initialize bot and application."""
        try:
            # Create bot instance
            self.bot = Bot(token=self.token)
            
            # Create application
            self.application = Application.builder().token(self.token).build()
            
            # Register error handler
            self.application.add_error_handler(self.error_handler)
            
            # Register commands (will be implemented in commands module)
            await self.register_commands()
            
            logger.info("Bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {str(e)}")
            raise
            
    async def register_commands(self) -> None:
        """Register bot commands and handlers."""
        # Will be implemented when we create commands module
        pass
            
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle bot errors."""
        try:
            error = context.error
            logger.error(f"Update {update} caused error: {str(error)}")
            
            # Get chat for error message
            chat_id = update.effective_chat.id if update and update.effective_chat else None
            
            if chat_id:
                error_message = (
                    "⚠️ Произошла ошибка при обработке запроса.\n"
                    "Пожалуйста, попробуйте позже или обратитесь к администратору."
                )
                await context.bot.send_message(chat_id=chat_id, text=error_message)
                
            # Notify admins about error
            if self.admin_chat_id:
                admin_message = (
                    f"🔴 *Ошибка в боте*\n"
                    f"Чат: {chat_id}\n"
                    f"Update: {update}\n"
                    f"Ошибка: {str(error)}"
                )
                await context.bot.send_message(
                    chat_id=self.admin_chat_id,
                    text=admin_message,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error in error handler: {str(e)}")
            
    async def start(self) -> None:
        """Start the bot."""
        try:
            if not self.application:
                await self.initialize()
                
            # Start bot
            await self.application.start()
            logger.info("Bot started successfully")
            
            # Run bot until stopped
            await self.application.run_polling()
            
        except Exception as e:
            logger.error(f"Failed to start bot: {str(e)}")
            raise
            
    async def stop(self) -> None:
        """Stop the bot."""
        try:
            if self.application:
                await self.application.stop()
                logger.info("Bot stopped successfully")
                
        except Exception as e:
            logger.error(f"Failed to stop bot: {str(e)}")
            raise

# Create bot instance
bot = UnicfloBot() 