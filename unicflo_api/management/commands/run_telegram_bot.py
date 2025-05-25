from django.core.management.base import BaseCommand
from django.conf import settings
from unicflo_api.telegram.bot import run_bot
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run the Telegram bot'

    def handle(self, *args, **options):
        self.stdout.write('Starting Telegram bot...')
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stderr.write(self.style.ERROR('TELEGRAM_BOT_TOKEN not set in settings'))
            return

        try:
            # Run the bot
            run_bot()
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Bot stopped'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error running bot: {e}'))
            logger.error(f"Bot error: {e}", exc_info=True) 