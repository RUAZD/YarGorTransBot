import os

import firebase_admin
from aiogram import Bot
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from firebase_admin import credentials

load_dotenv('variables.env')


def firebase_config():
    dir_path = os.path.dirname(__file__)
    dirname = os.path.split(dir_path)[-1]

    filename = None
    for name in os.listdir(dirname):
        if 'firebase' in name and name.endswith('.json'):
            filename = name
            break
    assert filename, FileNotFoundError

    path = os.path.join(dirname, filename)
    database_url = os.getenv('DATABASE_URL')

    cred = credentials.Certificate(path)
    firebase_admin.initialize_app(cred, dict(databaseURL=database_url))
    return None


firebase_config()

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
