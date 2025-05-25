"""
Django management command to run the Telegram bot.
"""

import asyncio
import logging
import signal
from django.core.management.base import BaseCommand
from django.conf import settings
from unicflo_api.telegram import UnicfloBot

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run the Telegram bot'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = None
        self._shutdown = False
        
    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Starting Telegram bot...'))
            
            # Set up signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Create event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Create and run bot
            self.bot = UnicfloBot()
            loop.run_until_complete(self._run_bot())
            
        except Exception as e:
            logger.error(f"Error running bot: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error running bot: {str(e)}'))
            
        finally:
            if loop:
                loop.close()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.stdout.write(self.style.WARNING('\nReceived shutdown signal...'))
        self._shutdown = True
    
    async def _run_bot(self):
        """Run the bot and handle shutdown."""
        try:
            # Start the bot
            await self.bot.start()
            
            # Keep running until shutdown signal
            while not self._shutdown:
                await asyncio.sleep(1)
            
            # Stop the bot gracefully
            self.stdout.write(self.style.WARNING('\nStopping bot...'))
            await self.bot.stop()
            self.stdout.write(self.style.SUCCESS('Bot stopped successfully'))
            
        except Exception as e:
            logger.error(f"Error in bot execution: {str(e)}")
            raise 