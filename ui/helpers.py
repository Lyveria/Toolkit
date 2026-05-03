# ui/helpers.py
from rich.text import Text
from datetime import datetime

def format_header(title: str) -> str:
    """Форматирует заголовок"""
    return f"ТУЛКИТ v 1.0 | {title} | MondManu"


def create_journal_entry(message: str) -> str:
    """Создаёт запись в журнал с временем"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    return f"[{timestamp}] {message}\n"