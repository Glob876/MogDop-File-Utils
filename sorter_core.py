import os
import shutil
import json
import hashlib
from datetime import datetime
import threading
import time
import re
import subprocess

MONTHS_EN = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
}

class FileSorterCore:
    def __init__(self, config_path="sorter_config.json"):
        self.config_path = config_path
        self.config_lock = threading.Lock()
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
            "excluded_files": "sorter_config.json,sorter_log.txt,sorter_history.json",
            "multi_sources": [],
            "multi_target": "",
            "last_path": "",
            "dry_run": False,
            "ignore_hidden": True,
            "min_size_mb": 0.0,
            "max_size_mb": 0.0,
            "monitor_enabled": False,
            "monitor_folders": [],
            "monitor_interval_sec": 5.0,
            "monitor_target": "",
            "recursive_sort": False,
            "custom_rules": {},
            "enable_logging": True,
            "log_file_path": "sorter_log.txt",
            "history_file": "sorter_history.json",
            "fast_hash_large_files": True
        }
        self.config = self.load_config()

        self.monitor_thread = None
        self.monitor_stop_event = threading.Event()

        if self.config.get("monitor_enabled", False):
            self.start_monitoring()

    def load_config(self):
        with self.config_lock:
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        return {**self.defaults, **json.load(f)}
                except Exception:
                    return self.defaults.copy()
            return self.defaults.copy()

    def save_config(self, new_config):
        with self.config_lock:
            old_enabled = self.config.get("monitor_enabled", False)
            self.config.update(new_config)
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
            except Exception:
                pass
        
        new_enabled = new_config.get("monitor_enabled", False)
        if new_enabled and not old_enabled:
            self.start_monitoring()
        elif not new_enabled and old_enabled:
            self.stop_monitoring()

    def start_monitoring(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        self.monitor_stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        self.monitor_stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            self.monitor_thread = None

    def _monitor_loop(self):
        while not self.monitor_stop_event.is_set():
            with self.config_lock:
                enabled = self.config.get("monitor_enabled", False)
                folders = list(self.config.get("monitor_folders", []))
                target = self.config.get("monitor_target", "")
                interval = float(self.config.get("monitor_interval_sec", 5.0))

            if not enabled:
                time.sleep(1.0)
                continue

            if interval < 1.0:
                interval = 1.0

            if folders:
                for folder in folders:
                    if os.path.exists(folder):
                        dest = target if target else folder
                        try:
                            for _ in self.sort_directory_generator(folder, target_dir=dest):
                                pass
                        except Exception:
                            pass

            steps = max(1, int(interval))
            for _ in range(steps):
                if self.monitor_stop_event.is_set():
                    break
                time.sleep(interval / steps)

    def get_file_hash(self, filepath):
        hasher = hashlib.md5()
        try:
            size = os.path.getsize(filepath)
            with self.config_lock:
                fast_hash = self.config.get("fast_hash_large_files", True)

            if fast_hash and size > 100 * 1024 * 1024:
                with open(filepath, 'rb') as f:
                    hasher.update(f.read(1024 * 1024))
                    f.seek(-1024 * 1024, 2)
                    hasher.update(f.read(1024 * 1024))
                hasher.update(str(size).encode())
                return hasher.hexdigest()
            else:
                with open(filepath, 'rb') as f:
                    for chunk in iter(lambda: f.read(131072), b""):
                        hasher.update(chunk)
                return hasher.hexdigest()
        except (OSError, PermissionError):
            return None

    def _clean_empty_folders(self, path):
        with self.config_lock:
            ignore_hidden = self.config.get("ignore_hidden", True)
        for root, dirs, _ in os.walk(path, topdown=False):
            for d in dirs:
                if ignore_hidden and d.startswith('.'):
                    continue
                dp = os.path.join(root, d)
                try: 
                    if not os.listdir(dp): 
                        os.rmdir(dp)
                except Exception: 
                    pass

    def _is_size_allowed(self, filepath):
        try:
            with self.config_lock:
                min_size = float(self.config.get("min_size_mb", 0.0))
                max_size = float(self.config.get("max_size_mb", 0.0))

            if min_size <= 0.0 and max_size <= 0.0:
                return True

            sz_bytes = os.path.getsize(filepath)
            sz_mb = sz_bytes / 1048576.0

            if min_size > 0.0 and sz_mb < min_size:
                return False
            if max_size > 0.0 and sz_mb > max_size:
                return False
            return True
        except (OSError, PermissionError, ValueError):
            return False

    def _write_log(self, message):
        with self.config_lock:
            enabled = self.config.get("enable_logging", True)
            log_path = self.config.get("log_file_path", "sorter_log.txt")
        if not enabled:
            return
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass

    def _save_history(self, history_data):
        with self.config_lock:
            h_file = self.config.get("history_file", "sorter_history.json")
        try:
            with open(h_file, "w", encoding="utf-8") as f:
                json.dump(history_data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def _load_history(self):
        with self.config_lock:
            h_file = self.config.get("history_file", "sorter_history.json")
        if os.path.exists(h_file):
            try:
                with open(h_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def sort_directory_generator(self, src_dir, target_dir=None):
        if not target_dir: 
            target_dir = src_dir
        if not os.path.exists(src_dir):
            yield "error", f"Specified path does not exist: {src_dir}"
            return
            
        with self.config_lock:
            dry_run_mode = self.config.get("dry_run", False)
            ignore_hidden = self.config.get("ignore_hidden", True)
            overwrite = self.config.get("overwrite", False)
            date_sort = self.config.get("date_sort", False)
            move_unknown = self.config.get("move_unknown", True)
            clean_empty = self.config.get("clean_empty", True)
            recursive_sort = self.config.get("recursive_sort", False)
            excluded_files_raw = self.config.get("excluded_files", "")
            extensions_config = self.config.get("extensions", {}).copy()
            custom_rules_config = self.config.get("custom_rules", {}).copy()
            
        prefix = "[SIMULATION] " if dry_run_mode else ""
        
        yield "info", f"{prefix}Analyzing directory: {src_dir}"
        self._write_log(f"Starting sort process in {src_dir} (recursive: {recursive_sort})")
        
        excl = {x.strip().lower() for x in excluded_files_raw.split(",") if x.strip()}
        excl.add("sorter_config.json")
        excl.add("sorter_log.txt")
        excl.add("sorter_history.json")

        ext_to_category = {}
        for cat, exts in extensions_config.items():
            for e in exts.split(','):
                clean_ext = e.strip().lower()
                if clean_ext:
                    if not clean_ext.startswith('.'):
                        clean_ext = '.' + clean_ext
                    ext_to_category[clean_ext] = cat

        custom_rules = []
        for pattern, cat in custom_rules_config.items():
            try:
                custom_rules.append((re.compile(pattern, re.IGNORECASE), cat))
            except Exception as e:
                yield "info", f"Skipping invalid custom regex pattern '{pattern}': {str(e)}"

        files_to_process = []
        abs_target_dir = os.path.abspath(target_dir)
        abs_src_dir = os.path.abspath(src_dir)

        if recursive_sort:
            for root, dirs, files in os.walk(src_dir):
                abs_root = os.path.abspath(root)
                if abs_root.startswith(abs_target_dir) and abs_root != abs_src_dir:
                    continue
                if ignore_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                for f in files:
                    if ignore_hidden and f.startswith('.'):
                        continue
                    if f.lower() in excl:
                        continue
                    src_path = os.path.join(root, f)
                    if not os.path.isfile(src_path):
                        continue
                    if not self._is_size_allowed(src_path):
                        continue
                    files_to_process.append((f, src_path))
        else:
            try:
                raw_files = os.listdir(src_dir)
                for f in raw_files:
                    if ignore_hidden and f.startswith('.'):
                        continue
                    if f.lower() in excl:
                        continue
                    src_path = os.path.join(src_dir, f)
                    if not os.path.isfile(src_path):
                        continue
                    if not self._is_size_allowed(src_path):
                        continue
                    files_to_process.append((f, src_path))
            except Exception as e:
                yield "error", f"Failed to read directory: {str(e)}"
                return

        total = len(files_to_process)
        if total == 0:
            yield "skip", f"No files to sort in: {src_dir}"
            yield "success", f"No files to sort in: {src_dir}"
            self._write_log(f"Sort process completed: No files found in {src_dir}")
            return

        count = 0
        session_history = []
        for index, (f, src_path) in enumerate(files_to_process):
            yield "progress", {"current": index + 1, "total": total}

            ext = os.path.splitext(f)[1].lower()
            category = None
            for regex, cat in custom_rules:
                if regex.search(f):
                    category = cat
                    break
            
            if not category:
                category = ext_to_category.get(ext)
            
            if not category and move_unknown:
                category = "Other"
            
            if not category:
                yield "skip", f"Category not found, file left intact: {f}"
                continue

            dest_dir = os.path.join(target_dir, category)
            if date_sort:
                try:
                    dt = datetime.fromtimestamp(os.path.getmtime(src_path))
                    m_name = MONTHS_EN.get(dt.month, "Unknown")
                    dest_dir = os.path.join(dest_dir, str(dt.year), m_name)
                except Exception:
                    pass
            
            dest_path = os.path.join(dest_dir, f)
            
            if os.path.exists(dest_path):
                if overwrite:
                    if not dry_run_mode:
                        try: 
                            os.remove(dest_path)
                        except Exception: 
                            pass
                else:
                    n, e = os.path.splitext(f)
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(dest_dir, f"{n}_{counter}{e}")
                        counter += 1
                    yield "conflict", f"{prefix}Name conflict. Target will be renamed to {os.path.basename(dest_path)}"

            try:
                if not dry_run_mode:
                    os.makedirs(dest_dir, exist_ok=True)
                    shutil.move(src_path, dest_path)
                    session_history.append({"src": src_path, "dst": dest_path})
                count += 1
                yield "move", f"{prefix}Processed: {f} -> {category}"
                self._write_log(f"{prefix}Moved: {src_path} -> {dest_path}")
            except Exception as e:
                yield "error", f"Move error for {f}: {str(e)}"
                self._write_log(f"Error moving {src_path} to {dest_path}: {str(e)}")
        
        if not dry_run_mode and session_history:
            self._save_history(session_history)

        if clean_empty and not dry_run_mode:
            self._clean_empty_folders(src_dir)
            
        yield "success", f"{prefix}Processing completed for {src_dir}! Actions: {count} files"
        self._write_log(f"{prefix}Sort process completed for {src_dir}. Moved {count} files.")

    def unsort_directory_generator(self, target_dir):
        if not target_dir or not os.path.exists(target_dir):
            yield "error", "Specified path not found!"
            return

        with self.config_lock:
            dry_run_mode = self.config.get("dry_run", False)
            ignore_hidden = self.config.get("ignore_hidden", True)
            clean_empty = self.config.get("clean_empty", True)
            extensions_config = self.config.get("extensions", {}).copy()
            
        prefix = "[SIMULATION] " if dry_run_mode else ""

        yield "info", f"{prefix}Starting reverse sorting (extraction) for: {target_dir}"
        self._write_log(f"Starting unsort process in {target_dir}")
        all_files = []
        cats = list(extensions_config.keys()) + ["Other"]
        
        for c in cats:
            cp = os.path.join(target_dir, c)
            if os.path.isdir(cp):
                for r, dirs, fs in os.walk(cp):
                    if ignore_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                    for f in fs: 
                        if ignore_hidden and f.startswith('.'):
                            continue
                        all_files.append(os.path.join(r, f))
                        
        total = len(all_files)
        yield "info", f"Found files in categories: {total}"
        if total == 0:
            yield "success", "No files to extract."
            self._write_log("Unsort completed: No files to extract.")
            return

        count = 0
        for i, fp in enumerate(all_files):
            yield "progress", {"current": i + 1, "total": total}
            fname = os.path.basename(fp)
            dst = os.path.join(target_dir, fname)
            
            if os.path.exists(dst):
                n, e = os.path.splitext(fname)
                counter = 1
                while os.path.exists(dst):
                    dst = os.path.join(target_dir, f"{n}_old_{counter}{e}")
                    counter += 1
                yield "conflict", f"{prefix}Conflict. Target will be renamed to: {os.path.basename(dst)}"
                
            try:
                if not dry_run_mode:
                    shutil.move(fp, dst)
                count += 1
                yield "move", f"{prefix}Extracted: {fname}"
                self._write_log(f"{prefix}Extracted: {fp} -> {dst}")
            except Exception as e:
                yield "error", f"Extraction error for {fname}: {str(e)}"
                self._write_log(f"Error extracting {fp} to {dst}: {str(e)}")

        if clean_empty and not dry_run_mode:
            yield "info", "Cleaning up empty category folders..."
            self._clean_empty_folders(target_dir)

        yield "success", f"{prefix}Reverse sorting completed! Processed files: {count}"
        self._write_log(f"{prefix}Unsort completed. Extracted {count} files.")

    def scan_duplicates_generator(self, path):
        if not path or not os.path.exists(path):
            yield "error", "Specified path not found!"
            return
            
        yield "info", f"Scanning for duplicates in: {path}"
        self._write_log(f"Starting duplicate scan in {path}")
        with self.config_lock:
            ignore_hidden = self.config.get("ignore_hidden", True)
            auto_dupes = self.config.get("auto_dupes", False)
        
        size_groups = {}
        for root_dir, dirs, files in os.walk(path):
            if ignore_hidden:
                dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if ignore_hidden and f.startswith('.'):
                    continue
                fp = os.path.join(root_dir, f)
                try:
                    sz = os.path.getsize(fp)
                    size_groups.setdefault(sz, []).append(fp)
                except (OSError, PermissionError):
                    continue
                    
        potential_files = []
        for sz, paths in size_groups.items():
            if len(paths) > 1:
                potential_files.extend(paths)
                
        total = len(potential_files)
        yield "info", f"Analyzing potential duplicates: {total} candidates matching sizes"
        
        if total == 0:
            yield "success", "No duplicate file sizes found."
            self._write_log("Duplicate scan completed: No duplicate sizes found.")
            return

        hashes = {}
        for i, fp in enumerate(potential_files):
            yield "progress", {"current": i + 1, "total": total}
            h = self.get_file_hash(fp)
            if h: 
                hashes.setdefault(h, []).append(fp)

        groups = [ps for ps in hashes.values() if len(ps) > 1]
        
        if not groups:
            yield "success", "No absolute duplicates found."
            self._write_log("Duplicate scan completed: No absolute duplicates found.")
            return

        if auto_dupes:
            to_del = []
            for g in groups: 
                to_del.extend(g[1:])
            yield "info", f"Found {len(to_del)} duplicates. Starting auto-deletion..."
            count = 0
            for i, p in enumerate(to_del):
                try:
                    os.remove(p)
                    count += 1
                    yield "move", f"Deleted duplicate: {p}"
                    self._write_log(f"Deleted duplicate file: {p}")
                except Exception as e:
                    yield "error", f"Deletion error: {str(e)}"
                    self._write_log(f"Error deleting duplicate {p}: {str(e)}")
                yield "progress", {"current": i + 1, "total": len(to_del)}
            yield "success", f"Auto-deletion completed. Destroyed: {count}"
            self._write_log(f"Duplicate scan auto-deletion completed. Deleted {count} files.")
        else:
            yield "progress", {"current": total, "total": total}
            yield "dupe_groups", groups
            yield "info", "Review the duplicates above. Run with --auto-dupes to automatically delete copies."
            self._write_log(f"Duplicate scan completed. Found {len(groups)} duplicate groups.")

    def rollback_last_session_generator(self):
        history = self._load_history()
        if not history:
            yield "error", "No sorting history found to roll back."
            return

        with self.config_lock:
            dry_run_mode = self.config.get("dry_run", False)
        prefix = "[SIMULATION] " if dry_run_mode else ""
        yield "info", f"{prefix}Starting rollback of the last session ({len(history)} operations)..."
        self._write_log(f"Starting rollback session of {len(history)} operations.")

        total = len(history)
        count = 0
        successful_reversals = []
        unsuccessful_reversals = []

        for i, op in enumerate(reversed(history)):
            yield "progress", {"current": i + 1, "total": total}
            src = op.get("src")
            dst = op.get("dst")

            if not src or not dst:
                continue

            if not os.path.exists(dst):
                yield "skip", f"Target file not found at sorted location: {dst}."
                unsuccessful_reversals.append(op)
                continue

            final_src = src
            if os.path.exists(final_src):
                n, e = os.path.splitext(os.path.basename(src))
                parent = os.path.dirname(src)
                counter = 1
                while os.path.exists(final_src):
                    final_src = os.path.join(parent, f"{n}_restored_{counter}{e}")
                    counter += 1
                yield "conflict", f"Original path occupied. Restoring to: {os.path.basename(final_src)}"

            try:
                if not dry_run_mode:
                    os.makedirs(os.path.dirname(final_src), exist_ok=True)
                    shutil.move(dst, final_src)
                count += 1
                yield "move", f"{prefix}Restored: {os.path.basename(dst)} -> {final_src}"
                self._write_log(f"{prefix}Restored: {dst} -> {final_src}")
            except Exception as e:
                yield "error", f"Rollback error for {os.path.basename(dst)}: {str(e)}"
                self._write_log(f"Error during rollback of {dst} to {final_src}: {str(e)}")
                unsuccessful_reversals.append(op)

        if not dry_run_mode:
            self._save_history(unsuccessful_reversals)
            
        yield "success", f"{prefix}Rollback session completed! Successfully restored: {count}/{total} files."
        self._write_log(f"{prefix}Rollback session completed. Restored {count}/{total} files.")

    def generate_stats_generator(self, path):
        if not path or not os.path.exists(path):
            yield "error", "Specified path not found!"
            return

        yield "info", f"Analyzing directory statistics for: {path}"
        with self.config_lock:
            ignore_hidden = self.config.get("ignore_hidden", True)
            extensions_config = self.config.get("extensions", {}).copy()

        ext_to_category = {}
        for cat, exts in extensions_config.items():
            for e in exts.split(','):
                clean_ext = e.strip().lower()
                if clean_ext:
                    if not clean_ext.startswith('.'):
                        clean_ext = '.' + clean_ext
                    ext_to_category[clean_ext] = cat

        total_files = 0
        total_size = 0
        category_stats = {}
        ext_stats = {}

        temp_files_list = []
        for root, dirs, files in os.walk(path):
            if ignore_hidden:
                dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if ignore_hidden and f.startswith('.'):
                    continue
                temp_files_list.append(os.path.join(root, f))

        total_candidates = len(temp_files_list)
        if total_candidates == 0:
            yield "stats_data", {"total_files": 0, "total_size_mb": 0.0, "categories": {}, "extensions": {}}
            yield "success", "No files found to analyze."
            return

        for i, fp in enumerate(temp_files_list):
            yield "progress", {"current": i + 1, "total": total_candidates}
            try:
                sz = os.path.getsize(fp)
                ext = os.path.splitext(fp)[1].lower()
                cat = ext_to_category.get(ext, "Other")

                total_files += 1
                total_size += sz

                if cat not in category_stats:
                    category_stats[cat] = {"count": 0, "size_bytes": 0}
                category_stats[cat]["count"] += 1
                category_stats[cat]["size_bytes"] += sz

                if ext not in ext_stats:
                    ext_stats[ext] = {"count": 0, "size_bytes": 0}
                ext_stats[ext]["count"] += 1
                ext_stats[ext]["size_bytes"] += sz
            except (OSError, PermissionError):
                continue

        stats_summary = {
            "total_files": total_files,
            "total_size_mb": round(total_size / 1048576.0, 2),
            "categories": {k: {"count": v["count"], "size_mb": round(v["size_bytes"] / 1048576.0, 2)} for k, v in category_stats.items()},
            "extensions": {k: {"count": v["count"], "size_mb": round(v["size_bytes"] / 1048576.0, 2)} for k, v in sorted(ext_stats.items(), key=lambda item: item[1]["size_bytes"], reverse=True)[:15]}
        }

        yield "stats_data", stats_summary
        yield "success", f"Statistics generation completed for {path}."

    def convert_files_generator(self, path, conv_input, conv_output):
        if not path or not os.path.exists(path):
            yield "error", "Specified path not found!"
            return
            
        if not conv_input or not conv_output:
            yield "error", "Both input type/file and target format must be specified!"
            return

        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            yield "error", "ffmpeg was not found in system PATH. Please install ffmpeg and make sure it is in PATH."
            return

        target_ext = conv_output.strip().lower().lstrip('.')
        with self.config_lock:
            overwrite = self.config.get("overwrite", False)
            dry_run_mode = self.config.get("dry_run", False)
            
        prefix = "[SIMULATION] " if dry_run_mode else ""
        yield "info", f"{prefix}Searching files for conversion matching '{conv_input}' to '{target_ext}' in: {path}"
        self._write_log(f"Starting conversion process in {path} (input: {conv_input}, output: {target_ext})")

        files_to_convert = []
        
        direct_file = None
        if os.path.isfile(conv_input):
            direct_file = conv_input
        elif os.path.isfile(os.path.join(path, conv_input)):
            direct_file = os.path.join(path, conv_input)
            
        if direct_file:
            files_to_convert.append(direct_file)
        else:
            target_exts = set()
            conv_input_lower = conv_input.lower().strip()
            
            if conv_input_lower == "@images":
                exts_str = self.config.get("extensions", {}).get("Images", "")
                target_exts = {e.strip().lower() for e in exts_str.split(",") if e.strip()}
            elif conv_input_lower in ("@video", "@videos"):
                exts_str = self.config.get("extensions", {}).get("Video", "")
                target_exts = {e.strip().lower() for e in exts_str.split(",") if e.strip()}
            elif conv_input_lower in ("@audio", "@music"):
                exts_str = self.config.get("extensions", {}).get("Music", "")
                target_exts = {e.strip().lower() for e in exts_str.split(",") if e.strip()}
            else:
                clean_ext = conv_input_lower
                if not clean_ext.startswith('.'):
                    clean_ext = '.' + clean_ext
                target_exts = {clean_ext}
                
            target_exts = {e if e.startswith('.') else '.' + e for e in target_exts}
            
            recursive_sort = self.config.get("recursive_sort", False)
            ignore_hidden = self.config.get("ignore_hidden", True)
            
            if recursive_sort:
                for root, dirs, files in os.walk(path):
                    if ignore_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                    for f in files:
                        if ignore_hidden and f.startswith('.'):
                            continue
                        ext = os.path.splitext(f)[1].lower()
                        if ext in target_exts:
                            files_to_convert.append(os.path.join(root, f))
            else:
                try:
                    for f in os.listdir(path):
                        if ignore_hidden and f.startswith('.'):
                            continue
                        fp = os.path.join(path, f)
                        if os.path.isfile(fp):
                            ext = os.path.splitext(f)[1].lower()
                            if ext in target_exts:
                                files_to_convert.append(fp)
                except Exception as e:
                    yield "error", f"Failed to scan directory: {str(e)}"
                    return

        total = len(files_to_convert)
        if total == 0:
            yield "skip", f"No matching files found to convert in: {path}"
            yield "success", "No files to convert."
            self._write_log(f"Conversion completed: No matching files found in {path}")
            return

        yield "info", f"Found {total} files matching '{conv_input}'"
        
        count = 0
        for i, fp in enumerate(files_to_convert):
            yield "progress", {"current": i + 1, "total": total}
            
            dir_name = os.path.dirname(fp)
            base_name = os.path.splitext(os.path.basename(fp))[0]
            src_ext = os.path.splitext(fp)[1].lower().lstrip('.')
            
            if src_ext == target_ext:
                yield "skip", f"Already in target format: {os.path.basename(fp)}"
                continue
                
            dest_path = os.path.join(dir_name, f"{base_name}.{target_ext}")
            
            if os.path.exists(dest_path):
                if overwrite:
                    pass
                else:
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(dir_name, f"{base_name}_{counter}.{target_ext}")
                        counter += 1
                    yield "conflict", f"Target file already exists. Renamed output to: {os.path.basename(dest_path)}"

            try:
                if not dry_run_mode:
                    cmd = [ffmpeg_path, "-y", "-i", fp, dest_path]
                    
                    startupinfo = None
                    if os.name == 'nt':
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        
                    subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        startupinfo=startupinfo,
                        check=True
                    )
                count += 1
                yield "move", f"{prefix}Converted: {os.path.basename(fp)} -> {os.path.basename(dest_path)}"
                self._write_log(f"{prefix}Converted: {fp} -> {dest_path}")
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.strip() if e.stderr else "Subprocess returned non-zero exit status."
                yield "error", f"FFmpeg conversion error for {os.path.basename(fp)}: {err_msg}"
                self._write_log(f"FFmpeg conversion error for {fp} to {dest_path}: {err_msg}")
            except Exception as e:
                yield "error", f"Error converting {os.path.basename(fp)}: {str(e)}"
                self._write_log(f"Error converting {fp} to {dest_path}: {str(e)}")

        yield "success", f"{prefix}Conversion completed! Successfully processed {count} files."
        self._write_log(f"{prefix}Conversion completed. Processed {count}/{total} files.")