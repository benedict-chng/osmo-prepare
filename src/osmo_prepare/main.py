import os
import re
import shutil
import subprocess
from typing import NamedTuple
from rich.console import Console
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
    TaskID,
)
from rich.table import Table
from rich.panel import Panel

from osmo_prepare.utils import (
    get_console,
    print_banner,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_processing,
    print_section_header,
    create_error_panel,
    create_summary_table,
)
from osmo_prepare.formatters import (
    format_file_size,
    format_duration,
    get_file_size,
    get_directory_size,
    Timer,
)


class GroupInfo(NamedTuple):
    """Information about a video group."""

    group_name: str
    chunk_count: int
    total_size: int


class ProcessingStats(NamedTuple):
    """Statistics from processing operations."""

    groups_processed: int
    groups_total: int
    files_copied: int
    files_joined: int
    total_input_size: int
    total_output_size: int
    space_saved: int
    execution_time: int
    errors: list[tuple[str, str, str]]


def validate_directory(directory: str, console: Console) -> bool:
    """Validate that a directory exists and is accessible."""
    if not os.path.isdir(directory):
        create_error_panel(
            console,
            "Directory Not Found",
            f"The specified directory does not exist: {directory}",
            "Please check the path and try again.",
        )
        return False
    return True


def check_disk_space(directory: str, required_bytes: int, console: Console) -> bool:
    """Check if there's enough disk space available."""
    try:
        import shutil

        stat = shutil.disk_usage(directory)
        available_bytes = stat.free

        if available_bytes < required_bytes:
            print_warning(
                console,
                f"Low disk space: {format_file_size(available_bytes)} available, "
                f"{format_file_size(required_bytes)} required",
            )
            return False

        print_info(
            console,
            f"Disk space check passed: {format_file_size(available_bytes)} available",
        )
        return True
    except Exception as e:
        print_warning(console, f"Could not check disk space: {e}")
        return True


def list_filenames(directory: str, console: Console) -> list[str]:
    """List all MP4 video files in the specified directory."""
    try:
        files_and_dirs = os.listdir(directory)
        filenames = [f for f in files_and_dirs if is_video_file(directory, f)]
        return filenames
    except FileNotFoundError:
        create_error_panel(
            console,
            "Directory Not Found",
            f"The directory '{directory}' does not exist.",
        )
        raise
    except Exception as e:
        create_error_panel(
            console,
            "Error Listing Files",
            f"An error occurred while listing files: {e}",
        )
        raise


def is_video_file(directory: str, filename: str) -> bool:
    """Check if a file is a video file."""
    return os.path.isfile(
        os.path.join(directory, filename)
    ) and filename.upper().endswith(".MP4")


def clear_processed_dir(processed_media_dir: str, console: Console) -> bool:
    """Clear the processed directory."""
    try:
        files = os.listdir(processed_media_dir)
        if not files:
            return True

        print_processing(console, f"Clearing {processed_media_dir}...")
        deleted_count = 0

        for filename in files:
            file_path = os.path.join(processed_media_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    deleted_count += 1
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    deleted_count += 1
            except Exception as e:
                print_warning(console, f"Failed to delete {file_path}: {e}")

        print_success(
            console, f"Cleared {deleted_count} item(s) from {processed_media_dir}"
        )
        return True

    except Exception as e:
        print_warning(console, f"Could not clear processed directory: {e}")
        return False


def copy_files_to_processed(
    media_dir: str,
    dest_dir: str,
    filenames: list[str],
    console: Console,
    progress: Progress,
    copy_task: TaskID,
) -> bool:
    """Copy files from media directory to processed directory with progress bar."""
    print_info(console, f"Copying {len(filenames)} file(s) from {media_dir}...")

    total_bytes = 0
    copied_bytes = 0

    for filename in filenames:
        src = os.path.join(media_dir, filename)
        total_bytes += get_file_size(src)

    progress.update(copy_task, total=total_bytes)

    for filename in filenames:
        src = os.path.join(media_dir, filename)
        dest = os.path.join(dest_dir, filename)

        try:
            shutil.copy(src, dest)
            file_size = get_file_size(dest)
            copied_bytes += file_size
            progress.update(copy_task, completed=copied_bytes)
        except Exception as e:
            print_error(console, f"Failed to copy {filename}: {e}")
            return False

    print_success(
        console, f"Copied {len(filenames)} file(s) ({format_file_size(total_bytes)})"
    )
    return True


def group_related_videos(
    video_filenames: list[str], directory: str, console: Console
) -> tuple[dict[str, list[str]], list[GroupInfo], int]:
    """Group related videos and return group information."""
    unchunked_filename_pattern = r"^DJI_\d{4}\.MP4$"

    grouped = {}
    skipped_count = 0

    for filename in video_filenames:
        if re.match(unchunked_filename_pattern, filename):
            skipped_count += 1
            continue

        group_name = filename[:8]

        if group_name not in grouped:
            grouped[group_name] = []

        grouped[group_name].append(filename)

    for group_name in grouped:
        grouped[group_name].sort()

    group_info_list = []
    for group_name, filenames in grouped.items():
        total_size = sum(get_file_size(os.path.join(directory, f)) for f in filenames)
        group_info_list.append(
            GroupInfo(
                group_name=group_name, chunk_count=len(filenames), total_size=total_size
            )
        )

    print_section_header(console, "Video Groups Found")

    table = Table(box=None)
    table.add_column("Group Name", style="cyan")
    table.add_column("Chunks", justify="right", style="white")
    table.add_column("Size", justify="right", style="white")

    for group_info in sorted(group_info_list, key=lambda x: x.group_name):
        table.add_row(
            group_info.group_name,
            str(group_info.chunk_count),
            format_file_size(group_info.total_size),
        )

    console.print(table)

    if skipped_count > 0:
        print_info(console, f"Skipped {skipped_count} already-joined file(s)")

    return grouped, group_info_list, skipped_count


def create_input_parameter_file(processed_dir: str, filenames: list[str]) -> None:
    """Create FFmpeg input parameter file."""
    with open(os.path.join(processed_dir, "filelist.txt"), "w") as file:
        for filename in filenames:
            line = "file '{fname}'\n".format(fname=filename)
            file.write(line)


def parse_ffmpeg_progress(stderr_line: str) -> tuple[float, int, int] | None:
    """Parse FFmpeg stderr line for progress information.

    Returns:
        tuple: (progress_percent, current_seconds, output_bytes) or None
    """
    if not stderr_line:
        return None

    try:
        time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})", stderr_line)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = float(time_match.group(3))
            current_seconds = int(hours * 3600 + minutes * 60 + seconds)

            size_match = re.search(r"size=(\d+)kB", stderr_line)
            output_bytes = int(size_match.group(1)) * 1024 if size_match else 0

            return (0.0, current_seconds, output_bytes)

    except (ValueError, AttributeError):
        pass

    return None


def join_videofile(
    processed_dir: str,
    output_filename: str,
    console: Console,
    progress: Progress,
    join_task: TaskID,
) -> tuple[bool, str, int]:
    """Join video files using FFmpeg with progress monitoring.

    Returns:
        tuple: (success, error_message, output_size)
    """
    output_path = os.path.join(processed_dir, output_filename + ".MP4")

    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        os.path.join(processed_dir, "filelist.txt"),
        "-c",
        "copy",
        output_path,
    ]

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        last_output_size = 0
        stderr_lines = []

        if process.stderr:
            for line in process.stderr:
                stderr_lines.append(line)
                result = parse_ffmpeg_progress(line)
                if result and result[2] > 0:
                    _, _, output_bytes = result
                    if output_bytes > last_output_size:
                        last_output_size = output_bytes

        process.wait()

        if process.returncode == 0:
            output_size = get_file_size(output_path)
            return True, "", output_size
        else:
            error_output = "".join(stderr_lines)
            return False, error_output, 0

    except FileNotFoundError:
        return False, "FFmpeg not found. Please install FFmpeg.", 0
    except Exception as e:
        return False, str(e), 0


def delete_input_files(
    processed_dir: str, input_files: list[str], console: Console
) -> bool:
    """Delete input files after successful join."""
    deleted_count = 0

    for filename in input_files:
        try:
            os.remove(os.path.join(processed_dir, filename))
            deleted_count += 1
        except Exception as e:
            print_warning(console, f"Failed to delete {filename}: {e}")

    if deleted_count > 0:
        print_success(console, f"Cleaned up {deleted_count} chunk file(s)")

    return True


def display_final_summary(stats: ProcessingStats, console: Console) -> None:
    """Display the final processing summary."""
    print_section_header(console, "Processing Complete")

    summary_data = {
        "Groups Processed": f"{stats.groups_processed}/{stats.groups_total}",
        "Files Copied": str(stats.files_copied),
        "Files Joined": str(stats.files_joined),
        "Total Input Size": format_file_size(stats.total_input_size),
        "Total Output Size": format_file_size(stats.total_output_size),
        "Disk Space Saved": format_file_size(stats.space_saved),
        "Execution Time": format_duration(stats.execution_time),
    }

    create_summary_table(console, summary_data, "Summary Statistics")

    if stats.groups_processed == stats.groups_total and not stats.errors:
        print_success(console, "All operations completed successfully!")
    else:
        if stats.groups_processed < stats.groups_total:
            print_warning(
                console,
                f"Only {stats.groups_processed}/{stats.groups_total} groups were processed",
            )

        if stats.errors:
            print_error(console, f"Encountered {len(stats.errors)} error(s)")

            for error_type, error_msg, details in stats.errors:
                create_error_panel(console, error_type, error_msg, details)


def main() -> None:
    console = get_console()

    print_banner(console)

    media_dir = "/media/benedict/disk/DCIM/100MEDIA"
    processed_media_dir = "./processed"

    timer = Timer()
    timer.start()

    errors = []

    print_section_header(console, "Initialization")

    if not validate_directory(media_dir, console):
        return

    if not validate_directory(processed_media_dir, console):
        try:
            os.makedirs(processed_media_dir, exist_ok=True)
            print_success(console, f"Created directory: {processed_media_dir}")
        except Exception as e:
            create_error_panel(
                console,
                "Directory Creation Failed",
                f"Could not create {processed_media_dir}: {e}",
            )
            return

    if not clear_processed_dir(processed_media_dir, console):
        pass

    try:
        video_filenames = list_filenames(media_dir, console)

        if not video_filenames:
            print_warning(console, f"No video files found in {media_dir}")
            return

        print_info(
            console, f"Found {len(video_filenames)} video file(s) in {media_dir}"
        )

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            copy_task = progress.add_task("[cyan]Copying files...", total=0)

            if not copy_files_to_processed(
                media_dir,
                processed_media_dir,
                video_filenames,
                console,
                progress,
                copy_task,
            ):
                return

            progress.stop_task(copy_task)

            video_filenames = list_filenames(processed_media_dir, console)
            grouped_filenames, group_info_list, skipped_count = group_related_videos(
                video_filenames, processed_media_dir, console
            )

            total_size = sum(gi.total_size for gi in group_info_list)

            if not check_disk_space(processed_media_dir, total_size, console):
                pass

            if not grouped_filenames:
                print_warning(console, "No video groups to join")
                return

            print_section_header(console, "Processing Groups")

            groups_total = len(group_info_list)
            groups_processed = 0
            files_joined = 0
            total_output_size = 0
            total_input_size = total_size

            join_task = progress.add_task(
                "[cyan]Joining videos...", total=len(group_info_list)
            )

            for idx, group_info in enumerate(
                sorted(group_info_list, key=lambda x: x.group_name)
            ):
                group_name = group_info.group_name
                chunk_files = grouped_filenames[group_name]

                console.print(
                    f"\n[{idx + 1}/{groups_total}] Processing [cyan]{group_name}[/cyan] ({group_info.chunk_count} chunks)..."
                )

                create_input_parameter_file(processed_media_dir, chunk_files)

                success, error_msg, output_size = join_videofile(
                    processed_media_dir, group_name, console, progress, join_task
                )

                if success:
                    print_success(
                        console,
                        f"Joined {group_name} ({format_file_size(output_size)})",
                    )
                    delete_input_files(processed_media_dir, chunk_files, console)
                    groups_processed += 1
                    files_joined += 1
                    total_output_size += output_size
                    progress.update(join_task, completed=idx + 1)
                else:
                    print_error(console, f"Failed to join {group_name}")
                    errors.append(
                        ("Join Failed", f"Could not join {group_name}", error_msg)
                    )

            progress.stop_task(join_task)

        timer.stop()

        stats = ProcessingStats(
            groups_processed=groups_processed,
            groups_total=groups_total,
            files_copied=len(video_filenames),
            files_joined=files_joined,
            total_input_size=total_input_size,
            total_output_size=total_output_size,
            space_saved=total_input_size - total_output_size + (skipped_count * 0),
            execution_time=timer.elapsed(),
            errors=errors,
        )

        display_final_summary(stats, console)

    except KeyboardInterrupt:
        print_warning(console, "\nOperation cancelled by user")
    except Exception as e:
        create_error_panel(
            console, "Unexpected Error", f"An unexpected error occurred: {e}"
        )
        raise


if __name__ == "__main__":
    main()
