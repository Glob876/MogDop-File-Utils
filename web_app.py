import os
import subprocess
import sys
import json
import tkinter as tk
from tkinter import filedialog
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from sorter_core import FileSorterCore

app = Flask(__name__)
core = FileSorterCore()

if not os.path.exists('templates'):
    os.makedirs('templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stream')
def stream_action():
    """Главный роут потоковой передачи (SSE) для всех функций"""
    action = request.args.get('action')
    path = request.args.get('path', '')
    
    def event_generator():
        try:
            if action == 'single':
                yield from core.sort_directory_generator(path)
            elif action == 'unsort':
                yield from core.unsort_directory_generator(path)
            elif action == 'scan_dupes':
                yield from core.scan_duplicates_generator(path)
            elif action == 'multi':
                target = request.args.get('target', '')
                sources_str = request.args.get('sources', '[]')
                sources = json.loads(sources_str)
                incl = request.args.get('include_target', 'false') == 'true'
                
                if incl and target not in sources:
                    sources.append(target)
                    
                if not target:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Целевая папка не указана!'})}\n\n"
                    return
                    
                for src in sources:
                    yield from core.sort_directory_generator(src, target_dir=target)
                    
                yield "success", "Мульти-сортировка полностью завершена!"
                
        except Exception as e:
            yield "error", f"Критическая ошибка: {str(e)}"

    # Вспомогательная обертка для JSON
    def format_sse(gen):
        for event_type, message in gen:
            yield f"data: {json.dumps({'type': event_type, 'message': message}, ensure_ascii=False)}\n\n"

    return Response(stream_with_context(format_sse(event_generator())), content_type='text/event-stream')

@app.route('/api/dupes/delete', methods=['POST'])
def delete_dupes():
    """Обработка ручного выбора файлов на удаление"""
    files = request.json.get('files', [])
    count = 0
    for f in files:
        try:
            os.remove(f)
            count += 1
        except:
            pass
    return jsonify({"status": "success", "count": count})

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        core.save_config(request.json)
        return jsonify({"status": "saved"})
    return jsonify(core.config)

@app.route('/api/browse', methods=['GET'])
def browse():
    selected_path = ""
    if sys.platform.startswith('linux'):
        try:
            proc = subprocess.run(['zenity', '--file-selection', '--directory', '--title=Выберите папку'],
                                 capture_output=True, text=True)
            if proc.returncode == 0:
                selected_path = proc.stdout.strip()
        except: pass

    if not selected_path:
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            selected_path = filedialog.askdirectory()
            root.destroy()
        except Exception as e:
            return jsonify({"error": str(e), "path": ""})

    return jsonify({"path": selected_path})

if __name__ == '__main__':
    if sys.platform.startswith('linux'):
        os.environ['TK_SILENCE_DEPRECATION'] = '1'
    print("\nWEB UI: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)