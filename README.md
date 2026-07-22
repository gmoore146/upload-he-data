# upload-he-data

Automated background service to monitor incoming He Pycnometer lab outputs and organise them into dedicated `WNxyz` subfolders within SharePoint/OneDrive.

## Repository Layout

```text
upload-he-data/
├── .env                  <-- [LOCAL ONLY] Local PC folder paths
├── .env.example          <-- Template for paths configuration
├── .gitignore            <-- Excludes secrets and temporary files from Git
├── pyproject.toml        <-- Project dependencies and script runner setup
├── README.md             <-- Setup documentation
└── src/
    └── upload_he_data/
        ├── __init__.py   <-- Package initializer
        └── main.py       <-- File system monitoring & file-sorting logic
```

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
Open `.env` in Notepad and set your local directory paths:
```bash
WATCH_DIRECTORY="C:\LabOutputs\Incoming"
ONEDRIVE_DIRECTORY="C:\Users\{USERNAME}\Puraffinity\Puraffinity - Documents\General\Analytical\Internal Testing\He Pycnometer\Raw Data Files"
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