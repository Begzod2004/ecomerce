from django.contrib.auth import login
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import ObjectDoesNotExist
from asgiref.sync import sync_to_async
from .models import User
import logging

logger = logging.getLogger(__name__)

class TelegramWebAppAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Check if request comes from Telegram WebApp
        user_id = request.GET.get('user_id')
        
        if user_id:
            try:
                # Get user by telegram_id
                user = User.objects.select_related().get(telegram_id=user_id)
                # Log user in
                if not request.user.is_authenticated:
                    login(request, user)
            except ObjectDoesNotExist:
                logger.warning(f"User with telegram_id {user_id} not found")
            except Exception as e:
                logger.error(f"Error in TelegramWebAppAuthMiddleware: {str(e)}")
        
        return None 