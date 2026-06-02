#!/usr/bin/env python3

import argparse
import sys
import json
import time
from colorama import init, Fore, Back, Style
from sorter_core import FileSorterCore

# Initialize colorama with automatic style reset on each operation
init(autoreset=True)

def main():
    parser = argparse.ArgumentParser(
        description=f"{Fore.CYAN}{Style.BRIGHT}MogDop File Utils - Core Engine CLI{Style.RESET_ALL}\n"
                    f"Консольный инструмент для автоматической сортировки, извлечения и поиска дубликатов файлов.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Fore.YELLOW}Примеры использования:{Style.RESET_ALL}
  {Fore.GREEN}1. Простая сортировка файлов в папке:{Style.RESET_ALL}
     python cli_main.py single -p /path/to/folder --date-sort

  {Fore.GREEN}2. Поиск и автоматическое удаление дубликатов:{Style.RESET_ALL}
     python cli_main.py dupes -p /path/to/folder --auto-dupes

  {Fore.GREEN}3. Возврат файлов в исходное состояние (рассортировка):{Style.RESET_ALL}
     python cli_main.py unsort -p /path/to/folder --clean-empty

  {Fore.GREEN}4. Сортировка из нескольких папок в одну общую целевую папку:{Style.RESET_ALL}
     python cli_main.py multi -s /src1 /src2 -t /target_folder

  {Fore.GREEN}5. Постоянный фоновый мониторинг каталогов в реальном времени (BETA):{Style.RESET_ALL}
     python cli_main.py monitor -s /src1 /src2 -t /target_folder
"""
    )
    
    # Mode configurations
    mode_group = parser.add_argument_group(f"{Fore.MAGENTA}Режимы работы (выберите один){Style.RESET_ALL}")
    mode_group.add_argument("mode", choices=["single", "multi", "unsort", "dupes", "monitor"], 
                        help="Режим работы программы")
    
    # Path configuration group
    path_group = parser.add_argument_group(f"{Fore.MAGENTA}Настройка путей{Style.RESET_ALL}")
    path_group.add_argument("-p", "--path", type=str, metavar="PATH",
                        help="Путь к целевой папке (для режимов 'single', 'unsort', 'dupes' и 'monitor')")
    path_group.add_argument("-t", "--target", type=str, metavar="TARGET",
                        help="Путь к результирующей папке (для режимов 'multi' и 'monitor')")
    path_group.add_argument("-s", "--sources", type=str, nargs="+", metavar="SOURCES",
                        help="Список исходных папок через пробел (для режимов 'multi' и 'monitor')")
    
    # Engine option attributes
    config_group = parser.add_argument_group(f"{Fore.MAGENTA}Параметры сортировки{Style.RESET_ALL}")
    config_group.add_argument("--date-sort", action="store_true", 
                              help="Дополнительно сортировать файлы во вложенные папки Год/Месяц")
    config_group.add_argument("--clean-empty", action="store_true", 
                              help="Удалять пустые папки после перемещения файлов")
    config_group.add_argument("--overwrite", action="store_true", 
                              help="Перезаписывать файлы с одинаковыми именами в целевой папке")
    config_group.add_argument("--auto-dupes", action="store_true", 
                              help="Автоматически удалять найденные дубликаты без подтверждения")
    config_group.add_argument("--ignore-unknown", action="store_true", 
                              help="Не перемещать файлы с неизвестными расширениями (оставлять на месте)")
    config_group.add_argument("--interval", type=float, default=5.0,
                              help="Интервал проверки в секундах для режима 'monitor' (по умолчанию: 5)")
    
    # Print usage statistics if executed empty
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
        
    args = parser.parse_args()
    
    # Initialize Core sorter engine
    core = FileSorterCore()
    
    # Synchronize script arguments with configuration dictionary
    if args.date_sort: core.config['date_sort'] = True
    if args.clean_empty: core.config['clean_empty'] = True
    if args.overwrite: core.config['overwrite'] = True
    if args.auto_dupes: core.config['auto_dupes'] = True
    if args.ignore_unknown: core.config['move_unknown'] = False

    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}=== MogDop File Utils CLI ==={Style.RESET_ALL}")
    
    def process_generator(generator):
        """Displays core step outputs alongside terminal color schemes."""
        last_was_progress = False
        
        for e_type, msg in generator:
            if e_type == "progress":
                percent = int((msg["current"] / msg["total"]) * 100) if msg["total"] > 0 else 100
                sys.stdout.write(f"\r{Fore.CYAN}[PROGRESS] {percent}% ({msg['current']}/{msg['total']}){Style.RESET_ALL}     ")
                sys.stdout.flush()
                last_was_progress = True
            elif e_type == "dupe_groups":
                if last_was_progress:
                    print()
                    last_was_progress = False
                print(f"\n{Fore.YELLOW}{Style.BRIGHT}[DUPLICATES FOUND]{Style.RESET_ALL}")
                for i, group in enumerate(msg):
                    print(f"  {Fore.CYAN}Группа {i+1}{Style.RESET_ALL} ({len(group)} файлов):")
                    for fp in group:
                        print(f"    - {Fore.WHITE}{fp}{Style.RESET_ALL}")
                print(f"\nЗапустите с флагом {Fore.GREEN}--auto-dupes{Style.RESET_ALL} для автоматического удаления копий.")
            else:
                if last_was_progress:
                    print()  # Reset line output
                    last_was_progress = False
                
                # Assign terminal coloration mappings based on core step
                if e_type == "error":
                    color_prefix = f"{Fore.RED}{Style.BRIGHT}[ERROR]{Style.RESET_ALL} {Fore.RED}"
                elif e_type == "success":
                    color_prefix = f"{Fore.GREEN}{Style.BRIGHT}[SUCCESS]{Style.RESET_ALL} {Fore.GREEN}"
                elif e_type == "conflict":
                    color_prefix = f"{Fore.YELLOW}{Style.BRIGHT}[CONFLICT]{Style.RESET_ALL} {Fore.YELLOW}"
                elif e_type == "skip":
                    color_prefix = f"{Style.DIM}[SKIP] "
                elif e_type == "move":
                    color_prefix = f"{Fore.GREEN}[MOVE] "
                else:  # Information details
                    color_prefix = f"{Fore.CYAN}[INFO] "
                
                print(f"{color_prefix}{msg}{Style.RESET_ALL}")

    # Process mode routing choices
    if args.mode == "single":
        if not args.path:
            print(f"{Fore.RED}[ERROR] Аргумент --path (-p) обязателен для режима single.{Style.RESET_ALL}")
            return
        process_generator(core.sort_directory_generator(args.path))
        
    elif args.mode == "unsort":
        if not args.path:
            print(f"{Fore.RED}[ERROR] Аргумент --path (-p) обязателен для режима unsort.{Style.RESET_ALL}")
            return
        process_generator(core.unsort_directory_generator(args.path))
        
    elif args.mode == "dupes":
        if not args.path:
            print(f"{Fore.RED}[ERROR] Аргумент --path (-p) обязателен для режима dupes.{Style.RESET_ALL}")
            return
        process_generator(core.scan_duplicates_generator(args.path))
        
    elif args.mode == "multi":
        if not args.target or not args.sources:
            print(f"{Fore.RED}[ERROR] Оба аргумента --target (-t) и --sources (-s) обязательны для режима multi.{Style.RESET_ALL}")
            return
        
        print(f"{Fore.CYAN}[INFO] Целевая папка для объединения: {args.target}{Style.RESET_ALL}")
        for src in args.sources:
            print(f"\n{Fore.YELLOW}--- Обработка источника: {src} ---{Style.RESET_ALL}")
            process_generator(core.sort_directory_generator(src, target_dir=args.target))
            
    elif args.mode == "monitor":
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}[ВНИМАНИЕ] Функция автоматического мониторинга папок запущена в режиме BETA! Пожалуйста, сделайте резервную копию важных файлов.{Style.RESET_ALL}")
        
        # Build collection of monitoring paths
        monitor_paths = []
        if args.path:
            monitor_paths.append(args.path)
        if args.sources:
            monitor_paths.extend(args.sources)
            
        if not monitor_paths:
            print(f"{Fore.RED}[ERROR] Пожалуйста, укажите хотя бы одну папку для отслеживания через --path (-p) или --sources (-s).{Style.RESET_ALL}")
            return
            
        target_dir = args.target if args.target else None
        target_msg = target_dir if target_dir else "на месте (in-place)"
        
        print(f"{Fore.CYAN}[INFO] Запуск мониторинга в реальном времени: {', '.join(monitor_paths)} (Интервал: {args.interval}с, Направление: {target_msg})")
        print(f"{Fore.CYAN}[INFO] Нажмите Ctrl+C для завершения.{Style.RESET_ALL}")
        
        try:
            while True:
                for src in monitor_paths:
                    for event_type, msg in core.sort_directory_generator(src, target_dir=target_dir):
                        if event_type == "move":
                            print(f"{Fore.GREEN}[MONITOR ACTION] {msg}{Style.RESET_ALL}")
                        elif event_type == "error":
                            print(f"{Fore.RED}[MONITOR ERROR] {msg}{Style.RESET_ALL}")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print(f"\n{Fore.CYAN}[INFO] Мониторинг остановлен.{Style.RESET_ALL}")
            
    print(f"\n{Fore.MAGENTA}============================={Style.RESET_ALL}")

if __name__ == "__main__":
    main()