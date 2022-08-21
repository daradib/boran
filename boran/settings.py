import json
from pathlib import Path

from django.utils.crypto import get_random_string
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

# Load the secret key if possible, otherwise generate one.
secret_filename = BASE_DIR / 'data/secrets.json'
try:
    with open(secret_filename) as f:
        SECRETS = json.load(f)
    SECRET_KEY = SECRETS['SECRET_KEY']
except Exception:
    SECRET_KEY = get_random_string(50)
    SECRETS = {'SECRET_KEY': SECRET_KEY}
    json.dump(SECRETS, open(secret_filename, 'w'))

if 'DEBUG' in SECRETS and SECRETS['DEBUG']:
    DEBUG = True
    sentry_env = 'dev'
else:
    DEBUG = False
    ALLOWED_HOSTS = ['boran.quietapple.org']
    sentry_env = 'prod'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

if 'SENTRY_DSN' in SECRETS:
    sentry_sdk.init(
        dsn=SECRETS['SENTRY_DSN'],
        environment=sentry_env,
        integrations=[DjangoIntegration()],
        traces_sample_rate=SECRETS.get('SENTRY_SAMPLE_RATE', 0),
    )

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'import_export',
    'massadmin',
    'phonenumber_field',
    'phonebank',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'boran.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'boran.wsgi.application'

if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'data/db.sqlite3',
        },
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': SECRETS['DATABASE_NAME'],
            'USER': SECRETS['DATABASE_USER'],
            'PASSWORD': SECRETS['DATABASE_PASSWORD'],
            'HOST': 'localhost',
        },
    }

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = False
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
USE_TZ = True

STATIC_ROOT = BASE_DIR / 'data/static'
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

LOGIN_URL = '/admin/login/'
LOGOUT_URL = '/admin/logout/'

FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

IMPORT_EXPORT_SKIP_ADMIN_LOG = True
PHONENUMBER_DEFAULT_REGION = 'US'
