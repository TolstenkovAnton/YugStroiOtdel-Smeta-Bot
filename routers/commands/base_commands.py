from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, MessageEntity

from buttons.keyboard_utils import *


router = Router(name=__name__)


@router.message(F.text == ButtonName.BACK_TO_MAIN)
@router.message(Command('start'))
async def start_handle(message: Message):
    text = f'Привет, {message.from_user.full_name}, вы используете бот «ЮгСтройОтдел» Смета. Начнём работу вместе!'
    name_bold = MessageEntity(
        type='bold',
        offset=len('Привет, '),
        length=len(message.from_user.full_name),
    )
    company_bold = MessageEntity(
        type='bold',
        offset=len('Привет, ')+len(message.from_user.full_name)+len(', вы используете бот '),
        length=14,
    )
    entities = [name_bold, company_bold]
    await message.answer(
        text=text,
        entities=entities,
        reply_markup=keyboard_by_start(),
    )


@router.message(F.text == ButtonName.HELP)
@router.message(Command('help'))
async def help_handle(message: Message):
    text = 'Я помогаю вести подсчёты услуг компании «ЮгСтройОтдел».'
    text += ' Перейдите в раздел «К вычислениям» и выберите опцию'
    text += ' единичного подсчёта или создания сметы, чтобы приступить.'
    company_bold = MessageEntity(
        type='bold',
        offset=len('Я помогаю вести подсчёты услуг компании '),
        length=14,
    )
    entities = [company_bold]
    await message.answer(text=text, entities=entities)
