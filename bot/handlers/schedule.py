import re
from datetime import datetime, date, time
from typing import Optional

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from firebase_admin import db

from API import website_get_all_routes, website_get_route
from bot.utils.my_markup_builders import Markup

router = Router()
# Виды транспорта для стартового меню
tr_tp_ej = {1: '🚌', 2: '🚎', 3: '🚃'}
tr_tp_st_nm = {1: 'автобусов', 2: 'троллейбусов', 3: 'трамваев'}
tr_tp_ft_nm = {1: 'автобуса', 2: 'троллейбуса', 3: 'трамвая'}
tr_tp_if_nm = {1: 'АВТОБУСЕ', 2: 'ТРОЛЛЕЙБУСЕ', 3: 'ТРАМВАЕ'}
tr_tp_sz = {1: 7, 2: 2, 3: 1}


class ScheduleCbF(CallbackData, prefix='schedule'):
    act: str  # action
    rt: Optional[int] = None  # route_type
    rid: Optional[int] = None  # route_id
    back: Optional[str] = None


class ScheduleStates(StatesGroup):
    route = State()


@router.callback_query(ScheduleCbF.filter(F.act == 'start'))
@router.callback_query(ScheduleCbF.filter(F.act == 'back_to_start'))
async def _schedule_start_handler_(query: CallbackQuery, callback_data: ScheduleCbF) -> None:
    cbd = callback_data
    ej, nm = tr_tp_ej.get(cbd.rt, "🚐"), tr_tp_st_nm.get(cbd.rt, 'транспорта')

    text = f'{ej} <b>Расписание {nm}</b>'
    markup = Markup()
    for route in website_get_all_routes(vt=cbd.rt):
        markup.btn(str(route.num), ScheduleCbF(act='fast', rt=cbd.rt, rid=route.rid))
    markup.packs(tr_tp_sz.get(cbd.rt, 4))
    markup.btr('<< Вернуться в главное меню 📋', 'main_menu')

    await query.message.edit_text(text=text, reply_markup=markup.as_markup())
    await query.answer('Выберите номер маршрута #️⃣')


@router.callback_query(ScheduleCbF.filter(F.act.in_(('fast', 'full'))))
@router.callback_query(ScheduleCbF.filter(F.act.in_(('back_to_fast', 'back_to_full'))))
async def fast_schedule_handler(query: CallbackQuery, callback_data: ScheduleCbF) -> None:
    cbd = callback_data
    schedule, is_fast = website_get_route(cbd.rid), cbd.act.endswith('fast')
    ej, nm = tr_tp_ej.get(cbd.rt, "🚐"), tr_tp_ft_nm.get(cbd.rt, 'маршрута')
    now: time = datetime.now().time()

    text = ('🗓' if is_fast else '📅') + f' <b>Расписание <a href="{schedule.url}">{nm} № {schedule.num}</a></b>'
    if is_fast:
        text += f'\n<b><u>на ближайшее время</u> ⌚️ {now.strftime("%H:%M:%S")}</b>\n'

    if schedule.is_schedule:
        if is_fast:
            weekday: int = date.today().weekday()
            for k, v in schedule.schedule.items():
                if (
                        (k == 'Ежедневно') or (k == 'Суббота' and weekday == 5) or (
                        k == 'Воскресенье' and weekday == 6) or
                        (k == 'Рабочие дни' and 0 <= weekday < 5) or (k == 'Выходные дни' and weekday > 4)
                ):
                    text += f'\n<b>{k}</b>\n\n'
                    for station, _time_ in v.items():
                        time_list = [time(*[int(o) for o in item.strip().split(':')])
                                     for item in _time_.strip('.').split(',')]
                        _next_ = None
                        index = 0
                        for __time__ in time_list:
                            if __time__ > now:
                                _next_ = __time__
                                index = time_list.index(_next_)
                                break
                        list_1, list_2 = time_list[:index][-4:], time_list[index + 1:][:8]
                        text += f'<b><u>{station}</u></b>\n'
                        if len(list_1) > 0:
                            gen = ', '.join([f'{__time__.strftime("%H.%M")}' for __time__ in list_1])
                            text += f'<pre>… {gen},</pre>'
                        text += f'<b>{_next_.strftime("%H.%M")}</b>'
                        if len(list_2) > 0:
                            gen = ', '.join([('\n' if i == 4 else '') + f'{__time__.strftime("%H.%M")}'
                                             for i, __time__ in enumerate(time_list[index + 1:][:8])])
                            text += f',<pre>{gen} …</pre>'
                        else:
                            text += '.'
                        text += '\n'
        else:
            for k, v in schedule.schedule.items():
                text += f'\n\n<b><i>{k}</i></b>\n\n'
                for station, _time_ in v.items():
                    text += f'<b><u>{station}</u></b>\n'
                    text += f'<pre>{_time_.replace(":", ".")}</pre>'

    markup = Markup()
    if is_fast:
        markup.btr('🔁 >> Обновить время <<', query.data)
        markup.btr('📅 Полное расписание >>', ScheduleCbF(act='full', rt=cbd.rt, rid=cbd.rid))
    else:
        markup.btr('<< Краткое расписание 🗓', ScheduleCbF(act='fast', rt=cbd.rt, rid=cbd.rid))
    favorites = db.reference('/users/').child(str(query.from_user.id)).child('favourites').child('schedule').get()
    favorites = favorites if favorites is not None else list()
    back = 'fast' if is_fast else 'full'
    if cbd.rid not in favorites:
        markup.btr('⭐️ Добавить в избранное ➕', ScheduleCbF(act='add_to_favorites', rid=cbd.rid, back=back))
    else:
        markup.btr('🌟 Удалить из избранного 🗑', ScheduleCbF(act='delete_from_favorites', rid=cbd.rid, back=back))
    markup.btr('🚏 О маршруте >>', ScheduleCbF(act='info', rt=cbd.rt, rid=cbd.rid, back=back))
    if cbd.back != 'favorites':
        markup.btr(f'<< 🔁 Выбрать другой маршрут {ej}', ScheduleCbF(act='back_to_start', rt=cbd.rt))
    else:
        markup.btr(f'<< ⭐️ Вернуться к избранному', 'favorites')

    await query.message.edit_text(text=text, reply_markup=markup.as_markup())
    if is_fast:
        await query.answer(f'Укороченное расписание {nm} № {schedule.num} 🗓')
    else:
        await query.answer(f'Полное расписание {nm} № {schedule.num} 📅')


@router.callback_query(ScheduleCbF.filter(F.act == 'add_to_favorites'))
@router.callback_query(ScheduleCbF.filter(F.act == 'delete_from_favorites'))
async def _favourites_schedule_handler_(query: CallbackQuery, callback_data: ScheduleCbF) -> None:
    cbd, uid = callback_data, query.from_user.id
    favorites = db.reference('/users/').child(str(uid)).child('favourites').child('schedule').get()
    favorites = favorites if favorites is not None else list()
    if cbd.rid not in favorites and cbd.act == 'add_to_favorites':
        favorites.append(cbd.rid)
        db.reference('/users/').child(str(uid)).child('favourites').child('schedule').set(favorites)
        await query.answer('Маршрут добавлен в избранное ⭐️')
    elif cbd.rid in favorites and cbd.act == 'delete_from_favorites':
        favorites.remove(cbd.rid)
        db.reference('/users/').child(str(uid)).child('favourites').child('schedule').set(favorites)
        await query.answer('Маршрут удалён из избранного 🗑')
    await fast_schedule_handler(query, ScheduleCbF(act=cbd.back, rt=cbd.rt, rid=cbd.rid))


@router.callback_query(ScheduleCbF.filter(F.act == 'info'))
async def _schedule_info_handler_(query: CallbackQuery, callback_data: ScheduleCbF) -> None:
    cbd = callback_data
    schedule = website_get_route(cbd.rid)
    ej, nm = tr_tp_ej.get(cbd.rt, "🚐"), tr_tp_if_nm.get(cbd.rt, 'МАРШРУТЕ')
    text = f'ℹ️ <b><u>ИНФОРМАЦИЯ О {nm} № {schedule.num}:</u></b>\n\n'
    if isinstance(schedule.info, dict):
        for direct, info in schedule.info.items():
            size, dist, _time_ = info.values()
            text += f'<b><i>{direct}</i></b>:\nОстановок: <b>{size}</b>\n'
            text += f'Протяжённость: <b>{dist}</b>\nВремя движения: <b>{_time_}</b>\n\n'
    if isinstance(schedule.stations, dict):
        text += f'🚏 <b><u>Список остановок:</u></b>\n'
        for direct, stations in schedule.stations.items():
            text += f'\n<b><i>{direct}:</i></b>\n\n'
            for station in stations:
                text += f'• <a href="{station["url"]}">{station["name"]}</a>\n'
    markup = Markup()
    markup.btr(f'<< 📅 Вернуться к расписанию', ScheduleCbF(act=f'back_to_{cbd.back}', rt=cbd.rt, rid=cbd.rid))
    await query.message.edit_text(text=text, reply_markup=markup.as_markup())


@router.message(lambda message: re.fullmatch(r'\d{1,3}[АБКПСТабкпстABKPSTabkpst]?', message.text))
async def command(message: Message) -> None:
    msg_txt = message.text.upper()
    for eng_char, rus_char in tuple(zip(tuple('ABKPST'), tuple('АБКПСТ'))):
        if eng_char in msg_txt:
            msg_txt = msg_txt.replace(eng_char, rus_char)
    # (difflib.SequenceMatcher(None, msg_txt, route.num).ratio() > 2 / 3)
    routes = [*website_get_all_routes(vt=1), *website_get_all_routes(vt=2), *website_get_all_routes(vt=3)]
    routes = [route for route in routes if msg_txt in route.num]
    lucky_routes = [1 if route.num == msg_txt else 0 for route in routes]
    markup = Markup()
    if len(routes) == 0:
        markup.btn('удалить', 'delete_me').btp('меню', 'hub')
        await message.answer('Маршрут не найден!', reply_markup=markup.as_markup())
    # elif sum(lucky_routes) == 1:
    #     route = routes[lucky_routes.index(1)]
    #     await fast_schedule_handler(message, ScheduleCbF(act='fast', rt=route.vt, rid=route.rid))
    else:
        [markup.btn(
            f'{route.num}' + ('', 'тб', 'тм')[route.vt - 1],
            ScheduleCbF(act='fast', rt=route.vt, rid=route.rid).pack()
        ) for route in routes]
        markup.packs(3)
        await message.answer(text='Найденные маршруты:', reply_markup=markup.as_markup())
