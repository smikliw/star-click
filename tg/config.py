import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    WEBAPP_URL = os.getenv('WEBAPP_URL')
    ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
    BOT_USERNAME = os.getenv('BOT_USERNAME', '@your_bot')