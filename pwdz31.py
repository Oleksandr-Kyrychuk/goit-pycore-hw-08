import os
import sys
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

def copy_file(src_path, dest_dir):
    ext = os.path.splitext(src_path)[1].lower().lstrip('.')
    if not ext:
        ext = 'no_extension'
    target_dir = os.path.join(dest_dir, ext)
    os.makedirs(target_dir, exist_ok=True)
    dest_path = os.path.join(target_dir, os.path.basename(src_path))
    try:
        shutil.copy2(src_path, dest_path)
        # print(f"Copied {src_path} -> {dest_path}")
    except Exception as e:
        print(f"Error copying {src_path}: {e}")

def process_directory(src_dir, dest_dir, executor):
    futures = []
    try:
        for entry in os.scandir(src_dir):
            if entry.is_file():
                futures.append(executor.submit(copy_file, entry.path, dest_dir))
            elif entry.is_dir():
                # Рекурсивний виклик у новому потоці
                futures.append(executor.submit(process_directory, entry.path, dest_dir, executor))
    except PermissionError as e:
        print(f"Permission error accessing {src_dir}: {e}")
    return futures

def main():
    if len(sys.argv) < 2:
        print("Usage: python file_sorter_threads.py <source_dir> [<dest_dir>]")
        sys.exit(1)

    source_dir = sys.argv[1]
    dest_dir = sys.argv[2] if len(sys.argv) > 2 else "dist"

    if not os.path.isdir(source_dir):
        print(f"Source directory '{source_dir}' does not exist or is not a directory")
        sys.exit(1)

    os.makedirs(dest_dir, exist_ok=True)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = process_directory(source_dir, dest_dir, executor)
        # Очікуємо завершення всіх завдань
        for future in as_completed(futures):
            pass

if __name__ == "__main__":
    main()
