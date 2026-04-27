# tests/test_display.py
# Tests for interface/display.py
# Lines: 298

"""Tests for display utilities module."""

import pytest
from unittest.mock import patch
from io import StringIO

from interface.display import (
    # Constants
    TERMINAL_WIDTH,
    BOX_H, BOX_V, BOX_TL, BOX_TR, BOX_BL, BOX_BR,
    VERSION,
    TITLE_ART,
    
    # Colors
    Colors,
    colored,
    
    # Formatting
    format_record,
    format_record_colored,
    format_money,
    format_percentage,
    format_height,
    format_reach,
    
    # Visual elements
    stat_bar,
    stat_letter_grade,
    progress_bar,
    
    # Screen functions
    clear_screen,
    print_header,
    print_divider,
    print_box,
    print_menu,
    print_table,
    
    # Input functions
    get_input,
    get_choice,
    get_number,
    confirm,
    pause,
)


# ============================================================================
# CONSTANTS TESTS
# ============================================================================

class TestConstants:
    """Test constant values."""
    
    def test_terminal_width(self):
        """Terminal width should be reasonable."""
        assert TERMINAL_WIDTH == 70
    
    def test_box_characters_defined(self):
        """Box drawing characters should be defined."""
        assert BOX_H == "-"
        assert BOX_V == "|"
        assert BOX_TL == "+"
        assert BOX_TR == "+"
        assert BOX_BL == "+"
        assert BOX_BR == "+"
    
    def test_version_format(self):
        """Version should be in semver format."""
        parts = VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)
    
    def test_title_art_exists(self):
        """Title art should exist and contain CAGE."""
        assert "CAGE" in TITLE_ART or "____" in TITLE_ART


# ============================================================================
# COLORS TESTS
# ============================================================================

class TestColors:
    """Test Colors class."""
    
    def test_colors_have_escape_codes(self):
        """Colors should contain ANSI escape codes when enabled."""
        Colors.enable()
        assert "\033[" in Colors.RED
        assert "\033[" in Colors.GREEN
        assert "\033[" in Colors.RESET
    
    def test_disable_colors(self):
        """Disabling colors should make them empty strings."""
        Colors.disable()
        assert Colors.RED == ""
        assert Colors.GREEN == ""
        assert Colors.RESET == ""
        # Re-enable for other tests
        Colors.enable()
    
    def test_enable_colors(self):
        """Enabling colors should restore escape codes."""
        Colors.disable()
        Colors.enable()
        assert "\033[" in Colors.RED
        assert Colors.is_enabled()
    
    def test_is_enabled(self):
        """is_enabled should track color state."""
        Colors.enable()
        assert Colors.is_enabled() is True
        Colors.disable()
        assert Colors.is_enabled() is False
        Colors.enable()


class TestColored:
    """Test colored function."""
    
    def test_colored_applies_color(self):
        """colored should wrap text in color codes."""
        Colors.enable()
        result = colored("test", Colors.RED)
        assert Colors.RED in result
        assert "test" in result
        assert Colors.RESET in result
    
    def test_colored_with_disabled_colors(self):
        """colored should work when colors disabled."""
        Colors.disable()
        result = colored("test", Colors.RED)
        assert "test" in result
        Colors.enable()


# ============================================================================
# FORMATTING TESTS
# ============================================================================

class TestFormatRecord:
    """Test record formatting."""
    
    def test_basic_record(self):
        """Format W-L record."""
        assert format_record(10, 5) == "10-5"
    
    def test_record_with_draws(self):
        """Format W-L-D record."""
        assert format_record(10, 5, 2) == "10-5-2"
    
    def test_record_zero_draws(self):
        """Zero draws should not show."""
        assert format_record(10, 5, 0) == "10-5"
    
    def test_undefeated(self):
        """Undefeated record."""
        assert format_record(15, 0) == "15-0"
    
    def test_winless(self):
        """Winless record."""
        assert format_record(0, 5) == "0-5"


class TestFormatRecordColored:
    """Test colored record formatting."""
    
    def test_colored_record(self):
        """Colored record should contain numbers."""
        Colors.enable()
        result = format_record_colored(10, 5)
        assert "10" in result
        assert "5" in result
    
    def test_colored_record_with_draws(self):
        """Colored record with draws."""
        Colors.enable()
        result = format_record_colored(10, 5, 2)
        assert "10" in result
        assert "5" in result
        assert "2" in result


class TestFormatMoney:
    """Test money formatting."""
    
    def test_format_money_basic(self):
        """Basic money formatting."""
        assert format_money(1000) == "$1,000"
    
    def test_format_money_large(self):
        """Large amounts with commas."""
        assert format_money(1000000) == "$1,000,000"
    
    def test_format_money_zero(self):
        """Zero amount."""
        assert format_money(0) == "$0"


class TestFormatPercentage:
    """Test percentage formatting."""
    
    def test_format_percentage_basic(self):
        """Basic percentage."""
        assert format_percentage(0.5) == "50.0%"
    
    def test_format_percentage_decimals(self):
        """Custom decimal places."""
        assert format_percentage(0.123456, 2) == "12.35%"
    
    def test_format_percentage_zero(self):
        """Zero percentage."""
        assert format_percentage(0) == "0.0%"


class TestFormatHeight:
    """Test height conversion."""
    
    def test_format_height(self):
        """Convert cm to feet/inches."""
        result = format_height(183)  # ~6'0"
        assert "'" in result
        assert '"' in result
    
    def test_format_height_short(self):
        """Short fighter."""
        result = format_height(165)  # ~5'5"
        assert "5'" in result


class TestFormatReach:
    """Test reach conversion."""
    
    def test_format_reach(self):
        """Convert cm to inches."""
        result = format_reach(188)  # ~74"
        assert '"' in result
        assert "74" in result or "73" in result  # Rounding


# ============================================================================
# VISUAL ELEMENTS TESTS
# ============================================================================

class TestStatBar:
    """Test stat bar generation."""
    
    def test_stat_bar_returns_string(self):
        """Stat bar should return a string."""
        result = stat_bar(50)
        assert isinstance(result, str)
    
    def test_stat_bar_contains_value(self):
        """Stat bar should show the value."""
        result = stat_bar(75)
        assert "75" in result
    
    def test_stat_bar_width(self):
        """Stat bar respects width."""
        result = stat_bar(50, width=10)
        # Should have mix of # and .
        assert "#" in result
        assert "." in result
    
    def test_stat_bar_full(self):
        """Full stat bar at 100."""
        result = stat_bar(100, width=10)
        assert "100" in result


class TestStatLetterGrade:
    """Test letter grade conversion."""
    
    def test_grade_a_plus(self):
        """90+ should be A+."""
        result = stat_letter_grade(95)
        assert "A+" in result
    
    def test_grade_b(self):
        """70 should be B."""
        result = stat_letter_grade(70)
        assert "B" in result
    
    def test_grade_c(self):
        """55 should be C."""
        result = stat_letter_grade(55)
        assert "C" in result
    
    def test_grade_f(self):
        """Below 40 should be F."""
        result = stat_letter_grade(30)
        assert "F" in result


class TestProgressBar:
    """Test progress bar generation."""
    
    def test_progress_bar_half(self):
        """50% progress bar."""
        result = progress_bar(50, 100)
        assert "50%" in result
        assert "[" in result
        assert "]" in result
    
    def test_progress_bar_full(self):
        """100% progress bar."""
        result = progress_bar(100, 100)
        assert "100%" in result
    
    def test_progress_bar_empty(self):
        """0% progress bar."""
        result = progress_bar(0, 100)
        assert "0%" in result
    
    def test_progress_bar_zero_total(self):
        """Handle zero total."""
        result = progress_bar(0, 0)
        assert "0%" in result


# ============================================================================
# SCREEN FUNCTION TESTS
# ============================================================================

class TestPrintHeader:
    """Test header printing."""
    
    def test_prints_title(self, capsys):
        """Header should include title."""
        print_header("TEST")
        captured = capsys.readouterr()
        assert "TEST" in captured.out
    
    def test_includes_box_chars(self, capsys):
        """Header should include box characters."""
        print_header("TEST")
        captured = capsys.readouterr()
        assert "+" in captured.out or "-" in captured.out


class TestPrintDivider:
    """Test divider printing."""
    
    def test_prints_line(self, capsys):
        """Divider should print a line."""
        print_divider()
        captured = capsys.readouterr()
        assert BOX_H in captured.out


class TestPrintBox:
    """Test box printing."""
    
    def test_prints_content(self, capsys):
        """Box should include content."""
        print_box(["Line 1", "Line 2"])
        captured = capsys.readouterr()
        assert "Line 1" in captured.out
        assert "Line 2" in captured.out
    
    def test_with_title(self, capsys):
        """Box with title."""
        print_box(["Content"], title="TITLE")
        captured = capsys.readouterr()
        assert "TITLE" in captured.out
        assert "Content" in captured.out


class TestPrintMenu:
    """Test menu printing."""
    
    def test_prints_options(self, capsys):
        """Menu should show options."""
        print_menu([("1", "First"), ("2", "Second")])
        captured = capsys.readouterr()
        assert "[1]" in captured.out
        assert "First" in captured.out
        assert "[2]" in captured.out
        assert "Second" in captured.out


class TestPrintTable:
    """Test table printing."""
    
    def test_prints_headers(self, capsys):
        """Table should show headers."""
        print_table(["Col1", "Col2"], [["A", "B"]])
        captured = capsys.readouterr()
        assert "Col1" in captured.out
        assert "Col2" in captured.out
    
    def test_prints_rows(self, capsys):
        """Table should show row data."""
        print_table(["Col1", "Col2"], [["Data1", "Data2"]])
        captured = capsys.readouterr()
        assert "Data1" in captured.out
        assert "Data2" in captured.out


# ============================================================================
# INPUT FUNCTION TESTS
# ============================================================================

class TestGetInput:
    """Test input getting."""
    
    def test_returns_input(self):
        """Should return user input."""
        with patch('builtins.input', return_value="test"):
            result = get_input()
            assert result == "test"
    
    def test_strips_whitespace(self):
        """Should strip whitespace."""
        with patch('builtins.input', return_value="  test  "):
            result = get_input()
            assert result == "test"
    
    def test_handles_eof(self):
        """Should handle EOF gracefully."""
        with patch('builtins.input', side_effect=EOFError):
            result = get_input()
            assert result == ""
    
    def test_handles_keyboard_interrupt(self):
        """Should handle Ctrl+C gracefully."""
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            result = get_input()
            assert result == ""


class TestGetChoice:
    """Test choice validation."""
    
    def test_valid_choice(self):
        """Valid choice should be returned."""
        with patch('builtins.input', return_value="1"):
            result = get_choice(["1", "2", "3"])
            assert result == "1"
    
    def test_invalid_choice(self):
        """Invalid choice should return None."""
        with patch('builtins.input', return_value="x"):
            result = get_choice(["1", "2", "3"])
            assert result is None
    
    def test_case_insensitive(self):
        """Choices should be case-insensitive."""
        with patch('builtins.input', return_value="A"):
            result = get_choice(["a", "b"])
            assert result == "a"


class TestGetNumber:
    """Test number input."""
    
    def test_valid_number(self):
        """Valid number should be returned."""
        with patch('builtins.input', return_value="42"):
            result = get_number()
            assert result == 42
    
    def test_invalid_number(self):
        """Invalid input should return None."""
        with patch('builtins.input', return_value="abc"):
            result = get_number()
            assert result is None
    
    def test_min_val(self):
        """Number below min should return None."""
        with patch('builtins.input', return_value="5"):
            result = get_number(min_val=10)
            assert result is None
    
    def test_max_val(self):
        """Number above max should return None."""
        with patch('builtins.input', return_value="100"):
            result = get_number(max_val=50)
            assert result is None
    
    def test_within_range(self):
        """Number in range should be returned."""
        with patch('builtins.input', return_value="25"):
            result = get_number(min_val=10, max_val=50)
            assert result == 25


class TestConfirm:
    """Test confirmation prompts."""
    
    def test_yes(self):
        """'y' should return True."""
        with patch('builtins.input', return_value="y"):
            assert confirm("Test?") is True
    
    def test_yes_full(self):
        """'yes' should return True."""
        with patch('builtins.input', return_value="yes"):
            assert confirm("Test?") is True
    
    def test_no(self):
        """'n' should return False."""
        with patch('builtins.input', return_value="n"):
            assert confirm("Test?") is False
    
    def test_invalid_is_false(self):
        """Invalid input should return False."""
        with patch('builtins.input', return_value="maybe"):
            assert confirm("Test?") is False


class TestPause:
    """Test pause function."""
    
    def test_waits_for_input(self):
        """Pause should wait for input."""
        with patch('builtins.input', return_value="") as mock_input:
            pause()
            mock_input.assert_called_once()
    
    def test_custom_message(self):
        """Pause should use custom message."""
        with patch('builtins.input', return_value="") as mock_input:
            pause("Custom message")
            mock_input.assert_called_with("Custom message")
