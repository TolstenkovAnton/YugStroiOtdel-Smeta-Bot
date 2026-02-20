import io
import time

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramNetworkError
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, BufferedInputFile, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from .states import EstimateStates
from buttons.keyboard_utils import *


router = Router(name=__name__)


@router.message(F.text == ButtonName.GEN_EST)
@router.message(Command('generate_estimate'))
async def generate_estimate_handle(message: Message, state: FSMContext):
    await state.update_data(estimate_items=[])
    text = 'Режим создания сметы активирован.\n<b>Выберите раздел услуг или завершите</b>.'
    await message.answer(
        text=text,
        parse_mode='HTML',
        reply_markup=keyboard_for_estimate_start(),
    )
    await state.set_state(EstimateStates.estimate_choosing_unit)


@router.message(EstimateStates.estimate_choosing_unit, F.text == ButtonNameEstimate.ADD_EST)
async def add_service_to_estimate(message: Message, state: FSMContext):
    text = f'<b>Выберите нужный раздел:</b>\n'
    for num, unit in enumerate(all_services, 1):
        if num == 7: break
        text += f'{num}. {unit["title"]}\n\n'
    await message.answer(
        text=text.strip(),
        parse_mode='HTML',
        reply_markup=keyboard_for_unit_choose_estimate(),
    )
    await state.set_state(EstimateStates.estimate_waiting_service)


@router.message(EstimateStates.estimate_waiting_service, F.text.in_(ButtonNameUnit.get_all_values()))
async def estimate_unit_chosen(message: Message, state: FSMContext):
    id_unit = int(message.text)
    unit = list(all_services[id_unit - 1].values())
    title = unit[0]
    unit_services = unit[1:]
    await state.update_data(selected_unit=id_unit - 1)
    text = f'<b>Выберите услугу в {title}:</b>\n'
    for num, item in enumerate(unit_services, 1):
        text += f'{num}. {item["name"]}\n\n'
    await message.answer(
        text=text,
        parse_mode='HTML',
        reply_markup=keyboard_for_service_in_unit_estimate(id_unit - 1),
    )
    await state.set_state(EstimateStates.estimate_waiting_quantity)


@router.message(EstimateStates.estimate_waiting_quantity, F.text.isdigit())
async def estimate_service_selected(message: Message, state: FSMContext):
    service_num = int(message.text)
    data = await state.get_data()
    unit_index = data['selected_unit']
    unit = list(all_services[unit_index].values())[1:]
    if 1 <= service_num <= len(unit):
        selected_service = unit[service_num - 1]
        await state.update_data(
            estimate_selected_service=selected_service,
            estimate_unit_index=unit_index,
        )
        text = (
            f'Услуга: <b>{selected_service["name"]}</b>\n\n'
            f'Цена: <b>{selected_service.get("price", "Не указана")} руб. за {selected_service["measure"]}</b>\n\n'
            f'Введите количество:'
        )
        await message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(EstimateStates.estimate_adding_service)
    else:
        await message.answer('Неверный номер. Попробуйте снова.')


@router.message(EstimateStates.estimate_adding_service, F.text.isdigit())
async def estimate_quantity_handle(message: Message, state: FSMContext):
    try:
        quantity = float(message.text.replace(',', '.').replace(' ', ''))
        if quantity <= 0:
            raise ValueError('Количество > 0')
        data = await state.get_data()
        selected_service = data['estimate_selected_service']
        price_per_unit = selected_service.get('price', 0)
        total_cost = round(quantity * price_per_unit, 2)
        item = {
            'name': selected_service['name'],
            'measure': selected_service['measure'],
            'quantity': quantity,
            'price_per_unit': price_per_unit,
            'total': total_cost
        }
        items = data.get('estimate_items', [])
        items.append(item)
        await state.update_data(estimate_items=items)
        text = (
            f'Добавлено: <b>{selected_service["name"]}</b> × {quantity} = <b>{total_cost}</b> ₽\n\n'
            f'Вернитесь к добавлению или завершите.'
        )
        await message.answer(
            text=text,
            parse_mode='HTML',
            reply_markup=keyboard_for_estimate_start(),
        )
        await state.set_state(EstimateStates.estimate_choosing_unit)
    except ValueError:
        await message.answer('Введите корректное число > 0.')
    except Exception:
        await message.answer('Ошибка расчёта. Попробуйте снова.')


@router.message(EstimateStates.estimate_choosing_unit, F.text == ButtonNameEstimate.FINISH_EST)
@router.message(EstimateStates.estimate_waiting_service, F.text == ButtonNameEstimate.FINISH_EST)
async def finish_estimate_handle(message: Message, state: FSMContext):
    data = await state.get_data()
    items = data.get('estimate_items', [])
    if not items:
        await message.answer('Смета пуста. Добавьте услуги.')
        return
    total_sum = sum(item['total'] for item in items)
    file_content = io.StringIO()
    file_content.write('=== СМЕТА ===\n\n')
    file_content.write('Позиции:\n')
    file_content.write('-' * 60 + '\n')
    file_content.write(f"{'Услуга':<30} {'Кол-во':<8} {'Цена/ед':<10} {'Сумма':<10}\n")
    file_content.write('-' * 60 + '\n')
    for item in items:
        file_content.write(
            f"{item['name'][:27]:<30} {item['quantity']:<8.2f} {item['price_per_unit']:<10.0f} {item['total']:<10.2f}\n"
        )
    file_content.write('-' * 60 + '\n')
    file_content.write(f"ИТОГО: {total_sum:.2f} ₽\n")
    file_content.write('\nДата: ' + time.strftime('%d.%m.%Y %H:%M'))

    dt = time.strftime('%d-%m-%Y_%Hh%Mmin', time.localtime())
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_DOCUMENT)
    await message.reply_document(
        document=BufferedInputFile(
            file_content.getvalue().encode('utf-8'),
            filename=f'Смета_{dt}.txt'
        ),
        reply_markup=keyboard_by_start(),
    )
    await state.clear()
