import subprocess
import os
import re


def get_cpu_detail_info() -> str:
    """Полный парсинг lscpu + системные параметры драйверов для вывода в терминал"""
    try:
        env = os.environ.copy()
        env["LC_ALL"] = "C"
        result = subprocess.run(["lscpu"], env=env, capture_output=True, text=True)
        output = result.stdout

        # Расширенный словарь перевода
        translation = {
            "architecture": "Архитектура",
            "cpu op-mode(s)": "Режимы работы",
            "address sizes": "Размеры адресов",
            "byte order": "Порядок байтов",
            "cpu(s)": "Всего логических ядер",
            "on-line cpu(s) list": "Список активных ядер",
            "vendor id": "ID Производителя",
            "model name": "Модель процессора",
            "cpu family": "Семейство процессора",
            "model": "Модель",
            "stepping": "Степпинг (ревизия)",
            "cpu mhz": "Текущая частота",
            "cpu max mhz": "Макс. частота",
            "cpu min mhz": "Мин. частота",
            "bogomips": "BogoMIPS",
            "virtualization": "Виртуализация",
            "hypervisor vendor": "Вендор гипервизора",
            "virtualization type": "Тип виртуализации",
            "l1d cache": "L1 Данные (кэш)",
            "l1i cache": "L1 Инструкции (кэш)",
            "l2 cache": "L2 Кэш",
            "l3 cache": "L3 Кэш",
            "numa node(s)": "Узлы NUMA"
        }

        # Функция для чтения системных параметров
        def read_sys(path):
            if os.path.exists(path):
                with open(path, 'r') as f: return f.read().strip()
            return None

        # Шапка
        info = [
            "\n[bold yellow]┌──────────────────────────────────────────────────────────┐[/bold yellow]",
            "[bold yellow]│           ПОДРОБНАЯ ИНФОРМАЦИЯ О ПРОЦЕССОРЕ              │[/bold yellow]",
            "[bold yellow]└──────────────────────────────────────────────────────────┘[/bold yellow]"
        ]

        # 1. Секция: Основное железо (из lscpu)
        lines = output.split('\n')
        for line in lines:
            if ':' in line:
                key, val = line.split(':', 1)
                key_clean = key.strip().lower()
                if key_clean in translation:
                    raw_val = val.strip()
                    # Красиво форматируем кэш и частоты
                    if "cache" in key_clean:
                        raw_val = raw_val.replace("KiB", "КБ").replace("MiB", "МБ").replace("instance", "шт.")
                    if "mhz" in key_clean:
                        try:
                            raw_val = f"{float(raw_val.replace(',', '.')) / 1000:.2f} ГГц"
                        except:
                            raw_val += " МГц"

                    info.append(f"[green] {translation[key_clean]:<30}:[/green] {raw_val}")

        # 2. Секция: Драйверы и управление питанием (из /sys)
        info.append("\n[bold cyan]► Параметры управления частотой (Драйверы):[/bold cyan]")

        driver = read_sys("/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver")
        gov = read_sys("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
        avail = read_sys("/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors")
        no_turbo = read_sys("/sys/devices/system/cpu/intel_pstate/no_turbo")

        # Исправлено: открывающий [green] закрывается [/green] или просто [/]
        info.append(f"[green]  Драйвер (scaling_driver)     :[/green] {driver or 'не найден'}")
        info.append(f"[green]  Режим (governor)            :[/green] {gov or 'не найден'}")

        if avail:
            # Здесь тоже была ошибка: [/cyan] вместо [/green]
            info.append(f"[green]  Доступные режимы            :[/green] {avail}")

        if no_turbo is not None:
            t_status = "[bold green]ВКЛЮЧЕН (0)[/bold green]" if no_turbo == "0" else "[bold red]ВЫКЛЮЧЕН (1)[/bold red]"
            info.append(f"[green]  Технология Turbo Boost      :[/green] {t_status}")

        # 3. Инструкции (Флаги)
        for line in lines:
            if line.lower().startswith("flags:"):
                info.append("\n[bold cyan]► Доступные инструкции (Флаги):[/bold cyan]")
                flags = line.split(':', 1)[1].strip().split()
                for i in range(0, len(flags), 6):  # По 6 в ряд
                    info.append("  " + " ".join(flags[i:i + 6]))

        info.append("\n[bold yellow]────────────────────────────────────────────────────────────[/bold yellow]\n")
        return "\n".join(info)

    except Exception as e:
        return f"[red] Ошибка модуля cpudetailinfo: {e}[/red]"