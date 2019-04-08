from keys import *
import sys
"""
Django settings for reopt_api project.

Generated by 'django-admin startproject' using Django 1.8.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import django


URDB_NOTIFICATION_EMAIL_LIST = urdb_error_team_emails_test
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = secret_key_

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'reo',
    'tastypie',
    'proforma',
    'resilience_stats',
    'django_celery_results',
    'django_extensions'
    )

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'reopt_api.urls'

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
            ],
        },
    },
]


WSGI_APPLICATION = 'reopt_api.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases


if os.environ.get('BUILD_TYPE') == 'jenkins':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ.get('DB_USERNAME'),
            'USER': os.environ.get('DB_USERNAME'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOSTNAME'),
            'PORT': os.environ.get('DB_PORT'),
        }
    }
elif 'test' in sys.argv or os.environ.get('APP_ENV') == 'local':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'reopt',
            'USER': 'reopt',
            'PASSWORD': 'reopt',
            'HOST': 'localhost',
            'PORT': '',
        }
}
else:
    DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.postgresql_psycopg2',
             'HOST': 'reopt-dev-db1.nrel.gov',
             'NAME': 'reopt_development',
             'OPTIONS': {
                 'options': '-c search_path=reopt_api'
             },
             'USER': dev_user,
             'PASSWORD': dev_user_password,
         }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Results backend
CELERY_RESULT_BACKEND = 'django-db'

# celery task registration
CELERY_IMPORTS = (
    'reo.src.reopt',
    'reo.api',
    'reo.scenario',
    'reo.results',
)

#if 'test' in sys.argv:
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES_EXCEPTIONS = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
if os.environ.get('BUILD_TYPE') == 'jenkins':
    STATIC_URL = '/static/'
else:
    STATIC_URL = '/'

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reopt_api.dev_settings")
django.setup()
