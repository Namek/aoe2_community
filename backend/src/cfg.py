import random
import string
import os

from dotenv import load_dotenv

load_dotenv(verbose=True)


RECORDINGS_PATH = os.getenv('RECORDINGS_PATH') or './database/files'
CORS_ALLOW_ORIGIN = os.getenv('CORS_ALLOW_ORIGIN')
STATICS_PATH = os.getenv('STATICS_PATH') or './static'
DB_TEMPLATE_PATH = os.getenv('DB_TEMPLATE_PATH') or './database/app.template.db'
DB_PATH = os.getenv('DB_PATH') or './database/app.db'
SESSION_SECRET = os.getenv('SESSION_SECRET') or ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(30))

ENABLE_DISCORD_BOT = bool(os.getenv('ENABLE_DISCORD_BOT') or True)
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_SERVER_ID = int(os.getenv('DISCORD_SERVER_ID') or 0)
DISCORD_SERVER_CHANNEL_NAMES = (os.getenv('DISCORD_SERVER_CHANNEL_NAMES') or '').split(',')
