import os
import shutil
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from datetime import datetime
import subprocess
import sys
import threading
from typing import Dict, List, Optional, Tuple, Any
from sorter_core import FileSorterCore

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

CONFIG_FILE = "sorter_config.json"
LOG_FILE = "sorter_log.txt"

DEFAULT_EXTENSIONS = {
    'Image': '.jpg,.jpeg,.png,.gif,.bmp,.svg,.webp,.tiff,.ico',
    'Documents': '.pdf,.doc,.docx,.txt,.xlsx,.pptx,.csv,.odt,.rtf',
    'Videos': '.mp4,.mkv,.avi,.mov,.webm,.flv,.wmv',
    'Music': '.mp3,.wav,.flac,.aac,.ogg,.m4a',
    'Archives': '.zip,.rar,.7z,.tar,.tar.xz,.gz,.bz2,.xz',
    'Coding': '.py,.html,.css,.js,.cpp,.c,.h,.java,.php,.json,.xml,.sb3,.rb,.go,.rs,.swift',
    'Packs': '.exe,.msi,.deb,.run,.appimage,.sh,.bat,.com'
}

LANGUAGES = {
    'RU': {
        'title': "MogDop's File Utils Legacy",
        'header_params': "ПАРАМЕТРЫ И НАСТРОЙКИ",
        'sub_general': "Общие настройки",
        'sub_categories': "Настройка категорий (расширения)",
        'single_mode': "Одиночный режим",
        'multi_mode': "Режим нескольких источников",
        'dupe_mode': "Поиск дубликатов",
        'auto_mode': "Фоновый мониторинг (Бета)",
        'file_menu': "Файл",
        'edit_menu': "Правка",
        'settings': "Настройки",
        'action_menu': "Действия",
        'select_target': "Целевая папка:",
        'sources_list': "Источники (папки):",
        'auto_src': "Папка слежения:",
        'auto_interval': "Интервал (сек):",
        'auto_enable': "Включить мониторинг",
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
        'apply_all': "Применить ко всем конфликтам в этот раз",
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
        'done': "Готово! Обработка завершена.",
        'err_path': "Путь не найден!",
        'dupe_win': "Выбор дубликатов",
        'confirm_reverse': "Вы уверены, что хотите вернуть все файлы из категорий в общую папку?",
        'preview_mode': "Режим предпросмотра (без перемещения)",
        'no_watchdog': "Режим отслеживания запущен.",
        'beta_warn_title': "Фоновый мониторинг",
        'beta_warn_msg': "Программа автоматически перемещает новые файлы. Проверьте настройки папок."
    },
    'EN': {
        'title': "MogDop's File Utils Legacy",
        'header_params': "PARAMETERS & SETTINGS",
        'sub_general': "General Settings",
        'sub_categories': "Category Settings (extensions)",
        'single_mode': "Single Mode",
        'multi_mode': "Multiple Sources Mode",
        'dupe_mode': "Duplicate Finder",
        'auto_mode': "Background Monitoring",
        'file_menu': "File",
        'edit_menu': "Edit",
        'settings': "Settings",
        'action_menu': "Actions",
        'select_target': "Target Folder:",
        'sources_list': "Sources:",
        'auto_src': "Watch Folder:",
        'auto_interval': "Interval (sec):",
        'auto_enable': "Enable Monitoring",
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
        'apply_all': "Apply to all conflicts this session",
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
        'done': "Done! Operations completed.",
        'err_path': "Path not found!",
        'dupe_win': "Duplicate Selector",
        'confirm_reverse': "Are you sure you want to return all files from categories to the root folder?",
        'preview_mode': "Preview mode (no moving)",
        'no_watchdog': "Monitoring mode is active.",
        'beta_warn_title': "Background Monitoring",
        'beta_warn_msg': "The program will automatically sort files. Please check paths."
    }
}

class StyledButton(tk.Button):
    def __init__(self, master: tk.Widget, text: str, command: callable, bg_color: str = COLOR_ACCENT, hover_color: str = COLOR_ACCENT_HOVER, fg_color: str = "white", **kwargs):
        super().__init__(
            master, text=text, command=command, bg=bg_color, fg=fg_color,
            activebackground=hover_color, activeforeground=fg_color,
            relief="flat", font=("Segoe UI", 9, "bold"), pady=7, cursor="hand2", **kwargs
        )
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.bind("<Enter>", lambda e: self.config(bg=self.hover_color))
        self.bind("<Leave>", lambda e: self.config(bg=self.bg_color))

class DuplicateSelector(tk.Toplevel):
    def __init__(self, parent: tk.Widget, dupe_groups: List[List[str]], lang: str):
        super().__init__(parent)
        self.to_delete: List[str] = []
        self.title(LANGUAGES[lang]['dupe_win'])
        self.geometry("750x650")
        self.configure(bg=COLOR_BG)
        self.grab_set()

        card = tk.Frame(self, bg=COLOR_CARD, padx=15, pady=15)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        canv = tk.Canvas(card, bg=COLOR_CARD, highlightthickness=0)
        bar = ttk.Scrollbar(card, orient="vertical", command=canv.yview)
        
        self.scroll_f = tk.Frame(canv, bg=COLOR_CARD)
        self.scroll_f.bind("<Configure>", lambda e: canv.configure(scrollregion=canv.bbox("all")))
        
        canv.create_window((0, 0), window=self.scroll_f, anchor="nw", width=660)
        canv.configure(yscrollcommand=bar.set)
        canv.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")

        self.checks: List[Tuple[tk.BooleanVar, str]] = []

        for group in dupe_groups:
            frame = tk.LabelFrame(self.scroll_f, text=f"Группа ({len(group)})", bg=COLOR_CARD, pady=10)
            frame.pack(fill="x", pady=10, padx=5)
            for i, path in enumerate(group):
                var = tk.BooleanVar(value=(i > 0))
                self.checks.append((var, path))
                cb = tk.Checkbutton(frame, text=path, variable=var, bg=COLOR_CARD, wraplength=600, justify="left")
                cb.pack(fill="x", padx=10, anchor="w")

        StyledButton(self, text="УДАЛИТЬ ВЫБРАННЫЕ / DELETE SELECTED", command=self.confirm, bg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER).pack(fill="x", side="bottom")

    def confirm(self) -> None:
        self.to_delete = [p for v, p in self.checks if v.get()]
        self.destroy()

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent: tk.Widget, app: 'FileSorterApp'):
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
        canv.create_window((0, 0), window=scroll_f, anchor="nw", width=620)
        canv.configure(yscrollcommand=bar.set)
        canv.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")

        self.p_card = tk.Frame(scroll_f, bg=COLOR_CARD, padx=25, pady=20, highlightbackground=COLOR_BORDER, highlightthickness=1)
        self.p_card.pack(fill="x", padx=15, pady=15)
        self.p_card.columnconfigure(1, weight=1)

        tk.Label(self.p_card, text=LANGUAGES[self.lang]['sub_general'], bg=COLOR_CARD, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        f_l = tk.Frame(self.p_card, bg=COLOR_CARD)
        f_l.grid(row=1, column=0, sticky="w", pady=5)
        tk.Label(f_l, text=LANGUAGES[self.lang]['set_lang'], bg=COLOR_CARD).pack(side="left")
        
        self.l_cb = ttk.Combobox(self.p_card, values=["RU", "EN"], state="readonly")
        self.l_cb.set(self.app.core.config.get("language", "RU"))
        self.l_cb.grid(row=1, column=1, sticky="ew", padx=10)

        f_e = tk.Frame(self.p_card, bg=COLOR_CARD)
        f_e.grid(row=2, column=0, sticky="w", pady=5)
        tk.Label(f_e, text=LANGUAGES[self.lang]['set_excluded'], bg=COLOR_CARD).pack(side="left")
        
        self.e_ex = ttk.Entry(self.p_card)
        self.e_ex.insert(0, self.app.core.config.get("excluded_files", ""))
        self.e_ex.grid(row=2, column=1, sticky="ew", padx=10)

        chk_row = 3
        chk_data = [
            ('move_unknown', 'set_unknown', "move_unknown"),
            ('overwrite', 'set_overwrite', "overwrite"),
            ('auto_dupes', 'set_auto_dupes', "auto_dupes"),
            ('date_sort', 'set_date_sort', "date_sort"),
            ('clean_empty', 'set_clean_empty', "clean_empty"),
            ('include_target_root', 'include_target', "include_target_root")
        ]
        self.vars: Dict[str, tk.BooleanVar] = {}
        for key_sett, lang_key, var_name in chk_data:
            f = tk.Frame(self.p_card, bg=COLOR_CARD)
            f.grid(row=chk_row, column=0, columnspan=2, sticky="w", pady=2)
            self.vars[var_name] = tk.BooleanVar(value=self.app.core.config.get(var_name, False))
            tk.Checkbutton(f, text=LANGUAGES[self.lang][lang_key], variable=self.vars[var_name], bg=COLOR_CARD).pack(side="left")
            chk_row += 1

        tk.Label(self.p_card, text=LANGUAGES[self.lang]['sub_categories'], bg=COLOR_CARD, font=("Segoe UI", 10, "bold")).grid(row=chk_row, column=0, columnspan=2, sticky="w", pady=(15, 5))
        self.e_map: Dict[str, ttk.Entry] = {}
        self.cat_row = chk_row + 1
        self.refresh_categories()

    def refresh_categories(self) -> None:
        for widget in self.e_map.values():
            widget.destroy()
        curr = self.cat_row
        
        extensions_dict = self.app.core.config.get("extensions", DEFAULT_EXTENSIONS)
        for cat, exts in extensions_dict.items():
            lbl = tk.Label(self.p_card, text=cat, bg=COLOR_CARD)
            lbl.grid(row=curr, column=0, sticky="w", pady=2)
            en = ttk.Entry(self.p_card)
            en.insert(0, exts)
            en.grid(row=curr, column=1, sticky="ew", padx=10, pady=2)
            self.e_map[cat] = en
            curr += 1
            
        StyledButton(self.p_card, text=LANGUAGES[self.lang]['save'], command=self.apply).grid(row=curr, column=0, columnspan=2, sticky="ew", pady=25)

    def apply(self) -> None:
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
        self.app.core.save_config(new_settings)
        self.app.lang = new_settings["language"]
        self.app.create_main_ui()
        messagebox.showinfo(LANGUAGES[self.app.lang]['success'], "Settings Saved!")
        self.destroy()

class FileSorterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.core = FileSorterCore()
        self.lang = self.core.config.get("language", "RU")
        
        self.root.title(LANGUAGES[self.lang]['title'])
        self.root.geometry("950x950")
        self.root.configure(bg=COLOR_BG)
        
        if os.path.exists("logo.ico"):
            try:
                self.root.iconbitmap("logo.ico")
            except Exception:
                pass
        
        self.source_path = tk.StringVar(value=self.core.config.get("last_path", ""))
        self.multi_target = tk.StringVar(value=self.core.config.get("multi_target", ""))
        self.dupe_folder = tk.StringVar(value="")
        self.multi_sources: List[str] = self.core.config.get("multi_sources", [])
        self.include_target_var = tk.BooleanVar(value=self.core.config.get("include_target_root", False))
        self.preview_mode = tk.BooleanVar(value=self.core.config.get("dry_run", False))

        self.auto_src = tk.StringVar(value=self.core.config.get("monitor_folders", [""])[0] if self.core.config.get("monitor_folders") else "")
        self.auto_dst = tk.StringVar(value=self.core.config.get("monitor_target", ""))
        self.auto_interval = tk.IntVar(value=int(self.core.config.get("monitor_interval_sec", 10)))
        self.auto_enabled = tk.BooleanVar(value=self.core.config.get("monitor_enabled", False))

        self.create_menu()
        self.create_main_ui()

    def get_directory_path(self, title: str = "Select Directory") -> str:
        return filedialog.askdirectory(title=title)

    def create_menu(self) -> None:
        m = tk.Menu(self.root)
        
        f_m = tk.Menu(m, tearoff=0)
        f_m.add_command(label=LANGUAGES[self.lang]['view_logs'], command=self.open_logs)
        f_m.add_command(label=LANGUAGES[self.lang]['clear_logs'], command=self.clear_logs)
        f_m.add_command(label=LANGUAGES[self.lang]['open_dir'], command=self.open_app_dir)
        f_m.add_separator()
        f_m.add_command(label="Exit", command=self.root.quit)
        m.add_cascade(label=LANGUAGES[self.lang]['file_menu'], menu=f_m)
        
        e_m = tk.Menu(m, tearoff=0)
        e_m.add_command(label=LANGUAGES[self.lang]['settings'], command=self.open_settings)
        e_m.add_separator()
        e_m.add_command(label=LANGUAGES[self.lang]['restore_cats'], command=self.restore_categories)
        e_m.add_separator()
        e_m.add_command(label=LANGUAGES[self.lang]['reset_config'], command=self.reset_all_settings)
        m.add_cascade(label=LANGUAGES[self.lang]['edit_menu'], menu=e_m)
        
        self.root.config(menu=m)

    def open_logs(self):
        if os.path.exists(LOG_FILE):
            if sys.platform == 'win32':
                os.startfile(LOG_FILE)
            else:
                subprocess.Popen(['xdg-open', LOG_FILE])

    def open_app_dir(self):
        cwd = os.getcwd()
        if sys.platform == 'win32':
            os.startfile(cwd)
        else:
            subprocess.Popen(['xdg-open', cwd])

    def clear_logs(self) -> None:
        try:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("")
            messagebox.showinfo("Log", LANGUAGES[self.lang]['success'])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def reset_all_settings(self) -> None:
        if messagebox.askyesno("Reset", "Сбросить все настройки? / Reset all settings?"):
            if os.path.exists(CONFIG_FILE):
                try:
                    os.remove(CONFIG_FILE)
                except Exception:
                    pass
            self.core = FileSorterCore()
            self.lang = self.core.config["language"]
            self.create_main_ui()

    def restore_categories(self) -> None:
        self.core.config["extensions"] = DEFAULT_EXTENSIONS.copy()
        self.core.save_config(self.core.config)
        self.create_main_ui()
        messagebox.showinfo("Edit", LANGUAGES[self.lang]['success'])

    def open_settings(self) -> None:
        SettingsWindow(self.root, self)

    def create_main_ui(self) -> None:
        self.root.title(LANGUAGES[self.lang]['title'])
        self.create_menu()
        
        for w in self.root.winfo_children():
            if not isinstance(w, tk.Menu):
                w.destroy()
                
        self.status_label = tk.Label(self.root, text="", bg=COLOR_BORDER, fg=COLOR_TEXT, font=("Segoe UI", 10, "italic"), pady=7)
        self.status_label.pack(side="bottom", fill="x")
        
        main_f = tk.Frame(self.root, bg=COLOR_BG)
        main_f.pack(fill="both", expand=True)
        
        canv = tk.Canvas(main_f, bg=COLOR_BG, highlightthickness=0)
        bar = ttk.Scrollbar(main_f, orient="vertical", command=canv.yview)
        
        scroll_f = tk.Frame(canv, bg=COLOR_BG)
        scroll_f.bind("<Configure>", lambda e: canv.configure(scrollregion=canv.bbox("all")))
        
        canv.create_window((0, 0), window=scroll_f, anchor="nw", width=910)
        canv.configure(yscrollcommand=bar.set)
        canv.pack(side="left", fill="both", expand=True, padx=(10, 0))
        bar.pack(side="right", fill="y")
        
        self.p_var = tk.DoubleVar()
        self.p_bar = ttk.Progressbar(scroll_f, variable=self.p_var, maximum=100)
        self.p_bar.pack(fill="x", padx=15, pady=10)

        # 1. Одиночный режим
        single_f = tk.Frame(scroll_f, bg=COLOR_CARD, padx=20, pady=15, highlightbackground=COLOR_BORDER, highlightthickness=1)
        single_f.pack(fill="x", padx=15, pady=10)
        
        h_s = tk.Frame(single_f, bg=COLOR_CARD)
        h_s.pack(anchor="w", pady=(0, 10))
        tk.Label(h_s, text=LANGUAGES[self.lang]['single_mode'], bg=COLOR_CARD, font=("Segoe UI", 11, "bold")).pack(side="left")
        
        f_p = tk.Frame(single_f, bg=COLOR_CARD)
        f_p.pack(fill="x", pady=5)
        ttk.Entry(f_p, textvariable=self.source_path).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(f_p, text="...", command=lambda: self.browse(self.source_path), bg=COLOR_BORDER, relief="flat", padx=10).pack(side="right", padx=5)
        
        StyledButton(single_f, text=LANGUAGES[self.lang]['btn_run'], command=self.run_single_sorting).pack(fill="x", pady=2)
        
        f_rev = tk.Frame(single_f, bg=COLOR_CARD)
        f_rev.pack(fill="x")
        StyledButton(f_rev, text=LANGUAGES[self.lang]['btn_reverse'], command=self.run_unsorting_single, bg_color=COLOR_SECONDARY, hover_color=COLOR_SECONDARY_HOVER).pack(fill="x", side="left", expand=True)

        # 2. Мульти режим
        multi_f = tk.Frame(scroll_f, bg=COLOR_CARD, padx=20, pady=15, highlightbackground=COLOR_BORDER, highlightthickness=1)
        multi_f.pack(fill="x", padx=15, pady=10)
        
        tk.Label(multi_f, text=LANGUAGES[self.lang]['multi_mode'], bg=COLOR_CARD, font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT).pack(anchor="w", pady=(0, 10))
        
        f_mt = tk.Frame(multi_f, bg=COLOR_CARD)
        f_mt.pack(anchor="w")
        tk.Label(f_mt, text=LANGUAGES[self.lang]['select_target'], bg=COLOR_CARD).pack(side="left")
        
        f_t = tk.Frame(multi_f, bg=COLOR_CARD)
        f_t.pack(fill="x", pady=2)
        ttk.Entry(f_t, textvariable=self.multi_target).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(f_t, text="...", command=lambda: self.browse(self.multi_target, True), bg=COLOR_BORDER, relief="flat", padx=10).pack(side="right", padx=5)
        
        f_ms = tk.Frame(multi_f, bg=COLOR_CARD)
        f_ms.pack(anchor="w", pady=(5,0))
        tk.Label(f_ms, text=LANGUAGES[self.lang]['sources_list'], bg=COLOR_CARD).pack(side="left")
        
        f_list = tk.Frame(multi_f, bg=COLOR_CARD)
        f_list.pack(fill="x", pady=5)
        
        self.src_lb = tk.Listbox(f_list, height=4, bg=COLOR_BG, relief="flat", font=("Segoe UI", 9))
        self.src_lb.pack(side="left", fill="x", expand=True)
        for s in self.multi_sources:
            self.src_lb.insert(tk.END, s)
            
        f_btn = tk.Frame(f_list, bg=COLOR_CARD)
        f_btn.pack(side="right", padx=5)
        StyledButton(f_btn, text="+", command=self.add_src, width=4).pack(pady=2)
        StyledButton(f_btn, text="-", command=self.rem_src, bg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER, width=4).pack()
        
        StyledButton(multi_f, text=LANGUAGES[self.lang]['btn_run'], command=self.run_multi_sorting).pack(fill="x", pady=5)

        # 3. Дубликаты
        dupe_f = tk.Frame(scroll_f, bg=COLOR_CARD, padx=20, pady=15, highlightbackground=COLOR_BORDER, highlightthickness=1)
        dupe_f.pack(fill="x", padx=15, pady=10)
        
        h_d = tk.Frame(dupe_f, bg=COLOR_CARD)
        h_d.pack(anchor="w", pady=(0, 10))
        tk.Label(h_d, text=LANGUAGES[self.lang]['dupe_mode'], bg=COLOR_CARD, font=("Segoe UI", 11, "bold")).pack(side="left")
        
        f_d = tk.Frame(dupe_f, bg=COLOR_CARD)
        f_d.pack(fill="x", pady=5)
        ttk.Entry(f_d, textvariable=self.dupe_folder).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(f_d, text="...", command=lambda: self.browse(self.dupe_folder), bg=COLOR_BORDER, relief="flat", padx=10).pack(side="right", padx=5)
        
        StyledButton(dupe_f, text=LANGUAGES[self.lang]['btn_find_dupes'], command=self.run_dupe_finder).pack(fill="x", pady=5)

        # 4. Фоновый мониторинг
        auto_f = tk.Frame(scroll_f, bg=COLOR_CARD, padx=20, pady=15, highlightbackground="#ffeaa7", highlightthickness=2)
        auto_f.pack(fill="x", padx=15, pady=10)
        
        h_a = tk.Frame(auto_f, bg=COLOR_CARD)
        h_a.pack(anchor="w", pady=(0, 10))
        tk.Label(h_a, text=LANGUAGES[self.lang]['auto_mode'], bg=COLOR_CARD, font=("Segoe UI", 11, "bold"), fg="#e17055").pack(side="left")

        f_a1 = tk.Frame(auto_f, bg=COLOR_CARD)
        f_a1.pack(fill="x", pady=2)
        tk.Label(f_a1, text=LANGUAGES[self.lang]['auto_src'], bg=COLOR_CARD, width=15, anchor="w").pack(side="left")
        ttk.Entry(f_a1, textvariable=self.auto_src).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(f_a1, text="...", command=lambda: self.browse(self.auto_src), bg=COLOR_BORDER, relief="flat", padx=10).pack(side="right", padx=5)

        f_a2 = tk.Frame(auto_f, bg=COLOR_CARD)
        f_a2.pack(fill="x", pady=2)
        tk.Label(f_a2, text=LANGUAGES[self.lang]['select_target'], bg=COLOR_CARD, width=15, anchor="w").pack(side="left")
        ttk.Entry(f_a2, textvariable=self.auto_dst).pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(f_a2, text="...", command=lambda: self.browse(self.auto_dst), bg=COLOR_BORDER, relief="flat", padx=10).pack(side="right", padx=5)

        f_a3 = tk.Frame(auto_f, bg=COLOR_CARD)
        f_a3.pack(fill="x", pady=(10, 0))
        tk.Label(f_a3, text=LANGUAGES[self.lang]['auto_interval'], bg=COLOR_CARD).pack(side="left")
        ttk.Spinbox(f_a3, from_=5, to=3600, textvariable=self.auto_interval, width=8).pack(side="left", padx=5)
        
        cb_auto = tk.Checkbutton(f_a3, text=LANGUAGES[self.lang]['auto_enable'], variable=self.auto_enabled, bg=COLOR_CARD, font=("Segoe UI", 9, "bold"), fg=COLOR_SUCCESS, command=self.toggle_auto_watcher)
        cb_auto.pack(side="right")

        # Режим предпросмотра
        f_pre = tk.Frame(scroll_f, bg=COLOR_BG)
        f_pre.pack(pady=10)
        tk.Checkbutton(f_pre, text=LANGUAGES[self.lang]['preview_mode'], variable=self.preview_mode, bg=COLOR_BG, fg=COLOR_ACCENT, font=("Segoe UI", 9, "bold"), command=self.update_preview_mode).pack(side="left")

    def update_preview_mode(self):
        self.core.config["dry_run"] = self.preview_mode.get()
        self.core.save_config(self.core.config)

    def toggle_auto_watcher(self) -> None:
        self.core.config["monitor_enabled"] = self.auto_enabled.get()
        self.core.config["monitor_folders"] = [self.auto_src.get()] if self.auto_src.get() else []
        self.core.config["monitor_target"] = self.auto_dst.get()
        self.core.config["monitor_interval_sec"] = float(self.auto_interval.get())
        self.core.save_config(self.core.config)
        
        if self.auto_enabled.get():
            messagebox.showwarning(LANGUAGES[self.lang]['beta_warn_title'], LANGUAGES[self.lang]['beta_warn_msg'])

    def browse(self, var: tk.StringVar, multi: bool = False) -> None:
        f = self.get_directory_path("Select Directory")
        if f:
            var.set(f)
            if multi:
                self.core.config["multi_target"] = f
            else:
                self.core.config["last_path"] = f
            self.core.save_config(self.core.config)

    def add_src(self) -> None:
        f = self.get_directory_path("Select Source Directory")
        if f and f not in self.multi_sources:
            self.multi_sources.append(f)
            self.src_lb.insert(tk.END, f)
            self.core.config["multi_sources"] = self.multi_sources
            self.core.save_config(self.core.config)

    def rem_src(self) -> None:
        s = self.src_lb.curselection()
        if s:
            val = self.src_lb.get(s[0])
            self.multi_sources.remove(val)
            self.src_lb.delete(s[0])
            self.core.config["multi_sources"] = self.multi_sources
            self.core.save_config(self.core.config)

    def run_dupe_finder(self) -> None:
        p = self.dupe_folder.get()
        if not p or not os.path.exists(p):
            messagebox.showerror("Error", LANGUAGES[self.lang]['err_path'])
            return
            
        self.p_var.set(0)
        
        def run():
            groups = []
            for event_type, msg in self.core.scan_duplicates_generator(p):
                if event_type == "progress":
                    self.p_var.set(int((msg["current"] / msg["total"]) * 100))
                elif event_type == "dupe_groups":
                    groups = msg
                self.root.update_idletasks()
            
            self.p_var.set(100)
            if not groups:
                messagebox.showinfo("Info", "Дубликаты не найдены / No duplicates found.")
                self.p_var.set(0)
                return
                
            if self.core.config.get("auto_dupes", False):
                messagebox.showinfo(LANGUAGES[self.lang]['success'], LANGUAGES[self.lang]['done'])
                self.p_var.set(0)
                return

            self.root.after(0, lambda: self.show_dupe_selector(groups))

        threading.Thread(target=run, daemon=True).start()

    def show_dupe_selector(self, groups):
        sel = DuplicateSelector(self.root, groups, self.lang)
        self.root.wait_window(sel)
        if sel.to_delete:
            count = 0
            for path in sel.to_delete:
                try:
                    os.remove(path)
                    count += 1
                except Exception:
                    pass
            messagebox.showinfo(LANGUAGES[self.lang]['success'], f"Удалено файлов: {count}")
        self.p_var.set(0)

    def run_single_sorting(self) -> None:
        p = self.source_path.get()
        if os.path.exists(p):
            self.p_var.set(0)
            def run():
                for event_type, msg in self.core.sort_directory_generator(p):
                    if event_type == "progress":
                        self.p_var.set(int((msg["current"] / msg["total"]) * 100))
                    self.root.update_idletasks()
                self.p_var.set(100)
                messagebox.showinfo(LANGUAGES[self.lang]['success'], LANGUAGES[self.lang]['done'])
                self.p_var.set(0)
            threading.Thread(target=run, daemon=True).start()

    def run_multi_sorting(self) -> None:
        t = self.multi_target.get()
        if os.path.exists(t):
            self.p_var.set(0)
            def run():
                srcs = list(self.multi_sources)
                if self.include_target_var.get():
                    srcs.append(t)
                for s in srcs:
                    if os.path.exists(s):
                        for event_type, msg in self.core.sort_directory_generator(s, target_dir=t):
                            if event_type == "progress":
                                self.p_var.set(int((msg["current"] / msg["total"]) * 100))
                            self.root.update_idletasks()
                self.p_var.set(100)
                messagebox.showinfo(LANGUAGES[self.lang]['success'], LANGUAGES[self.lang]['done'])
                self.p_var.set(0)
            threading.Thread(target=run, daemon=True).start()

    def run_unsorting_single(self) -> None:
        p = self.source_path.get()
        if p and os.path.exists(p):
            if not messagebox.askyesno("?", LANGUAGES[self.lang]['confirm_reverse']):
                return
            self.p_var.set(0)
            def run():
                for event_type, msg in self.core.unsort_directory_generator(p):
                    if event_type == "progress":
                        self.p_var.set(int((msg["current"] / msg["total"]) * 100))
                    self.root.update_idletasks()
                self.p_var.set(100)
                messagebox.showinfo(LANGUAGES[self.lang]['success'], LANGUAGES[self.lang]['done'])
                self.p_var.set(0)
            threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    if sys.platform == 'win32':
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
            
    app = FileSorterApp(root)
    root.mainloop()