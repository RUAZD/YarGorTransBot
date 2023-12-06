"""
Middleware for messages and callbacks, logging
"""

import asyncio
import concurrent.futures
import datetime as dt
import logging
import os
import traceback
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery
from aiogram.types import User as AiogramUser
from asynclog import AsyncLogDispatcher
from firebase_admin import db

_logger_ = logging.getLogger()
_logger_.setLevel(logging.INFO)
_handler_ = AsyncLogDispatcher(lambda msg: print(msg))
_handler_.setLevel(logging.INFO)
_logger_.addHandler(_handler_)


async def log(key: str, msg: Any, *, time: dt.datetime = None, user: AiogramUser = None) -> None:
    """
    My asynchronous logger

    :param key: Log level (INFO, ERROR, MESSAGE, CALLBACK_QUERY)
    :param msg: The message that will be displayed in the log
    :param time: The time of logging the action (optional)
    :param user: User Information (optional)
    """

    def sync_log():
        nonlocal msg, time

        if time is None:
            time = dt.datetime.now()

        user_info = ''
        if user:
            db.reference('/users/').child(str(user.id)).child('telegram_account').update(user.__dict__)
            username = f' @{user.username}' if user.username else ''
            user_info = f' {user.full_name}{username} ({user.id})'

        msg = str(msg).replace('\n', '\\n')
        txt = f'[{time.strftime("%Y/%m/%d %H:%M:%S:%f")}] [{key}]{user_info} {msg}'.strip()

        os.makedirs('logs', exist_ok=True)
        with open(os.path.join('logs', f'{time.strftime("%Y.%m.%d")}.txt'), 'a', encoding='UTF-8') as file:
            file.write(f'{txt}\n')
        print(txt)

    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, sync_log)


class MessageMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]], message: Message,
                       data: Dict[str, Any]) -> Any:
        time, result, user = dt.datetime.now(), None, message.from_user
        try:
            data.update(uid=user.id)
            result = await handler(message, data)
        except Exception as exception:
            print(traceback.format_exc())
        await log(f'Message {message.message_id}', message.text, time=time, user=user)
        return result


class CallbackMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]], query: CallbackQuery,
                       data: Dict[str, Any]) -> Any:
        time, result, user = dt.datetime.now(), None, query.from_user
        try:
            data.update(uid=user.id)
            result = await handler(query, data)
        except TelegramBadRequest as exception:
            if 'are exactly the same as a current' not in exception.message:
                print(traceback.format_exc())
        except Exception as exception:
            print(traceback.format_exc())
        await log(f'Button', f'{query.data} [{query.message.text}]', time=time, user=user)
        return result
