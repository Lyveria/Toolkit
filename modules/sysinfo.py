import platform
import psutil
import subprocess
import os


def get_size(bytes_val, suffix="Б"):
    """Перевод байтов в КБ/МБ/ГБ"""
    factor = 1024
    for unit in ["", "К", "М", "Г", "Т", "П"]:
        if bytes_val < factor:
            return f"{bytes_val:.2f} {unit}{suffix}"
        bytes_val /= factor


def get_system_info() -> str:
    """Собирает всю информацию о железе"""
    info = []

    # Заголовок убрали, он теперь будет рисоваться на рамке!

    # 1. ОС и Ядро
    uname = platform.uname()
    info.append(f"ОС: {uname.system}")
    info.append(f"Ядро: {uname.release}")

    # 2. Версия BIOS
    bios_version = "Неизвестно"
    if uname.system == "Linux":
        try:
            with open('/sys/class/dmi/id/bios_version', 'r') as f:
                bios_version = f.read().strip()
        except Exception:
            try:
                bios_version = subprocess.check_output(
                    "dmidecode -s bios-version",
                    shell=True,
                    stderr=subprocess.DEVNULL
                ).decode().strip()
            except Exception:
                pass

    info.append(f"BIOS: {bios_version}")

    # 3. Процессор
    cpu_model = platform.processor()
    if not cpu_model and uname.system == "Linux":
        try:
            command = "cat /proc/cpuinfo | grep 'model name' | uniq"
            cpu_model = subprocess.check_output(command, shell=True).decode().strip().split(":")[1].strip()
        except Exception:
            cpu_model = "Неизвестный ЦП"

    info.append(f"\nПроцессор: {cpu_model}")
    info.append(f"Ядра: {psutil.cpu_count(logical=False)} Физ. / {psutil.cpu_count(logical=True)} Лог.")

    # 4. Оперативная память
    svmem = psutil.virtual_memory()
    info.append(f"ОЗУ: {get_size(svmem.used)} / {get_size(svmem.total)} ({svmem.percent}%)")

    # 5. Видеокарта
    if uname.system == "Linux":
        try:
            gpu_info = subprocess.check_output("lspci | grep -i vga", shell=True).decode().strip()
            gpu_name = gpu_info.split(":")[-1].strip()
            info.append(f"Видеокарта: {gpu_name}")
        except Exception:
            info.append("Видеокарта: lspci не найден")

    return "\n".join(info)


if __name__ == "__main__":
    print(get_system_info())