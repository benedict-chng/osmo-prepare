# Osmo-Prepare

## Purpose
**Osmo-Prepare** is a utility designed to join videos that are split by the DJI Osmo Action camera due to its 4GB file size limit. The joined video files are placed in the `/processed` folder, making them ready for easy upload to cloud drives.

## Requirements
- Python 3.11 (or later)
- FFmpeg 4.4.x or later (required to join video fragments)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver

## Installation

### Install uv (if not already installed)
```bash
# On macOS/Linux (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip (slower)
pip install uv
```

### Install the project
```bash
# Clone the repository
git clone <repository-url>
cd osmo-prepare

# Install the project with uv (creates virtual environment)
uv sync
```

## Usage

### Using CLI commands (recommended)
After running `uv sync`, you can use the installed CLI commands:

1. **Auto-join all videos from media directory**:
   ```bash
   uv run osmo-prepare
   ```
   
   This will:
   - Copy videos from `/media/benedict/disk/DCIM/100MEDIA` (configurable)
   - Group related videos and join them
   - Save joined videos to `./processed/`

2. **Manually join specific videos**:
   ```bash
   uv run osmo-join <output_name> <file1.mp4> <file2.mp4> ...
   ```
   
   Example:
   ```bash
   uv run osmo-join combined video1.mp4 video2.mp4 video3.mp4
   ```

### Using Python module directly
```bash
# Run the main joiner
uv run python -m osmo_prepare.main

# Run the manual joiner
uv run python -m osmo_prepare.join
```

## Configuration

### Change media directory
Edit `src/osmo_prepare/main.py` and modify the `media_dir` variable:
```python
media_dir = '/path/to/your/videos'
```

### Development

Adding dependencies:
```bash
# Add runtime dependency
uv add <package-name>

# Add development dependency
uv add --dev <package-name>

# Update lock file
uv lock
```

Running tests (if added):
```bash
uv run pytest
```

## Notes
- The script automatically detects video files that belong together based on their filenames (first 8 characters).
- Videos matching the pattern `DJI_XXXX.MP4` are skipped (already joined videos).
- Ensure there is enough space in the `/processed` folder to accommodate the joined videos.
- The project uses [uv](https://github.com/astral-sh/uv) for fast dependency management and virtual environment handling.

---

Enjoy seamless video merging with Osmo-Prepare!
