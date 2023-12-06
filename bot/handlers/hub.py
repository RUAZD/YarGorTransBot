from typing import Union

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from API import website_get_route, get_time_by_st_id, get_station_by_name
from API.dtpax import get_station_by_id
from .schedule import ScheduleCbF
from .stations import StationsCbF
from ..utils.my_markup_builders import Markup
from firebase_admin import db

router = Router()


@router.message(CommandStart())
@router.callback_query(F.data == 'main_menu')
async def _main_menu_handler_(event: Union[Message, CallbackQuery]) -> None:
    text = f'😇 Здравствуйте, {event.from_user.first_name}!\n'
    text += 'Я могу помочь вам с Ярославским транспортом 🚌'

    markup = Markup()
    markup.btr('⭐️ Избранное ⭐️', 'favorites')
    markup.btp('Расписание автобусов 🚌', ScheduleCbF(act='start', rt=1))
    markup.btn('Троллейбусы 🚎', ScheduleCbF(act='start', rt=2))
    markup.btp('Трамваи 🚃', ScheduleCbF(act='start', rt=3))
    markup.btp('Остановки 🚏', 'stations')

    if isinstance(event, Message):
        await event.answer(text=text, reply_markup=markup.as_markup())
        await event.delete()
    elif isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, reply_markup=markup.as_markup())
        await event.answer('Выберите действие 📋')


@router.callback_query(F.data == 'favorites')
async def _message_deletion_handler_(query: CallbackQuery) -> None:
    obj = db.reference('/users/').child(str(query.from_user.id)).child('favourites')
    favorites_stations = obj.child('stations').get()
    favorites_stations = favorites_stations if favorites_stations is not None else list()
    favorites_schedule = obj.child('schedule').get()
    favorites_schedule = favorites_schedule if favorites_schedule is not None else list()

    markup = Markup()
    for rid in favorites_schedule:
        schedule = website_get_route(rid)
        markup.btn(schedule.num, ScheduleCbF(act='fast', rid=rid, back='favorites'))
    markup.packs(4)
    for sid in favorites_stations:
        name = await get_station_by_id(sid)
        markup.btr(name, StationsCbF(action='get', station_id=sid, back='favorites'))
    markup.btr('<< Вернуться в главное меню 📋', 'main_menu')

    await query.message.edit_text(text='⭐️ Ваши избранные маршруты и остановки', reply_markup=markup.as_markup())


@router.callback_query(F.data == 'delete_me')
async def _message_deletion_handler_(query: CallbackQuery) -> None:
    try:
        await query.message.delete()
    except TelegramBadRequest:
        await query.message.edit_text('<i>Сообщение удалено</i>')
    await query.answer('Сообщение скрыто ✔️')
