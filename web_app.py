import os
import subprocess
import sys
import json
import tkinter as tk
from tkinter import filedialog
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_from_directory
from sorter_core import FileSorterCore

app = Flask(__name__)
core = FileSorterCore()

if not os.path.exists('templates'):
    os.makedirs('templates')

@app.route('/logo.ico')
def favicon():
    """Utility route serving the main dashboard favicon icon."""
    return send_from_directory(os.path.abspath('.'), 'logo.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/bg')
def get_custom_bg():
    """Route serving the custom background image safely."""
    path = request.args.get('path', 'bg.png')
    if not path:
        path = 'bg.png'
        
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path) and os.path.isfile(abs_path):
        return send_from_directory(os.path.dirname(abs_path), os.path.basename(abs_path))
        
    if os.path.exists('bg.png'):
        return send_from_directory(os.path.abspath('.'), 'bg.png')
        
    return '', 404

@app.route('/api/stream')
def stream_action():
    """Main SSE stream route for all functions."""
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
                    yield "error", "Target folder not specified!"
                    return
                    
                for src in sources:
                    yield from core.sort_directory_generator(src, target_dir=target)
                    
                yield "success", "Multi-source sorting fully completed!"
                
        except Exception as e:
            yield "error", f"Critical error: {str(e)}"

    def format_sse(gen):
        for event_type, message in gen:
            yield f"data: {json.dumps({'type': event_type, 'message': message}, ensure_ascii=False)}\n\n"

    return Response(stream_with_context(format_sse(event_generator())), content_type='text/event-stream')

@app.route('/api/dupes/delete', methods=['POST'])
def delete_dupes():
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
    mode = request.args.get('mode', 'dir')
    selected_path = ""
    if sys.platform.startswith('linux'):
        try:
            cmd = ['zenity', '--file-selection']
            if mode == 'dir':
                cmd.append('--directory')
            cmd.append('--title=Select File' if mode == 'file' else '--title=Select Folder')
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                selected_path = proc.stdout.strip()
        except: pass

    if not selected_path:
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            if mode == 'file':
                selected_path = filedialog.askopenfilename(
                    title="Select Background Image",
                    filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.gif"), ("All files", "*.*")]
                )
            else:
                selected_path = filedialog.askdirectory(title="Select Folder")
            root.destroy()
        except Exception as e:
            return jsonify({"error": str(e), "path": ""})

    return jsonify({"path": selected_path})

if __name__ == '__main__':
    if sys.platform.startswith('linux'):
        os.environ['TK_SILENCE_DEPRECATION'] = '1'
    print("\nWEB UI: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)