from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from .meta import *
from services import all_services


def keyboard_by_start():
    btn_help = KeyboardButton(text=ButtonName.HELP)
    btn_compute = KeyboardButton(text=ButtonName.COMPUTE)
    btn_pricing = KeyboardButton(text=ButtonName.PRICING)
    markup = ReplyKeyboardMarkup(keyboard=[[btn_help], [btn_compute], [btn_pricing]])
    return markup


def keyboard_for_compute():
    btn_single_calc = KeyboardButton(text=ButtonName.SINGLE_CALC)
    btn_gen_est = KeyboardButton(text=ButtonName.GEN_EST)
    btn_back = KeyboardButton(text=ButtonName.BACK_TO_MAIN)
    markup = ReplyKeyboardMarkup(keyboard=[[btn_single_calc], [btn_gen_est], [btn_back]])
    return markup


def keyboard_for_unit_choose():
    btn_log = KeyboardButton(text=ButtonNameUnit.LOG)
    btn_des = KeyboardButton(text=ButtonNameUnit.DES)
    btn_prep = KeyboardButton(text=ButtonNameUnit.PREP)
    btn_dem_walls = KeyboardButton(text=ButtonNameUnit.DEM_WALLS)
    btn_dem_floor = KeyboardButton(text=ButtonNameUnit.DEM_FLOOR)
    btn_dem_roof = KeyboardButton(text=ButtonNameUnit.DEM_ROOF)
    btn_back_to_single_calc = KeyboardButton(text=ButtonName.COMPUTE)
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [btn_log, btn_des, btn_prep],
            [btn_dem_walls, btn_dem_floor, btn_dem_roof],
            [btn_back_to_single_calc]
        ]
    )
    return markup


def keyboard_for_service_in_unit(service_index: int):
    unit = list(all_services[service_index].values())
    unit = unit[1:]
    services_count = len(unit)
    if services_count <= 3:
        buttons_per_row = services_count
    elif services_count <= 6:
        buttons_per_row = 3
    elif services_count <= 10:
        buttons_per_row = 4
    elif services_count <= 15:
        buttons_per_row = 5
    else:
        buttons_per_row = 5
    keyboard = []
    for i in range(1, services_count + 1, buttons_per_row):
        row = []
        for j in range(buttons_per_row):
            if i + j > services_count:
                break
            row.append(KeyboardButton(text=str(i+j)))
        keyboard.append(row)
    keyboard.append([KeyboardButton(text=ButtonName.COMPUTE)])
    markup = ReplyKeyboardMarkup(
        keyboard=keyboard,
    )
    return markup
