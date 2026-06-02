# MD File Utils - Premium Suite

![bg](https://i.ibb.co.com/bw3trPB/Chat-GPT-Image-May-19-2026-04-47-23-PM.png)

MD File Utils is a modern, feature-rich desktop and CLI file management application built with a Python Core engine and a stunning glass-morphism web interface. It transforms chaotic file organization into a streamlined, automated experience with intelligent sorting, duplicate detection, reverse actions, and real-time monitoring.

## Features

### 1. Intelligent File Sorting
Automatically categorizes files into logical folders based on extensions and regex patterns:
- **Single Mode** - Sort files within a single directory (with recursive support).
- **Multi-Source Mode** - Aggregate files from multiple source locations into one target directory.

### 2. Reverse & Rollback Actions
- **Unsort (Reverse)** - Extract all files from categorized subfolders back to the root directory.
- **Rollback Session** - Undo the exact movements made during the last sorting session using the history log.

### 3. Advanced Duplicate Finder
Uses pre-filtering by file size and chunk-based MD5 hashing for large files to identify true binary duplicates regardless of their filenames. Includes an option for instant auto-deletion.

### 4. Real-Time Folder Monitor (Beta)
Runs a background, thread-safe watcher that monitors specified directories (e.g., Downloads folder) and automatically sorts new incoming files in real-time.

### 5. Statistics & Analytics
Generates a detailed breakdown of any directory, showing total size, file counts, top categories, and most heavy extensions.

### 6. Fine-Grained Controls
- **Size Filtering** - Ignore files smaller or larger than specified MB thresholds.
- **Custom Regex Rules** - Assign specific files to categories based on complex Regular Expressions.
- **Safety Features** - Simulation Mode (Dry Run) and options to handle hidden files or filename conflicts.

### 7. Aesthetic Web UI & Customization
- Fully bilingual (English, Russian, Spanish, Chinese, German).
- Custom UI accents, dynamic mesh/grid patterns, and custom background image support with blur/opacity sliders.
- Real-time terminal telemetry logs using Server-Sent Events (SSE).

### 8. Powerful Command-Line Interface (CLI)
Full access to the Core Engine directly from the terminal for scripting and headless environments.

## Installation

### Prerequisites
- Python 3.8+
- `pip` package manager

### Setup

```bash
# Clone or download the application
cd md-file-utils

# Install dependencies
pip install Flask colorama

# Run the Web UI server
python start_server.py
```
*The server will automatically open your default browser to `http://127.0.0.1:5000`.*

## Dependencies
The application requires the following Python packages:
- `Flask` - Backend web framework and API server.
- `colorama` - Terminal color styling for the CLI engine.

## Usage

### Web Interface
- **Single / Multi** - Select folders, configure sorting options (date sort, clean empty, size limits), and execute.
- **Duplicates** - Select a directory to deep-scan for duplicate files. View the match groups and purge clones.
- **Monitor** - Add folders to watch, set the interval, and enable real-time background sorting.
- **Settings** - Customize category dictionaries, background images, and language.

### Command-Line Interface (CLI)
You can run the engine directly from your terminal:

```bash
# View all available commands
python cli_main.py --help

# Sort a single folder
python cli_main.py single -p /path/to/folder --date-sort

# Merge multiple sources into a target folder
python cli_main.py multi -s /src1 /src2 -t /target_folder

# Find and auto-delete duplicates
python cli_main.py dupes -p /path/to/folder --auto-dupes

# Revert the last sorting session
python cli_main.py rollback

# Generate statistics for a directory
python cli_main.py stats -p /path/to/folder
```

## Keyboard Shortcuts (Web UI)
| Shortcut | Action |
| :--- | :--- |
| `Alt + M` | Toggle secret deep scan mode UI triggers |
| `Ctrl + Shift + S` | Toggle slow-motion debug UI delays |

## Configuration
Settings are automatically saved to `sorter_config.json` in the application directory. It tracks:
- Category extensions and regex mappings (`extensions`, `custom_rules`).
- Operation modifiers (`move_unknown`, `date_sort`, `clean_empty`, `overwrite`, `min_size_mb`, `max_size_mb`).
- Visual preferences (`bg_style`, `bg_image_path`, `bg_blur`).
- Active monitored paths.

## Project Structure

```text
md-file-utils/
├── start_server.py    # Main entry point (Web UI auto-starter)
├── web_app.py         # Flask API backend
├── cli_main.py        # Command-Line Interface application
├── sorter_core.py     # Core Engine (Sorting, Hashing, Monitoring)
├── index.html         # Frontend (Tailwind, Glassmorphism)
└── README.md          # Documentation
```

## API Endpoints (Web UI)
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/config` | GET/POST | Load or save application settings |
| `/api/stream` | GET | Server-Sent Events (SSE) stream for real-time engine telemetry |
| `/api/dupes/delete` | POST | Delete an array of selected duplicate files |
| `/api/browse` | GET | Open native OS dialog for folder/file selection |
| `/api/bg` | GET | Safely serve custom background images |

## License
MIT License

## Support
For issues or feature requests, please open an issue in the repository.
