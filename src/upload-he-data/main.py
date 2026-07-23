import os
import re
import time
import shutil
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

load_dotenv() #loads variables from local .env file

USERNAME = os.getlogin() #gets local active windows user profile name dynamically

RAW_WATCH = os.getenv("WATCH_DIRECTORY", r"C:\LabOutputs\Incoming") #pulls path from env
RAW_ONEDRIVE = os.getenv("ONEDRIVE_DIRECTORY", "") #pulls path from env

WATCH_DIRECTORY = RAW_WATCH.format(USERNAME=USERNAME) #resolves username placeholder if present
ONEDRIVE_DIRECTORY = RAW_ONEDRIVE.format(USERNAME=USERNAME) #resolves username placeholder if present

# UPDATE: Removed the ^ so it searches for WNxyz ANYWHERE in the filename
WN_PATTERN = re.compile(r"WN\d{3}", re.IGNORECASE) 


def wait_for_file_completion(file_path, timeout=30): #holds off moving file while lab equipment writes data
    start_time = time.time() #records start timestamp
    last_size = -1 #initialises file size tracker

    while time.time() - start_time < timeout: #loop until timeout reached
        try:
            current_size = os.path.getsize(file_path) #checks current file size on disk
            if current_size == last_size and current_size > 0: #if size stopped growing and we can access it
                with open(file_path, "a+"): #test if file is still locked by lab software
                    return True #file write complete
            last_size = current_size #update last seen file size
        except (OSError, PermissionError): #triggers if file is locked during write
            pass #keep waiting
        time.sleep(1) #pause 1 second before checking size again
        
    return False #returns false if write exceeds timeout limit


class LabDataHandler(FileSystemEventHandler): #event handler class triggered on folder changes
    def on_created(self, event): #runs whenever new file drops in folder
        if event.is_directory: #ignore subfolders
            return

        file_path = event.src_path #full path to newly created file
        file_name = os.path.basename(file_path) #extract just the file name

        if file_name.startswith("~") or file_name.endswith(".tmp"): #ignore temporary files
            return

        if not wait_for_file_completion(file_path): #wait for lab software to finish saving
            print(f"[WARNING] Could not access '{file_name}' (file write timeout).")
            return

        match = WN_PATTERN.search(file_name) #search filename for wn code pattern
        if match:
            wn_code = match.group(0).upper() #extract code and force uppercase
            
            target_folder = os.path.join(ONEDRIVE_DIRECTORY, wn_code) #build full target folder path

            if not os.path.exists(target_folder): #check if wn folder exists
                os.makedirs(target_folder) #create subfolder if missing
                print(f"[CREATED FOLDER] {target_folder}")

            # OVERWRITE CHECK: Prevents deleting existing files with the same name
            base_name, extension = os.path.splitext(file_name)
            destination_path = os.path.join(target_folder, file_name)
            
            counter = 1
            while os.path.exists(destination_path): # Check if file already exists in target folder
                new_name = f"{base_name}_{counter}{extension}" # Append _1, _2, etc.
                destination_path = os.path.join(target_folder, new_name)
                counter += 1

            try:
                shutil.move(file_path, destination_path) #move file from incoming to sharepoint
                final_name = os.path.basename(destination_path)
                print(f"[MOVED] '{file_name}' -> '{wn_code}\{final_name}'")
            except Exception as e:
                print(f"[ERROR] Failed to move '{file_name}': {e}")
        else:
            print(f"[SKIPPED] '{file_name}' — No WNxyz code detected.") #skip files without wn code


def run(): #entry point for uv script execution
    if not ONEDRIVE_DIRECTORY: #prevents running without configured path
        raise ValueError("ONEDRIVE_DIRECTORY is not set in environment variables or .env file.")

    event_handler = LabDataHandler() #initialise event handler
    observer = Observer() #initialise watchdog observer
    
    observer.schedule(event_handler, path=WATCH_DIRECTORY, recursive=False) #attach observer to folder

    print("--- He Pycnometer Auto-Sorter Active ---")
    print(f"Monitoring: {WATCH_DIRECTORY}")
    print(f"Destination: {ONEDRIVE_DIRECTORY}\n")

    observer.start() #start background watcher thread

    try:
        while True: #keep script running continuously
            time.sleep(1)
    except KeyboardInterrupt: #listen for manual exit command
        observer.stop() #stop watcher thread

    observer.join() #clean exit


if __name__ == "__main__":
    run()