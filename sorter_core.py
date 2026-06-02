import os
import shutil
import json
import hashlib
from datetime import datetime
import threading
import time

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
            "last_path": "",
            "dry_run": False,
            "ignore_hidden": True,
            "min_size_mb": 0.0,
            "max_size_mb": 0.0,
            # Background monitoring configurations
            "monitor_enabled": False,
            "monitor_folders": [],
            "monitor_interval_sec": 5.0,
            "monitor_target": ""
        }
        self.config = self.load_config()

        # Monitoring daemon assets
        self.monitor_thread = None
        self.monitor_stop_event = threading.Event()

        # Safely trigger background monitoring if enabled on init
        if self.config.get("monitor_enabled", False):
            self.start_monitoring()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return {**self.defaults, **json.load(f)}
            except Exception:
                return self.defaults
        return self.defaults

    def save_config(self, new_config):
        old_enabled = self.config.get("monitor_enabled", False)
        self.config.update(new_config)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        
        new_enabled = self.config.get("monitor_enabled", False)
        # Handle state transitions for background processes
        if new_enabled and not old_enabled:
            self.start_monitoring()
        elif not new_enabled and old_enabled:
            self.stop_monitoring()

    def start_monitoring(self):
        """Launches thread-safe background process monitoring."""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        self.monitor_stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Requests graceful shutdown of background process thread."""
        self.monitor_stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            self.monitor_thread = None

    def _monitor_loop(self):
        """Infinite loop designed for background task monitoring execution."""
        while not self.monitor_stop_event.is_set():
            enabled = self.config.get("monitor_enabled", False)
            if not enabled:
                time.sleep(1.0)
                continue

            folders = self.config.get("monitor_folders", [])
            target = self.config.get("monitor_target", "")
            interval = float(self.config.get("monitor_interval_sec", 5.0))
            if interval < 1.0:
                interval = 1.0

            if folders:
                for folder in folders:
                    if os.path.exists(folder):
                        dest = target if target else folder
                        try:
                            # Silently deplete generator results during background work
                            for _ in self.sort_directory_generator(folder, target_dir=dest):
                                pass
                        except Exception:
                            pass

            # Segment sleeping checks to remain responsive to stop signals
            steps = max(1, int(interval))
            for _ in range(steps):
                if self.monitor_stop_event.is_set():
                    break
                time.sleep(interval / steps)

    def get_file_hash(self, filepath):
        """Safe block-by-block MD5 hash calculation for files of any size."""
        hasher = hashlib.md5()
        try:
            # Using 128KB chunk sizes for optimal read buffering
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(131072), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, PermissionError):
            return None

    def _clean_empty_folders(self, path):
        """Recursively search for and delete empty directories."""
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
        """Verify if file size falls within the configured min/max boundaries."""
        try:
            min_size = float(self.config.get("min_size_mb", 0.0))
            max_size = float(self.config.get("max_size_mb", 0.0))

            # Optimisation: skip system stats call if constraints are disabled
            if min_size <= 0.0 and max_size <= 0.0:
                return True

            sz_bytes = os.path.getsize(filepath)
            sz_mb = sz_bytes / 1048576.0 # 1024 * 1024

            if min_size > 0.0 and sz_mb < min_size:
                return False
            if max_size > 0.0 and sz_mb > max_size:
                return False
            return True
        except (OSError, PermissionError, ValueError):
            return False

    # --- 1. SORTING (Single & Multi) ---
    def sort_directory_generator(self, src_dir, target_dir=None):
        if not target_dir: 
            target_dir = src_dir
        if not os.path.exists(src_dir):
            yield "error", f"Specified path does not exist: {src_dir}"
            return
            
        dry_run_mode = self.config.get("dry_run", False)
        ignore_hidden = self.config.get("ignore_hidden", True)
        overwrite = self.config.get("overwrite", False)
        date_sort = self.config.get("date_sort", False)
        move_unknown = self.config.get("move_unknown", True)
        clean_empty = self.config.get("clean_empty", True)
        prefix = "[SIMULATION] " if dry_run_mode else ""
        
        yield "info", f"{prefix}Analyzing directory: {src_dir}"
        
        try:
            raw_files = os.listdir(src_dir)
        except Exception as e:
            yield "error", f"Failed to read directory: {str(e)}"
            return

        # Precompile exclusions and category mapping once
        excl = {x.strip().lower() for x in self.config.get("excluded_files", "").split(",") if x.strip()}
        excl.add("sorter_config.json")
        excl.add("sorter_log.txt")

        ext_to_category = {}
        for cat, exts in self.config.get("extensions", {}).items():
            for e in exts.split(','):
                clean_ext = e.strip().lower()
                if clean_ext:
                    if not clean_ext.startswith('.'):
                        clean_ext = '.' + clean_ext
                    ext_to_category[clean_ext] = cat

        # Pre-filter files to get an accurate progress total
        files_to_process = []
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

        total = len(files_to_process)
        if total == 0:
            yield "skip", f"No files to sort in: {src_dir}"
            yield "success", f"No files to sort in: {src_dir}"
            return

        count = 0
        for index, (f, src_path) in enumerate(files_to_process):
            yield "progress", {"current": index + 1, "total": total}

            ext = os.path.splitext(f)[1].lower()
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
                    # Rename collision handler
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
                count += 1
                yield "move", f"{prefix}Processed: {f} -> {category}"
            except Exception as e:
                yield "error", f"Move error for {f}: {str(e)}"
        
        if clean_empty and not dry_run_mode:
            self._clean_empty_folders(src_dir)
            
        yield "success", f"{prefix}Processing completed for {src_dir}! Actions: {count} files"

    # --- 2. REVERSE SORTING (Unsort) ---
    def unsort_directory_generator(self, target_dir):
        if not target_dir or not os.path.exists(target_dir):
            yield "error", "Specified path not found!"
            return

        dry_run_mode = self.config.get("dry_run", False)
        ignore_hidden = self.config.get("ignore_hidden", True)
        clean_empty = self.config.get("clean_empty", True)
        prefix = "[SIMULATION] " if dry_run_mode else ""

        yield "info", f"{prefix}Starting reverse sorting (extraction) for: {target_dir}"
        all_files = []
        cats = list(self.config.get("extensions", {}).keys()) + ["Other"]
        
        for c in cats:
            cp = os.path.join(target_dir, c)
            if os.path.isdir(cp):
                for r, dirs, fs in os.walk(cp):
                    if ignore_hidden:
                        # Prune hidden subdirectories from the walk trajectory
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                    for f in fs: 
                        if ignore_hidden and f.startswith('.'):
                            continue
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
            except Exception as e:
                yield "error", f"Extraction error for {fname}: {str(e)}"

        if clean_empty and not dry_run_mode:
            yield "info", "Cleaning up empty category folders..."
            self._clean_empty_folders(target_dir)

        yield "success", f"{prefix}Reverse sorting completed! Processed files: {count}"

    # --- 3. DUPLICATE FINDER ---
    def scan_duplicates_generator(self, path):
        if not path or not os.path.exists(path):
            yield "error", "Specified path not found!"
            return
            
        yield "info", f"Scanning for duplicates in: {path}"
        ignore_hidden = self.config.get("ignore_hidden", True)
        auto_dupes = self.config.get("auto_dupes", False)
        
        size_groups = {}
        for root_dir, dirs, files in os.walk(path):
            if ignore_hidden:
                # Prune hidden subdirectories to speed up disk scanning dramatically
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
            return

        if auto_dupes:
            to_del = []
            for g in groups: 
                # Retain the first copy as original and queue other copies for deletion
                to_del.extend(g[1:])
            yield "info", f"Found {len(to_del)} duplicates. Starting auto-deletion..."
            count = 0
            for i, p in enumerate(to_del):
                try:
                    os.remove(p)
                    count += 1
                    yield "move", f"Deleted duplicate: {p}"
                except Exception as e:
                    yield "error", f"Deletion error: {str(e)}"
                yield "progress", {"current": i + 1, "total": len(to_del)}
            yield "success", f"Auto-deletion completed. Destroyed: {count}"
        else:
            yield "progress", {"current": total, "total": total}
            yield "dupe_groups", groups
            yield "info", "Review the duplicates above. Run with --auto-dupes to automatically delete copies."