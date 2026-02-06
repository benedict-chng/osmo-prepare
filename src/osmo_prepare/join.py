import sys
import os
from typing import NamedTuple
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from osmo_prepare.utils import (
    get_console,
    print_success,
    print_error,
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
    Timer,
)
from osmo_prepare.main import (
    create_input_parameter_file,
    join_videofile,
)


class JoinStats(NamedTuple):
    """Statistics from join operation."""

    input_files_count: int
    total_input_size: int
    output_filename: str
    output_size: int
    execution_time: int


def validate_input_files(filenames: list[str], console: Console) -> bool:
    """Validate that all input files exist."""
    print_section_header(console, "Validating Input Files")

    all_exist = True
    file_info = []

    for filename in filenames:
        if os.path.isfile(filename):
            file_size = get_file_size(filename)
            file_info.append((filename, file_size, True))
            print_success(console, f"{filename} ({format_file_size(file_size)})")
        else:
            file_info.append((filename, 0, False))
            print_error(console, f"{filename} - Not found")
            all_exist = False

    console.print()

    return all_exist


def show_join_summary(
    filenames: list[str], output_filename: str, console: Console
) -> None:
    """Show a summary of the join operation."""
    total_size = sum(get_file_size(f) for f in filenames if os.path.isfile(f))

    summary_data = {
        "Input Files": str(len(filenames)),
        "Total Input Size": format_file_size(total_size),
        "Output File": output_filename + ".MP4",
    }

    create_summary_table(console, summary_data, "Join Summary")
    console.print()


def show_help(console: Console) -> None:
    """Display usage help."""
    help_text = """Join 2 or more video files together.

[cyan]Usage:[/cyan]
    [yellow]osmo-join[/yellow] [green][dest_name][/green] [blue][file1][/blue] [blue][file2][/blue] ...

[cyan]Arguments:[/cyan]
    [green]dest_name[/green]       Name for the output file (without .MP4 extension)
    [blue]file1, file2, ...[/blue]  Video files to join

[cyan]Example:[/cyan]
    osmo-join combined video1.mp4 video2.mp4 video3.mp4
    
    This will create [green]combined.MP4[/green] by joining the three input files.
"""
    console.print(
        Panel(help_text, title="[yellow]osmo-join Help[/yellow]", border_style="cyan")
    )


def display_join_success(stats: JoinStats, console: Console) -> None:
    """Display success message after joining."""
    console.print()

    summary_data = {
        "Input Files": str(stats.input_files_count),
        "Output File": stats.output_filename + ".MP4",
        "Output Size": format_file_size(stats.output_size),
        "Duration": format_duration(stats.execution_time),
    }

    create_summary_table(console, summary_data, "Join Complete")

    print_success(console, "All done!")
    console.print()


def main() -> None:
    console = get_console()

    if len(sys.argv) < 3:
        show_help(console)
        sys.exit(1)

    output_filename = sys.argv[1]
    input_files = sys.argv[2:]

    print_section_header(console, "osmo-join Video Joiner")

    timer = Timer()
    timer.start()

    if not validate_input_files(input_files, console):
        create_error_panel(
            console,
            "Validation Failed",
            "One or more input files do not exist.",
            "Please check the file paths and try again.",
        )
        sys.exit(1)

    show_join_summary(input_files, output_filename, console)

    processed_dir = "./processed"

    print_processing(console, "Preparing to join files...")

    try:
        os.makedirs(processed_dir, exist_ok=True)
    except Exception as e:
        create_error_panel(
            console,
            "Directory Creation Failed",
            f"Could not create {processed_dir}: {e}",
        )
        sys.exit(1)

    create_input_parameter_file(processed_dir=processed_dir, filenames=input_files)

    print_info(console, "Joining video files...")
    console.print("[dim]This may take a while depending on file sizes...[/dim]")
    console.print()

    from rich.progress import (
        Progress,
        BarColumn,
        TextColumn,
        TimeRemainingColumn,
        TransferSpeedColumn,
        TaskID,
    )

    try:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            join_task = progress.add_task("[cyan]Joining videos...", total=100)

            success, error_msg, output_size = join_videofile(
                processed_dir, output_filename, console, progress, join_task
            )

            if success:
                progress.update(join_task, completed=100)
                timer.stop()

                stats = JoinStats(
                    input_files_count=len(input_files),
                    total_input_size=sum(get_file_size(f) for f in input_files),
                    output_filename=output_filename,
                    output_size=output_size,
                    execution_time=timer.elapsed(),
                )

                display_join_success(stats, console)
                sys.exit(0)
            else:
                timer.stop()

                console.print()
                create_error_panel(
                    console,
                    "Join Failed",
                    "FFmpeg encountered an error while joining the videos.",
                    error_msg,
                )
                console.print()
                print_error(console, "Please check:")
                print_info(console, "  • All input files are valid video files")
                print_info(console, "  • All input files have the same codec/format")
                print_info(console, "  • You have sufficient disk space")
                sys.exit(1)

    except KeyboardInterrupt:
        print_error(console, "\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        create_error_panel(
            console, "Unexpected Error", f"An unexpected error occurred: {e}"
        )
        raise


if __name__ == "__main__":
    main()
