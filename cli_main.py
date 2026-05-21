import sys
from sorter_core import FileSorterCore

def main():
    core = FileSorterCore()
    if len(sys.argv) < 2:
        print("Usage: python cli_main.py [path_to_sort]")
        return

    path = sys.argv[1]
    print(f"Sorting files in: {path}...")
    count = core.sort_directory(path)
    print(f"Done! Processed {count} files.")

if __name__ == "__main__":
    main()