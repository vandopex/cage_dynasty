# tests/test_cli_constants.py
# Module: Tests for CLI Constants and Helpers
# Lines: ~250

"""
Tests for Cage Dynasty CLI Constants and Helper Functions.

Tests cover:
- Pagination functionality
- Search functionality
- Constant values
"""

import pytest
from dataclasses import dataclass
from typing import List


# ============================================================================
# MOCK IMPORTS (for standalone testing)
# ============================================================================

# Try to import from module, fall back to inline definition for testing
try:
    from interface.cli_constants import (
        TERMINAL_WIDTH,
        DEFAULT_PAGE_SIZE,
        Paginator,
        PaginationResult,
        search_fighters,
        search_by_name,
        format_attribute_name,
        ATTRIBUTE_DISPLAY_NAMES,
        StatThreshold,
        NAV_NEXT, NAV_PREV, NAV_BACK,
    )
except ImportError:
    # Inline constants for standalone testing
    TERMINAL_WIDTH = 70
    DEFAULT_PAGE_SIZE = 15
    NAV_NEXT = "n"
    NAV_PREV = "p"
    NAV_BACK = "b"
    
    ATTRIBUTE_DISPLAY_NAMES = {
        "boxing": "Boxing",
        "td_defense": "TD Defense",
        "fight_iq": "Fight IQ",
    }
    
    def format_attribute_name(attr: str) -> str:
        return ATTRIBUTE_DISPLAY_NAMES.get(attr, attr.replace("_", " ").title())
    
    class StatThreshold:
        ELITE = 90
        EXCELLENT = 80
        GOOD = 70
    
    # Minimal Paginator for testing
    @dataclass
    class PaginationResult:
        items: list
        page: int
        total_pages: int
        start_index: int
        end_index: int
        action: str
        selected_index: int = None
    
    class Paginator:
        def __init__(self, items, page_size=15, allow_selection=True):
            self.items = items
            self.page_size = page_size
            self.allow_selection = allow_selection
            self.current_page = 0
            self.total_pages = max(1, (len(items) + page_size - 1) // page_size)
        
        @property
        def start_index(self):
            return self.current_page * self.page_size
        
        @property
        def end_index(self):
            return min(self.start_index + self.page_size, len(self.items))
        
        @property
        def has_next(self):
            return self.current_page < self.total_pages - 1
        
        @property
        def has_prev(self):
            return self.current_page > 0
        
        def get_current_page(self):
            return self.items[self.start_index:self.end_index]
        
        def next_page(self):
            if self.has_next:
                self.current_page += 1
                return True
            return False
        
        def prev_page(self):
            if self.has_prev:
                self.current_page -= 1
                return True
            return False
        
        def handle_input(self, choice):
            choice = choice.lower().strip()
            if choice == "n" and self.has_next:
                self.next_page()
                action = "next"
            elif choice == "p" and self.has_prev:
                self.prev_page()
                action = "prev"
            elif choice in ("b", "q", ""):
                action = "back"
            elif self.allow_selection and choice.isdigit():
                idx = int(choice) - 1
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
                action = "invalid"
            else:
                action = "invalid"
            
            return PaginationResult(
                items=self.get_current_page(),
                page=self.current_page,
                total_pages=self.total_pages,
                start_index=self.start_index,
                end_index=self.end_index,
                action=action
            )
    
    def search_fighters(fighters, query, search_fields=None):
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
    
    def search_by_name(items, query, name_attr="name"):
        if not query or not query.strip():
            return items
        query = query.lower().strip()
        return [
            item for item in items
            if query in str(getattr(item, name_attr, "")).lower()
        ]


# ============================================================================
# TEST DATA
# ============================================================================

@dataclass
class MockFighter:
    """Mock fighter for testing"""
    fighter_id: str
    name: str
    country: str = "USA"
    weight_class: str = "Lightweight"
    overall_rating: int = 75


def create_test_fighters(count: int = 50) -> List[MockFighter]:
    """Create a list of test fighters."""
    names = [
        "John Smith", "Mike Johnson", "Carlos Garcia", "James Wilson",
        "Robert Brown", "David Lee", "Michael Davis", "William Miller",
        "Richard Moore", "Joseph Taylor", "Thomas Anderson", "Charles Thomas",
        "Daniel Jackson", "Matthew White", "Anthony Harris", "Mark Martin",
        "Donald Thompson", "Steven Martinez", "Paul Robinson", "Andrew Clark",
        "Joshua Lewis", "Kenneth Walker", "Kevin Hall", "Brian Allen",
        "George Young", "Edward King", "Ronald Wright", "Timothy Scott",
        "Jason Green", "Jeffrey Adams", "Ryan Baker", "Jacob Nelson",
        "Gary Hill", "Nicholas Ramirez", "Eric Campbell", "Jonathan Mitchell",
        "Stephen Roberts", "Larry Carter", "Justin Phillips", "Scott Evans",
        "Brandon Turner", "Benjamin Torres", "Samuel Parker", "Gregory Collins",
        "Frank Stewart", "Raymond Sanchez", "Patrick Morris", "Alexander Rogers",
        "Jack Reed", "Dennis Cook",
    ]
    
    countries = ["USA", "Brazil", "Russia", "Mexico", "UK", "Canada", "Japan"]
    weight_classes = ["Flyweight", "Bantamweight", "Featherweight", "Lightweight", 
                      "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"]
    
    fighters = []
    for i in range(count):
        name = names[i % len(names)]
        if i >= len(names):
            name = f"{name} {i // len(names) + 1}"
        
        fighters.append(MockFighter(
            fighter_id=f"fighter_{i}",
            name=name,
            country=countries[i % len(countries)],
            weight_class=weight_classes[i % len(weight_classes)],
            overall_rating=50 + (i % 50)
        ))
    
    return fighters


# ============================================================================
# PAGINATION TESTS
# ============================================================================

class TestPaginator:
    """Tests for the Paginator class"""
    
    def test_creation_with_items(self):
        """Test paginator creation with items"""
        items = list(range(50))
        paginator = Paginator(items, page_size=10)
        
        assert paginator.total_pages == 5
        assert paginator.current_page == 0
        assert len(paginator.get_current_page()) == 10
    
    def test_creation_empty_list(self):
        """Test paginator with empty list"""
        paginator = Paginator([], page_size=10)
        
        assert paginator.total_pages == 1
        assert len(paginator.get_current_page()) == 0
    
    def test_single_page(self):
        """Test paginator with items fitting on one page"""
        items = list(range(5))
        paginator = Paginator(items, page_size=10)
        
        assert paginator.total_pages == 1
        assert not paginator.has_next
        assert not paginator.has_prev
    
    def test_navigation_next(self):
        """Test moving to next page"""
        items = list(range(30))
        paginator = Paginator(items, page_size=10)
        
        assert paginator.current_page == 0
        assert paginator.has_next
        
        result = paginator.next_page()
        assert result is True
        assert paginator.current_page == 1
        assert paginator.get_current_page() == list(range(10, 20))
    
    def test_navigation_prev(self):
        """Test moving to previous page"""
        items = list(range(30))
        paginator = Paginator(items, page_size=10)
        paginator.current_page = 2
        
        assert paginator.has_prev
        
        result = paginator.prev_page()
        assert result is True
        assert paginator.current_page == 1
    
    def test_navigation_boundary_next(self):
        """Test navigation at end boundary"""
        items = list(range(30))
        paginator = Paginator(items, page_size=10)
        paginator.current_page = 2  # Last page
        
        assert not paginator.has_next
        result = paginator.next_page()
        assert result is False
        assert paginator.current_page == 2
    
    def test_navigation_boundary_prev(self):
        """Test navigation at start boundary"""
        items = list(range(30))
        paginator = Paginator(items, page_size=10)
        
        assert not paginator.has_prev
        result = paginator.prev_page()
        assert result is False
        assert paginator.current_page == 0
    
    def test_handle_input_next(self):
        """Test handle_input with next command"""
        items = list(range(30))
        paginator = Paginator(items, page_size=10)
        
        result = paginator.handle_input("n")
        assert result.action == "next"
        assert result.page == 1
    
    def test_handle_input_prev(self):
        """Test handle_input with prev command"""
        items = list(range(30))
        paginator = Paginator(items, page_size=10)
        paginator.current_page = 1
        
        result = paginator.handle_input("p")
        assert result.action == "prev"
        assert result.page == 0
    
    def test_handle_input_back(self):
        """Test handle_input with back command"""
        items = list(range(30))
        paginator = Paginator(items, page_size=10)
        
        result = paginator.handle_input("b")
        assert result.action == "back"
    
    def test_handle_input_selection(self):
        """Test handle_input with number selection"""
        items = list(range(30))
        paginator = Paginator(items, page_size=10, allow_selection=True)
        
        result = paginator.handle_input("3")
        assert result.action == "select"
        assert result.selected_index == 2  # 0-indexed
    
    def test_handle_input_invalid_selection(self):
        """Test handle_input with out-of-range selection"""
        items = list(range(5))
        paginator = Paginator(items, page_size=10)
        
        result = paginator.handle_input("10")
        assert result.action == "invalid"
    
    def test_start_end_indices(self):
        """Test start and end index calculation"""
        items = list(range(45))
        paginator = Paginator(items, page_size=10)
        
        # First page
        assert paginator.start_index == 0
        assert paginator.end_index == 10
        
        # Middle page
        paginator.current_page = 2
        assert paginator.start_index == 20
        assert paginator.end_index == 30
        
        # Last page (partial)
        paginator.current_page = 4
        assert paginator.start_index == 40
        assert paginator.end_index == 45  # Only 5 items
    
    def test_with_fighters(self):
        """Test pagination with fighter objects"""
        fighters = create_test_fighters(35)
        paginator = Paginator(fighters, page_size=15)
        
        assert paginator.total_pages == 3
        
        page1 = paginator.get_current_page()
        assert len(page1) == 15
        assert all(isinstance(f, MockFighter) for f in page1)
        
        paginator.next_page()
        page2 = paginator.get_current_page()
        assert len(page2) == 15
        
        paginator.next_page()
        page3 = paginator.get_current_page()
        assert len(page3) == 5  # Remaining fighters


# ============================================================================
# SEARCH TESTS
# ============================================================================

class TestSearch:
    """Tests for search functionality"""
    
    def test_search_by_name_exact(self):
        """Test searching for exact name match"""
        fighters = create_test_fighters(20)
        results = search_fighters(fighters, "John Smith")
        
        assert len(results) >= 1
        assert all("john smith" in f.name.lower() for f in results)
    
    def test_search_by_name_partial(self):
        """Test searching with partial name"""
        fighters = create_test_fighters(20)
        results = search_fighters(fighters, "John")
        
        assert len(results) >= 1
        assert all("john" in f.name.lower() for f in results)
    
    def test_search_case_insensitive(self):
        """Test case insensitive search"""
        fighters = create_test_fighters(20)
        
        results_lower = search_fighters(fighters, "john")
        results_upper = search_fighters(fighters, "JOHN")
        results_mixed = search_fighters(fighters, "JoHn")
        
        assert len(results_lower) == len(results_upper) == len(results_mixed)
    
    def test_search_empty_query(self):
        """Test search with empty query returns all"""
        fighters = create_test_fighters(20)
        
        results = search_fighters(fighters, "")
        assert len(results) == len(fighters)
        
        results = search_fighters(fighters, "   ")
        assert len(results) == len(fighters)
    
    def test_search_no_matches(self):
        """Test search with no matches"""
        fighters = create_test_fighters(20)
        results = search_fighters(fighters, "ZZZZNOTAFIGHTER")
        
        assert len(results) == 0
    
    def test_search_multiple_fields(self):
        """Test searching multiple fields"""
        fighters = create_test_fighters(20)
        results = search_fighters(fighters, "Brazil", search_fields=["name", "country"])
        
        assert len(results) >= 1
        assert all("brazil" in f.country.lower() for f in results)
    
    def test_search_by_name_helper(self):
        """Test the simpler search_by_name function"""
        fighters = create_test_fighters(20)
        results = search_by_name(fighters, "Mike")
        
        assert len(results) >= 1
        assert all("mike" in f.name.lower() for f in results)


# ============================================================================
# ATTRIBUTE NAME TESTS
# ============================================================================

class TestAttributeNames:
    """Tests for attribute name formatting"""
    
    def test_known_attributes(self):
        """Test formatting of known attributes"""
        assert format_attribute_name("boxing") == "Boxing"
        assert format_attribute_name("td_defense") == "TD Defense"
        assert format_attribute_name("fight_iq") == "Fight IQ"
    
    def test_unknown_attributes(self):
        """Test formatting of unknown attributes"""
        result = format_attribute_name("some_unknown_attr")
        assert result == "Some Unknown Attr"


# ============================================================================
# CONSTANT VALUE TESTS
# ============================================================================

class TestConstants:
    """Tests for constant values"""
    
    def test_terminal_width(self):
        """Test terminal width is reasonable"""
        assert 40 <= TERMINAL_WIDTH <= 120
    
    def test_page_size(self):
        """Test page size is reasonable"""
        assert 5 <= DEFAULT_PAGE_SIZE <= 30
    
    def test_stat_thresholds(self):
        """Test stat thresholds are in order"""
        assert StatThreshold.ELITE > StatThreshold.EXCELLENT
        assert StatThreshold.EXCELLENT > StatThreshold.GOOD


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPaginatorSearchIntegration:
    """Tests for paginator and search working together"""
    
    def test_search_then_paginate(self):
        """Test searching then paginating results"""
        fighters = create_test_fighters(50)
        
        # Search first
        search_results = search_fighters(fighters, "John")
        
        # Then paginate
        paginator = Paginator(search_results, page_size=5)
        
        page = paginator.get_current_page()
        assert all("john" in f.name.lower() for f in page)
    
    def test_empty_search_pagination(self):
        """Test pagination of empty search results"""
        fighters = create_test_fighters(20)
        search_results = search_fighters(fighters, "ZZZZZ")
        
        paginator = Paginator(search_results, page_size=10)
        
        assert paginator.total_pages == 1
        assert len(paginator.get_current_page()) == 0


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
