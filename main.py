import logging
import os
import re
import shutil
import sys
import time

from dotenv import load_dotenv
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# pythonw has no console (sys.stdout is None), so only log to stdout when one exists
handlers = [logging.FileHandler("he_sorter_log.txt")]
if sys.stdout:
    handlers.append(logging.StreamHandler(sys.stdout))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=handlers,
)

load_dotenv()

WATCH_DIRECTORY = os.path.abspath(os.getenv("WATCH_DIRECTORY", r"C:\LabOutputs\Incoming"))
PROCESSED_DIRECTORY = os.path.abspath(os.getenv("PROCESSED_DIRECTORY", r"C:\LabOutputs\Processed"))
ONEDRIVE_DIRECTORY = os.getenv("ONEDRIVE_DIRECTORY", "")

WN_PATTERN = re.compile(r"WN\d{3}", re.IGNORECASE)
G400_PATTERN = re.compile(r"(G400Plus|G400\+|G\+)-(\d{2})", re.IGNORECASE)


def wait_for_file_completion(file_path, timeout=30):
    """Wait until the file size stops changing and it can be opened."""
    deadline = time.time() + timeout
    last_size = -1
    while time.time() < deadline:
        try:
            size = os.path.getsize(file_path)
            if size == last_size and size > 0:
                with open(file_path, "a+"):
                    return True
            last_size = size
        except OSError:
            pass
        time.sleep(1)
    return False


def target_subfolder(file_name):
    """Relative destination folder for a file name, or None if it has no sample code."""
    if match := WN_PATTERN.search(file_name):
        return match.group(0).upper()
    if match := G400_PATTERN.search(file_name):
        return os.path.join("G400+", f"G400+-{match.group(2)}")
    return None


def get_unique_destination(target_folder, file_name):
    """Append _1, _2, ... to avoid overwriting an existing file."""
    base_name, extension = os.path.splitext(file_name)
    destination = os.path.join(target_folder, file_name)
    counter = 1
    while os.path.exists(destination):
        destination = os.path.join(target_folder, f"{base_name}_{counter}{extension}")
        counter += 1
    return destination


def process_file(file_path):
    file_name = os.path.basename(file_path)
    if file_name.startswith("~") or file_name.endswith(".tmp") or not os.path.isfile(file_path):
        return

    subfolder = target_subfolder(file_name)
    if not subfolder:
        logging.info(f"[SKIPPED] '{file_path}' — No WNxyz or G400+-xy code detected.")
        return

    if not wait_for_file_completion(file_path):
        logging.warning(f"Could not access '{file_path}' (file write timeout).")
        return

    try:
        onedrive_target = os.path.join(ONEDRIVE_DIRECTORY, subfolder)
        processed_target = os.path.join(PROCESSED_DIRECTORY, subfolder)
        os.makedirs(onedrive_target, exist_ok=True)
        os.makedirs(processed_target, exist_ok=True)

        processed_dest = get_unique_destination(processed_target, file_name)
        onedrive_dest = get_unique_destination(onedrive_target, file_name)

        # Local backup first, then move to OneDrive (removes the original from the watch folder)
        shutil.copy2(file_path, processed_dest)
        shutil.move(file_path, onedrive_dest)

        logging.info(
            f"[SUCCESS] '{file_path}' saved to both:\n"
            f"   -> OneDrive: {onedrive_dest}\n"
            f"   -> Local: {processed_dest}"
        )
    except Exception as e:
        logging.error(f"[ERROR] Failed to process '{file_path}': {e}")


class LabDataHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            process_file(event.src_path)

    def on_moved(self, event):
        # Files written as .tmp and then renamed only fire a move event
        if not event.is_directory and os.path.dirname(event.dest_path) == WATCH_DIRECTORY:
            process_file(event.dest_path)


def run():
    if not ONEDRIVE_DIRECTORY:
        raise ValueError("ONEDRIVE_DIRECTORY is not set in environment variables or .env file.")

    os.makedirs(WATCH_DIRECTORY, exist_ok=True)

    logging.info("--- He Pycnometer Auto-Sorter Starting ---")
    logging.info(f"Monitoring: {WATCH_DIRECTORY}")
    logging.info(f"OneDrive Destination: {ONEDRIVE_DIRECTORY}")
    logging.info(f"Local Processed Destination: {PROCESSED_DIRECTORY}\n")

    logging.info("Scanning for existing files in the incoming directory...")
    for entry in os.scandir(WATCH_DIRECTORY):
        process_file(entry.path)
    logging.info("Initial scan complete. Beginning real-time monitoring.\n")

    observer = Observer()
    observer.schedule(LabDataHandler(), path=WATCH_DIRECTORY, recursive=False)
    observer.start()
    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        logging.info("Shutting down observer...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    run()
