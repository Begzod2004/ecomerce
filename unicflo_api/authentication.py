from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth import get_user_model
from drf_spectacular.extensions import OpenApiAuthenticationExtension

User = get_user_model()

class TelegramAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        telegram_id = request.META.get('HTTP_X_TELEGRAM_ID')
        
        if not telegram_id:
            return None

        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found. Please start the Telegram bot first.')

        return (user, None)

    def authenticate_header(self, request):
        return 'X-Telegram-ID'

class TelegramAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = TelegramAuthentication
    name = 'TelegramAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-Telegram-ID',
            'description': 'Telegram user ID obtained from the bot after /start command'
        } 