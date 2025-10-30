import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 123456789  # Ganti dengan Telegram ID kamu (opsional)

# Gender options
GENDER_MALE = "Pria"
GENDER_FEMALE = "Wanita"

# Limits
MAX_BIO_LENGTH = 200
MIN_AGE = 18
MAX_AGE = 60