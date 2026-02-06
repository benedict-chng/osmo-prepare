import time


def format_file_size(bytes_size: int) -> str:
    """Format bytes to human-readable file size."""
    if bytes_size == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(bytes_size)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"

    return f"{size:.1f} {units[unit_index]}"


def format_duration(seconds: int) -> str:
    """Format seconds to HH:MM:SS."""
    if seconds < 60:
        return f"{seconds:02d}s"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_file_size(filepath: str) -> int:
    """Get file size in bytes."""
    import os

    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0


def get_directory_size(directory: str) -> tuple[int, int]:
    """Get total size and file count of all files in directory.

    Returns:
        tuple: (total_bytes, file_count)
    """
    import os

    total_size = 0
    file_count = 0

    try:
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except OSError:
                    continue
    except OSError:
        pass

    return total_size, file_count


class Timer:
    """Simple timer for measuring execution time."""

    def __init__(self):
        self.start_time: float | None = None
        self.end_time: float | None = None

    def start(self) -> None:
        """Start the timer."""
        self.start_time = time.time()

    def stop(self) -> None:
        """Stop the timer."""
        self.end_time = time.time()

    def elapsed(self) -> int:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0

        end = self.end_time if self.end_time is not None else time.time()
        return int(end - self.start_time)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
