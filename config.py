import os
from dotenv import load_dotenv

# Environment Loading Rules (from user_global):
# 1. If .env.production exists, load it EXCLUSIVELY.
# 2. Otherwise, load .env.docker THEN .env.docker.local.

env_prod = ".env.production"
env_docker = ".env.docker"
env_local = ".env.docker.local"

if os.path.exists(env_prod):
    load_dotenv(env_prod, override=True)
else:
    if os.path.exists(env_docker):
        load_dotenv(env_docker)
    if os.path.exists(env_local):
        load_dotenv(env_local, override=True)

# MongoDB Configuration
MONGO_URI = os.environ.get('MONGO_URI', "mongodb://mongo:27017/")
DATABASE_NAME = os.environ.get('DATABASE_NAME', "redirect_db")
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', "urls")

# Flask Configuration
# We use separate variables for internal and external ports if needed
FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.environ.get('FLASK_PORT', 5000))
FLASK_DEBUG = bool(int(os.environ.get('FLASK_DEBUG', 0)))
SECRET_KEY = os.environ.get('SECRET_KEY', 'lean-secret-key-2024')

# App Settings
MAX_REDIRECTS = 5
SHORT_CODE_LENGTH = 8

# Keywords that trigger a "Smart Stop" in the redirect resolver
# to avoid following links into login/auth pages.
RESOLVE_STOP_KEYWORDS = ['signin', 'login', 'auth', 'cas', 'oauth', 'accounts', 'openid']
