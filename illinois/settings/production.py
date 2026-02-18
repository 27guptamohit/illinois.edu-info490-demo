# Paste in and as: illinois/settings/production.py

# We will first import everything from base.py (our new settings.py file that we renamed to base.py)
from .base import *

DEBUG = False

# Replace it with your name:
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database for the development server
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        # put the DB in project-root/data/db.sqlite3
        'NAME': BASE_DIR / 'data' / 'db.sqlite3',
    }
}

# New addition
CORS_ALLOWED_ORIGINS = [
    "https://vega.github.io",
    "https://vega.github.io/editor",
]

# Or if you want to allow api data access to everyone, add
# CORS_ALLOW_ALL_ORIGINS = True
