import os
import subprocess
import getpass
import platform
from datetime import datetime
from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Static, RichLog, Input, Button
from textual.containers import Horizontal, Vertical
from rich.text import Text

# Импорты модулей
from modules.sysinfo import get_system_info
from modules.hardware.cpu.cpuinfo import get_cpu_info
from modules.hardware.cpu.cpudetailinfo import get_cpu_detail_info
from config import GOV_TRANSLATIONS, APP_TITLE, MENU_TITLES
from modules.hardware.cpu.cpufreq_manager import (
    set_governor,
    toggle_turbo_boost,
    save_current_settings_to_systemd,
    remove_saved_settings,
    is_saved_settings_exist
)
class TopBar(Static):
    def compose(self) -> ComposeResult:
        yield Button("В главное меню", id="btn_home")
        yield Static("", id="topbar-title")
        yield Button("Выход", id="btn_exit")


class TerminalContainer(Vertical): BORDER_TITLE = "Терминал"


class RightTop(RichLog): BORDER_TITLE = "Системная Информация"


class RightMid(Static): BORDER_TITLE = "Активные Задачи"


class RightBottom(Static): BORDER_TITLE = "Системный Журнал"


class MainMenu(Vertical):
    BORDER_TITLE = "Главное Меню"

    def compose(self) -> ComposeResult:
        yield Button("1. Работа с железом", id="btn_1")
        yield Button("2. Поиск Windows разделов", id="btn_2")
        yield Button("3. Дамп NTLM хешей (SAM)", id="btn_3")
        yield Button("4. Сетевой сканер", id="btn_4")
        yield Button("5. Очистить терминал", id="btn_5")


class HardwareMenu(Vertical):
    BORDER_TITLE = "Модуль: Железо"

    def compose(self) -> ComposeResult:
        yield Button("1. Процессор", id="btn_hw_1")
        yield Button("2. Видеокарта", id="btn_hw_2")
        yield Button("3. Оперативная память", id="btn_hw_3")
        yield Button("4. Диски", id="btn_hw_4")
        yield Button("0. Назад", id="btn_hw_0")


class CpuMenu(Vertical):
    BORDER_TITLE = "Инструменты: Процессор"

    def compose(self) -> ComposeResult:
        yield Button("1. Подробная информация", id="btn_cpu_1")
        yield Button("2. Режимы работы (Governor)", id="btn_cpu_2")
        yield Button("0. Назад", id="btn_cpu_0")
        yield Button("00. В главное меню", id="btn_cpu_00")


class GovMenu(Vertical):
    BORDER_TITLE = "Выбор режима CPU"

    def compose(self) -> ComposeResult:
        yield Vertical(id="gov-buttons-container")
        yield Button("0. Назад", id="btn_gov_back")


class ToolkitApp(App):
    CSS = """
    TopBar { dock: top; height: 3; border: heavy cyan; layout: horizontal; }
    #btn_home, #btn_exit { width: auto; height: 1; border: none; background: transparent; padding: 0 1; }
    #btn_home { color: #00ff00; }
    #btn_exit { color: #ff0000; }
    #topbar-title { width: 1fr; content-align: center middle; color: white; text-style: bold; }

    #left-sidebar { width: 60%; height: 100%; }
    #right-sidebar { width: 40%; height: 100%; }
    #menu-container { height: 1fr; border: heavy green; padding: 1; overflow-y: auto; }

    MainMenu, HardwareMenu, CpuMenu, GovMenu { height: auto; }
    #hw-menu, #cpu-menu, #gov-menu { display: none; }

    Button { 
        width: 100%; height: auto; min-height: 1;
        background: #121212; color: #00ff00; border: none; 
        border-left: vkey green; margin-bottom: 1; 
    }
    Button:hover { background: #2a2a2a; color: white; border-left: vkey cyan; }

    TerminalContainer { height: 2fr; border: heavy blue; overflow-y: auto; }
    #terminal-log { height: 1fr; padding: 0 1; overflow-y: auto; }
    #terminal-input { dock: bottom; border: none; border-top: solid blue; background: $background; }

    RightTop { height: 1fr; border: heavy yellow; padding: 1; overflow-y: auto; }
    RightMid { height: 1fr; border: heavy magenta; padding: 1; overflow-y: auto; }
    RightBottom { height: 3fr; border: heavy red; padding: 1; overflow-y: auto; }
    """

    def compose(self) -> ComposeResult:
        yield TopBar()
        with Horizontal():
            with Vertical(id="left-sidebar"):
                with Vertical(id="menu-container"):
                    yield MainMenu(id="main-menu")
                    yield HardwareMenu(id="hw-menu")
                    yield CpuMenu(id="cpu-menu")
                    yield GovMenu(id="gov-menu")
                with TerminalContainer():
                    yield RichLog(id="terminal-log", markup=True)
                    yield Input(placeholder="Введите номер или команду...", id="terminal-input")
            with Vertical(id="right-sidebar"):
                yield RightTop()
                yield RightMid(Text("► Ожидание запуска задач..."))
                yield RightBottom(Text("[12:00] Интерфейс готов"))

    def update_header(self, text: str) -> None:
        self.query_one("#topbar-title", Static).update(APP_TITLE.format(mode=text))

    def read_sys(self, path):
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return f.read().strip()
            except:
                return None
        return None

    def reset_to_main_menu(self) -> None:
        self.current_menu = "main"
        for m in ["#cpu-menu", "#hw-menu", "#gov-menu"]:
            self.query_one(m).display = False
        self.query_one("#main-menu").display = True
        self.update_header("ГЛАВНОЕ МЕНЮ")

        rt = self.query_one(RightTop)
        rt.styles.height = "1fr"
        self.query_one(RightMid).styles.height = "1fr"
        self.query_one(RightBottom).styles.height = "3fr"
        rt.border_title = "Системная Информация"
        rt.clear()
        rt.write(get_system_info())

    def on_mount(self) -> None:
        self.current_menu = "main"
        self.update_header("ГЛАВНОЕ МЕНЮ")
        self.query_one(RightTop).write(get_system_info())
        self.query_one("#terminal-input").focus()

    async def show_gov_menu(self):
        self.current_menu = "gov"
        self.query_one("#cpu-menu").display = False
        self.query_one("#gov-menu").display = True
        self.update_header("МЕНЮ: ПРОЦЕССОР -> РЕЖИМЫ")

        container = self.query_one("#gov-buttons-container")
        await container.query("*").remove()

        avail_raw = self.read_sys("/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors")
        current_gov = self.read_sys("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
        no_turbo = self.read_sys("/sys/devices/system/cpu/intel_pstate/no_turbo")

        # Кнопки выбора governor
        if avail_raw:
            for g in avail_raw.split():
                is_active = (g == current_gov)
                name = GOV_TRANSLATIONS.get(g, g)
                btn = Button(f"{'●' if is_active else '○'} {name}", id=f"set_gov_{g}")
                if is_active:
                    btn.styles.color = "#00ff00"
                else:
                    btn.styles.color = "#ffff00"
                container.mount(btn)

        # Кнопка Turbo Boost
        if no_turbo is not None:
            t_status = "ВКЛ" if no_turbo == "0" else "ВЫКЛ"
            t_btn = Button(f"⚡ Turbo Boost: {t_status}", id="toggle_turbo")
            t_btn.styles.color = "#00ff00" if no_turbo == "0" else "#ff0000"
            container.mount(t_btn)

        # Разделитель (пустая кнопка-строка)
        container.mount(Button("─────────────────────────────", id="separator", disabled=True))

        # Кнопка сохранения текущих настроек
        save_btn = Button("💾 Сохранить текущие настройки как стандартные", id="btn_save_settings")
        save_btn.styles.color = "#00ffff"
        container.mount(save_btn)

        # Кнопка сброса (только если есть сохранённый сервис)
        if is_saved_settings_exist():
            reset_btn = Button("🗑️ Сбросить до стандартных настроек", id="btn_reset_settings")
            reset_btn.styles.color = "#ff8800"
            container.mount(reset_btn)

        # Кнопка назад
        container.mount(Button("0. Назад", id="btn_gov_back"))

    def execute_menu_action(self, command: str) -> None:
        log = self.query_one("#terminal-log", RichLog)
        rt = self.query_one(RightTop)

        if self.current_menu == "main" and command == "1":
            self.current_menu = "hw"
            self.query_one("#main-menu").display = False
            self.query_one("#hw-menu").display = True
            self.update_header("МЕНЮ: РАБОТА С ЖЕЛЕЗОМ")

        elif self.current_menu == "hw":
            if command == "0":
                self.reset_to_main_menu()
            elif command == "1":
                self.current_menu = "cpu"
                self.query_one("#hw-menu").display = False
                self.query_one("#cpu-menu").display = True
                self.update_header("МЕНЮ: ПРОЦЕССОР")
                rt.styles.height = "2fr"
                self.query_one(RightMid).styles.height = "1fr"
                self.query_one(RightBottom).styles.height = "1fr"
                rt.border_title = "Информация о процессоре"
                rt.clear()
                rt.write(get_cpu_info())

        elif self.current_menu == "cpu":
            if command == "0":
                self.current_menu = "hw"
                self.query_one("#cpu-menu").display = False
                self.query_one("#hw-menu").display = True
            elif command == "1":
                log.write(get_cpu_detail_info())
            elif command == "2":
                self.run_worker(self.show_gov_menu())

    def update_cpu_info_panel(self):
        """Обновляет правую верхнюю панель с информацией о процессоре"""
        rt = self.query_one(RightTop)
        rt.clear()
        rt.write(get_cpu_info())

    def add_to_journal(self, message: str):
        """Добавляет сообщение в Системный журнал (сверху, с временем)"""
        journal = self.query_one(RightBottom)
        timestamp = datetime.now().strftime("%H:%M:%S")
        current_text = journal.renderable.plain if hasattr(journal.renderable, 'plain') else str(journal.renderable)
        new_entry = f"[{timestamp}] {message}\n"
        journal.update(Text(new_entry + current_text))

    @on(Button.Pressed)
    async def handle_button_click(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        # === ГЛОБАЛЬНЫЕ КНОПКИ ===
        if btn_id == "btn_home":
            self.reset_to_main_menu()
            return
        if btn_id == "btn_exit":
            self.exit()
            return
        if btn_id == "btn_gov_back":
            self.current_menu = "cpu"
            self.query_one("#gov-menu").display = False
            self.query_one("#cpu-menu").display = True
            return

        # === КНОПКИ ИЗ GOV MENU (режимы CPU) ===
        if btn_id == "btn_save_settings":
            success, msg = save_current_settings_to_systemd()
            log = self.query_one("#terminal-log", RichLog)
            if success:
                log.write(f"[green]✓ {msg}[/green]")
                self.add_to_journal(msg)
                await self.show_gov_menu()
            else:
                log.write(f"[red]✗ {msg}[/red]")
            return

        if btn_id == "btn_reset_settings":
            success, msg = remove_saved_settings()
            log = self.query_one("#terminal-log", RichLog)
            if success:
                log.write(f"[green]✓ {msg}[/green]")
                self.add_to_journal(msg)
                await self.show_gov_menu()
            else:
                log.write(f"[red]✗ {msg}[/red]")
            return

        if btn_id.startswith("set_gov_"):
            gov = btn_id.replace("set_gov_", "")
            success, msg = set_governor(gov)
            log = self.query_one("#terminal-log", RichLog)
            if success:
                gov_rus = GOV_TRANSLATIONS.get(gov, gov)
                log.write(f"[green]✓ Установлен режим: {gov_rus}[/green]")
                self.add_to_journal(f"Режим CPU изменён на {gov_rus}")
                self.update_cpu_info_panel()
            else:
                log.write(f"[red]✗ {msg}[/red]")
            await self.show_gov_menu()
            return

        if btn_id == "toggle_turbo":
            success, msg, new_val = toggle_turbo_boost()
            log = self.query_one("#terminal-log", RichLog)
            if success:
                status_text = "включён" if new_val == 0 else "выключен"
                log.write(f"[green]✓ Turbo Boost {status_text}[/green]")
                self.add_to_journal(f"Turbo Boost {status_text}")
                self.update_cpu_info_panel()
            else:
                log.write(f"[red]✗ {msg}[/red]")
            await self.show_gov_menu()
            return

        # === КНОПКИ ИЗ CPU MENU (подробная информация, режимы работы) ===
        if btn_id == "btn_cpu_1":
            log = self.query_one("#terminal-log", RichLog)
            log.write(get_cpu_detail_info())
            return

        if btn_id == "btn_cpu_2":
            self.run_worker(self.show_gov_menu())
            return

        if btn_id == "btn_cpu_0":
            self.current_menu = "hw"
            self.query_one("#cpu-menu").display = False
            self.query_one("#hw-menu").display = True
            return

        if btn_id == "btn_cpu_00":
            self.reset_to_main_menu()
            return

        # === КНОПКИ ИЗ HARDWARE MENU ===
        if btn_id == "btn_hw_0":
            self.reset_to_main_menu()
            return

        if btn_id == "btn_hw_1":
            self.current_menu = "cpu"
            self.query_one("#hw-menu").display = False
            self.query_one("#cpu-menu").display = True
            self.update_header("МЕНЮ: ПРОЦЕССОР")
            rt = self.query_one(RightTop)
            rt.styles.height = "2fr"
            self.query_one(RightMid).styles.height = "1fr"
            self.query_one(RightBottom).styles.height = "1fr"
            rt.border_title = "Информация о процессоре"
            rt.clear()
            rt.write(get_cpu_info())
            return

        # TODO: btn_hw_2, btn_hw_3, btn_hw_4 — добавить позже
        if btn_id == "btn_hw_2":
            log = self.query_one("#terminal-log", RichLog)
            log.write("[yellow]Видеокарта — в разработке[/yellow]")
            return

        if btn_id == "btn_hw_3":
            log = self.query_one("#terminal-log", RichLog)
            log.write("[yellow]Оперативная память — в разработке[/yellow]")
            return

        if btn_id == "btn_hw_4":
            log = self.query_one("#terminal-log", RichLog)
            log.write("[yellow]Диски — в разработке[/yellow]")
            return

        # === КНОПКИ ИЗ MAIN MENU ===
        if btn_id == "btn_1":
            self.current_menu = "hw"
            self.query_one("#main-menu").display = False
            self.query_one("#hw-menu").display = True
            self.update_header("МЕНЮ: РАБОТА С ЖЕЛЕЗОМ")
            return

        if btn_id == "btn_2":
            log = self.query_one("#terminal-log", RichLog)
            log.write("[yellow]Поиск Windows разделов — в разработке[/yellow]")
            return

        if btn_id == "btn_3":
            log = self.query_one("#terminal-log", RichLog)
            log.write("[yellow]Дамп NTLM хешей (SAM) — в разработке[/yellow]")
            return

        if btn_id == "btn_4":
            log = self.query_one("#terminal-log", RichLog)
            log.write("[yellow]Сетевой сканер — в разработке[/yellow]")
            return

        if btn_id == "btn_5":
            log = self.query_one("#terminal-log", RichLog)
            log.clear()
            log.write("[green]Терминал очищен[/green]")
            return

        # Если кнопка не распознана — выводим предупреждение
        log = self.query_one("#terminal-log", RichLog)
        log.write(f"[red]Неизвестная кнопка: {btn_id}[/red]")

    @on(Input.Submitted, "#terminal-input")
    def process_command(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        if not cmd:
            return
        log = self.query_one("#terminal-log", RichLog)
        log.write(f"\n[bold cyan]# {cmd}[/bold cyan]")
        event.input.value = ""

        if cmd in ["home", "00"]:
            self.reset_to_main_menu()
        elif cmd.isdigit():
            self.execute_menu_action(cmd)
        else:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.stdout:
                log.write(res.stdout.strip())
            if res.stderr:
                log.write(f"[red]{res.stderr}[/red]")


if __name__ == "__main__":
    ToolkitApp().run()