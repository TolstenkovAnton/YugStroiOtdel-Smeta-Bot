from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from buttons.keyboard_utils import *


router = Router(name=__name__)


@router.message(F.text == ButtonName.BACK_TO_MAIN)
@router.message(Command('start'))
async def start_handle(message: Message):
    text = (f'Привет, <b>{message.from_user.full_name}</b>, '
            f'вы используете бот <b>«ЮгСтройОтдел»</b> Смета. Начнём работу вместе!')
    await message.answer(
        text=text,
        parse_mode='HTML',
        reply_markup=keyboard_by_start(),
    )


@router.message(F.text == ButtonName.HELP)
@router.message(Command('help'))
async def help_handle(message: Message):
    text = 'Я помогаю вести подсчёты услуг компании <b>«ЮгСтройОтдел»</b>.'
    text += ' Перейдите в раздел «К вычислениям» и выберите опцию'
    text += ' единичного подсчёта или создания сметы, чтобы приступить.'
    await message.answer(
        text=text,
        parse_mode='HTML',
        reply_markup=keyboard_by_start(),
    )
