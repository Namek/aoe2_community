import random
import string
import os

from dotenv import load_dotenv

load_dotenv(verbose=True)

ENABLE_WEBSITE = os.getenv('ENABLE_WEBSITE') in ["True", "1"]
WEBSITE_URL = os.getenv('WEBSITE_URL', '')
RECORDINGS_PATH = os.getenv('RECORDINGS_PATH', './database/files')
CAN_FAIL_ON_RECORDING_PARSE = os.getenv('CAN_FAIL_ON_RECORDING_PARSE', '1') == '1'
CORS_ALLOW_ORIGIN = os.getenv('CORS_ALLOW_ORIGIN')
STATICS_PATH = os.getenv('STATICS_PATH', '../frontend/dist')
DB_TEMPLATE_PATH = os.getenv('DB_TEMPLATE_PATH', './database/app.template.db')
DB_PATH = os.getenv('DB_PATH', './database/app.db')
SESSION_SECRET = os.getenv('SESSION_SECRET', ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(30)))
