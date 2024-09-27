# Osmo-Prepare

## Purpose
**Osmo-Prepare** is a utility designed to join videos that are split by the DJI Osmo Action camera due to its 4GB file size limit. The joined video files are placed in the `/processed` folder, making them ready for easy upload to cloud drives.

## Requirements
- Python 3.11 (or later) is required to run this project. The script has been tested and works with Python 3.11.
- FFmpeg 4.4.x required to join video fragments.

## Installation
1. **Ensure Python is installed**: Download and install Python 3.11 from the [official website](https://www.python.org/downloads/), if you haven't already.
2. **Clone the repository** (if applicable) or download the project files.

## Usage
1. Place your video files in the appropriate directory (e.g., `/input`).
2. Open a terminal or command prompt and navigate to the project directory.
3. Run the following command to join the videos:

    ```sh
    python main.py
    ```

4. After the process completes, your joined video files will be available in the `/processed` folder.

## Notes
- The script automatically detects video files that belong together based on their filenames.
- Ensure there is enough space in the `/processed` folder to accommodate the joined videos.

---

Enjoy seamless video merging with Osmo-Prepare!
