import os
import shutil
import json
import hashlib
from datetime import datetime

MONTHS_EN = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
}

class FileSorterCore:
    def __init__(self, config_path="sorter_config.json"):
        self.config_path = config_path
        self.defaults = {
            "extensions": {
                'Images': '.jpg,.jpeg,.png,.gif,.bmp,.svg,.webp,.tiff,.ico',
                'Documents': '.pdf,.doc,.docx,.txt,.xlsx,.pptx,.csv,.odt,.rtf',
                'Video': '.mp4,.mkv,.avi,.mov,.webm,.flv,.wmv',
                'Music': '.mp3,.wav,.flac,.aac,.ogg,.m4a',
                'Archives': '.zip,.rar,.7z,.tar,.tar.xz,.gz,.bz2,.xz',
                'Programming': '.py,.html,.css,.js,.cpp,.c,.h,.java,.php,.json,.xml,.sb3,.rb,.go,.rs,.swift',
                'System': '.exe,.msi,.deb,.run,.appimage,.sh,.bat,.com'
            },
            "move_unknown": True,
            "date_sort": False,
            "clean_empty": True,
            "overwrite": False,
            "auto_dupes": False,
            "include_target_root": False,
            "excluded_files": "sorter_config.json,sorter_log.txt",
            "multi_sources": [],
            "multi_target": "",
            "last_path": ""
        }
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return {**self.defaults, **json.load(f)}
            except:
                return self.defaults
        return self.defaults

    def save_config(self, new_config):
        self.config.update(new_config)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get_file_hash(self, filepath):
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

    def _clean_empty_folders(self, path):
        for root, dirs, _ in os.walk(path, topdown=False):
            for d in dirs:
                dp = os.path.join(root, d)
                try: 
                    if not os.listdir(dp): os.rmdir(dp)
                except: pass

    # --- 1. SORTING (Single & Multi) ---
    def sort_directory_generator(self, src_dir, target_dir=None):
        if not target_dir: target_dir = src_dir
        if not os.path.exists(src_dir):
            yield "error", f"Specified path does not exist: {src_dir}"
            return
            
        yield "info", f"Analyzing directory: {src_dir}"
        
        try:
            files = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))]
        except Exception as e:
            yield "error", f"Failed to read directory: {str(e)}"
            return

        total = len(files)
        if total == 0:
            yield "skip", f"No files to sort in: {src_dir}"
            return

        count = 0
        excl = [x.strip().lower() for x in self.config.get("excluded_files", "").split(",") if x.strip()]
        
        for index, f in enumerate(files):
            yield "progress", {"current": index + 1, "total": total}
            
            if f.lower() in excl or f in ["sorter_config.json", "sorter_log.txt"]:
                yield "skip", f"Skipped (in exceptions): {f}"
                continue
                
            src_path = os.path.join(src_dir, f)
            ext = os.path.splitext(f)[1].lower()
            
            category = None
            for cat, exts in self.config["extensions"].items():
                if ext in [e.strip().lower() for e in exts.split(',') if e.strip()]:
                    category = cat; break
            
            if not category and self.config["move_unknown"]:
                category = "Other"
            
            if not category:
                yield "skip", f"Category not found, file left intact: {f}"
                continue

            dest_dir = os.path.join(target_dir, category)
            if self.config["date_sort"]:
                dt = datetime.fromtimestamp(os.path.getmtime(src_path))
                m_name = MONTHS_EN.get(dt.month, "Unknown")
                dest_dir = os.path.join(dest_dir, str(dt.year), m_name)
            
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, f)
            
            if os.path.exists(dest_path):
                if self.config["overwrite"]:
                    try: os.remove(dest_path)
                    except: pass
                else:
                    n, e = os.path.splitext(f)
                    dest_path = os.path.join(dest_dir, f"{n}_{datetime.now().strftime('%H%M%S')}{e}")
                    yield "conflict", f"Name conflict. Renamed to {os.path.basename(dest_path)}"

            try:
                shutil.move(src_path, dest_path)
                count += 1
                yield "move", f"Moved: {f} -> {category}"
            except Exception as e:
                yield "error", f"Move error for {f}: {str(e)}"
        
        if self.config["clean_empty"]:
            self._clean_empty_folders(src_dir)
            
        yield "success", f"Processing completed for {src_dir}! Moved: {count} files"

    # --- 2. REVERSE SORTING (Unsort) ---
    def unsort_directory_generator(self, target_dir):
        if not target_dir or not os.path.exists(target_dir):
            yield "error", "Specified path not found!"
            return

        yield "info", f"Starting reverse sorting (extraction) for: {target_dir}"
        all_files = []
        cats = list(self.config["extensions"].keys()) + ["Other"]
        
        for c in cats:
            cp = os.path.join(target_dir, c)
            if os.path.isdir(cp):
                for r, _, fs in os.walk(cp):
                    for f in fs: 
                        all_files.append(os.path.join(r, f))
                        
        total = len(all_files)
        yield "info", f"Found files in categories: {total}"
        if total == 0:
            yield "success", "No files to extract."
            return

        count = 0
        for i, fp in enumerate(all_files):
            yield "progress", {"current": i + 1, "total": total}
            fname = os.path.basename(fp)
            dst = os.path.join(target_dir, fname)
            
            if os.path.exists(dst):
                n, e = os.path.splitext(fname)
                dst = os.path.join(target_dir, f"{n}_old_{datetime.now().strftime('%H%M%S')}{e}")
                yield "conflict", f"Conflict. Renamed to: {os.path.basename(dst)}"
                
            try:
                shutil.move(fp, dst)
                count += 1
                yield "move", f"Extracted: {fname}"
            except Exception as e:
                yield "error", f"Extraction error for {fname}: {str(e)}"

        if self.config["clean_empty"]:
            yield "info", "Cleaning up empty category folders..."
            self._clean_empty_folders(target_dir)

        yield "success", f"Reverse sorting completed! Extracted files: {count}"

    # --- 3. DUPLICATE FINDER ---
    def scan_duplicates_generator(self, path):
        if not path or not os.path.exists(path):
            yield "error", "Specified path not found!"
            return
            
        yield "info", f"Scanning for duplicates in: {path}"
        all_files = []
        for root_dir, _, files in os.walk(path):
            for f in files: 
                all_files.append(os.path.join(root_dir, f))
                
        total = len(all_files)
        yield "info", f"Files to analyze: {total}"
        if total == 0:
            yield "success", "Directory is empty."
            return

        hashes = {}
        for i, fp in enumerate(all_files):
            if i % max(1, total // 100) == 0:
                yield "progress", {"current": i + 1, "total": total}
            h = self.get_file_hash(fp)
            if h: hashes.setdefault(h, []).append(fp)

        groups = [ps for ps in hashes.values() if len(ps) > 1]
        
        if not groups:
            yield "success", "No duplicates found."
            return

        if self.config.get("auto_dupes", False):
            to_del = []
            for g in groups: to_del.extend(g[1:])
            yield "info", f"Found {len(to_del)} duplicates. Starting auto-deletion..."
            count = 0
            for i, p in enumerate(to_del):
                try:
                    os.remove(p)
                    count += 1
                    yield "move", f"Deleted duplicate: {p}"
                except Exception as e:
                    yield "error", f"Deletion error: {str(e)}"
                if i % 5 == 0:
                    yield "progress", {"current": i + 1, "total": len(to_del)}
            yield "success", f"Auto-deletion completed. Destroyed: {count}"
        else:
            yield "progress", {"current": total, "total": total}
            yield "dupe_groups", groups
            yield "info", "Waiting for user selection to delete..."