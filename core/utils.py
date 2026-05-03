# core/utils.py
import os
from pathlib import Path
from datetime import datetime

def read_sys(path: str) -> str | None:
    """Безопасное чтение файлов из /sys и других системных путей"""
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except (OSError, FileNotFoundError):
        return None


def get_size(bytes_val: int, suffix: str = "Б") -> str:
    """Конвертирует байты в удобный формат (КБ, МБ, ГБ и т.д.)"""
    factor = 1024
    for unit in ["", "К", "М", "Г", "Т", "П"]:
        if bytes_val < factor:
            return f"{bytes_val:.2f} {unit}{suffix}"
        bytes_val /= factor
    return f"{bytes_val:.2f} П{suffix}"


def get_timestamp() -> str:
    """Возвращает текущее время в формате ЧЧ:ММ:СС"""
    return datetime.now().strftime("%H:%M:%S")