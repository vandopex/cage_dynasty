# interface/cli_constants.py
# Module: CLI Constants and Helpers
# Lines: ~280
#
# Centralized constants and reusable helper functions for the CLI.
# Includes pagination, search, and display configuration.

"""
Cage Dynasty - CLI Constants and Helpers

Centralized configuration for:
- Terminal display settings
- Color themes
- Pagination
- Fighter search
- Stat thresholds
- Game balance constants
"""

from typing import List, Optional, Tuple, Dict, Any, Callable, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# DISPLAY CONFIGURATION
# ============================================================================

# Terminal dimensions
TERMINAL_WIDTH = 70
TERMINAL_HEIGHT = 40

# Box drawing characters
BOX_H = "-"
BOX_V = "|"
BOX_TL = "+"
BOX_TR = "+"
BOX_BL = "+"
BOX_BR = "+"

# Stat bar configuration
STAT_BAR_WIDTH = 20
STAT_BAR_FILLED = "#"
STAT_BAR_EMPTY = "."


# ============================================================================
# PAGINATION CONFIGURATION
# ============================================================================

DEFAULT_PAGE_SIZE = 15
MAX_PAGE_SIZE = 25
MIN_PAGE_SIZE = 5

# Pagination navigation keys
NAV_NEXT = "n"
NAV_PREV = "p"
NAV_BACK = "b"
NAV_QUIT = "q"


# ============================================================================
# STAT THRESHOLDS (for coloring and grading)
# ============================================================================

class StatThreshold:
    """Thresholds for stat evaluation"""
    ELITE = 90
    EXCELLENT = 80
    GOOD = 70
    AVERAGE = 60
    BELOW_AVERAGE = 50
    POOR = 40


# Letter grade thresholds
GRADE_THRESHOLDS = {
    "A+": 90,
    "A": 85,
    "A-": 80,
    "B+": 75,
    "B": 70,
    "B-": 65,
    "C+": 60,
    "C": 55,
    "C-": 50,
    "D+": 45,
    "D": 40,
    "F": 0,
}


# ============================================================================
# ECONOMY CONSTANTS
# ============================================================================

# Fight of the Night bonus (imported from fotn.py but fallback here)
DEFAULT_FOTN_BONUS = 50_000

# Signing bonus ranges by tier
SIGNING_BONUS_RANGES = {
    "prospect": (5_000, 15_000),
    "regional": (10_000, 30_000),
    "national": (25_000, 75_000),
    "elite": (50_000, 150_000),
    "champion": (100_000, 500_000),
}

# Base weekly training costs
TRAINING_CAMP_COST = 2_500


# ============================================================================
# FIGHT CONFIGURATION
# ============================================================================

# Standard fight lengths
STANDARD_ROUNDS = 3
TITLE_FIGHT_ROUNDS = 5
MAIN_EVENT_ROUNDS = 5

# Training camp defaults
DEFAULT_CAMP_WEEKS = 8
MIN_CAMP_WEEKS = 4
MAX_CAMP_WEEKS = 12

# Weeks until fight (scheduling)
DEFAULT_WEEKS_UNTIL_FIGHT = 8


# ============================================================================
# ATTRIBUTE DISPLAY NAMES
# ============================================================================

ATTRIBUTE_DISPLAY_NAMES = {
    "boxing": "Boxing",
    "kicks": "Kicks",
    "wrestling": "Wrestling",
    "bjj": "BJJ",
    "cardio": "Cardio",
    "strength": "Strength",
    "speed": "Speed",
    "power": "Power",
    "chin": "Chin",
    "recovery": "Recovery",
    "td_defense": "TD Defense",
    "top_control": "Top Control",
    "submissions": "Submissions",
    "clinch": "Clinch",
    "accuracy": "Accuracy",
    "head_movement": "Head Movement",
    "footwork": "Footwork",
    "fight_iq": "Fight IQ",
    "composure": "Composure",
}


def format_attribute_name(attr: str) -> str:
    """Format an attribute name for display."""
    return ATTRIBUTE_DISPLAY_NAMES.get(attr, attr.replace("_", " ").title())


# ============================================================================
# PAGINATION HELPER
# ============================================================================

@dataclass
class PaginationResult:
    """Result of pagination display"""
    items: List[Any]
    page: int
    total_pages: int
    start_index: int
    end_index: int
    action: str  # "select", "next", "prev", "back"
    selected_index: Optional[int] = None


T = TypeVar('T')


class Paginator(Generic[T]):
    """
    Reusable pagination helper for lists.
    
    Usage:
        paginator = Paginator(fighters, page_size=15)
        
        while True:
            items = paginator.get_current_page()
            # Display items...
            
            choice = input("> ")
            result = paginator.handle_input(choice)
            
            if result.action == "back":
                break
            elif result.action == "select":
                # Handle selection
                selected = items[result.selected_index]
    """
    
    def __init__(
        self, 
        items: List[T], 
        page_size: int = DEFAULT_PAGE_SIZE,
        allow_selection: bool = True
    ):
        self.items = items
        self.page_size = min(max(page_size, MIN_PAGE_SIZE), MAX_PAGE_SIZE)
        self.allow_selection = allow_selection
        self.current_page = 0
        self._calculate_pages()
    
    def _calculate_pages(self) -> None:
        """Calculate total pages."""
        if not self.items:
            self.total_pages = 1
        else:
            self.total_pages = (len(self.items) + self.page_size - 1) // self.page_size
    
    @property
    def start_index(self) -> int:
        """Get start index for current page."""
        return self.current_page * self.page_size
    
    @property
    def end_index(self) -> int:
        """Get end index for current page."""
        return min(self.start_index + self.page_size, len(self.items))
    
    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.current_page < self.total_pages - 1
    
    @property
    def has_prev(self) -> bool:
        """Check if there's a previous page."""
        return self.current_page > 0
    
    def get_current_page(self) -> List[T]:
        """Get items for current page."""
        return self.items[self.start_index:self.end_index]
    
    def next_page(self) -> bool:
        """Move to next page. Returns True if successful."""
        if self.has_next:
            self.current_page += 1
            return True
        return False
    
    def prev_page(self) -> bool:
        """Move to previous page. Returns True if successful."""
        if self.has_prev:
            self.current_page -= 1
            return True
        return False
    
    def go_to_page(self, page: int) -> bool:
        """Go to specific page. Returns True if valid."""
        if 0 <= page < self.total_pages:
            self.current_page = page
            return True
        return False
    
    def handle_input(self, choice: str) -> PaginationResult:
        """
        Handle user input and return result.
        
        Args:
            choice: User input string
            
        Returns:
            PaginationResult with action and optional selection
        """
        choice = choice.lower().strip()
        
        # Navigation
        if choice == NAV_NEXT and self.has_next:
            self.next_page()
            return PaginationResult(
                items=self.get_current_page(),
                page=self.current_page,
                total_pages=self.total_pages,
                start_index=self.start_index,
                end_index=self.end_index,
                action="next"
            )
        
        if choice == NAV_PREV and self.has_prev:
            self.prev_page()
            return PaginationResult(
                items=self.get_current_page(),
                page=self.current_page,
                total_pages=self.total_pages,
                start_index=self.start_index,
                end_index=self.end_index,
                action="prev"
            )
        
        if choice in (NAV_BACK, NAV_QUIT, ""):
            return PaginationResult(
                items=self.get_current_page(),
                page=self.current_page,
                total_pages=self.total_pages,
                start_index=self.start_index,
                end_index=self.end_index,
                action="back"
            )
        
        # Selection by number
        if self.allow_selection and choice.isdigit():
            idx = int(choice) - 1  # 1-indexed display
            if 0 <= idx < len(self.get_current_page()):
                return PaginationResult(
                    items=self.get_current_page(),
                    page=self.current_page,
                    total_pages=self.total_pages,
                    start_index=self.start_index,
                    end_index=self.end_index,
                    action="select",
                    selected_index=idx
                )
        
        # Invalid input - stay on current page
        return PaginationResult(
            items=self.get_current_page(),
            page=self.current_page,
            total_pages=self.total_pages,
            start_index=self.start_index,
            end_index=self.end_index,
            action="invalid"
        )
    
    def get_nav_options(self) -> List[Tuple[str, str]]:
        """Get navigation menu options."""
        options = []
        if self.has_prev:
            options.append((NAV_PREV, "Previous page"))
        if self.has_next:
            options.append((NAV_NEXT, "Next page"))
        options.append((NAV_BACK, "Back"))
        return options
    
    def format_page_header(self, title: str = "") -> str:
        """Format page indicator string."""
        if self.total_pages <= 1:
            return title
        return f"{title} (Page {self.current_page + 1}/{self.total_pages})"


# ============================================================================
# SEARCH HELPER
# ============================================================================

def search_fighters(
    fighters: List[Any],
    query: str,
    search_fields: Optional[List[str]] = None
) -> List[Any]:
    """
    Search fighters by name or other fields.
    
    Args:
        fighters: List of fighter objects (must have 'name' attribute)
        query: Search query string
        search_fields: Optional list of attributes to search (default: name only)
        
    Returns:
        List of matching fighters
    """
    if not query or not query.strip():
        return fighters
    
    query = query.lower().strip()
    search_fields = search_fields or ["name"]
    
    results = []
    for fighter in fighters:
        for field in search_fields:
            value = getattr(fighter, field, None)
            if value and query in str(value).lower():
                results.append(fighter)
                break
    
    return results


def search_by_name(items: List[Any], query: str, name_attr: str = "name") -> List[Any]:
    """
    Simple name search for any list of objects.
    
    Args:
        items: List of objects
        query: Search query
        name_attr: Attribute name to search (default: "name")
        
    Returns:
        Filtered list matching query
    """
    if not query or not query.strip():
        return items
    
    query = query.lower().strip()
    return [
        item for item in items
        if query in str(getattr(item, name_attr, "")).lower()
    ]


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Display
    "TERMINAL_WIDTH",
    "TERMINAL_HEIGHT",
    "BOX_H", "BOX_V", "BOX_TL", "BOX_TR", "BOX_BL", "BOX_BR",
    "STAT_BAR_WIDTH", "STAT_BAR_FILLED", "STAT_BAR_EMPTY",
    
    # Pagination
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "MIN_PAGE_SIZE",
    "NAV_NEXT", "NAV_PREV", "NAV_BACK", "NAV_QUIT",
    "Paginator",
    "PaginationResult",
    
    # Stats
    "StatThreshold",
    "GRADE_THRESHOLDS",
    
    # Economy
    "DEFAULT_FOTN_BONUS",
    "SIGNING_BONUS_RANGES",
    "TRAINING_CAMP_COST",
    
    # Fight config
    "STANDARD_ROUNDS",
    "TITLE_FIGHT_ROUNDS",
    "MAIN_EVENT_ROUNDS",
    "DEFAULT_CAMP_WEEKS",
    "MIN_CAMP_WEEKS",
    "MAX_CAMP_WEEKS",
    "DEFAULT_WEEKS_UNTIL_FIGHT",
    
    # Attributes
    "ATTRIBUTE_DISPLAY_NAMES",
    "format_attribute_name",
    
    # Search
    "search_fighters",
    "search_by_name",
]
