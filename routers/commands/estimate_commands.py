import io
import time

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .states import EstimateStates
from buttons.keyboard_utils import *


router = Router(name=__name__)


@router.message(F.text == ButtonName.GEN_EST)
@router.message(Command('generate_estimate'))
async def generate_estimate_handle(message: Message, state: FSMContext):
    await state.update_data(estimate_items=[])
    text = 'Режим создания сметы активирован.\n<b>Вы можете добавить услугу</b>.'
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


@router.message(EstimateStates.estimate_adding_service)
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
            f'Добавлена услуга <b>{selected_service["name"]}</b> в количестве <b>{quantity}</b> '
            f'({selected_service['measure']}) = <b>{total_cost}</b> ₽.\n\n'
            f'Продолжите добавление или посчитайте смету.'
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


pdfmetrics.registerFont(TTFont('Roboto-Light', 'fonts/Roboto-Light.ttf'))
pdfmetrics.registerFont(TTFont('Roboto-ExtraBoldItalic', 'fonts/Roboto-ExtraBoldItalic.ttf'))


@router.message(EstimateStates.estimate_choosing_unit, F.text == ButtonNameEstimate.FINISH_EST)
@router.message(EstimateStates.estimate_waiting_service, F.text == ButtonNameEstimate.FINISH_EST)
async def finish_estimate_handle(message: Message, state: FSMContext):
    data = await state.get_data()
    items = data.get('estimate_items', [])
    if not items:
        await message.answer('Смета пуста. Добавьте услуги.')
        return
    total_sum = sum(item['total'] for item in items)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.5 * cm,
        leftMargin=0.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )
    styles = getSampleStyleSheet()
    company_title = ParagraphStyle(
        'CompanyTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=10,
        alignment=1,
        fontName='Roboto-ExtraBoldItalic',
        textColor=HexColor('#1e3a8a')
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        alignment=1,
        fontName='Roboto-Light',
        textColor=HexColor('#64748b')
    )
    date_style = ParagraphStyle(
        'Date',
        fontSize=10,
        spaceAfter=15,
        fontName='Roboto-Light',
        textColor=HexColor('#64748b'),
        alignment=2
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        fontName='Roboto-Light',
        fontSize=8.5,
        leftIndent=3,
        rightIndent=3,
        spaceAfter=1,
        alignment=0,
        leading=10
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        fontName='Roboto-ExtraBoldItalic',
        fontSize=9,
        leftIndent=3,
        rightIndent=3,
        spaceAfter=1,
        alignment=1,
        leading=11,
        textColor=colors.whitesmoke
    )
    total_style = ParagraphStyle(
        'TotalCell',
        fontName='Roboto-ExtraBoldItalic',
        fontSize=11,
        leftIndent=0,
        rightIndent=5,
        alignment=2,
        leading=13,
        textColor=HexColor('#1e40af')
    )
    story = []
    story.append(Paragraph('«ЮгСтройОтдел»', company_title))
    story.append(Paragraph('СМЕТА', subtitle_style))
    story.append(Spacer(1, 12))
    story.append(
        HRFlowable(width="100%", thickness=1, lineCap='round', color=HexColor('#e2e8f0'), spaceBefore=5, spaceAfter=15))
    table_data = []
    header_row = [
        Paragraph('№', table_header_style),
        Paragraph('Услуга', table_header_style),
        Paragraph('Кол-во', table_header_style),
        Paragraph('Ед. изм.', table_header_style),
        Paragraph('Цена / ед.', table_header_style),
        Paragraph('Сумма', table_header_style)
    ]
    table_data.append(header_row)
    for i, item in enumerate(items, 1):
        table_data.append([
            Paragraph(str(i), table_cell_style),
            Paragraph(item['name'], table_cell_style),
            Paragraph(f'{item["quantity"]:.2f}', table_cell_style),
            Paragraph(f'{item["measure"]}', table_cell_style),
            Paragraph(f'{item["price_per_unit"]:.2f} ₽', table_cell_style),
            Paragraph(f'{item["total"]:.2f} ₽', table_cell_style)
        ])
    table_data.append([
        Paragraph('', table_cell_style),
        Paragraph('', table_cell_style),
        Paragraph('', table_cell_style),
        Paragraph('', table_cell_style),
        Paragraph('ИТОГО:', total_style),
        Paragraph(f'{total_sum:.2f} ₽', total_style)
    ])
    table = Table(table_data, colWidths=[
        0.7 * cm,
        8.0 * cm,
        1.5 * cm,
        1.4 * cm,
        2.4 * cm,
        2.7 * cm
    ])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1e40af')),
        ('BACKGROUND', (4, -1), (5, -1), HexColor('#dbeafe')),
        ('ALIGN', (0, 1), (0, -2), 'CENTER'),
        ('ALIGN', (1, 1), (1, -2), 'LEFT'),
        ('ALIGN', (2, 1), (3, -2), 'RIGHT'),
        ('ALIGN', (4, -1), (5, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -2), 0.5, HexColor('#cbd5e1')),
        ('BOX', (0, 0), (-1, -2), 0.5, HexColor('#cbd5e1')),
        ('LINEBELOW', (0, -2), (-1, -2), 1, HexColor('#cbd5e1')),
        ('BOX', (4, -1), (5, -1), 0.8, HexColor('#1e40af')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOP_PADDING', (0, 0), (-1, -1), 4),
        ('BOTTOM_PADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [HexColor('#f8fafc'), HexColor('#ffffff')]),
        ('INNERGRID', (0, 0), (-1, -2), 0.25, HexColor('#e2e8f0')),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width='100%', thickness=1, lineCap='round', color=HexColor('#e2e8f0'), spaceBefore=10,
                            spaceAfter=10))
    date_text = f'Сформировано: {time.strftime("%d.%m.%Y %H:%M")}'
    story.append(Paragraph(date_text, date_style))
    doc.build(story)
    buffer.seek(0)
    dt = time.strftime('%d-%m-%Y_%Hh%Mmin', time.localtime())
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_DOCUMENT)
    await message.reply_document(
        document=BufferedInputFile(buffer.read(), filename=f'Смета_{dt}.pdf'),
        reply_markup=keyboard_by_start(),
    )
    await state.clear()
