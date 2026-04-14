#!/usr/bin/env python3
# ============================================================
#  Voice Studio — A Termux Text-to-Speech Tool
#  Powered by edge-tts | No API key required
#  Works fully offline-menu, online for TTS generation
# ============================================================

import os
import sys
import json
import time
import asyncio
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# --------------- Dependency Check ---------------
def check_dependencies():
    """Make sure required Python packages are installed."""
    missing = []
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        missing.append("edge-tts")
    try:
        from rich.console import Console  # noqa: F401
    except ImportError:
        missing.append("rich")
    try:
        import colorama  # noqa: F401
    except ImportError:
        missing.append("colorama")

    if missing:
        print("\n[!] Missing dependencies: " + ", ".join(missing))
        print("    Run:  pip install -r requirements.txt\n")
        sys.exit(1)

check_dependencies()

# --------------- Imports (after check) ---------------
import edge_tts
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from colorama import init, Fore, Style

# Initialize colorama for cross-platform color support
init(autoreset=True)

# --------------- Rich Console ---------------
console = Console()

# --------------- Paths ---------------
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
HISTORY_DIR = BASE_DIR / "history"
HISTORY_FILE = HISTORY_DIR / "history.json"
ASSETS_DIR = BASE_DIR / "assets"

# Create directories if they don't exist
for folder in [OUTPUT_DIR, HISTORY_DIR, ASSETS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# --------------- Default Voices ---------------
VOICES = {
    "English": {
        "Female": "en-US-AriaNeural",
        "Male": "en-US-GuyNeural",
    },
    "Urdu": {
        "Female": "ur-PK-UzmaNeural",
        "Male": "ur-PK-AsadNeural",
    },
    "Hindi": {
        "Female": "hi-IN-SwaraNeural",
        "Male": "hi-IN-MadhurNeural",
    },
}

# ============================================================
#  HISTORY HELPERS
# ============================================================

def load_history() -> list:
    """Load generation history from JSON file."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_history(history: list):
    """Save generation history to JSON file."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)


def add_history_entry(filename: str, text: str, voice: str, language: str, gender: str):
    """Add a new entry to the generation history."""
    history = load_history()
    filepath = OUTPUT_DIR / filename
    size = filepath.stat().st_size if filepath.exists() else 0
    entry = {
        "filename": filename,
        "text": text[:100] + ("..." if len(text) > 100 else ""),
        "voice": voice,
        "language": language,
        "gender": gender,
        "size_bytes": size,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    history.append(entry)
    save_history(history)

# ============================================================
#  UTILITY HELPERS
# ============================================================

def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def format_size(size_bytes: int) -> str:
    """Convert bytes to a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def check_internet() -> bool:
    """Quick internet connectivity check using edge-tts list voices."""
    try:
        # Try a lightweight socket connection
        import socket
        socket.setdefaulttimeout(5)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except OSError:
        return False


def play_audio(filepath: str):
    """Play an MP3 file using termux-media-player (Termux) or fallback."""
    try:
        # Try termux-media-player first (requires termux-api)
        result = subprocess.run(
            ["termux-media-player", "play", filepath],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            console.print("[bold green]▶  Now playing audio...[/bold green]")
        else:
            raise FileNotFoundError
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: try mpv, play (sox), or aplay
        for player in ["mpv", "play", "aplay", "ffplay"]:
            try:
                subprocess.Popen(
                    [player, filepath],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                console.print(f"[bold green]▶  Playing with {player}...[/bold green]")
                return
            except FileNotFoundError:
                continue
        console.print("[bold yellow]⚠  No audio player found. Install termux-api or mpv.[/bold yellow]")


def stop_audio():
    """Stop currently playing audio via termux-media-player."""
    try:
        result = subprocess.run(
            ["termux-media-player", "stop"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            console.print("[bold green]⏹  Audio playback stopped.[/bold green]")
        else:
            raise FileNotFoundError
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: kill known players
        for player in ["mpv", "play", "aplay", "ffplay"]:
            try:
                subprocess.run(["pkill", player], capture_output=True, timeout=5)
            except Exception:
                pass
        console.print("[bold yellow]⏹  Attempted to stop playback.[/bold yellow]")

# ============================================================
#  BANNER
# ============================================================

def show_banner():
    """Display the stylish ASCII startup banner for Voice Studio."""
    banner_text = r"""
[bold cyan]
 ██╗   ██╗ ██████╗ ██╗ ██████╗███████╗
 ██║   ██║██╔═══██╗██║██╔════╝██╔════╝
 ██║   ██║██║   ██║██║██║     █████╗  
 ╚██╗ ██╔╝██║   ██║██║██║     ██╔══╝  
  ╚████╔╝ ╚██████╔╝██║╚██████╗███████╗
   ╚═══╝   ╚═════╝ ╚═╝ ╚═════╝╚══════╝
 ███████╗████████╗██╗   ██╗██████╗ ██╗ ██████╗ 
 ██╔════╝╚══██╔══╝██║   ██║██╔══██╗██║██╔═══██╗
 ███████╗   ██║   ██║   ██║██║  ██║██║██║   ██║
 ╚════██║   ██║   ██║   ██║██║  ██║██║██║   ██║
 ███████║   ██║   ╚██████╔╝██████╔╝██║╚██████╔╝
 ╚══════╝   ╚═╝    ╚═════╝ ╚═════╝ ╚═╝ ╚═════╝
[/bold cyan]"""

    console.print(banner_text)
    console.print(
        Panel(
            Text("Voice Studio — Text to Speech for Termux", justify="center", style="bold white"),
            subtitle="[dim]Powered by edge-tts | No API Key Required[/dim]",
            border_style="bright_cyan",
            box=box.DOUBLE,
        )
    )
    console.print()

# ============================================================
#  MAIN MENU
# ============================================================

def show_menu():
    """Display the main menu with all options."""
    table = Table(
        title="[bold bright_cyan]📋  MAIN MENU[/bold bright_cyan]",
        box=box.ROUNDED,
        border_style="bright_cyan",
        title_style="bold bright_cyan",
        show_lines=True,
    )
    table.add_column("Option", style="bold yellow", justify="center", width=8)
    table.add_column("Description", style="bold white", width=45)

    menu_items = [
        ("1", "🎙  Generate Speech from Text"),
        ("2", "📋  Preview Available Voices"),
        ("3", "📂  View Generation History"),
        ("4", "🔍  Search Generated Files"),
        ("5", "🗑  Delete Old Generated Files"),
        ("6", "🧹  Clear Full History"),
        ("7", "⏹  Stop Currently Playing Audio"),
        ("8", "📊  Show Total Generated Files Count"),
        ("9", "💾  Show Total Storage Used"),
        ("0", "❌  Exit Voice Studio"),
    ]

    for opt, desc in menu_items:
        table.add_row(opt, desc)

    console.print(table)
    console.print()

# ============================================================
#  FEATURE 1 — Generate Speech
# ============================================================

def select_language() -> str | None:
    """Let user pick a language. Returns language name or None."""
    console.print("\n[bold bright_cyan]🌐  Select Language:[/bold bright_cyan]")
    console.print("  [bold yellow]1[/bold yellow]  English")
    console.print("  [bold yellow]2[/bold yellow]  Urdu")
    console.print("  [bold yellow]3[/bold yellow]  Hindi")
    choice = input(f"\n{Fore.CYAN}  Enter choice (1-3): {Style.RESET_ALL}").strip()
    mapping = {"1": "English", "2": "Urdu", "3": "Hindi"}
    if choice not in mapping:
        console.print("[bold red]✖  Invalid language choice.[/bold red]")
        return None
    return mapping[choice]


def select_gender() -> str | None:
    """Let user pick Male or Female. Returns gender string or None."""
    console.print("\n[bold bright_cyan]🧑  Select Voice Gender:[/bold bright_cyan]")
    console.print("  [bold yellow]1[/bold yellow]  Female")
    console.print("  [bold yellow]2[/bold yellow]  Male")
    choice = input(f"\n{Fore.CYAN}  Enter choice (1-2): {Style.RESET_ALL}").strip()
    mapping = {"1": "Female", "2": "Male"}
    if choice not in mapping:
        console.print("[bold red]✖  Invalid gender choice.[/bold red]")
        return None
    return mapping[choice]


async def generate_speech(text: str, voice: str, output_path: str):
    """Use edge-tts to generate speech and save to file."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def feature_generate_speech():
    """Full workflow: get text → language → gender → filename → generate → play."""
    console.print(Panel("[bold bright_cyan]🎙  Generate Speech from Text[/bold bright_cyan]", border_style="cyan"))

    # --- Check internet ---
    if not check_internet():
        console.print("[bold red]✖  No internet connection![/bold red]")
        console.print("[dim]  edge-tts requires internet to generate speech. Please check your connection.[/dim]")
        return

    # --- Get text ---
    text = input(f"\n{Fore.CYAN}  Enter the text you want to convert to speech:\n  > {Style.RESET_ALL}").strip()
    if not text:
        console.print("[bold red]✖  Text cannot be empty![/bold red]")
        return

    # --- Select language ---
    language = select_language()
    if not language:
        return

    # --- Select gender ---
    gender = select_gender()
    if not gender:
        return

    # --- Resolve voice ---
    voice = VOICES[language][gender]
    console.print(f"\n  [dim]Using voice:[/dim] [bold green]{voice}[/bold green]")

    # --- Get filename ---
    filename = input(f"\n{Fore.CYAN}  Enter filename (without .mp3): {Style.RESET_ALL}").strip()
    if not filename:
        console.print("[bold red]✖  Filename cannot be empty![/bold red]")
        return

    # Sanitize filename (remove special characters)
    safe_filename = "".join(c for c in filename if c.isalnum() or c in (" ", "-", "_")).strip()
    if not safe_filename:
        console.print("[bold red]✖  Invalid filename after sanitization![/bold red]")
        return

    safe_filename += ".mp3"
    output_path = str(OUTPUT_DIR / safe_filename)

    # --- Generate with spinner ---
    console.print()
    try:
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold cyan]Generating speech, please wait..."),
            console=console,
        ) as progress:
            task = progress.add_task("generating", total=None)
            asyncio.run(generate_speech(text, voice, output_path))
            progress.update(task, completed=True)
    except Exception as e:
        console.print(f"[bold red]✖  Error generating speech: {e}[/bold red]")
        console.print("[dim]  This may be a network issue. Please try again.[/dim]")
        return

    # --- Verify file ---
    if not os.path.exists(output_path):
        console.print("[bold red]✖  File was not created. Something went wrong.[/bold red]")
        return

    file_size = os.path.getsize(output_path)
    console.print(f"\n[bold green]✔  Speech saved:[/bold green] {safe_filename}  ({format_size(file_size)})")

    # --- Add to history ---
    add_history_entry(safe_filename, text, voice, language, gender)

    # --- Auto-play ---
    console.print()
    play_audio(output_path)

# ============================================================
#  FEATURE 2 — Preview Available Voices
# ============================================================

def feature_preview_voices():
    """Display a table of all available default voices."""
    console.print(Panel("[bold bright_cyan]📋  Available Voices[/bold bright_cyan]", border_style="cyan"))

    table = Table(box=box.ROUNDED, border_style="bright_cyan", show_lines=True)
    table.add_column("#", style="bold yellow", justify="center", width=4)
    table.add_column("Language", style="bold white", width=12)
    table.add_column("Gender", style="bold magenta", width=10)
    table.add_column("Voice ID", style="bold green", width=25)

    idx = 1
    for lang, genders in VOICES.items():
        for gender, voice_id in genders.items():
            table.add_row(str(idx), lang, gender, voice_id)
            idx += 1

    console.print(table)

# ============================================================
#  FEATURE 3 — View History
# ============================================================

def feature_view_history():
    """Display generation history in a nice table."""
    console.print(Panel("[bold bright_cyan]📂  Generation History[/bold bright_cyan]", border_style="cyan"))

    history = load_history()
    if not history:
        console.print("[bold yellow]  No history found. Generate some speech first![/bold yellow]")
        return

    table = Table(box=box.ROUNDED, border_style="bright_cyan", show_lines=True)
    table.add_column("#", style="bold yellow", justify="center", width=4)
    table.add_column("Filename", style="bold white", width=25)
    table.add_column("Language", style="bold magenta", width=10)
    table.add_column("Gender", style="bold blue", width=8)
    table.add_column("Size", style="bold green", width=10)
    table.add_column("Created", style="dim", width=20)
    table.add_column("Text Preview", style="dim italic", width=30)

    for i, entry in enumerate(history, 1):
        table.add_row(
            str(i),
            entry.get("filename", "N/A"),
            entry.get("language", "N/A"),
            entry.get("gender", "N/A"),
            format_size(entry.get("size_bytes", 0)),
            entry.get("created_at", "N/A"),
            entry.get("text", "N/A"),
        )

    console.print(table)

# ============================================================
#  FEATURE 4 — Search Files
# ============================================================

def feature_search_files():
    """Search generated MP3 files by name."""
    console.print(Panel("[bold bright_cyan]🔍  Search Generated Files[/bold bright_cyan]", border_style="cyan"))

    query = input(f"\n{Fore.CYAN}  Enter search keyword: {Style.RESET_ALL}").strip().lower()
    if not query:
        console.print("[bold red]✖  Search keyword cannot be empty![/bold red]")
        return

    # Search in output directory
    results = []
    for f in OUTPUT_DIR.iterdir():
        if f.is_file() and query in f.name.lower():
            stat = f.stat()
            results.append({
                "name": f.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })

    if not results:
        console.print(f"[bold yellow]  No files found matching '{query}'.[/bold yellow]")
        return

    table = Table(box=box.ROUNDED, border_style="bright_cyan", show_lines=True)
    table.add_column("#", style="bold yellow", justify="center", width=4)
    table.add_column("Filename", style="bold white", width=30)
    table.add_column("Size", style="bold green", width=12)
    table.add_column("Modified", style="dim", width=20)

    for i, r in enumerate(results, 1):
        table.add_row(str(i), r["name"], format_size(r["size"]), r["created"])

    console.print(table)
    console.print(f"\n  [bold green]Found {len(results)} file(s).[/bold green]")

# ============================================================
#  FEATURE 5 — Delete Old Files
# ============================================================

def feature_delete_files():
    """Delete specific or all generated MP3 files."""
    console.print(Panel("[bold bright_cyan]🗑  Delete Generated Files[/bold bright_cyan]", border_style="cyan"))

    files = sorted([f for f in OUTPUT_DIR.iterdir() if f.is_file() and f.suffix == ".mp3"])
    if not files:
        console.print("[bold yellow]  No MP3 files found in output folder.[/bold yellow]")
        return

    # List files
    table = Table(box=box.ROUNDED, border_style="bright_cyan", show_lines=True)
    table.add_column("#", style="bold yellow", justify="center", width=4)
    table.add_column("Filename", style="bold white", width=30)
    table.add_column("Size", style="bold green", width=12)

    for i, f in enumerate(files, 1):
        table.add_row(str(i), f.name, format_size(f.stat().st_size))

    console.print(table)

    console.print("\n  [bold yellow]Enter file number to delete, 'all' to delete all, or 'c' to cancel.[/bold yellow]")
    choice = input(f"\n{Fore.CYAN}  Choice: {Style.RESET_ALL}").strip().lower()

    if choice == "c":
        console.print("[dim]  Cancelled.[/dim]")
        return

    if choice == "all":
        confirm = input(f"{Fore.RED}  Are you sure? This will delete ALL MP3 files! (yes/no): {Style.RESET_ALL}").strip().lower()
        if confirm == "yes":
            count = 0
            for f in files:
                try:
                    f.unlink()
                    count += 1
                except Exception:
                    pass
            console.print(f"[bold green]✔  Deleted {count} file(s).[/bold green]")
        else:
            console.print("[dim]  Cancelled.[/dim]")
        return

    # Delete single file by number
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(files):
            target = files[idx]
            target.unlink()
            console.print(f"[bold green]✔  Deleted: {target.name}[/bold green]")
        else:
            console.print("[bold red]✖  Invalid file number.[/bold red]")
    except ValueError:
        console.print("[bold red]✖  Invalid input. Enter a number, 'all', or 'c'.[/bold red]")

# ============================================================
#  FEATURE 6 — Clear Full History
# ============================================================

def feature_clear_history():
    """Clear the entire generation history JSON file."""
    console.print(Panel("[bold bright_cyan]🧹  Clear Full History[/bold bright_cyan]", border_style="cyan"))

    history = load_history()
    if not history:
        console.print("[bold yellow]  History is already empty.[/bold yellow]")
        return

    console.print(f"  [dim]Current history has {len(history)} entries.[/dim]")
    confirm = input(f"\n{Fore.RED}  Are you sure you want to clear all history? (yes/no): {Style.RESET_ALL}").strip().lower()

    if confirm == "yes":
        save_history([])
        console.print("[bold green]✔  History cleared successfully.[/bold green]")
    else:
        console.print("[dim]  Cancelled.[/dim]")

# ============================================================
#  FEATURE 7 — Stop Audio
# ============================================================

def feature_stop_audio():
    """Stop any currently playing audio."""
    console.print(Panel("[bold bright_cyan]⏹  Stop Playing Audio[/bold bright_cyan]", border_style="cyan"))
    stop_audio()

# ============================================================
#  FEATURE 8 — Total Files Count
# ============================================================

def feature_total_files():
    """Show total count of generated MP3 files."""
    console.print(Panel("[bold bright_cyan]📊  Total Generated Files[/bold bright_cyan]", border_style="cyan"))

    mp3_files = [f for f in OUTPUT_DIR.iterdir() if f.is_file() and f.suffix == ".mp3"]
    count = len(mp3_files)

    if count == 0:
        console.print("[bold yellow]  No MP3 files found in output folder.[/bold yellow]")
    else:
        console.print(f"  [bold green]Total generated MP3 files: {count}[/bold green]")

# ============================================================
#  FEATURE 9 — Total Storage Used
# ============================================================

def feature_total_storage():
    """Show total disk space used by generated MP3 files."""
    console.print(Panel("[bold bright_cyan]💾  Total Storage Used[/bold bright_cyan]", border_style="cyan"))

    mp3_files = [f for f in OUTPUT_DIR.iterdir() if f.is_file() and f.suffix == ".mp3"]

    if not mp3_files:
        console.print("[bold yellow]  No MP3 files found in output folder.[/bold yellow]")
        return

    total_size = sum(f.stat().st_size for f in mp3_files)
    console.print(f"  [bold green]Files: {len(mp3_files)}[/bold green]")
    console.print(f"  [bold green]Total storage used: {format_size(total_size)}[/bold green]")

# ============================================================
#  MAIN LOOP
# ============================================================

def main():
    """Main application entry point — runs the menu loop."""
    clear_screen()
    show_banner()

    while True:
        show_menu()
        choice = input(f"{Fore.CYAN}  ➤  Enter your choice: {Style.RESET_ALL}").strip()
        console.print()

        if choice == "1":
            feature_generate_speech()
        elif choice == "2":
            feature_preview_voices()
        elif choice == "3":
            feature_view_history()
        elif choice == "4":
            feature_search_files()
        elif choice == "5":
            feature_delete_files()
        elif choice == "6":
            feature_clear_history()
        elif choice == "7":
            feature_stop_audio()
        elif choice == "8":
            feature_total_files()
        elif choice == "9":
            feature_total_storage()
        elif choice == "0":
            console.print("[bold bright_cyan]  👋  Thank you for using Voice Studio! Goodbye.\n[/bold bright_cyan]")
            sys.exit(0)
        else:
            console.print("[bold red]✖  Invalid choice! Please select a valid option (0-9).[/bold red]")

        # Pause before showing menu again
        console.print()
        input(f"{Fore.CYAN}  Press Enter to continue...{Style.RESET_ALL}")
        clear_screen()
        show_banner()


# ============================================================
#  ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold bright_cyan]  👋  Interrupted. Goodbye![/bold bright_cyan]\n")
        sys.exit(0)
