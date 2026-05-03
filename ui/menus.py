# ui/menus.py
from textual.containers import Vertical
from textual.widgets import Button
from textual.widgets import Static  # Добавим для совместимости


class TopBar(Vertical):
    def compose(self):
        yield Button("В главное меню", id="btn_home")
        yield Button("Выход", id="btn_exit")


class MainMenu(Vertical):
    BORDER_TITLE = "Главное Меню"

    def compose(self):
        yield Button("1. Работа с железом", id="btn_1")
        yield Button("2. Поиск Windows разделов", id="btn_2")
        yield Button("3. Дамп NTLM хешей (SAM)", id="btn_3")
        yield Button("4. Сетевой сканер", id="btn_4")
        yield Button("5. Очистить терминал", id="btn_5")


class HardwareMenu(Vertical):
    BORDER_TITLE = "Модуль: Железо"

    def compose(self):
        yield Button("1. Процессор", id="btn_hw_1")
        yield Button("2. Видеокарта", id="btn_hw_2")
        yield Button("3. Оперативная память", id="btn_hw_3")
        yield Button("4. Диски", id="btn_hw_4")
        yield Button("0. Назад", id="btn_hw_0")


class CpuMenu(Vertical):
    BORDER_TITLE = "Инструменты: Процессор"

    def compose(self):
        yield Button("1. Подробная информация", id="btn_cpu_1")
        yield Button("2. Режимы работы (Governor)", id="btn_cpu_2")
        yield Button("0. Назад", id="btn_cpu_0")
        yield Button("00. В главное меню", id="btn_cpu_00")


class GovMenu(Vertical):
    BORDER_TITLE = "Выбор режима CPU"

    def compose(self):
        yield Vertical(id="gov-buttons-container")
        yield Button("0. Назад", id="btn_gov_back")