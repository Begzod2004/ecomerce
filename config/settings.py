import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$0==97wp-02u1ir2z-if8o9s8$h_h#mrvzvv#!*qw!7zp+@)5z'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    # 'unfold',
    # 'unfold.contrib.filters',
    # 'unfold.contrib.forms',
    # 'crispy_forms',
    # 'crispy_tailwind',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'drf_spectacular',
    'corsheaders',
    'unicflo_api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'unicflo_api.middleware.TelegramWebAppAuthMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'unicflo_api.authentication.TelegramAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'UNICFLO API',
    'DESCRIPTION': 'API for UNICFLO e-commerce platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
        'defaultModelsExpandDepth': -1,
        'defaultModelExpandDepth': 3,
        'defaultModelRendering': 'model',
        'displayRequestDuration': True,
        'docExpansion': 'list',
        'filter': True,
        'operationsSorter': 'alpha',
        'showExtensions': True,
        'showCommonExtensions': True,
        'supportedSubmitMethods': ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'],
    },
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    'SERVE_AUTHENTICATION': None,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'SERVE_PUBLIC': True,
    'TAGS': [
        {'name': 'User Management', 'description': 'Управление пользователями'},
        {'name': 'Category Management', 'description': 'Управление категориями товаров'},
        {'name': 'Subcategory Management', 'description': 'Управление подкатегориями товаров'},
        {'name': 'Brand Management', 'description': 'Управление брендами'},
        {'name': 'Color Management', 'description': 'Управление цветами'},
        {'name': 'Size Management', 'description': 'Управление размерами'},
        {'name': 'Material Management', 'description': 'Управление материалами'},
        {'name': 'Season Management', 'description': 'Управление сезонами'},
        {'name': 'Shipping Management', 'description': 'Управление методами доставки'},
        {'name': 'Product Management', 'description': 'Управление товарами'},
        {'name': 'Cart Management', 'description': 'Управление корзиной'},
        {'name': 'Order Management', 'description': 'Управление заказами'},
        {'name': 'Address Management', 'description': 'Управление адресами'},
        {'name': 'Wishlist Management', 'description': 'Управление списком желаний'},
    ],
    'SECURITY': [
        {
            'TelegramAuth': []
        }
    ],
    'SECURITY_DEFINITIONS': {
        'TelegramAuth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-Telegram-ID',
            'description': 'Telegram user ID obtained from the bot after /start command'
        }
    }
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'https://unicflo.com',
    'http://192.168.1.102:3000',
    'http://192.168.1.104:3000',
    'http://localhost:8001',
    'http://127.0.0.1:8001',
    'http://82.97.248.29:8001',
]

# Allow all origins temporarily for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-telegram-id',
]

SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8001',
    'http://127.0.0.1:8001',
    'http://82.97.248.29:8001',
]

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        },
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/unicflo.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'unicflo_api': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, 'env', 'Lib', 'site-packages', 'drf_spectacular_sidecar', 'static'),
]

# Create necessary directories
os.makedirs(os.path.join(BASE_DIR, 'static'), exist_ok=True)

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Create necessary directories
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, 'profile_pictures'), exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, 'product_images'), exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, 'category_images'), exist_ok=True)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'unicflo_api.User'

# Telegram Integration
TELEGRAM_BOT_TOKEN = '7803699406:AAGhJJtyBi-GRKPQBEHUSBgHNGH7Oo6C31w'
TELEGRAM_ADMIN_USER_IDS = [int(id) for id in os.getenv('TELEGRAM_ADMIN_USER_IDS', '').split(',') if id]
TELEGRAM_ORDER_BOT_TOKEN = os.getenv('TELEGRAM_ORDER_BOT_TOKEN', '')  # Order bot token
TELEGRAM_ADMIN_CHAT_ID = os.getenv('TELEGRAM_ADMIN_CHAT_ID', '')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://fixbanget-next.vercel.app')

# Unfold settings
UNFOLD = {
    "SITE_TITLE": "Unicflo Admin",
    "SITE_HEADER": "Unicflo",
    "SITE_URL": "/",
    "SITE_ICON": None,  # Replace with a URL path to your favicon
    "DASHBOARD": "unicflo_api.admin_dashboard.AdminDashboard",  # Class-based dashboard
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
#     "SIDEBAR": {
#         "show_search": True,
#         "show_all_applications": True,
#         "navigation": [
#             {
#                 "title": "E-commerce",
#                 "items": [
#                         {
#                         "title": "Dashboard",
#                         "icon": "dashboard",
#                         "link": "admin:index",
#                     },
#                     {
#                         "title": "Products",
#                         "icon": "inventory_2",
#                         "link": "admin:unicflo_api_product_changelist",
#                     },
#                     {
#                         "title": "Categories",
#                         "icon": "category",
#                         "link": "admin:unicflo_api_category_changelist",
#                     },
#                     {
#                         "title": "Orders",
#                         "icon": "shopping_cart",
#                         "link": "admin:unicflo_api_order_changelist",
#                     },
#                     {
#                         "title": "Customers",
#                         "icon": "people",
#                         "link": "admin:unicflo_api_user_changelist",
#                     },
#                     {
#                         "title": "Coupons",
#                         "icon": "local_offer",
#                         "link": "admin:unicflo_api_coupon_changelist",
#                     },
#                 ],
#             },
#             {
#                 "title": "Management",
#                 "items": [
#                     {
#                         "title": "Reviews",
#                         "icon": "star",
#                         "link": "admin:unicflo_api_productreview_changelist",
#                     },
#                     {
#                         "title": "Addresses",
#                         "icon": "map",
#                         "link": "admin:unicflo_api_address_changelist",
#                     },
#                 ],
#             },
#         ],
#     },
}

# Crispy Forms settings
# CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
# CRISPY_TEMPLATE_PACK = "tailwind"

# Admin site customization
JAZZMIN_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": "Unicflo Админ",
    # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_header": "Unicflo",
    # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_brand": "Unicflo",
    # Welcome text on the login screen
    "welcome_sign": "Добро пожаловать в панель администратора Unicflo",
    # Copyright on the footer
    "copyright": "Unicflo Ltd",
    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,
    # Links to put along the top menu
    "topmenu_links": [
        {"name": "Главная", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Сайт", "url": "/", "new_window": True},
    ],
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    # Use modals instead of popups
    "related_modal_active": True,
    # Relative paths to custom CSS/JS scripts (must be present in static files)
    "custom_css": None,
    "custom_js": None,
    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": False,
    # List of apps (and/or models) to base side menu ordering off of
    "order_with_respect_to": [
        "auth",
        "unicflo_api.User",
        "unicflo_api.Category",
        "unicflo_api.Product",
        "unicflo_api.ProductReview",
        "unicflo_api.Order",
        "unicflo_api.Coupon",
    ],
    # Custom links to append to app groups, keyed on app name
    "custom_links": {
        "unicflo_api": [
            {
                "name": "Статистика заказов", 
                "url": "admin:order_stats", 
                "icon": "fas fa-chart-line",
                "permissions": ["unicflo_api.view_order"]
            },
        ]
    },
    # Custom icons for side menu apps/models
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "unicflo_api.User": "fas fa-user",
        "unicflo_api.Category": "fas fa-list",
        "unicflo_api.Product": "fas fa-box-open",
        "unicflo_api.ProductReview": "fas fa-star",
        "unicflo_api.Order": "fas fa-shopping-cart",
        "unicflo_api.Coupon": "fas fa-percent",
        "unicflo_api.Address": "fas fa-map-marker-alt",
        "unicflo_api.Cart": "fas fa-shopping-basket",
        "unicflo_api.Wishlist": "fas fa-heart",
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-purple",
    "accent": "accent-purple",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-purple",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "cyborg",
    "dark_mode_theme": "cyborg",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    }
}

# Redis configuration
REDIS_HOST = 'redis'
REDIS_PORT = 6379

# Try to use Redis cache if django-redis is installed
try:
    import django_redis
    CACHES['redis'] = {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 1000,
            'CONNECTION_POOL_KWARGS': {'max_connections': 100},
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'unicflo',
        'TIMEOUT': 300,  # 5 minutes
    }
except ImportError:
    pass  # Django-Redis not installed, using default cache only

# Celery settings
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Telegram Bot settings
TELEGRAM_WEBHOOK_URL = None  # Optional: Set this if you want to use webhooks
TELEGRAM_ADMIN_USER_ID = None  # Optional: Set this to restrict admin commands

# Logging settings for Telegram bot
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'telegram_bot.log',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'telegram': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
