from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramNetworkError
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, BufferedInputFile, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from .states import ComputeStates
from buttons.keyboard_utils import *


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
                reply_markup=keyboard_by_start(),
            )
        )
    except TelegramNetworkError:
        await message.answer('Попробуйте запросить прайс-лист ещё раз.')


@router.message(F.text == ButtonName.SINGLE_CALC)
@router.message(Command('single_calculation'))
async def single_calculation_handle(message: Message, state: FSMContext):
    text = f'<b>Выберите нужный раздел:</b>\n'
    for num, unit, in enumerate(all_services, 1):
        if num == 7:
            break
        text += f'{num}. {unit['title']}\n\n'
    text = text.strip()
    await message.answer(
        text=text,
        parse_mode='HTML',
        reply_markup=keyboard_for_unit_choose(),
    )
    await state.set_state(ComputeStates.choosing_unit)


@router.message(ComputeStates.choosing_unit, F.text.in_(ButtonNameUnit.get_all_values()))
async def computing_unit_handle(message: Message, state: FSMContext):
    id_unit = int(message.text)
    unit = list(all_services[id_unit - 1].values())
    title = unit[0]
    unit = unit[1:]
    await state.update_data(selected_unit=id_unit - 1, unit_title=title)
    text = f'<b>Выберите услугу раздела {title} для подсчёта:</b>\n'
    for num, item in enumerate(unit, 1):
        text += f'{num}. {item['name']}\n\n'
    await message.answer(
        text=text,
        parse_mode='HTML',
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
            f'Выбрана услуга: <b>{selected_service['name']}</b>\n\n'
            f'Цена: <b>{selected_service.get('price', 'Не указана')} руб. за {selected_service['measure']}</b>\n\n'
            f'Введите количество единиц:'
        )
        await message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(remove_keyboard=True),
        )
        await state.set_state(ComputeStates.waiting_for_quantity)
    else:
        await message.answer('Неверный номер услуги. Попробуйте еще раз.')


@router.message(ComputeStates.waiting_for_quantity)
async def quantity_handle(message: Message, state: FSMContext):
    try:
        quantity = float(message.text.replace(',', '.').replace(' ', ''))
        if quantity <= 0:
            raise ValueError('Количество должно быть больше 0')
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
            reply_markup=keyboard_by_start(),
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
