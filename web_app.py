import os
import subprocess
import sys
import json
import tkinter as tk
from tkinter import filedialog
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_from_directory
from sorter_core import FileSorterCore

# Explicitly set the template folder relative to this file to prevent launch path errors
base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'))
core = FileSorterCore()

# Ensure templates directory exists
templates_dir = os.path.join(base_dir, 'templates')
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

def get_bg_dir():
    """Finds the absolute path to the 'bg' directory, checking multiple fallbacks case-insensitively."""
    # Try current working directory and script directory case-insensitively
    for parent in [os.getcwd(), base_dir]:
        if os.path.exists(parent):
            try:
                for item in os.listdir(parent):
                    if item.lower() == 'bg' and os.path.isdir(os.path.join(parent, item)):
                        return os.path.join(parent, item)
            except Exception:
                pass
    # Default fallback
    dir_script = os.path.join(base_dir, 'bg')
    os.makedirs(dir_script, exist_ok=True)
    return dir_script

@app.route('/logo.ico')
def favicon():
    """Utility route serving the main dashboard favicon icon."""
    return send_from_directory(base_dir, 'logo.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/bg')
def get_custom_bg():
    """Route serving the custom background image safely with multiple path fallbacks."""
    path = request.args.get('path', '')
    if not path:
        path = 'bg.png'
        
    # Normalize path and get base filename
    filename = os.path.basename(path.replace('\\', '/'))
    
    # Directories to search for the background image
    search_dirs = [
        get_bg_dir(),
        os.path.join(base_dir, 'bg'),
        os.path.join(os.getcwd(), 'bg'),
        base_dir,
        os.getcwd()
    ]
    
    for directory in search_dirs:
        if not directory or not os.path.exists(directory):
            continue
        full_path = os.path.join(directory, filename)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return send_from_directory(directory, filename)
            
    # Fallback to root bg.png
    root_bg = os.path.join(base_dir, 'bg.png')
    if os.path.exists(root_bg):
        return send_from_directory(base_dir, 'bg.png')
        
    return '', 404

@app.route('/api/backgrounds', methods=['GET'])
def list_backgrounds():
    """Endpoint listing all background image paths in multiple checked bg directories."""
    allowed_exts = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp')
    files = set()
    try:
        # Scan case-insensitive bg folders in cwd and base_dir
        for parent in [os.getcwd(), base_dir]:
            if not os.path.exists(parent):
                continue
            for item in os.listdir(parent):
                if item.lower() == 'bg':
                    bg_path = os.path.join(parent, item)
                    if os.path.isdir(bg_path):
                        for f in os.listdir(bg_path):
                            if f.lower().endswith(allowed_exts) and os.path.isfile(os.path.join(bg_path, f)):
                                files.add(f"bg/{f}")
        
        # Scan the root folder for default backgrounds like bg.png
        if os.path.exists(base_dir):
            for f in os.listdir(base_dir):
                if f.lower() == 'bg.png' and os.path.isfile(os.path.join(base_dir, f)):
                    files.add(f)
                    
        sorted_files = sorted(list(files))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    return jsonify(sorted_files)

@app.route('/api/backgrounds/upload', methods=['POST'])
def upload_background():
    """Endpoint allowing file upload directly to the 'bg' directory."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    allowed_exts = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp')
    if not file.filename.lower().endswith(allowed_exts):
        return jsonify({"error": "Invalid file type"}), 400
        
    bg_dir = get_bg_dir()
    filename = os.path.basename(file.filename)
    dest_path = os.path.join(bg_dir, filename)
    
    try:
        os.makedirs(bg_dir, exist_ok=True)
        file.save(dest_path)
        return jsonify({"status": "success", "filename": f"bg/{filename}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/backgrounds', methods=['DELETE'])
def delete_background():
    """Endpoint allowing deletion of a background image file from multiple scanned directories."""
    name = request.args.get('name', '')
    if not name:
        return jsonify({"error": "No filename specified"}), 400
        
    filename = os.path.basename(name)
    target_path = None
    
    for parent in [os.path.join(os.getcwd(), 'bg'), os.path.join(base_dir, 'bg'), base_dir]:
        p = os.path.join(parent, filename)
        if os.path.exists(p) and os.path.isfile(p):
            target_path = p
            break
            
    if target_path:
        try:
            os.remove(target_path)
            return jsonify({"status": "deleted"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "File not found"}), 404

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
    """Directory browsing logic supporting both web modal exploration and native OS dialog fallbacks."""
    path = request.args.get('path', '')
    
    if path:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path) and os.path.isdir(abs_path):
            try:
                dirs = []
                for item in os.listdir(abs_path):
                    full_item_path = os.path.join(abs_path, item)
                    if os.path.isdir(full_item_path) and not item.startswith('.'):
                        dirs.append(item)
                
                dirs.sort()
                parent = os.path.dirname(abs_path)
                if parent == abs_path:
                    parent = ""
                    
                return jsonify({
                    "path": abs_path,
                    "parent": parent,
                    "dirs": dirs
                })
            except Exception as e:
                return jsonify({"error": str(e), "path": abs_path, "parent": "", "dirs": []})

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

    return jsonify({
        "path": selected_path,
        "parent": os.path.dirname(selected_path) if selected_path else "",
        "dirs": []
    })

if __name__ == '__main__':
    if sys.platform.startswith('linux'):
        os.environ['TK_SILENCE_DEPRECATION'] = '1'
    print("\nWEB UI: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)