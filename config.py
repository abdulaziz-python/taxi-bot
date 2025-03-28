import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")
DRIVERS_GROUP_ID = int(os.getenv("DRIVERS_GROUP_ID"))
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME")