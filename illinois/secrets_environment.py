# Paste in and as: illinois/secrets_environment.py

# ==================================================

# This file is responsible for loading secret configuration values
# (API keys, database URLs, OAuth credentials, etc.) into Django.
#
# We use the `django-environ` library to read these values from a `.env` file
# and convert them into operating system environment variables.
#
# This lets us:
#   • Keep secrets out of GitHub
#   • Use different settings for development vs production
#   • Use the same codebase everywhere
#
# Example: If .env contains
#   OPENAI_API_KEY=sk-abc123
#
# then this library makes it available in Django as:
#   os.environ["OPENAI_API_KEY"]
#
# which we can access safely in settings.py using:
#   os.getenv("OPENAI_API_KEY")
#
# ==================================================

import environ
from pathlib import Path

# Create an environment reader object
# This object knows how to load key=value pairs from .env
# and expose them as OS environment variables.
env = environ.Env()

# Find project root (folder that contains manage.py and .env)
# IMPORTANT: Even though BASE_DIR exists in base.py, it does not exist yet when secrets_environment.py runs.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root
environ.Env.read_env(BASE_DIR / ".env")