# v0.8
from aiogram import Router
from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.types import Message
from typing import Optional
from datetime import datetime, date, time, timedelta
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import re
from API import website_get_all_routes, website_get_route, Route, Schedule
from bot.utils.my_markup_builders import Markup
import difflib

router = Router()


class CbF(CallbackData, prefix='schedule'):
    action: str
    route_type: int
    route_id: Optional[int] = None


class ScheduleInputStates(StatesGroup):
    bus_number = State()


@router.callback_query(CbF.filter(F.action == 'hub'))
async def schedule_hub_handler(query: CallbackQuery, callback_data: CbF) -> None:
    vt = callback_data.route_type
    routes = website_get_all_routes(vt=vt)
    markup = Markup()
    [markup.btn(
        f'{route.num}',
        CbF(action='fast', route_type=vt, route_id=route.rid).pack()
    ) for route in routes]
    match vt:
        case 1:
            text = f'[!] <b>Расписание автобусов</b>'
            markup.packs(7)
        case 2:
            text = f'[!] <b>Расписание троллейбусов</b>'
            markup.packs(2)
        case 3:
            text = f'[!] <b>Расписание трамваев</b>'
            markup.packs(1)
        case _:
            text = f'[!] <b>Расписание транспорта</b>'
            markup.packs(4)
    markup.btr('<< Вернуться в главное меню 📋', 'main_menu')

    await query.message.edit_text(text=text, reply_markup=markup.as_markup())
    await query.answer('[!] Выберите номер маршрута')


@router.callback_query(CbF.filter(F.action == 'fast'))
async def fast_schedule_route_handler(query: CallbackQuery, callback_data: CbF) -> None:
    schedule = website_get_route(callback_data.route_id)
    text = f'<b>Расписание <a href="{schedule.url}">'
    match callback_data.route_type:
        case 1:
            text += 'автобуса'
        case 2:
            text += 'троллейбуса'
        case 3:
            text += 'трамвая'
        case _:
            text += 'маршрута'
    text += f' № {schedule.num}</a></b>\n<i>на ближайшие 2 часа</i>\n\n'
    if schedule.is_schedule:
        weekday: int = date.today().weekday()
        now: time = datetime.now().time()
        for k, v in schedule.schedule.items():
            if (
                    (k == 'Ежедневно') or (k == 'Суббота' and weekday == 5) or (k == 'Воскресенье' and weekday == 6) or
                    (k == 'Рабочие дни' and 0 <= weekday < 5) or (k == 'Выходные дни' and weekday > 4)
            ):
                text += f'<b>{k}</b>\n\n'
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
                    text += '\n\n'

    markup = Markup()
    markup.btr('Full', CbF(action='full', route_type=callback_data.route_type))
    markup.btr('Вернуться', CbF(action='main_menu', route_type=callback_data.route_type))
    if isinstance(query, CallbackQuery):
        if query.message.reply_to_message:
            await query.message.reply_to_message.delete()
        await query.message.edit_text(text=text, reply_markup=markup.as_markup())
    else:
        await query.answer(text=text, reply_markup=markup.as_markup())

    # #################################
    # for k, v in schedule.schedule.items():
    #         text += f'<b>{k}</b>\n\n'
    #         for station, _time_ in v.items():
    #             _time_: str
    #             times = [time(*[int(o) for o in item.strip().split(':')]) for item in _time_.strip('.').split(',')]
    #             # times = [item for item in times if now < item < maxx]
    #             next1 = None
    #             for t in times:
    #                 if t > NOW:
    #                     next1 = t
    #                     break
    #             text += f'{station}\n<code>'
    #             is_n = True
    #             c = 0
    #             ind = next1
    #             for t in times:
    #                 if (datetime.now() - timedelta(minutes=30)).time() < t and c <= 8:
    #                     if t > NOW and is_n:
    #                         text += '</code>\n&gt;&gt;&gt; <b>'
    #                     text += f'{t.strftime("%H.%M")}, '
    #                     if t > NOW and is_n:
    #                         is_n = False
    #                         text += '</b>\n<code>'
    #                 if t > NOW:
    #                     c += 1
    #             text = text.rstrip(', ')
    #             text += '</code>\n\n'
    #             # sched = (" " + _time_).replace(":", ".").replace(" 0", "  ").strip(" .")
    #             # text += f'{station}\n<code>{", ".join([t.strftime("%H.%M") for t in times])}</code>\n\n'
    #     else:
    #         print(k)

    # markup = Markup()
    # markup.btr('Вернуться', CbF(action='hub', route_type=callback_data.route_type))
    # if query.message.reply_to_message:
    #     await query.message.reply_to_message.delete()
    # await query.message.edit_text(text, reply_markup=markup.as_markup())


@router.callback_query(CbF.filter())
async def NAME_NAME_NAME(query: CallbackQuery, callback_data: CbF) -> None:
    sch: Schedule = website_get_route(callback_data.route_id)

    text = f'<b>#Расписание <a href="{sch.url}">автобуса № {sch.num}</a></b>\n\n'
    for k, v in sch.schedule.items():
        text += f'<b>{k}</b>\n\n'
        for k2, v2 in v.items():
            sched = (" " + v2).replace(":", ".").replace(" 0", "  ").strip(" .")
            text += f'{k2}\n<code>{sched}</code>\n\n'

    markup = Markup()
    markup.btr('Вернуться', 'schedule')
    if query.message.reply_to_message:
        await query.message.reply_to_message.delete()
    await query.message.edit_text(text, reply_markup=markup.as_markup())


