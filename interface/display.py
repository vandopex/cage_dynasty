# interface/display.py
# Display utilities for Cage Dynasty CLI
# Lines: 296

"""
Display utilities, formatting functions, and UI helpers.

This module provides all text-based UI components used by the CLI:
- Terminal constants and box drawing characters
- Color codes and formatting
- Input/output helpers
- Visual elements (stat bars, letter grades)
"""

from typing import Optional, List, Tuple
import os


# ============================================================================
# CONSTANTS
# ============================================================================

TERMINAL_WIDTH = 70

# Box drawing (ASCII for maximum compatibility)
BOX_H = "-"
BOX_V = "|"
BOX_TL = "+"
BOX_TR = "+"
BOX_BL = "+"
BOX_BR = "+"

VERSION = "0.3.0"

TITLE_ART = r"""
   ____    _    ____ _____   ______   ___   _    _    ____ _______   __
  / ___|  / \  / ___| ____| |  _ \ \ / / \ | |  / \  / ___|_   _\ \ / /
 | |     / _ \| |  _|  _|   | | | \ V /|  \| | / _ \ \___ \ | |  \ V / 
 | |___ / ___ \ |_| | |___  | |_| || | | |\  |/ ___ \ ___) || |   | |  
  \____/_/   \_\____|_____| |____/ |_| |_| \_/_/   \_\____/ |_|   |_|  
"""


# ============================================================================
# COLORS
# ============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Standard colors
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    
    # Semantic colors
    GOLD = "\033[93m"
    WIN = "\033[92m"
    LOSS = "\033[91m"
    NEUTRAL = "\033[96m"
    HIGHLIGHT = "\033[1;97m"
    ORANGE = "\033[38;5;208m"
    
    _enabled = True
    
    @classmethod
    def disable(cls) -> None:
        """Disable all colors (for non-color terminals or testing)."""
        cls._enabled = False
        for attr in ['RESET', 'BOLD', 'DIM', 'RED', 'GREEN', 'YELLOW', 
                     'BLUE', 'MAGENTA', 'CYAN', 'WHITE', 'GOLD', 'WIN',
                     'LOSS', 'NEUTRAL', 'HIGHLIGHT', 'ORANGE']:
            setattr(cls, attr, "")
    
    @classmethod
    def enable(cls) -> None:
        """Re-enable colors."""
        cls._enabled = True
        cls.RESET = "\033[0m"
        cls.BOLD = "\033[1m"
        cls.DIM = "\033[2m"
        cls.RED = "\033[91m"
        cls.GREEN = "\033[92m"
        cls.YELLOW = "\033[93m"
        cls.BLUE = "\033[94m"
        cls.MAGENTA = "\033[95m"
        cls.CYAN = "\033[96m"
        cls.WHITE = "\033[97m"
        cls.GOLD = "\033[93m"
        cls.WIN = "\033[92m"
        cls.LOSS = "\033[91m"
        cls.NEUTRAL = "\033[96m"
        cls.HIGHLIGHT = "\033[1;97m"
        cls.ORANGE = "\033[38;5;208m"
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if colors are enabled."""
        return cls._enabled


def colored(text: str, color: str) -> str:
    """Apply color to text."""
    return f"{color}{text}{Colors.RESET}"


# ============================================================================
# FORMATTING FUNCTIONS
# ============================================================================

def format_record(wins: int, losses: int, draws: int = 0) -> str:
    """Format a fight record as W-L or W-L-D."""
    if draws:
        return f"{wins}-{losses}-{draws}"
    return f"{wins}-{losses}"


def format_record_colored(wins: int, losses: int, draws: int = 0) -> str:
    """Format a fight record with colored numbers."""
    w = colored(str(wins), Colors.WIN)
    l = colored(str(losses), Colors.LOSS)
    if draws > 0:
        d = colored(str(draws), Colors.NEUTRAL)
        return f"{w}-{l}-{d}"
    return f"{w}-{l}"


def format_money(amount: int) -> str:
    """Format currency with commas and dollar sign."""
    return f"${amount:,}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a value as a percentage."""
    return f"{value * 100:.{decimals}f}%"


def format_height(height_cm: int) -> str:
    """Convert centimeters to feet and inches."""
    total_inches = height_cm / 2.54
    feet = int(total_inches // 12)
    inches = int(total_inches % 12)
    return f"{feet}'{inches}\""


def format_reach(reach_cm: int) -> str:
    """Convert centimeters to inches for reach."""
    return f"{int(reach_cm / 2.54)}\""


# ============================================================================
# VISUAL ELEMENTS
# ============================================================================

def stat_bar(value: int, width: int = 20) -> str:
    """Create a visual stat bar with color coding.
    
    Args:
        value: Stat value (0-100)
        width: Width of the bar in characters
        
    Returns:
        Colored bar string with value
    """
    filled = int((value / 100) * width)
    empty = width - filled
    
    if value >= 80:
        color = Colors.GREEN
    elif value >= 60:
        color = Colors.YELLOW
    elif value >= 40:
        color = Colors.ORANGE
    else:
        color = Colors.RED
    
    bar = "#" * filled + "." * empty
    return f"{color}{bar}{Colors.RESET} {value}"


def stat_letter_grade(value: int) -> str:
    """Convert a stat value to a letter grade with color.
    
    Args:
        value: Stat value (0-100)
        
    Returns:
        Colored letter grade (A+ through F)
    """
    if value >= 90:
        return colored("A+", Colors.GREEN)
    elif value >= 85:
        return colored("A", Colors.GREEN)
    elif value >= 80:
        return colored("A-", Colors.GREEN)
    elif value >= 75:
        return colored("B+", Colors.CYAN)
    elif value >= 70:
        return colored("B", Colors.CYAN)
    elif value >= 65:
        return colored("B-", Colors.CYAN)
    elif value >= 60:
        return colored("C+", Colors.YELLOW)
    elif value >= 55:
        return colored("C", Colors.YELLOW)
    elif value >= 50:
        return colored("C-", Colors.YELLOW)
    elif value >= 45:
        return colored("D+", Colors.ORANGE)
    elif value >= 40:
        return colored("D", Colors.ORANGE)
    else:
        return colored("F", Colors.RED)


def progress_bar(current: int, total: int, width: int = 20) -> str:
    """Create a progress bar.
    
    Args:
        current: Current progress value
        total: Total/maximum value
        width: Width of the bar
        
    Returns:
        Progress bar string like [####....] 40%
    """
    if total <= 0:
        return "[" + "." * width + "] 0%"
    
    percent = min(current / total, 1.0)
    filled = int(percent * width)
    empty = width - filled
    percentage = int(percent * 100)
    
    return f"[{'#' * filled}{'.' * empty}] {percentage}%"


# ============================================================================
# SCREEN FUNCTIONS
# ============================================================================

def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str) -> None:
    """Print a boxed header with title."""
    print()
    print(BOX_TL + BOX_H * (TERMINAL_WIDTH - 2) + BOX_TR)
    print(BOX_V + title.center(TERMINAL_WIDTH - 2) + BOX_V)
    print(BOX_BL + BOX_H * (TERMINAL_WIDTH - 2) + BOX_BR)
    print()


def print_divider() -> None:
    """Print a horizontal divider line."""
    print(BOX_H * TERMINAL_WIDTH)


def print_box(lines: List[str], title: Optional[str] = None) -> None:
    """Print content in a box with optional title.
    
    Args:
        lines: List of strings to display
        title: Optional title for the box
    """
    print(BOX_TL + BOX_H * (TERMINAL_WIDTH - 2) + BOX_TR)
    if title:
        print(BOX_V + title.center(TERMINAL_WIDTH - 2) + BOX_V)
        print(BOX_V + BOX_H * (TERMINAL_WIDTH - 2) + BOX_V)
    for line in lines:
        display_line = line[:TERMINAL_WIDTH - 4]
        padding = TERMINAL_WIDTH - 4 - len(display_line)
        print(BOX_V + " " + display_line + " " * padding + " " + BOX_V)
    print(BOX_BL + BOX_H * (TERMINAL_WIDTH - 2) + BOX_BR)


def print_menu(options: List[Tuple[str, str]], prompt: str = "Choose") -> None:
    """Print a menu of options.
    
    Args:
        options: List of (key, description) tuples
        prompt: Optional prompt text (unused but kept for compatibility)
    """
    print()
    for key, description in options:
        print(f"  [{key}] {description}")
    print()


def print_table(headers: List[str], rows: List[List[str]], widths: Optional[List[int]] = None) -> None:
    """Print a simple text table.
    
    Args:
        headers: Column headers
        rows: List of row data (each row is a list of strings)
        widths: Optional column widths (auto-calculated if None)
    """
    if not widths:
        widths = [max(len(h), max(len(str(row[i])) for row in rows) if rows else 0) 
                  for i, h in enumerate(headers)]
    
    # Header
    header_line = "  " + "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print("  " + "-" * (sum(widths) + 2 * (len(widths) - 1)))
    
    # Rows
    for row in rows:
        row_line = "  " + "  ".join(str(cell).ljust(w) for cell, w in zip(row, widths))
        print(row_line)


# ============================================================================
# INPUT FUNCTIONS
# ============================================================================

def get_input(prompt: str = "> ") -> str:
    """Get user input with a prompt.
    
    Args:
        prompt: The prompt to display
        
    Returns:
        User input string (stripped), or empty string on EOF/interrupt
    """
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def get_choice(options: List[str], prompt: str = "Choose") -> Optional[str]:
    """Get a choice from a list of valid options.
    
    Args:
        options: List of valid option strings
        prompt: Prompt to display
        
    Returns:
        The chosen option (lowercase) or None if invalid
    """
    choice = get_input(f"{prompt}: ").lower()
    if choice in [o.lower() for o in options]:
        return choice
    return None


def get_number(prompt: str = "Enter number: ", min_val: int = None, max_val: int = None) -> Optional[int]:
    """Get a number from the user with optional range validation.
    
    Args:
        prompt: Prompt to display
        min_val: Minimum valid value (inclusive)
        max_val: Maximum valid value (inclusive)
        
    Returns:
        The number entered, or None if invalid
    """
    try:
        value = int(get_input(prompt))
        if min_val is not None and value < min_val:
            return None
        if max_val is not None and value > max_val:
            return None
        return value
    except ValueError:
        return None


def confirm(message: str) -> bool:
    """Ask for yes/no confirmation.
    
    Args:
        message: The confirmation message
        
    Returns:
        True if user confirms (y/yes), False otherwise
    """
    response = get_input(f"{message} (y/n): ").lower()
    return response in ("y", "yes")


def pause(message: str = "Press Enter to continue...") -> None:
    """Pause and wait for user to press Enter.
    
    Args:
        message: Message to display
    """
    get_input(message)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Constants
    "TERMINAL_WIDTH",
    "BOX_H", "BOX_V", "BOX_TL", "BOX_TR", "BOX_BL", "BOX_BR",
    "VERSION",
    "TITLE_ART",
    
    # Colors
    "Colors",
    "colored",
    
    # Formatting
    "format_record",
    "format_record_colored",
    "format_money",
    "format_percentage",
    "format_height",
    "format_reach",
    
    # Visual elements
    "stat_bar",
    "stat_letter_grade",
    "progress_bar",
    
    # Screen functions
    "clear_screen",
    "print_header",
    "print_divider",
    "print_box",
    "print_menu",
    "print_table",
    
    # Input functions
    "get_input",
    "get_choice",
    "get_number",
    "confirm",
    "pause",
]
