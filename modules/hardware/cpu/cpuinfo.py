import subprocess
import os
import re


def get_cpu_info() -> str:
    """Собирает полную информацию о процессоре для вывода в TUI"""
    try:
        # 1. Сбор данных через lscpu с английской локалью для стабильного парсинга
        env = os.environ.copy()
        env["LC_ALL"] = "C"
        result = subprocess.run(["lscpu"], env=env, capture_output=True, text=True)
        output = result.stdout

        data = {}
        for line in output.split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                data[key.strip().lower()] = val.strip()

        info = []

        # Вспомогательные функции для форматирования
        def read_sys_file(path):
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return f.read().strip()
            return None

        def format_cache_info(value):
            if not value or value == 'N/A':
                return 'N/A'
            # Перевод единиц
            value = value.replace('KiB', 'КБ').replace('MiB', 'МБ').replace('GiB', 'ГБ')
            # Перевод (instances) -> (шт.)
            if 'instance' in value:
                count = re.search(r'(\d+)\s+instance', value)
                if count:
                    value = re.sub(r'\(\d+\s+instance[s]?\)', f'({count.group(1)} шт.)', value)
            return value

        def to_ghz(mhz_str):
            if not mhz_str or mhz_str == 'N/A': return 'N/A'
            try:
                val = float(mhz_str.replace(',', '.')) / 1000
                return f"{val:.2f} ГГц"
            except:
                return f"{mhz_str} МГц"

        # Словарь перевода говерноров
        gov_map = {
            "performance": "Производительный (performance)",
            "powersave": "Энергосберегающий (powersave)",
            "ondemand": "По требованию (ondemand)",
            "conservative": "Консервативный (conservative)",
            "schedutil": "Оптимизированный (schedutil)",
            "userspace": "Пользовательский (userspace)"
        }

        # --- ФОРМИРОВАНИЕ ВЫВОДА ---

        # 1. Основное
        info.append(f"Модель: {data.get('model name', 'Неизвестно')}")
        info.append(f"Архитектура: {data.get('architecture', 'Неизвестно')}")
        info.append(f"Режим работы CPU: {data.get('cpu op-mode(s)', 'Неизвестно')}")
        info.append(f"Вендор: {data.get('vendor id', 'Неизвестно')}\n")

        # 2. Драйверы и Режимы
        driver = read_sys_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver")
        info.append(f"Драйвер частоты: {driver or 'Драйвер не найден'}")

        current_gov = read_sys_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
        if current_gov:
            info.append(f"Текущий режим: {gov_map.get(current_gov, current_gov)}")

        avail_govs_raw = read_sys_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors")
        if avail_govs_raw:
            translated_list = [gov_map.get(g, g) for g in avail_govs_raw.split()]
            info.append(f"Доступные режимы: {', '.join(translated_list)}")

        # Режим Turbo (1=ВЫКЛ, 0=ВКЛ согласно no_turbo)
        no_turbo = read_sys_file("/sys/devices/system/cpu/intel_pstate/no_turbo")
        if no_turbo is not None:
            status = "Включен (0)" if no_turbo == "0" else "Выключен (1)"
            info.append(f"Режим Turbo: {status}")
        else:
            info.append("Режим Turbo: Недоступен")

        info.append("")  # Разделитель

        # 3. Физические параметры
        cores = data.get('core(s) per socket', '1')
        sockets = data.get('socket(s)', '1')
        threads = data.get('cpu(s)', 'Неизвестно')
        try:
            total_cores = int(cores) * int(sockets)
        except:
            total_cores = cores

        info.append(f"Физических ядер: {total_cores}")
        info.append(f"Логических потоков: {threads}")
        info.append(f"Минимальная частота: {to_ghz(data.get('cpu min mhz'))}")
        info.append(f"Максимальная частота: {to_ghz(data.get('cpu max mhz'))}\n")

        # 4. Виртуализация
        info.append(f"Виртуализация: {data.get('virtualization', 'Не найдена')}")
        info.append(f"Гипервизор: {data.get('hypervisor vendor', 'Отсутствует')}")
        info.append(f"Тип виртуализации: {data.get('virtualization type', 'Отсутствует')}\n")

        # 5. Кэши
        l1d = data.get('l1d cache', data.get('l1d', 'N/A'))
        l1i = data.get('l1i cache', data.get('l1i', 'N/A'))
        l2 = data.get('l2 cache', data.get('l2', 'N/A'))
        l3 = data.get('l3 cache', data.get('l3', 'N/A'))

        info.append(f"Кэш L1d: {format_cache_info(l1d)}")
        info.append(f"Кэш L1i: {format_cache_info(l1i)}")
        info.append(f"Кэш L2: {format_cache_info(l2)}")
        info.append(f"Кэш L3: {format_cache_info(l3)}")

        # 6. Технологии
        flags = data.get('flags', '')
        important = []
        if 'aes' in flags: important.append('AES (Шифрование)')
        if 'avx' in flags: important.append('AVX (Векторные вычисления)')
        if 'vmx' in flags or 'svm' in flags: important.append('Hardware VT (Аппаратная виртуализация)')

        if important:
            info.append("\n[ Ключевые технологии ]")
            for flag in important:
                info.append(f" ► {flag}")

        return "\n".join(info)

    except Exception as e:
        return f"Ошибка модуля cpuinfo: {e}"