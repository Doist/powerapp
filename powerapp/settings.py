"""
Django settings for powerapp project.

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""
import environ
from datetime import timedelta
from powerapp.discovery import app_discovery

root = environ.Path(__file__) - 2
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['*']),
    API_ENDPOINT=(str, 'https://api.todoist.com'),
    SECURE_PROXY_SSL_HEADER=(list, ['HTTP_X_FORWARDED_PROTO', 'https']),
    GOOGLE_SITE_VERIFICATION=(str, ''),
    RAVEN_DSN=(str, None),
    REDIS_URL=(str, 'redis://'),
    # statsd default settings
    STATSD_CLIENT=(str, 'django_statsd.clients.null'),  # disabled by default
    STATSD_MODEL_SIGNALS=(bool, False),
    STATSD_CELERY_SIGNALS=(bool, False),
    STATSD_HOST=(str, 'localhost'),
    STATSD_PORT=(int, 8125),
    STATSD_PREFIX=(str, 'powerapp'),
    # graylog default settings
    GRAYLOG2_HOST=(str, None),
    GRAYLOG2_PORT=(int, 12201),
)
env.read_env('.env')

# Website URL
SITE_URL = env('SITE_URL')

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
# or "root('subdir')"
BASE_DIR = root()

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# The SSL header to mark the connection as "secure". It's important for your
# app to be behind the proxy.
# Read https://docs.djangoproject.com/en/1.8/ref/settings/#secure-proxy-ssl-header
# for more information.
SECURE_PROXY_SSL_HEADER = env('SECURE_PROXY_SSL_HEADER')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_statsd',
    'djcelery',
    'powerapp.core',
    'powerapp.sync_bridge',
    'raven.contrib.django.raven_compat',
] + app_discovery()

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
    'powerapp.core.logging_utils.RequestContextMiddleware',
    'powerapp.core.statsd_middleware.GrafanaRequestTimingMiddleware',
)

LOGIN_URL = 'web_login'
AUTH_USER_MODEL = 'core.User'
AUTHENTICATION_BACKENDS = ('powerapp.core.django_auth_backend.TodoistUserAuth', )

ROOT_URLCONF = 'powerapp.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.core.context_processors.static',
                'powerapp.core.context_processors.settings_values',
            ],
        },
    },
]


STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
STATICFILES_DIRS = [root('powerapp/project_static')]

WSGI_APPLICATION = 'powerapp.wsgi.application'


DATABASES = {
    'default': env.db()
}


CACHES = {
    'default': env.cache('REDIS_URL'),
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = 'staticfiles'

# ==========================================================
# Celery (with Redis) Settings
# ==========================================================
REDIS_URL = env('REDIS_URL')
BROKER_URL = '%s/0' % REDIS_URL
CELERY_RESULT_BACKEND = '%s/1' % REDIS_URL
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_IGNORE_RESULT = True

CELERYBEAT_SCHEDULE = {
    'schedule_sync_tasks': {
        'task': 'powerapp.core.cron.schedule_sync_tasks',
        'schedule': timedelta(minutes=2),
    },
    'schedule_cron_tasks': {
        'task': 'powerapp.core.cron.schedule_cron_tasks',
        'schedule': timedelta(minutes=2),
    },
}
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

# Kill tasks after 5 minutes of execution by default
# Use time_limit argument to override this value for a particular task
CELERYD_TASK_TIME_LIMIT = 60 * 5

# ==========================================================
# Statsd settings
# ==========================================================

STATSD_CLIENT = env('STATSD_CLIENT')
STATSD_MODEL_SIGNALS = env('STATSD_MODEL_SIGNALS')
STATSD_CELERY_SIGNALS = env('STATSD_CELERY_SIGNALS')
STATSD_HOST = env('STATSD_HOST')
STATSD_PORT = env('STATSD_PORT')
STATSD_PREFIX = env('STATSD_PREFIX')

# ==========================================================
# PowerApp settings
# ==========================================================

API_ENDPOINT = env('API_ENDPOINT')
TODOIST_CLIENT_ID = env('TODOIST_CLIENT_ID')
TODOIST_CLIENT_SECRET = env('TODOIST_CLIENT_SECRET')
GOOGLE_SITE_VERIFICATION = env('GOOGLE_SITE_VERIFICATION')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    # Colored formatter for our logs
    'formatters': {
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s%(levelname)-8s%(reset)s %(white)s%(name)s %(blue)s%(message)s',
            'reset': True,
            'log_colors': {
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'red',
            }
        }
    },

    # Default Django filters
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'context_filter': {
            '()': 'powerapp.core.logging_utils.ContextFilter',
            'fields': {
                'project': 'powerapp',
            },
        },
    },

    # Log handlers: to console and to email (unless DEBUG=True)
    # We log exceptions on console even when DEBUG is True, because that's
    # just easier to handle callbacks
    'handlers': {
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'colored'
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },

    # Root logger
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },

    # All other loggers
    'loggers': {
        'powerapp': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'mail_admins'],
            'propagate': False,
        },
        'py.warnings': {
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'handlers': ['console'],
            'propagate': False,
        },
    }
}

if env('RAVEN_DSN') is not None:
    RAVEN_CONFIG = {
        'dsn': env('RAVEN_DSN')
    }

if env('GRAYLOG2_HOST') is not None:
    LOGGING['handlers']['graypy'] = {
        'level': 'DEBUG',
        'class': 'graypy.GELFHandler',
        'host': env('GRAYLOG2_HOST'),
        'port': env('GRAYLOG2_PORT'),
        'filters': ['context_filter'],
    }
    LOGGING['loggers']['powerapp']['handlers'].append('graypy')
