
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = list(map(int, os.getenv("ADMINS", "").split(",")))
ALCHEMY_ENGINE = os.getenv("ALCHEMY_ENGINE")
REDIS_URL = os.getenv("REDIS_URL")
