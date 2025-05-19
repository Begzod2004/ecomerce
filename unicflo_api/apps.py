from django.apps import AppConfig


class UnicfloApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'unicflo_api'
    
    def ready(self):
        import unicflo_api.signals  # Import the signals module