from aiogram.fsm.state import State, StatesGroup


class ComputeStates(StatesGroup):
    waiting_for_service = State()
    waiting_for_quantity = State()
    choosing_unit = State()


class EstimateStates(StatesGroup):
    estimate_choosing_unit = State()
    estimate_waiting_service = State()
    estimate_waiting_quantity = State()
    estimate_adding_service = State()
