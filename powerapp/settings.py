"""
Django settings for powerapp project.

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""
import environ
from powerapp.discovery import app_discovery

root = environ.Path(__file__) - 2
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['*']),
    API_ENDPOINT=(str, 'https://api.todoist.com'),
    SECURE_PROXY_SSL_HEADER=(list, ['HTTP_X_FORWARDED_PROTO', 'https']),
)
env.read_env('.env')

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
    'powerapp.core',
    'powerapp.sync_hub',
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
# PowerApp settings
# ==========================================================

API_ENDPOINT = env('API_ENDPOINT')
TODOIST_CLIENT_ID = env('TODOIST_CLIENT_ID')
TODOIST_CLIENT_SECRET = env('TODOIST_CLIENT_SECRET')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    # Colored formatter for our logs
    'formatters': {
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s',
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
    },

    # Log handlers: to console and to email (unless DEBUG=True)
    # We log exceptions on console even when DEBUG is True, because that's
    # just easier to handle callbacks
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'colored'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        }
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
    }
}
