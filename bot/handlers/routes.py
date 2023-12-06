from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram import F
from datetime import datetime
from typing import Optional

from aiogram import F
from aiogram import Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot.utils.my_markup_builders import Markup
from aiogram import Router
from API import get_station_by_name, Station, get_routes, Route

router = Router()


class CbDRoutes(CallbackData, prefix='ROUTES'):
    type: str
class CbF(CallbackData, prefix='routes'):
    type: str
    action: Optional[str] = None
    station_name: Optional[str] = None
    station_id: Optional[int] = None
    alternative_station_id: Optional[int] = None

class States(StatesGroup):
    input_route = State()
# Station = namedtuple('Station', 'name, address, station_id')


@router.callback_query(CbDRoutes.filter())
async def list_of_stations_handler(query: CallbackQuery, callback_data: CbF) -> None:
    t = callback_data.type
    res = await get_routes()
    res = list(filter(lambda x: x.is_urban is True, res))
    res = list(filter(lambda x: x.vehicle_type_id == 4, res))
    res = list(sorted(res, key=lambda x: x.num))
    text = ', '.join([u.name for u in res])
    o = len(res)
    list_of_names = list()
    markup = Markup()
    for r in res:
        r: Route
        if r.name not in list_of_names:
            list_of_names.append(r.name)
            markup.btn(r.name, '1')
    o = len(list_of_names)
    markup.packs(4)
    markup.btn('back', 'main_menu')
    await query.message.edit_text(
        f'Напишите название маршрута в?{o}:\n' + text,
        reply_markup=markup.as_markup()
    )
    # await state.set_state(States.input_route)


