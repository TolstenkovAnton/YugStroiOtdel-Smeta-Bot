from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramNetworkError


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
    text += ' Перейдите в раздел <b>«К вычислениям»</b> и выберите опцию'
    text += ' единичного подсчёта или создания сметы, чтобы приступить.'
    await message.answer(
        text=text,
        parse_mode='HTML',
        reply_markup=keyboard_by_start(),
    )


@router.message(F.text == ButtonName.PRICING)
@router.message(Command('pricing'))
async def pricing_handle(message: Message):
    try:
        await message.bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.UPLOAD_DOCUMENT,
        )
        await message.reply_document(
            document=FSInputFile(
                path='pricing_2026-02-13.pdf',
                filename='actual_pricing.pdf',
            ),
            reply_markup=keyboard_by_start(),
        )
    except TelegramNetworkError:
        await message.answer('Попробуйте запросить прайс-лист ещё раз.')


@router.message(F.text == ButtonName.COMPUTE)
@router.message(Command('compute_unit'))
async def compute_handle(message: Message):
    text = 'Выберите опцию единичного подсчёта или создания сметы.'
    await message.answer(
        text=text,
        reply_markup=keyboard_for_compute(),
    )
