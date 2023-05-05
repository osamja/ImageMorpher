from .settings import *
import os
from dotenv import load_dotenv

load_dotenv()

# Development Redis configuration for Dramatiq
DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.redis.RedisBroker",
    "OPTIONS": {
        "url": "redis://dev-my-redis:6379",
    },
    "MIDDLEWARE": [
        "dramatiq.middleware.Prometheus",
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
        "django_dramatiq.middleware.AdminMiddleware",
    ]
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DEV_POSTGRES_DB'),
        'USER': os.environ.get('DEV_POSTGRES_USER'),
        'PASSWORD': os.environ.get('DEV_POSTGRES_PASSWORD'),
        'HOST': os.environ.get('DEV_POSTGRES_HOST'),
        'PORT': os.environ.get('DEV_POSTGRES_PORT'),
        'CONN_MAX_AGE': 600,
        # 'OPTIONS': {
        #     'options': '-c timezone=utc'
        # }
    }
}
