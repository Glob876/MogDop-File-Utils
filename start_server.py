import os
import sys
import time
import threading
import webbrowser
import importlib.util

def check_dependencies():
    missing = []
    if importlib.util.find_spec("flask") is None:
        missing.append("flask")
    
    if missing:
        print("ВНИМАНИЕ! Отсутствуют необходимые библиотеки.")
        print(f"Пожалуйста, установите их командой: {sys.executable} -m pip install {' '.join(missing)}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)

def open_browser():
    time.sleep(1.5)
    url = "http://localhost:8080"
    print(f"\n[+] Открываем браузер по адресу {url} ...\n")
    webbrowser.open(url)

def main():
    print("="*50)
    print(" Инициализация MogDop File Utils (Web Edition) ")
    print("="*50)
    
    check_dependencies()

    try:
        from web_app import app
    except ImportError as e:
        print(f"\n[ОШИБКА] Не удалось импортировать web_app.py. Убедитесь, что файл существует.")
        print(f"Детали: {e}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)

    threading.Thread(target=open_browser, daemon=True).start()

    print("[+] Запуск локального сервера...")
    app.run(host='localhost', port=8080, debug=True, use_reloader=False)

if __name__ == "__main__":
    main()