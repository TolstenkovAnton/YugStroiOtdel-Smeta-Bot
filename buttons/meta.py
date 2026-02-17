class ButtonName:
    HELP = 'О боте'
    COMPUTE = 'К вычислениям'
    PRICING = 'Посмотреть прайс-лист'
    SINGLE_CALC = 'Единичный подсчёт'
    GEN_EST = 'Создать смету'
    BACK_TO_MAIN = 'Главное меню'


class ButtonNameUnit:
    LOG = '1'
    DES = '2'
    PREP = '3'
    DEM_WALLS = '4'
    DEM_FLOOR = '5'
    DEM_ROOF = '6'

    @classmethod
    def get_all_values(cls):
        return [
            getattr(cls, attr) for attr in dir(cls)
            if not attr.startswith('_') and not callable(getattr(cls, attr)) and attr.isupper()
        ]
