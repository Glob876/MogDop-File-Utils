import os
import shutil
import json
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from datetime import datetime
import subprocess
import sys

# Стили оформления
COLOR_BG = "#ececec"
COLOR_CARD = "#ffffff"
COLOR_TEXT = "#2d3436"
COLOR_HEADER_BG = "#2d3436"
COLOR_ACCENT = "#0984e3"
COLOR_ACCENT_HOVER = "#0773c5"
COLOR_SECONDARY = "#636e72"
COLOR_SECONDARY_HOVER = "#535c68"
COLOR_BORDER = "#dfe6e9"
COLOR_DANGER = "#ff7675"
COLOR_DANGER_HOVER = "#d63031"
COLOR_SUCCESS = "#00b894"
COLOR_HELP = "#636e72"

CONFIG_FILE = "sorter_config.json"
LOG_FILE = "sorter_log.txt"

# Расширенный список форматов
DEFAULT_EXTENSIONS = {
    'Изображения': '.jpg,.jpeg,.png,.gif,.bmp,.svg,.webp,.tiff,.ico',
    'Документы': '.pdf,.doc,.docx,.txt,.xlsx,.pptx,.csv,.odt,.rtf',
    'Видео': '.mp4,.mkv,.avi,.mov,.webm,.flv,.wmv',
    'Музыка': '.mp3,.wav,.flac,.aac,.ogg,.m4a',
    'Архивы': '.zip,.rar,.7z,.tar,.tar.xz,.gz,.bz2,.xz',
    'Программирование': '.py,.html,.css,.js,.cpp,.c,.h,.java,.php,.json,.xml,.sb3,.rb,.go,.rs,.swift',
    'Системные и пакеты': '.exe,.msi,.deb,.run,.appimage,.sh,.bat,.com'
}

LANGUAGES = {
    'RU': {
        'title': "MogDop's File Utils",
        'header_params': "ПАРАМЕТРЫ И НАСТРОЙКИ",
        'sub_general': "Общие настройки",
        'sub_categories': "Настройка категорий (расширения)",
        'single_mode': "Одиночный режим",
        'multi_mode': "Режим нескольких источников",
        'dupe_mode': "Поиск дубликатов",
        'file_menu': "Файл",
        'edit_menu': "Правка",
        'settings': "Настройки",
        'action_menu': "Действия",
        'select_target': "Целевая папка:",
        'sources_list': "Источники (папки):",
        'include_target': "Сортировать файлы в целевой папке тоже",
        'btn_add': "Добавить папку",
        'btn_remove': "Удалить выбранную",
        'btn_run': "НАЧАТЬ СОРТИРОВКУ",
        'btn_reverse': "ОБРАТНАЯ СОРТИРОВКА",
        'btn_find_dupes': "НАЙТИ И УДАЛИТЬ ДУБЛИКАТЫ",
        'conflict_title': "Конфликт имен",
        'conflict_msg': "Файл '{file}' уже существует.",
        'opt_replace': "Заменить",
        'opt_rename': "Переименовать",
        'set_lang': "Язык интерфейса:",
        'set_excluded': "Исключения (через запятую):",
        'set_unknown': "Создавать папку 'Другое'",
        'set_overwrite': "Перезаписывать файлы без спроса",
        'set_auto_dupes': "Авто-удаление дубликатов",
        'set_date_sort': "Сортировать подпапки по дате (Год/Месяц)",
        'set_clean_empty': "Удалять пустые папки после работы",
        'save': "ПРИМЕНИТЬ НАСТРОЙКИ",
        'view_logs': "Открыть лог-файл",
        'clear_logs': "Очистить логи",
        'open_dir': "Открыть папку программы",
        'reset_config': "Сбросить все настройки",
        'add_category': "Добавить новую категорию",
        'restore_cats': "Восстановить категории",
        'success': "Успех",
        'done': "Готово! Файлов обработано: ",
        'err_path': "Путь не найден!",
        'dupe_win': "Выбор дубликатов",
        'confirm_reverse': "Вы уверены, что хотите вернуть все файлы из категорий в общую папку?",
        'preview_mode': "Режим предпросмотра (без перемещения)"
    },
    'EN': {
        'title': "MogDop's File Utils",
        'header_params': "PARAMETERS & SETTINGS",
        'sub_general': "General Settings",
        'sub_categories': "Category Settings (extensions)",
        'single_mode': "Single Mode",
        'multi_mode': "Multiple Sources Mode",
        'dupe_mode': "Duplicate Finder",
        'file_menu': "File",
        'edit_menu': "Edit",
        'settings': "Settings",
        'action_menu': "Actions",
        'select_target': "Target Folder:",
        'sources_list': "Sources:",
        'include_target': "Sort target folder too",
        'btn_add': "Add Folder",
        'btn_remove': "Remove Selected",
        'btn_run': "START SORTING",
        'btn_reverse': "REVERSE SORTING",
        'btn_find_dupes': "FIND & REMOVE DUPLICATES",
        'conflict_title': "Conflict",
        'conflict_msg': "File '{file}' already exists.",
        'opt_replace': "Replace",
        'opt_rename': "Rename",
        'set_lang': "Language:",
        'set_excluded': "Excluded (comma separated):",
        'set_unknown': "Create 'Other' folder",
        'set_overwrite': "Overwrite without prompt",
        'set_auto_dupes': "Auto-delete duplicates",
        'set_date_sort': "Sort subfolders by date (Year/Month)",
        'set_clean_empty': "Delete empty folders after work",
        'save': "APPLY SETTINGS",
        'view_logs': "Open log file",
        'clear_logs': "Clear log file",
        'open_dir': "Open program directory",
        'reset_config': "Reset all settings",
        'add_category': "Add new category",
        'restore_cats': "Restore categories",
        'success': "Success",
        'done': "Done! Files processed: ",
        'err_path': "Path not found!",
        'dupe_win': "Duplicate Selector",
        'confirm_reverse': "Are you sure you want to return all files from categories to the root folder?",
        'preview_mode': "Preview mode (no moving)"
    }
}

HELP_TEXTS = {
    'RU': {
        'single': "Одиночный режим: Файлы в выбранной папке будут распределены по категориям прямо внутри неё.",
        'multi_target': "Целевая папка: Место, куда будут перемещены файлы из всех папок-источников.",
        'multi_src': "Источники: Список папок, из которых программа будет забирать файлы для сортировки.",
        'dupe_scan': "Дубликаты: Программа сравнит файлы по их содержимому (хешу) и предложит удалить копии.",
        'preview': "Режим предпросмотра: Программа запишет в лог, что она собирается сделать, не перемещая файлы реально.",
        'lang': "Язык: Смена языка интерфейса (требуется переоткрытие окон).",
        'excluded': "Исключения: Файлы с этими именами или расширениями будут проигнорированы программой.",
        'unknown': "Папка 'Другое': Если расширение файла неизвестно, он попадет в папку 'Другое' вместо того, чтобы остаться на месте.",
        'overwrite': "Перезапись: Если в папке назначения уже есть файл с таким именем, он будет заменен новым без уведомления.",
        'auto_dupe': "Авто-удаление: Программа сама удалит все копии, оставив только один оригинальный файл.",
        'date_sort': "Сортировка по дате: Внутри каждой категории (например, Изображения) будут созданы папки Год -> Месяц.",
        'clean': "Очистка: Удалять папки, которые стали пустыми после перемещения файлов из них.",
        'incl_target': "Включая цель: Сортировать файлы не только из источников, но и те, что уже лежат в целевой папке.",
        'reverse': "Обратная сортировка: Выносит все файлы из папок-категорий обратно в корень выбранной папки."
    },
    'EN': {
        'single': "Single Mode: Files in the selected folder will be sorted into categories inside that same folder.",
        'multi_target': "Target Folder: The destination where files from all source folders will be moved.",
        'multi_src': "Sources: A list of folders from which the program will take files to sort.",
        'dupe_scan': "Duplicates: The program compares file contents (hashes) and offers to delete copies.",
        'preview': "Preview Mode: The program logs intended actions without actually moving any files.",
        'lang': "Language: Change interface language (requires reopening windows).",
        'excluded': "Excluded: Files with these names or extensions will be ignored by the program.",
        'unknown': "Other Folder: If a file extension is unknown, it will be moved to 'Other' instead of staying put.",
        'overwrite': "Overwrite: If a file exists in the destination, it will be replaced without prompt.",
        'auto_dupe': "Auto-delete: The program will automatically remove copies, keeping only one original.",
        'date_sort': "Date Sorting: Inside each category, subfolders Year -> Month will be created.",
        'clean': "Cleaning: Delete folders that become empty after files are moved out.",
        'incl_target': "Include Target: Sort files not only from sources but also those already in the target folder.",
        'reverse': "Reverse Sort: Moves all files out of category folders back into the root of the selected folder."
    }
}

MONTHS_RU = {1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь", 7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"}

def get_file_hash(filepath):
    hasher = hashlib.md5()
    try:
        if os.path.getsize(filepath) > 100 * 1024 * 1024:
            with open(filepath, 'rb') as f:
                hasher.update(f.read(1024*1024))
                f.seek(-1024*1024, 2)
                hasher.update(f.read(1024*1024))
        else:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
        return hasher.hexdigest()
    except:
        return None

class HelpMarker(tk.Label):
    def __init__(self, master, help_key, lang, status_label):
        super().__init__(master, text=" [?] ", fg=COLOR_ACCENT, bg=master["bg"], cursor="question_arrow", font=("Segoe UI", 9, "bold"))
        self.help_text = HELP_TEXTS[lang].get(help_key, "")
        self.status_label = status_label
        self.bind("<Enter>", self._show)
        self.bind("<Leave>", self._hide)

    def _show(self, e):
        self.status_label.config(text=self.help_text, fg=COLOR_ACCENT)

    def _hide(self, e):
        self.status_label.config(text="")

class StyledButton(tk.Button):
    def __init__(self, master, text, command, bg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, fg_color="white", **kwargs):
        super().__init__(
            master, text=text, command=command, bg=bg_color, fg=fg_color,
            activebackground=hover_color, activeforeground=fg_color,
            relief="flat", font=("Segoe UI", 9, "bold"), pady=7, cursor="hand2", **kwargs
        )
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.bind("<Enter>", lambda e: self.config(bg=self.hover_color))
        self.bind("<Leave>", lambda e: self.config(bg=self.bg_color))

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.lang = app.lang
        self.title(LANGUAGES[self.lang]['settings'])
        self.geometry("650x750")
        self.configure(bg=COLOR_BG)
        self.grab_set()

        self.status_label = tk.Label(self, text="", bg=COLOR_BORDER, fg=COLOR_TEXT, font=("Segoe UI", 9, "italic"), pady=5)
        self.status_label.pack(side="bottom", fill="x")

        canv = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        bar = ttk.Scrollbar(self, orient="vertical", command=canv.yview)
        scroll_f = tk.Frame(canv, bg=COLOR_BG)
        
        scroll_f.bind("<Configure>", lambda e: canv.configure(scrollregion=canv.bbox("all")))
        canv.create_window((0,0), window=scroll_f, anchor="nw", width=620)
        canv.configure(yscrollcommand=bar.set)
        canv.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")

        self.p_card = tk.Frame(scroll_f, bg=COLOR_CARD, padx=25, pady=20, highlightbackground=COLOR_BORDER, highlightthickness=1)
        self.p_card.pack(fill="x", padx=15, pady=15)
        self.p_card.columnconfigure(1, weight=1)

        # Общие
        tk.Label(self.p_card, text=LANGUAGES[self.lang]['sub_general'], bg=COLOR_CARD, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Язык
        f_l = tk.Frame(self.p_card, bg=COLOR_CARD)
        f_l.grid(row=1, column=0, sticky="w", pady=5)
        tk.Label(f_l, text=LANGUAGES[self.lang]['set_lang'], bg=COLOR_CARD).pack(side="left")
        HelpMarker(f_l, 'lang', self.lang, self.status_label).pack(side="left")
        self.l_cb = ttk.Combobox(self.p_card, values=["RU", "EN"], state="readonly")
        self.l_cb.set(self.app.settings["language"])
        self.l_cb.grid(row=1, column=1, sticky="ew", padx=10)

        # Исключения
        f_e = tk.Frame(self.p_card, bg=COLOR_CARD)
        f_e.grid(row=2, column=0, sticky="w", pady=5)
        tk.Label(f_e, text=LANGUAGES[self.lang]['set_excluded'], bg=COLOR_CARD).pack(side="left")
        HelpMarker(f_e, 'excluded', self.lang, self.status_label).pack(side="left")
        self.e_ex = ttk.Entry(self.p_card)
        self.e_ex.insert(0, self.app.settings["excluded_files"])
        self.e_ex.grid(row=2, column=1, sticky="ew", padx=10)

        # Чекбоксы
        chk_row = 3
        chk_data = [
            ('move_unknown', 'set_unknown', 'unknown', "move_unknown"),
            ('overwrite', 'set_overwrite', 'overwrite', "overwrite"),
            ('auto_dupes', 'set_auto_dupes', 'auto_dupe', "auto_dupes"),
            ('date_sort', 'set_date_sort', 'date_sort', "date_sort"),
            ('clean_empty', 'set_clean_empty', 'clean', "clean_empty"),
            ('include_target_root', 'include_target', 'incl_target', "include_target_root")
        ]
        self.vars = {}
        for key_sett, lang_key, help_key, var_name in chk_data:
            f = tk.Frame(self.p_card, bg=COLOR_CARD)
            f.grid(row=chk_row, column=0, columnspan=2, sticky="w", pady=2)
            self.vars[var_name] = tk.BooleanVar(value=self.app.settings[var_name])
            tk.Checkbutton(f, text=LANGUAGES[self.lang][lang_key], variable=self.vars[var_name], bg=COLOR_CARD).pack(side="left")
            HelpMarker(f, help_key, self.lang, self.status_label).pack(side="left")
            chk_row += 1

        # Категории
        tk.Label(self.p_card, text=LANGUAGES[self.lang]['sub_categories'], bg=COLOR_CARD, font=("Segoe UI", 10, "bold")).grid(row=chk_row, column=0, columnspan=2, sticky="w", pady=(15, 5))
        self.e_map = {}
        self.cat_row = chk_row + 1
        self.refresh_categories()

    def refresh_categories(self):
        for widget in self.e_map.values(): widget.destroy()
        curr = self.cat_row
        for cat, exts in self.app.settings["extensions"].items():
            lbl = tk.Label(self.p_card, text=cat, bg=COLOR_CARD)
            lbl.grid(row=curr, column=0, sticky="w", pady=2)
            en = ttk.Entry(self.p_card)
            en.insert(0, exts)
            en.grid(row=curr, column=1, sticky="ew", padx=10, pady=2)
            self.e_map[cat] = en
            curr += 1
        StyledButton(self.p_card, text=LANGUAGES[self.lang]['save'], command=self.apply).grid(row=curr, column=0, columnspan=2, sticky="ew", pady=25)

    def apply(self):
        new_settings = {
            "extensions": {c: e.get() for c, e in self.e_map.items()},
            "language": self.l_cb.get(),
            "move_unknown": self.vars["move_unknown"].get(),
            "overwrite": self.vars["overwrite"].get(),
            "excluded_files": self.e_ex.get(),
            "auto_dupes": self.vars["auto_dupes"].get(),
            "date_sort": self.vars["date_sort"].get(),
            "clean_empty": self.vars["clean_empty"].get(),
            "include_target_root": self.vars["include_target_root"].get()
        }
        self.app.settings.update(new_settings)
        self.app.lang = new_settings["language"]
        self.app.save_settings()
        self.app.create_main_ui()
        messagebox.showinfo(LANGUAGES[self.app.lang]['success'], "Settings Saved!")
        self.destroy()

class FileSorterApp:
    def __init__(self, root):
        self.root = root
        self.settings = self.load_settings()
        self.lang = self.settings.get("language", "RU")
        
        self.root.title(LANGUAGES[self.lang]['title'])
        self.root.geometry("950x850")
        self.root.configure(bg=COLOR_BG)
        
        self.source_path = tk.StringVar(value=self.settings.get("last_path", ""))
        self.multi_target = tk.StringVar(value=self.settings.get("multi_target", ""))
        self.dupe_folder = tk.StringVar(value="")
        self.multi_sources = self.settings.get("multi_sources", [])
        self.include_target_var = tk.BooleanVar(value=self.settings.get("include_target_root", False))
        self.preview_mode = tk.BooleanVar(value=False)
        
        self.create_menu()
        self.create_main_ui()

    def load_settings(self):
        defaults = {
            "extensions": DEFAULT_EXTENSIONS, "auto_dupes": False, "include_target_root": False, 
            "multi_sources": [], "excluded_files": "", "move_unknown": True, "overwrite": False, 
            "language": "RU", "date_sort": False, "clean_empty": True, "last_path": "", "multi_target": ""
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    for k, v in defaults.items(): d.setdefault(k, v)
                    return d
            except: pass
        return defaults

    def save_settings(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=4)

    def log(self, msg):
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

    def get_directory_path(self, title="Select Directory"):
        """Оптимизированный выбор папок для Linux и других систем"""
        if sys.platform.startswith('linux'):
            # Пробуем Zenity (нативный диалог в GNOME/GTK)
            try:
                proc = subprocess.run(['zenity', '--file-selection', '--directory', f'--title={title}'],
                                     capture_output=True, text=True)
                if proc.returncode == 0:
                    return proc.stdout.strip()
            except: pass

            # Пробуем KDialog (нативный диалог в KDE)
            try:
                proc = subprocess.run(['kdialog', '--getexistingdirectory', '--title', title],
                                     capture_output=True, text=True)
                if proc.returncode == 0:
                    return proc.stdout.strip()
            except: pass
        
        # Стандартный диалог Tkinter (Windows, Mac или Linux без утилит)
        return filedialog.askdirectory(title=title)

    def create_menu(self):
        m = tk.Menu(self.root)
        f_m = tk.Menu(m, tearoff=0)
        f_m.add_command(label=LANGUAGES[self.lang]['view_logs'], command=lambda: self.universal_open(LOG_FILE))
        f_m.add_command(label=LANGUAGES[self.lang]['clear_logs'], command=self.clear_logs)
        f_m.add_command(label=LANGUAGES[self.lang]['open_dir'], command=lambda: self.universal_open(os.getcwd()))
        f_m.add_separator()
        f_m.add_command(label="Exit", command=self.root.quit)
        m.add_cascade(label=LANGUAGES[self.lang]['file_menu'], menu=f_m)
        e_m = tk.Menu(m, tearoff=0)
        e_m.add_command(label=LANGUAGES[self.lang]['settings'], command=self.open_settings)
        e_m.add_separator()
        e_m.add_command(label=LANGUAGES[self.lang]['add_category'], command=self.add_new_category_dialog)
        e_m.add_command(label=LANGUAGES[self.lang]['restore_cats'], command=self.restore_categories)
        e_m.add_separator()
        e_m.add_command(label=LANGUAGES[self.lang]['reset_config'], command=self.reset_all_settings)
        m.add_cascade(label=LANGUAGES[self.lang]['edit_menu'], menu=e_m)
        self.root.config(menu=m)

    def clear_logs(self):
        with open(LOG_FILE, "w", encoding="utf-8") as f: f.write("")
        messagebox.showinfo("Log", LANGUAGES[self.lang]['success'])

    def reset_all_settings(self):
        if messagebox.askyesno("Reset", "Сбросить все настройки до заводских?"):
            if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
            self.settings = self.load_settings()
            self.lang = self.settings["language"]
            self.create_main_ui()

    def restore_categories(self):
        self.settings["extensions"] = DEFAULT_EXTENSIONS.copy()
        self.save_settings()
        self.create_main_ui()
        messagebox.showinfo("Edit", LANGUAGES[self.lang]['success'])

    def add_new_category_dialog(self):
        name = simpledialog.askstring("Category", LANGUAGES[self.lang]['add_category'])
        if name:
            self.settings["extensions"][name] = ""
            self.save_settings()
            self.open_settings()

    def universal_open(self, path):
        if not path or not os.path.exists(path): return
        try:
            if sys.platform == 'win32': os.startfile(path)
            elif sys.platform == 'darwin': subprocess.Popen(['open', path])
            else: subprocess.Popen(['xdg-open', path])
        except: pass

    def open_settings(self):
        SettingsWindow(self.root, self)

    def create_main_ui(self):
        self.root.title(LANGUAGES[self.lang]['title'])
        self.create_menu()
        for w in self.root.winfo_children():
            if not isinstance(w, tk.Menu): w.destroy()
        self.status_label = tk.Label(self.root, text="", bg=COLOR_BORDER, fg=COLOR_TEXT, font=("Segoe UI", 10, "italic"), pady=7)
        self.status_label.pack(side="bottom", fill="x")
        main_f = tk.Frame(self.root, bg=COLOR_BG); main_f.pack(fill="both", expand=True)
        canv = tk.Canvas(main_f, bg=COLOR_BG, highlightthickness=0); bar = ttk.Scrollbar(main_f, orient="vertical", command=canv.yview)
        scroll_f = tk.Frame(canv, bg=COLOR_BG); scroll_f.bind("<Configure>", lambda e: canv.configure(scrollregion=canv.bbox("all")))
        canv.create_window((0, 0), window=scroll_f, anchor="nw", width=910); canv.configure(yscrollcommand=bar.set); canv.pack(side="left", fill="both", expand=True, padx=(10, 0)); bar.pack(side="right", fill="y")
        self.p_var = tk.DoubleVar(); self.p_bar = ttk.Progressbar(scroll_f, variable=self.p_var, maximum=100); self.p_bar.pack(fill="x", padx=15, pady=10)

        # 1. Одиночный режим
        single_f = tk.Frame(scroll_f, bg=COLOR_CARD, padx=20, pady=15, highlightbackground=COLOR_BORDER, highlightthickness=1); single_f.pack(fill="x", padx=15, pady=10)
        h_s = tk.Frame(single_f, bg=COLOR_CARD); h_s.pack(anchor="w", pady=(0, 10))
        tk.Label(h_s, text=LANGUAGES[self.lang]['single_mode'], bg=COLOR_CARD, font=("Segoe UI", 11, "bold")).pack(side="left")
        HelpMarker(h_s, 'single', self.lang, self.status_label).pack(side="left")
        f_p = tk.Frame(single_f, bg=COLOR_CARD); f_p.pack(fill="x", pady=5)
        ttk.Entry(f_p, textvariable=self.source_path).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(f_p, text="...", command=lambda: self.browse(self.source_path), bg=COLOR_BORDER, relief="flat", padx=10).pack(side="right", padx=5)
        StyledButton(single_f, text=LANGUAGES[self.lang]['btn_run'], command=self.run_single_sorting).pack(fill="x", pady=2)
        f_rev = tk.Frame(single_f, bg=COLOR_CARD); f_rev.pack(fill="x")
        StyledButton(f_rev, text=LANGUAGES[self.lang]['btn_reverse'], command=self.run_unsorting_single, bg_color=COLOR_SECONDARY, hover_color=COLOR_SECONDARY_HOVER).pack(fill="x", side="left", expand=True)
        HelpMarker(f_rev, 'reverse', self.lang, self.status_label).pack(side="right", padx=5)

        # 2. Мульти режим
        multi_f = tk.Frame(scroll_f, bg=COLOR_CARD, padx=20, pady=15, highlightbackground=COLOR_BORDER, highlightthickness=1); multi_f.pack(fill="x", padx=15, pady=10)
        tk.Label(multi_f, text=LANGUAGES[self.lang]['multi_mode'], bg=COLOR_CARD, font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT).pack(anchor="w", pady=(0, 10))
        f_mt = tk.Frame(multi_f, bg=COLOR_CARD); f_mt.pack(anchor="w")
        tk.Label(f_mt, text=LANGUAGES[self.lang]['select_target'], bg=COLOR_CARD).pack(side="left")
        HelpMarker(f_mt, 'multi_target', self.lang, self.status_label).pack(side="left")
        f_t = tk.Frame(multi_f, bg=COLOR_CARD); f_t.pack(fill="x", pady=2)
        ttk.Entry(f_t, textvariable=self.multi_target).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(f_t, text="...", command=lambda: self.browse(self.multi_target, True), bg=COLOR_BORDER, relief="flat", padx=10).pack(side="right", padx=5)
        f_ms = tk.Frame(multi_f, bg=COLOR_CARD); f_ms.pack(anchor="w", pady=(5,0))
        tk.Label(f_ms, text=LANGUAGES[self.lang]['sources_list'], bg=COLOR_CARD).pack(side="left")
        HelpMarker(f_ms, 'multi_src', self.lang, self.status_label).pack(side="left")
        f_list = tk.Frame(multi_f, bg=COLOR_CARD); f_list.pack(fill="x", pady=5)
        self.src_lb = tk.Listbox(f_list, height=4, bg=COLOR_BG, relief="flat", font=("Segoe UI", 9)); self.src_lb.pack(side="left", fill="x", expand=True)
        for s in self.multi_sources: self.src_lb.insert(tk.END, s)
        f_btn = tk.Frame(f_list, bg=COLOR_CARD); f_btn.pack(side="right", padx=5)
        StyledButton(f_btn, text="+", command=self.add_src, width=4).pack(pady=2)
        StyledButton(f_btn, text="-", command=self.rem_src, bg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER, width=4).pack()
        StyledButton(multi_f, text=LANGUAGES[self.lang]['btn_run'], command=self.run_multi_sorting).pack(fill="x", pady=5)

        # 3. Дубликаты
        dupe_f = tk.Frame(scroll_f, bg=COLOR_CARD, padx=20, pady=15, highlightbackground=COLOR_BORDER, highlightthickness=1); dupe_f.pack(fill="x", padx=15, pady=10)
        h_d = tk.Frame(dupe_f, bg=COLOR_CARD); h_d.pack(anchor="w", pady=(0, 10))
        tk.Label(h_d, text=LANGUAGES[self.lang]['dupe_mode'], bg=COLOR_CARD, font=("Segoe UI", 11, "bold")).pack(side="left")
        HelpMarker(h_d, 'dupe_scan', self.lang, self.status_label).pack(side="left")
        f_d = tk.Frame(dupe_f, bg=COLOR_CARD); f_d.pack(fill="x", pady=5)
        ttk.Entry(f_d, textvariable=self.dupe_folder).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(f_d, text="...", command=lambda: self.browse(self.dupe_folder), bg=COLOR_BORDER, relief="flat", padx=10).pack(side="right", padx=5)
        StyledButton(dupe_f, text=LANGUAGES[self.lang]['btn_find_dupes'], command=self.run_dupe_finder).pack(fill="x", pady=5)

        # Превью
        f_pre = tk.Frame(scroll_f, bg=COLOR_BG); f_pre.pack(pady=10)
        tk.Checkbutton(f_pre, text=LANGUAGES[self.lang]['preview_mode'], variable=self.preview_mode, bg=COLOR_BG, fg=COLOR_ACCENT, font=("Segoe UI", 9, "bold")).pack(side="left")
        HelpMarker(f_pre, 'preview', self.lang, self.status_label).pack(side="left")

    def browse(self, var, multi=False):
        f = self.get_directory_path("Select Directory")
        if f:
            var.set(f)
            if multi: self.settings["multi_target"] = f
            else: self.settings["last_path"] = f
            self.save_settings()

    def add_src(self):
        f = self.get_directory_path("Select Source Directory")
        if f and f not in self.multi_sources:
            self.multi_sources.append(f); self.src_lb.insert(tk.END, f)
            self.settings["multi_sources"] = self.multi_sources; self.save_settings()

    def rem_src(self):
        s = self.src_lb.curselection()
        if s:
            val = self.src_lb.get(s[0]); self.multi_sources.remove(val); self.src_lb.delete(s[0])
            self.settings["multi_sources"] = self.multi_sources; self.save_settings()

    def run_dupe_finder(self):
        p = self.dupe_folder.get()
        if not p or not os.path.exists(p): return messagebox.showerror("!", LANGUAGES[self.lang]['err_path'])
        self.p_var.set(0)
        hashes = {}
        all_files = []
        for root_dir, _, files in os.walk(p):
            for f in files: all_files.append(os.path.join(root_dir, f))
        total = len(all_files)
        if total == 0: return
        for i, fp in enumerate(all_files):
            h = get_file_hash(fp)
            if h: hashes.setdefault(h, []).append(fp)
            if i % 10 == 0: self.p_var.set((i/total)*100); self.root.update_idletasks()
        groups = [ps for ps in hashes.values() if len(ps) > 1]
        self.p_var.set(100)
        if not groups: return messagebox.showinfo("Info", "No duplicates found.")
        to_del = []
        if self.settings["auto_dupes"]:
            for g in groups: to_del.extend(g[1:])
        else:
            sel = DuplicateSelector(self.root, groups, self.lang); self.root.wait_window(sel); to_del = sel.to_delete
        count = 0
        for path in to_del:
            try: 
                if not self.preview_mode.get(): os.remove(path)
                self.log(f"Deleted dupe: {path}"); count += 1
            except: pass
        messagebox.showinfo(LANGUAGES[self.lang]['success'], f"Processed: {count}"); self.p_var.set(0)

    def run_single_sorting(self):
        p = self.source_path.get(); 
        if os.path.exists(p): self._sort_engine(p, p)

    def run_multi_sorting(self):
        t = self.multi_target.get()
        if os.path.exists(t):
            srcs = list(self.multi_sources)
            if self.include_target_var.get(): srcs.append(t)
            for s in srcs:
                if os.path.exists(s): self._sort_engine(s, t)

    def _sort_engine(self, src_dir, dst_root):
        excl = [x.strip().lower() for x in self.settings["excluded_files"].split(",") if x.strip()]
        files = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))]
        total = len(files)
        if total == 0: return
        count = 0
        for i, f in enumerate(files):
            fp = os.path.join(src_dir, f)
            if f not in [CONFIG_FILE, LOG_FILE] and f.lower() not in excl:
                if self.process_move(fp, dst_root, f): count += 1
            self.p_var.set((i/total)*100); self.root.update_idletasks()
        if self.settings["clean_empty"] and not self.preview_mode.get(): self._clean_empty_folders(src_dir)
        self.p_var.set(100); messagebox.showinfo(LANGUAGES[self.lang]['success'], LANGUAGES[self.lang]['done'] + str(count)); self.p_var.set(0)

    def _clean_empty_folders(self, path):
        for root, dirs, _ in os.walk(path, topdown=False):
            for d in dirs:
                dp = os.path.join(root, d)
                try: 
                    if not os.listdir(dp): os.rmdir(dp)
                except: pass

    def process_move(self, src, target_root, fname):
        ext = os.path.splitext(fname)[1].lower()
        cat = None
        for c, exts in self.settings["extensions"].items():
            if ext in [e.strip().lower() for e in exts.split(',')]: cat = c; break
        if not cat and self.settings["move_unknown"]: cat = "Other" if self.lang == "EN" else "Другое"
        if not cat: return False
        d_dir = os.path.join(target_root, cat)
        if self.settings["date_sort"]:
            dt = datetime.fromtimestamp(os.path.getmtime(src))
            m_name = MONTHS_RU[dt.month] if self.lang == "RU" else dt.strftime('%B')
            d_dir = os.path.join(d_dir, str(dt.year), m_name)
        if self.preview_mode.get(): self.log(f"[PREVIEW] {fname} -> {d_dir}"); return True
        os.makedirs(d_dir, exist_ok=True)
        dst = os.path.join(d_dir, fname)
        if os.path.exists(dst):
            if self.settings["overwrite"]: 
                try: os.remove(dst)
                except: pass
            else:
                diag = ConflictDialog(self.root, fname, self.lang); self.root.wait_window(diag)
                if not diag.result: return False
                if diag.result == 'rename':
                    n, e = os.path.splitext(fname); dst = os.path.join(d_dir, f"{n}_{datetime.now().strftime('%H%M%S')}{e}")
        try: shutil.move(src, dst); return True
        except: return False

    def run_unsorting_single(self):
        p = self.source_path.get()
        if p and os.path.exists(p): self._unsort(p)

    def _unsort(self, p):
        if not messagebox.askyesno("?", LANGUAGES[self.lang]['confirm_reverse']): return
        self.p_var.set(0)
        all_files = []
        cats = list(self.settings["extensions"].keys()) + ["Other", "Другое"]
        for c in cats:
            cp = os.path.join(p, c)
            if os.path.isdir(cp):
                for r, _, fs in os.walk(cp):
                    for f in fs: all_files.append(os.path.join(r, f))
        count = 0
        total = len(all_files)
        for i, fp in enumerate(all_files):
            dst = os.path.join(p, os.path.basename(fp))
            if os.path.exists(dst):
                n, e = os.path.splitext(os.path.basename(fp))
                dst = os.path.join(p, f"{n}_old_{datetime.now().strftime('%H%M%S')}{e}")
            try: shutil.move(fp, dst); count += 1
            except: pass
            self.p_var.set((i/max(1, total))*100); self.root.update_idletasks()
        if self.settings["clean_empty"]: self._clean_empty_folders(p)
        self.p_var.set(100); messagebox.showinfo(LANGUAGES[self.lang]['success'], LANGUAGES[self.lang]['done'] + str(count)); self.p_var.set(0)

class DuplicateSelector(tk.Toplevel):
    def __init__(self, parent, dupe_groups, lang):
        super().__init__(parent); self.title(LANGUAGES[lang]['dupe_win']); self.geometry("700x600"); self.configure(bg=COLOR_BG); self.to_delete = []; self.grab_set()
        card = tk.Frame(self, bg=COLOR_CARD, padx=15, pady=15); card.pack(fill="both", expand=True, padx=20, pady=20)
        canv = tk.Canvas(card, bg=COLOR_CARD, highlightthickness=0); bar = ttk.Scrollbar(card, orient="vertical", command=canv.yview)
        self.scroll_f = tk.Frame(canv, bg=COLOR_CARD); self.scroll_f.bind("<Configure>", lambda e: canv.configure(scrollregion=canv.bbox("all")))
        canv.create_window((0,0), window=self.scroll_f, anchor="nw", width=620); canv.configure(yscrollcommand=bar.set); canv.pack(side="left", fill="both", expand=True); bar.pack(side="right", fill="y")
        self.checks = []
        for group in dupe_groups:
            frame = tk.LabelFrame(self.scroll_f, text=f"Группа ({len(group)})", bg=COLOR_CARD, pady=10)
            frame.pack(fill="x", pady=10, padx=5)
            for i, path in enumerate(group):
                var = tk.BooleanVar(value=(i > 0)); self.checks.append((var, path))
                cb = tk.Checkbutton(frame, text=path, variable=var, bg=COLOR_CARD, wraplength=550, justify="left"); cb.pack(fill="x", padx=10)
        StyledButton(self, text="УДАЛИТЬ ВЫБРАННЫЕ", command=self.confirm, bg_color=COLOR_DANGER).pack(fill="x", side="bottom")
    def confirm(self): self.to_delete = [p for v, p in self.checks if v.get()]; self.destroy()

class ConflictDialog(tk.Toplevel):
    def __init__(self, parent, filename, lang):
        super().__init__(parent); self.result = None; self.title(LANGUAGES[lang]['conflict_title']); self.geometry("450x200"); self.configure(bg=COLOR_CARD); self.grab_set()
        tk.Label(self, text=LANGUAGES[lang]['conflict_msg'].format(file=filename), bg=COLOR_CARD, pady=25, wraplength=400).pack()
        f = tk.Frame(self, bg=COLOR_CARD); f.pack(pady=10)
        StyledButton(f, text=LANGUAGES[lang]['opt_replace'], command=lambda: self.end('replace'), bg_color=COLOR_DANGER, width=15).pack(side="left", padx=5)
        StyledButton(f, text=LANGUAGES[lang]['opt_rename'], command=lambda: self.end('rename'), width=15).pack(side="left", padx=5)
    def end(self, m): self.result = m; self.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    if sys.platform == 'win32':
        try: from ctypes import windll; windll.shcore.SetProcessDpiAwareness(1)
        except: pass
    app = FileSorterApp(root); root.mainloop()
