from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def get_console() -> Console:
    """Get a Rich Console instance for terminal output."""
    return Console()


def print_banner(console: Console) -> None:
    """Display ASCII art banner."""
    banner = r"""
   ____                  ____  __
  / __ \____  ___  ____/ __ \/ /___ _
 / /_/ / __ \/ _ \/ __  / /_/ / / __ `/
/ _, _/ /_/ /  __/ /_/ / _, _/ / /_/ /
/_/ |_|\____/\___/\__,_/_/ |_/_/\__,_/
            [cyan]Video Joiner[/cyan]"""
    console.print(banner, justify="center")
    console.print()


def print_success(console: Console, message: str) -> None:
    """Print a success message with green checkmark."""
    console.print(f"[green]✓[/green] {message}")


def print_error(console: Console, message: str) -> None:
    """Print an error message with red X."""
    console.print(f"[red]✗[/red] {message}")


def print_warning(console: Console, message: str) -> None:
    """Print a warning message with yellow warning icon."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_info(console: Console, message: str) -> None:
    """Print an info message with blue info icon."""
    console.print(f"[cyan]ℹ[/cyan] {message}")


def print_processing(console: Console, message: str) -> None:
    """Print a processing message with hourglass icon."""
    console.print(f"[blue]⏳[/blue] {message}")


def print_section_header(console: Console, title: str) -> None:
    """Print a section header with a separator."""
    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    console.print("[dim]" + "─" * len(title) + "[/dim]\n")


def create_error_panel(
    console: Console, error_type: str, message: str, details: str | None = None
) -> None:
    """Create a formatted error panel."""
    error_text = Text()
    error_text.append(error_type + "\n", style="bold red")
    error_text.append(message, style="white")

    if details:
        error_text.append("\n\nDetails:\n", style="bold yellow")
        error_text.append(details, style="dim")

    console.print(Panel(error_text, title="[red]Error[/red]", border_style="red"))


def create_summary_table(
    console: Console, data: dict[str, str], title: str = "Summary"
) -> None:
    """Create a summary table from a dictionary."""
    from rich.table import Table

    table = Table(title=title, box=None, show_header=False)
    table.add_column(style="cyan", width=25)
    table.add_column(style="white")

    for key, value in data.items():
        table.add_row(key, value)

    console.print(table)
