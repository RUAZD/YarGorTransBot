import datetime as dt
from typing import Optional, Union

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from firebase_admin import db

from API import get_station_by_name, Station, get_time_by_st_id, Schedules
from API.dtpax import get_station_by_id
from bot.utils.my_markup_builders import Markup

router = Router()


class StationsCbF(CallbackData, prefix='stations'):
    action: str
    station_name: Optional[str] = None
    station_id: Optional[int] = None
    back: Optional[str] = None


class StationsStates(StatesGroup):
    input_name = State()


@router.callback_query(F.data == 'stations')
async def stations_invitation_handler(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(StationsStates.input_name)
    await state.update_data(query=query)

    text = '🚏 <b><u>Введите название остановки</u></b>'
    markup = Markup()
    markup.btr('<<< 📋 Вернуться в главное меню', 'main_menu')

    await query.message.edit_text(text=text, reply_markup=markup.as_markup())
    await query.answer('Ожидается ввод названия остановки 🚏')


@router.message(F.text.regexp(r'[А-Яа-яЁё., ()0-9-]+'))
@router.message(StationsStates.input_name)
@router.callback_query(StationsCbF.filter(F.action == 'back'))
async def input_station_name_handler(
        event: Union[Message, CallbackQuery], state: FSMContext, callback_data: StationsCbF = None) -> None:
    std = await state.get_data()
    if isinstance(event, Message):
        name = event.text
        if name is None:
            await event.reply('❌ Ваш ввод не является названием остановки 🚏')
            return None
        await state.update_data(name=name)
        station_search_result: list[Station] = await get_station_by_name(name)
        await state.update_data(station_search_result=station_search_result)
    else:
        station_search_result = std.get('station_search_result')
        if std.get('station_search_result') is None:
            name = std.get('name', callback_data.station_name)
            station_search_result: list[Station] = await get_station_by_name(name)
            await state.update_data(station_search_result=station_search_result)
    station_names = [station.name for station in station_search_result[:20]]

    text = '🚏 Выберите остановку'
    markup = Markup()
    uniq = list()
    for i, station in enumerate(station_search_result[:20]):
        c = station_names.count(station.name)
        if station.name not in uniq:
            uniq = [station.name, 0]
        uniq[1] += 1
        markup.btn(
            f'{f"[{uniq[1]}] " if c > 1 else ""} {station.name}',
            StationsCbF(
                action='get',
                station_name=f'{f"[{uniq[1]}] " if c > 1 else ""} ',
                station_id=station.station_id
            )
        )
    markup.packs(1)
    markup.btr('<< 🔁 Ввести другое название', 'stations')

    if isinstance(event, Message):
        query: CallbackQuery = (await state.get_data()).get('query')
        if query:
            await query.message.delete()
            await state.update_data(query=None)
        await state.update_data(message=event)
        await event.answer(text=text, reply_markup=markup.as_markup())
    else:
        await event.message.edit_text(text=text, reply_markup=markup.as_markup())


@router.callback_query(StationsCbF.filter(F.action == 'get'))
async def station_schedules_handler(query: CallbackQuery, uid: int, callback_data: StationsCbF,
                                    state: FSMContext) -> None:
    message: Message = (await state.get_data()).get('message')
    if message:
        await message.delete()
        await state.update_data(message=None)

    cbd = callback_data
    schedules: list[Schedules] = await get_time_by_st_id(cbd.station_id)
    name = await get_station_by_id(cbd.station_id)

    text = f'🚏 <b>{cbd.station_name}{name}</b>\n⌚️ Текущее время: <code>'
    text += dt.datetime.now().strftime("%H:%M:%S") + '</code>\n\n'
    for schedule in schedules:
        times = [f'<code>{time.strftime("%H.%M")}</code>' for time in schedule.arrival_times]
        text += f'<b>{schedule.name}</b> [{schedule.end_station}]:\n{", ".join(times)}\n\n'

    markup = Markup()
    markup.btr('🔁 Обновить расписание и время 🆕', query.data)
    favorites = db.reference('/users/').child(str(uid)).child('favourites').child('stations').get()
    favorites = favorites if favorites is not None else list()
    if cbd.station_id not in favorites:
        markup.btr('⭐️ Добавить в избранное ➕', StationsCbF(action='add_to_favorites', station_id=cbd.station_id))
    else:
        markup.btr('⭐️ Удалить из избранного ❌', StationsCbF(action='delete_from_favorites', station_id=cbd.station_id))
    markup.btr('< 🔁 Выбрать другую остановку', StationsCbF(action='back', station_name=cbd.station_name))
    if cbd.back != 'favorites':
        markup.btr('<<< 📋 Вернуться в главное меню', 'main_menu')
    else:
        markup.btr(f'<< ⭐️ Вернуться к избранному', 'favorites')

    if query.message.html_text != text.strip():
        await query.message.edit_text(text, reply_markup=markup.as_markup())
        await query.answer('Расписание обновлено 🆕')
    else:
        await query.answer('Пожалуйста, не торопитесь 🚷')


@router.callback_query(StationsCbF.filter(F.action == 'add_to_favorites'))
@router.callback_query(StationsCbF.filter(F.action == 'delete_from_favorites'))
async def favorite_station(query: CallbackQuery, uid: int, callback_data: StationsCbF, state) -> None:
    cbd = callback_data
    favorites = db.reference('/users/').child(str(uid)).child('favourites').child('stations').get()
    favorites = favorites if favorites is not None else list()
    if cbd.station_id not in favorites and cbd.action == 'add_to_favorites':
        favorites.append(cbd.station_id)
        db.reference('/users/').child(str(uid)).child('favourites').child('stations').set(favorites)
        await query.answer('Остановка добавлена в избранное ⭐️')
    elif cbd.station_id in favorites and cbd.action == 'delete_from_favorites':
        favorites.remove(cbd.station_id)
        db.reference('/users/').child(str(uid)).child('favourites').child('stations').set(favorites)
        await query.answer('Остановка удалена из избранного ❎')
    await station_schedules_handler(query, uid, cbd, state)
