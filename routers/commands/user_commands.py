import io
import time

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramNetworkError
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, BufferedInputFile, MessageEntity, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from buttons.keyboard_utils import *


class ComputeStates(StatesGroup):
    waiting_for_service = State()
    waiting_for_quantity = State()
    choosing_unit = State()


router = Router(name=__name__)


@router.message(F.text == ButtonName.COMPUTE)
@router.message(Command('compute_unit'))
async def compute_handle(message: Message):
    text = 'Выберите опцию единичного подсчёта или создания сметы.'
    await message.answer(
        text=text,
        reply_markup=keyboard_for_compute(),
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
            )
        )
    except TelegramNetworkError:
        await message.answer('Попробуйте запросить прайсинг ещё раз.')


@router.message(F.text == ButtonName.SINGLE_CALC)
@router.message(Command('single_calculation'))
async def single_calculation_handle(message: Message, state: FSMContext):
    text = f'Выберите нужный раздел:\n'
    for num, unit, in enumerate(all_services, 1):
        if num == 7:
            break
        text += f'{num}. {unit['title']}\n\n'
    text = text.strip()
    choose_bold = MessageEntity(
        type='bold',
        offset=0,
        length=len('Выберите нужный раздел:'),
    )
    entities = [choose_bold]
    await message.answer(
        text=text,
        entities=entities,
        reply_markup=keyboard_for_unit_choose(),
    )
    await state.set_state(ComputeStates.choosing_unit)


@router.message(F.text == ButtonName.GEN_EST)
@router.message(Command('generate_estimate'))
async def generate_estimate_handle(message: Message):
    file = io.StringIO()
    file.write('Смета...')
    dt = time.strftime('%d-%m-%Y_%Hh%Mmin', time.localtime())
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.UPLOAD_DOCUMENT,
    )
    await message.reply_document(
        document=BufferedInputFile(
            file=file.getvalue().encode('utf-8'),
            filename=f'Смета_{dt}.txt',
        )
    )


@router.message(ComputeStates.choosing_unit, F.text.in_(ButtonNameUnit.get_all_values()))
async def computing_unit_handle(message: Message, state: FSMContext):
    id_unit = int(message.text)
    unit = list(all_services[id_unit - 1].values())
    title = unit[0]
    unit = unit[1:]
    await state.update_data(selected_unit=id_unit - 1, unit_title=title)
    text = f'Выберите услугу раздела {title} для подсчёта:\n'
    services_bold = MessageEntity(
        type='bold',
        offset=0,
        length=len(f'Выберите услугу раздела {title} для подсчёта:'),
    )
    entities = [services_bold]
    for num, item in enumerate(unit, 1):
        text += f'{num}. {item['name']}\n\n'
    await message.answer(
        text=text,
        entities=entities,
        reply_markup=keyboard_for_service_in_unit(id_unit - 1)
    )
    await state.set_state(ComputeStates.waiting_for_service)


@router.message(ComputeStates.waiting_for_service, F.text.isdigit())
async def service_selected_handle(message: Message, state: FSMContext):
    service_num = int(message.text)
    data = await state.get_data()
    unit_index = data['selected_unit']
    unit = list(all_services[unit_index].values())[1:]
    if 1 <= service_num <= len(unit):
        selected_service = unit[service_num - 1]
        await state.update_data(
            selected_service=selected_service,
            unit_index=unit_index,
        )
        text = (
            f"Выбрана услуга: <b>{selected_service['name']}</b>\n\n"
            f"Цена: <b>{selected_service.get('price', 'Не указана')} руб. за {selected_service['measure']}</b>\n\n"
            f"Введите количество единиц:"
        )
        await message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(remove_keyboard=True),
        )
        await state.set_state(ComputeStates.waiting_for_quantity)
    else:
        await message.answer("Неверный номер услуги. Попробуйте еще раз.")


@router.message(ComputeStates.waiting_for_quantity)
async def quantity_handle(message: Message, state: FSMContext):
    try:
        quantity = float(message.text.replace(',', '.').replace(' ', ''))
        if quantity <= 0:
            raise ValueError("Количество должно быть больше 0")
        data = await state.get_data()
        selected_service = data['selected_service']
        price_per_unit = selected_service.get('price', 0)
        total_cost = quantity * price_per_unit
        text = (
            f'Стоимость услуги <b>{selected_service['name']}</b>'
            f' в количестве <b>{quantity}</b> ({selected_service['measure']}) = <b>{round(total_cost, 2)}</b> ₽.'
        )
        await message.answer(
            text=text,
            parse_mode='HTML',
            reply_markup=keyboard_by_start()
        )
        await state.clear()

    except ValueError:
        await message.answer(
            '<b>Ошибка!</b>\n'
            'Введите корректное число.',
            parse_mode="HTML",
        )
    except Exception:
        await message.answer(
            'Произошла ошибка при расчете. Попробуйте еще раз.',
        )
        await state.clear()
