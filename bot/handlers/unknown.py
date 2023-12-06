from aiogram import Router
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query()
async def _button_with_unknown_data_handler_(query: CallbackQuery) -> None:
    await query.answer('Эта кнопка ничего не делает 🌚')
