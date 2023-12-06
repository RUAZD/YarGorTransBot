from aiogram import Dispatcher
from aiohttp import ClientSession

from API import data
from bot.Middlewares import MessageMiddleware, CallbackMiddleware, log
from bot.handlers import routers
from .config import bot

dp = Dispatcher()
dp.message.middleware(MessageMiddleware())
dp.callback_query.middleware(CallbackMiddleware())
dp.include_routers(*routers)


async def main() -> None:
    session = ClientSession()
    data['session'] = session
    async with session:
        try:
            await log('Bot', 'Start!')
            await dp.start_polling(bot)
        finally:
            await bot.session.close()
            await log('Bot', 'Stop!')
