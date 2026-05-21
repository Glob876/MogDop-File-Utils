import os
import sys
import time
import threading
import webbrowser
import importlib.util

# 1. Проверка наличия нужных библиотек
def check_dependencies():
    missing = []
    if importlib.util.find_spec("flask") is None:
        missing.append("flask")
    
    if missing:
        print("ВНИМАНИЕ! Отсутствуют необходимые библиотеки.")
        print(f"Пожалуйста, установите их командой: {sys.executable} -m pip install {' '.join(missing)}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)

# 2. Функция для автоматического открытия браузера
def open_browser():
    # Ждем 1.5 секунды, чтобы Flask успел полностью запуститься
    time.sleep(1.5)
    url = "http://127.0.0.1:5000"
    print(f"\n[+] Открываем браузер по адресу {url} ...\n")
    webbrowser.open(url)

def main():
    print("="*50)
    print(" Инициализация MogDop File Utils (Web Edition) ")
    print("="*50)
    
    check_dependencies()

    # Импортируем приложение Flask из нашего web_app.py
    try:
        from web_app import app
    except ImportError as e:
        print(f"\n[ОШИБКА] Не удалось импортировать web_app.py. Убедитесь, что файл существует.")
        print(f"Детали: {e}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)

    # Запускаем таймер открытия браузера в отдельном потоке (фоновом)
    threading.Thread(target=open_browser, daemon=True).start()

    # Запускаем сам сервер (этот процесс блокирует консоль, поэтому браузер открывается в фоне)
    # use_reloader=False нужен, чтобы сервер не запускался дважды (что вызвало бы два открытия браузера)
    print("[+] Запуск локального сервера...")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)

if __name__ == "__main__":
    main()