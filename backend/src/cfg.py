import random
import string
import os

from dotenv import load_dotenv

load_dotenv(verbose=True)

ENABLE_WEBSITE = os.getenv('ENABLE_WEBSITE') in ["True", "1"]
ENABLE_DISCORD_BOT = os.getenv('ENABLE_DISCORD_BOT', False) in ["True", "1"]

# website
WEBSITE_URL = os.getenv('WEBSITE_URL', '')
RECORDINGS_PATH = os.getenv('RECORDINGS_PATH', './database/files')
CORS_ALLOW_ORIGIN = os.getenv('CORS_ALLOW_ORIGIN')
STATICS_PATH = os.getenv('STATICS_PATH', '../frontend/dist')
DB_TEMPLATE_PATH = os.getenv('DB_TEMPLATE_PATH', './database/app.template.db')
DB_PATH = os.getenv('DB_PATH', './database/app.db')
SESSION_SECRET = os.getenv('SESSION_SECRET', ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(30)))

# discord bot
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_SERVER_ID = int(os.getenv('DISCORD_SERVER_ID', 0))
DISCORD_SERVER_CHANNEL_NAMES = (os.getenv('DISCORD_SERVER_CHANNEL_NAMES', '')).split(',')
DISCORD_BOT_BUGGING_PEOPLE = os.getenv('DISCORD_BOT_BUGGING_PEOPLE', False) in ["True", "1"]
