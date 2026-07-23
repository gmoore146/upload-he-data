# upload-he-data

Automated background service to monitor incoming He Pycnometer lab outputs and organise them into dedicated `WNxyz` subfolders within SharePoint/OneDrive.

## Requirements

- Requires OneDrive to be synced to the lab PC in files.

## Setup Instructions

### 1. Clone the repository
Open Command Prompt and clone the project:
```cmd
git clone <your-github-repo-url>
cd upload-he-data
```

### 2. Configure Local Environment Variables
Create your local `.env` file from the example template:
```cmd
copy .env.example .env
```
Open `.env` in Notepad and set your local directory paths to match the lab PC:
```bash
WATCH_DIRECTORY="C:\Path\To\Your\Incoming\Folder"
ONEDRIVE_DIRECTORY="C:\Path\To\Your\OneDrive\Folder"
```

### 3. Install Dependencies
Initialize the project environment using `uv`:
```cmd
uv sync
```

### 4. Run the Service
Start the monitoring script manually in the terminal:
```cmd
uv run upload-he-data
```

## Running Automatically on Windows Startup

To run the script quietly in the background when the PC powers on:

1. Press `Win + R`, type `taskschd.msc`, and press **Enter** to open **Task Scheduler**.
2. Click **Create Basic Task...** in the right sidebar.
3. Set **Name** to `He Pycnometer Auto Sorter`.
4. Set **Trigger** to `When I log on`.
5. Set **Action** to `Start a program`:
   * **Program/script:** `uv`
   * **Add arguments:** `run pythonw -m upload_he_data.main`
   * **Start in:** `C:\path\to\upload-he-data`
6. Click **Finish**.

## Stopping the Service

If you need to stop the background script (for troubleshooting or updates):
1. Press `Ctrl + Shift + Esc` to open **Task Manager**.
2. Go to the **Details** tab.
3. Find `pythonw.exe`, right-click it, and select **End Task**.
*(Note: To prevent it from starting automatically again, disable it in Task Scheduler).*

## Updating the Script

When new changes are made to the code on GitHub, follow these steps on the lab PC to update:

1. Open Command Prompt and navigate to the project folder:
```cmd
cd C:\path\to\upload-he-data
```

2. Download the latest code:
```cmd
git pull
```

3. Sync any new dependencies:
```cmd
uv sync
```

4. Restart the PC to automatically launch the updated background script.