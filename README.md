MD File Utils - File Management Suite

https://i.ibb.co.com/bw3trPB/Chat-GPT-Image-May-19-2026-04-47-23-PM.png

MD File Utils is a modern, feature-rich desktop file management application built with a Python backend and a glass-morphism web interface. It transforms chaotic file organization into a streamlined, automated experience with intelligent sorting, duplicate detection, and real-time monitoring.
Features
1. Intelligent File Sorting

Automatically categorizes files into logical folders based on extensions:

    Single Mode - Sort files within a single directory

    Multi-Source Mode - Aggregate files from multiple locations into one target directory

2. Metadata Analysis

    EXIF extraction for photos - sort by capture date

    ID3 tag reading for music - organize by artist

3. Date & Size Organization

    Date sorting - Create nested year/month folder structures

    Size filtering - Group files into size tiers (Small <10MB to Gigantic >500MB)

4. Real-Time Folder Watcher

Monitor directories (e.g., Downloads folder) and automatically sort new files as they arrive.
5. Advanced Duplicate Finder

Uses MD5 hashing with chunk-reading for large files to identify true duplicates regardless of filename.
6. Bulk Renamer

Batch operations for case conversion and custom text prefixing.
7. Safety Controls

    Preview Mode (Dry Run) - See what would happen without making changes

    Copy Mode - Leave originals untouched, distribute copies

    Undo Last Action - Restore files to original locations

8. Customization & Analytics

    Fully bilingual (English, Russian, Spanish, Chinese, German)

    Light/Dark themes

    Customizable accent colors and background patterns

    Editable category extension mappings

Installation
Prerequisites

    Python 3.8+

    pip package manager

Setup
bash

# Clone or download the application
cd md-file-utils

# Install dependencies
pip install -r requirements.txt

# Run the server
python start_server.py

Then open your browser to http://localhost:8080
Dependencies

The application requires the following Python packages:

    watchdog - Real-time filesystem monitoring

    mutagen - Audio metadata (ID3 tags) extraction

    Pillow - Image metadata (EXIF) extraction

Usage
Quick Start

    Single Mode - Select a folder, choose sorting options, click "Start Sorting"

    Multi-Source Mode - Add source folders, set a target destination, click "Assemble Sources"

    Duplicates - Select a directory to scan for duplicate files

    Settings - Customize category extensions, accent colors, and operation parameters

Keyboard Shortcuts
Shortcut	Action
Alt + M	Toggle slow-motion debug mode
Ctrl + Shift + S	Toggle UI debug delays
Configuration

Settings are automatically saved to config.json in the application directory, including:

    Sorting preferences (date sort, overwrite, clean empty)

    Size filters (min/max file sizes)

    Hidden file handling

    Dry run mode

    Custom extension mappings for each category

Project Structure
text

md-file-utils/
├── start_server.py    # Main entry point
├── index.html         # Web interface
├── README.md          # Documentation
└── requirements.txt   # Python dependencies

API Endpoints
Endpoint	Method	Description
/api/config	GET/POST	Load/save application settings
/api/stream	GET	SSE stream for file operations
/api/dupes/delete	POST	Delete selected duplicate files
/api/browse	GET	Open folder selection dialog
License

MIT License
Support

For issues or feature requests, please open an issue in the repository.