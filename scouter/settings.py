# Django settings for scouter project.
import os
import posixpath
import sys
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
LOG_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, 'logs_dev'))

GOOGLE_SCOPE = ['https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/glass.timeline',
                'https://www.googleapis.com/auth/glass.location']
env = os.environ.get('ENV', 'local')
print env
# ENV = 'dev'
if env == 'production':
    ENV = 'production'
    DEBUG = False
    TEMPLATE_DEBUG = DEBUG
    # DATABASES = {
    #     'default': {
    #         'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
    #         'NAME': os.environ.get('DB_NAME'),                      # Or path to database file if using sqlite3.
    #         'USER': os.environ.get('DB_USER'),                      # Not used with sqlite3.
    #         'PASSWORD': os.environ.get('DB_PASSWORD'),                  # Not used with sqlite3.
    #         'HOST': os.environ.get('DB_HOST'),                      # Set to empty string for localhost. Not used with sqlite3.
    #         'PORT': os.environ.get('DB_PORT'),                      # Set to empty string for default. Not used with sqlite3.
    #     }
    # }
    GOOGLE_REDIRECT_URI = 'https://scouteronglass.com/oauth/google/redirect/'

else:
    ENV = 'dev'
    DEBUG = True
    TEMPLATE_DEBUG = DEBUG
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'scouter',                      # Or path to database file if using sqlite3.
            'USER': 'scouter',                      # Not used with sqlite3.
            'PASSWORD': 'password',                  # Not used with sqlite3.
            'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        }
    }
    GOOGLE_REDIRECT_URI = 'http://localhost:8000/oauth/google/redirect/'


ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    'scouter/static/',

)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'v+@7(495le9ik_b+tl+@ow==ryk8rid(fj%)+_ya%_*6=&amp;dq@2'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.request",
    'django.contrib.auth.context_processors.auth',
    # "allauth.account.context_processors.account",
    # "allauth.socialaccount.context_processors.socialaccount",
)


MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',

)


AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",

    # `allauth` specific authentication methods, such as login by e-mail
    # "allauth.account.auth_backends.AuthenticationBackend",
)

ROOT_URLCONF = 'scouter.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'scouter.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'website',
    # 'allauth',
    # 'allauth.account',
    # 'allauth.socialaccount',
    # 'allauth.socialaccount.providers.google',
    'south',
    'raven.contrib.django.raven_compat',
)


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
    'require_debug_false': {
    '()': 'django.utils.log.RequireDebugFalse'
    }
    },
    'formatters': {
    'verbose': {
    'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
    },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
    'mail_admins': {
    'level': 'ERROR',
    'filters': ['require_debug_false'],
    'class': 'django.utils.log.AdminEmailHandler'
    },
        'file_log': {                 # define and name a second handler
            'level': 'DEBUG',
            'class': 'logging.FileHandler',  # set the logging class to log to a file
            'formatter': 'verbose',         # define the formatter to associate
            'filename': os.path.join(PROJECT_ROOT, 'logs/output.log')  # log file
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
    'django.request': {
    'handlers': ['mail_admins'],
    'level': 'ERROR',
    'propagate': True,
    },
        'debugger': {
            'handlers': ['file_log', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'views': {               # define another logger
            'handlers': ['console'],  # associate a different handler
            'level': 'DEBUG',                 # specify the logging level
            'propagate': True,
        },
}
}

try:
    from scouter.production_settings import *
except Exception as e:
    print e
    pass
