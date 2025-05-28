SPECTACULAR_SETTINGS = {
    'TITLE': 'Unicflo API',
    'DESCRIPTION': 'API for Unicflo e-commerce platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'ENUM_NAME_OVERRIDES': {
        'AuthError': 'CustomAuthError',
        'OrderError': 'CustomOrderError',
        'Status5adEnum': 'OrderStatusEnum',
        'PaymentStatusEnum': 'OrderPaymentStatusEnum'
    }
} 