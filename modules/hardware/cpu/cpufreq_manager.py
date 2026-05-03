import os
import subprocess

SERVICE_NAME = "cpu-performance-toolkit"
SERVICE_PATH = f"/etc/systemd/system/{SERVICE_NAME}.service"


def set_governor(gov_name: str) -> tuple[bool, str]:
    """
    Устанавливает governor для всех ядер.
    Возвращает (успех, сообщение)
    """
    base_path = "/sys/devices/system/cpu"
    if not os.path.exists(f"{base_path}/cpu0/cpufreq"):
        return False, "CPU frequency scaling не поддерживается"

    cpus = [d for d in os.listdir(base_path) if d.startswith("cpu") and d[3:].isdigit()]
    success_count = 0

    for cpu in cpus:
        gov_path = f"{base_path}/{cpu}/cpufreq/scaling_governor"
        if os.path.exists(gov_path):
            try:
                with open(gov_path, 'w') as f:
                    f.write(gov_name)
                success_count += 1
            except Exception as e:
                return False, f"Ошибка на {cpu}: {e}"

    if success_count == 0:
        return False, "Не удалось установить governor ни на одном ядре"
    return True, f"Governor '{gov_name}' установлен на {success_count} ядрах"


def toggle_turbo_boost() -> tuple[bool, str, int]:
    """
    Инвертирует Turbo Boost.
    Возвращает (успех, сообщение, новое_значение: 0/1/None)
    """
    path = "/sys/devices/system/cpu/intel_pstate/no_turbo"
    if not os.path.exists(path):
        return False, "Turbo Boost не поддерживается (нет intel_pstate)", None

    try:
        with open(path, 'r') as f:
            current = f.read().strip()
        new_val = "1" if current == "0" else "0"
        with open(path, 'w') as f:
            f.write(new_val)
        status = "выключен" if new_val == "1" else "включен"
        return True, f"Turbo Boost {status}", int(new_val)
    except Exception as e:
        return False, f"Ошибка: {e}", None


def get_current_governor() -> str | None:
    """Возвращает текущий governor"""
    path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return f.read().strip()
        except:
            return None
    return None


def get_current_turbo_state() -> int | None:
    """
    Возвращает текущее состояние Turbo Boost:
    0 = Turbo ВКЛЮЧЁН
    1 = Turbo ВЫКЛЮЧЁН
    None = не поддерживается
    """
    path = "/sys/devices/system/cpu/intel_pstate/no_turbo"
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return int(f.read().strip())
        except:
            return None
    return None


def save_current_settings_to_systemd() -> tuple[bool, str]:
    """
    Сохраняет текущие настройки CPU (governor + turbo) в systemd сервис.
    Сервис будет применяться при каждой загрузке системы.
    """
    # Получаем текущие настройки
    gov = get_current_governor()
    turbo = get_current_turbo_state()

    if not gov:
        return False, "Не удалось определить текущий governor"

    # Создаём содержимое сервиса
    service_content = f"""[Unit]
Description=CPU Performance Toolkit - Apply CPU settings
After=multi-user.target
Before=cpufrequtils.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c 'echo {gov} | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'
"""

    # Добавляем команду для Turbo Boost, если поддерживается
    if turbo is not None:
        service_content += f"""ExecStart=/bin/bash -c 'echo {turbo} > /sys/devices/system/cpu/intel_pstate/no_turbo'
"""

    service_content += """
[Install]
WantedBy=multi-user.target
"""

    # Проверяем, есть ли права на запись в /etc/systemd/system
    if not os.access("/etc/systemd/system", os.W_OK):
        try:
            # Пробуем через sudo
            subprocess.run(["sudo", "touch", SERVICE_PATH], check=True, capture_output=True)
        except:
            return False, "Нет прав для создания сервиса. Запустите программу с sudo"

    try:
        # Записываем файл сервиса
        with open(SERVICE_PATH, 'w') as f:
            f.write(service_content)

        # Перезагружаем systemd и включаем сервис
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True, capture_output=True)
        subprocess.run(["sudo", "systemctl", "enable", SERVICE_NAME], check=True, capture_output=True)

        turbo_status = f", Turbo Boost {'ВЫКЛЮЧЁН' if turbo == 1 else 'ВКЛЮЧЁН'}" if turbo is not None else ""
        return True, f"Настройки сохранены: governor = {gov}{turbo_status}"

    except Exception as e:
        return False, f"Ошибка при создании сервиса: {e}"


def remove_saved_settings() -> tuple[bool, str]:
    """
    Удаляет созданный ранее systemd сервис.
    """
    if not os.path.exists(SERVICE_PATH):
        return False, "Сохранённые настройки не найдены"

    try:
        # Останавливаем и отключаем сервис
        subprocess.run(["sudo", "systemctl", "stop", SERVICE_NAME], check=False, capture_output=True)
        subprocess.run(["sudo", "systemctl", "disable", SERVICE_NAME], check=True, capture_output=True)

        # Удаляем файл сервиса
        subprocess.run(["sudo", "rm", SERVICE_PATH], check=True, capture_output=True)

        # Перезагружаем systemd
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True, capture_output=True)

        return True, "Сохранённые настройки удалены"

    except Exception as e:
        return False, f"Ошибка при удалении сервиса: {e}"


def is_saved_settings_exist() -> bool:
    """Проверяет, существует ли сохранённый сервис"""
    return os.path.exists(SERVICE_PATH)


def get_saved_settings_info() -> dict | None:
    """
    Возвращает информацию о сохранённых настройках.
    """
    if not os.path.exists(SERVICE_PATH):
        return None

    try:
        with open(SERVICE_PATH, 'r') as f:
            content = f.read()

        # Парсим governor из содержимого
        gov = None
        turbo = None

        for line in content.split('\n'):
            if 'scaling_governor' in line:
                # Ищем governor в команде echo
                import re
                match = re.search(r"echo (\w+) \| tee", line)
                if match:
                    gov = match.group(1)
            if 'no_turbo' in line:
                match = re.search(r"echo (\d+) >", line)
                if match:
                    turbo = "ВКЛ" if match.group(1) == "0" else "ВЫКЛ"

        return {
            "governor": gov,
            "turbo": turbo,
            "service_path": SERVICE_PATH
        }
    except:
        return {"service_path": SERVICE_PATH}