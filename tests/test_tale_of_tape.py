# tests/test_tale_of_tape.py
# Tests for the Tale of the Tape Display System
# Run: python3 -m pytest tests/test_tale_of_tape.py -v

"""
Tests for systems/tale_of_tape.py

Tests cover:
- Fighter data creation
- Stat comparisons
- Tale of tape generation
- Display formatting
- Matchup analysis
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from systems.tale_of_tape import (
    FighterTapeData,
    StatComparison,
    TaleOfTape,
    STAT_DISPLAY_NAMES,
    STRIKING_STATS,
    GRAPPLING_STATS,
    compare_stat,
    get_stat_comparison,
    calculate_category_advantage,
    analyze_matchup,
    generate_tale_of_tape,
    format_tale_of_tape,
    format_tale_of_tape_compact,
    get_quick_comparison,
    get_prediction_text,
    create_fighter_tape_data,
)


# ============================================================================
# FIGHTER DATA TESTS
# ============================================================================

class TestFighterTapeData:
    """Test FighterTapeData dataclass."""
    
    def test_default_values(self):
        """Should have sensible defaults."""
        f = FighterTapeData(name="Test Fighter")
        assert f.name == "Test Fighter"
        assert f.wins == 0
        assert f.losses == 0
        assert f.stats == {}
    
    def test_record_string_no_draws(self):
        """Should format record without draws."""
        f = FighterTapeData(name="Test", wins=10, losses=2, draws=0)
        assert f.get_record_string() == "10-2"
    
    def test_record_string_with_draws(self):
        """Should format record with draws."""
        f = FighterTapeData(name="Test", wins=10, losses=2, draws=1)
        assert f.get_record_string() == "10-2-1"
    
    def test_height_string(self):
        """Should format height correctly."""
        f = FighterTapeData(name="Test", height=71)  # 5'11"
        assert f.get_height_string() == "5'11\""
        
        f2 = FighterTapeData(name="Test", height=72)  # 6'0"
        assert f2.get_height_string() == "6'0\""
    
    def test_finish_rate(self):
        """Should calculate finish rate."""
        f = FighterTapeData(name="Test", wins=10, ko_wins=5, sub_wins=3)
        # 8 finishes out of 10 wins = 80%
        assert f.get_finish_rate() == 80.0
    
    def test_finish_rate_no_wins(self):
        """Should handle zero wins."""
        f = FighterTapeData(name="Test", wins=0)
        assert f.get_finish_rate() == 0.0
    
    def test_with_stats(self):
        """Should accept stats dict."""
        stats = {"boxing": 75, "wrestling": 60}
        f = FighterTapeData(name="Test", stats=stats)
        assert f.stats["boxing"] == 75
        assert f.stats["wrestling"] == 60


class TestStatComparison:
    """Test StatComparison dataclass."""
    
    def test_creation(self):
        """Should create with all fields."""
        comp = StatComparison(
            stat_name="boxing",
            display_name="Boxing",
            value1=80,
            value2=70,
            advantage=-1,
            difference=10,
        )
        assert comp.stat_name == "boxing"
        assert comp.value1 == 80
        assert comp.advantage == -1


# ============================================================================
# COMPARISON FUNCTION TESTS
# ============================================================================

class TestCompareStat:
    """Test compare_stat function."""
    
    def test_fighter1_advantage(self):
        """Fighter 1 should have advantage when higher."""
        comp = compare_stat("boxing", 80, 70)
        assert comp.advantage == -1
        assert comp.difference == 10
    
    def test_fighter2_advantage(self):
        """Fighter 2 should have advantage when higher."""
        comp = compare_stat("boxing", 60, 75)
        assert comp.advantage == 1
        assert comp.difference == 15
    
    def test_even_when_close(self):
        """Should be even when difference below threshold."""
        comp = compare_stat("boxing", 72, 70, threshold=5)
        assert comp.advantage == 0
    
    def test_advantage_at_threshold(self):
        """Should show advantage at exactly threshold."""
        comp = compare_stat("boxing", 75, 70, threshold=5)
        assert comp.advantage == -1
    
    def test_display_name(self):
        """Should use display name from mapping."""
        comp = compare_stat("takedown_defense", 70, 60)
        assert comp.display_name == "TD Defense"


class TestGetStatComparison:
    """Test get_stat_comparison function."""
    
    def test_compares_multiple_stats(self):
        """Should compare multiple stats."""
        f1 = FighterTapeData(name="F1", stats={"boxing": 80, "wrestling": 60})
        f2 = FighterTapeData(name="F2", stats={"boxing": 70, "wrestling": 75})
        
        comps = get_stat_comparison(f1, f2, ["boxing", "wrestling"])
        
        assert len(comps) == 2
        assert comps[0].stat_name == "boxing"
        assert comps[0].advantage == -1  # F1 better
        assert comps[1].stat_name == "wrestling"
        assert comps[1].advantage == 1  # F2 better
    
    def test_defaults_missing_stats(self):
        """Should default missing stats to 50."""
        f1 = FighterTapeData(name="F1", stats={"boxing": 80})
        f2 = FighterTapeData(name="F2", stats={})
        
        comps = get_stat_comparison(f1, f2, ["boxing"])
        
        assert comps[0].value1 == 80
        assert comps[0].value2 == 50


class TestCalculateCategoryAdvantage:
    """Test calculate_category_advantage function."""
    
    def test_fighter1_advantage(self):
        """Should return -1 when fighter 1 dominates."""
        comps = [
            StatComparison("a", "A", 80, 60, -1, 20),
            StatComparison("b", "B", 75, 55, -1, 20),
        ]
        assert calculate_category_advantage(comps) == -1
    
    def test_fighter2_advantage(self):
        """Should return 1 when fighter 2 dominates."""
        comps = [
            StatComparison("a", "A", 60, 80, 1, 20),
            StatComparison("b", "B", 55, 75, 1, 20),
        ]
        assert calculate_category_advantage(comps) == 1
    
    def test_even_when_close(self):
        """Should return 0 when roughly even."""
        comps = [
            StatComparison("a", "A", 72, 70, 0, 2),
            StatComparison("b", "B", 68, 70, 0, 2),
        ]
        assert calculate_category_advantage(comps) == 0


class TestAnalyzeMatchup:
    """Test analyze_matchup function."""
    
    def test_returns_all_categories(self):
        """Should return all advantage categories."""
        f1 = FighterTapeData(name="F1", stats={}, wins=10, losses=2)
        f2 = FighterTapeData(name="F2", stats={}, wins=5, losses=1)
        
        result = analyze_matchup(f1, f2)
        
        assert "striking" in result
        assert "grappling" in result
        assert "physical" in result
        assert "experience" in result
    
    def test_striking_advantage(self):
        """Should detect striking advantage."""
        f1 = FighterTapeData(name="F1", stats={
            "boxing": 85, "kicks": 80, "power": 85, "accuracy": 80
        })
        f2 = FighterTapeData(name="F2", stats={
            "boxing": 60, "kicks": 55, "power": 60, "accuracy": 55
        })
        
        result = analyze_matchup(f1, f2)
        assert result["striking"] == -1  # F1 advantage
    
    def test_grappling_advantage(self):
        """Should detect grappling advantage."""
        f1 = FighterTapeData(name="F1", stats={
            "wrestling": 60, "bjj": 55, "takedown_defense": 55, "submissions": 50
        })
        f2 = FighterTapeData(name="F2", stats={
            "wrestling": 85, "bjj": 80, "takedown_defense": 80, "submissions": 85
        })
        
        result = analyze_matchup(f1, f2)
        assert result["grappling"] == 1  # F2 advantage
    
    def test_experience_advantage(self):
        """Should detect experience advantage."""
        f1 = FighterTapeData(name="F1", wins=20, losses=5)  # 25 fights
        f2 = FighterTapeData(name="F2", wins=5, losses=1)   # 6 fights
        
        result = analyze_matchup(f1, f2)
        assert result["experience"] == -1  # F1 more experienced


# ============================================================================
# TALE OF TAPE GENERATION TESTS
# ============================================================================

class TestGenerateTaleOfTape:
    """Test generate_tale_of_tape function."""
    
    def test_basic_generation(self):
        """Should generate tale of tape."""
        f1 = FighterTapeData(name="Fighter One", stats={"boxing": 75})
        f2 = FighterTapeData(name="Fighter Two", stats={"boxing": 70})
        
        tape = generate_tale_of_tape(f1, f2)
        
        assert tape.fighter1 == f1
        assert tape.fighter2 == f2
        assert len(tape.stat_comparisons) > 0
    
    def test_with_title_fight(self):
        """Should mark as title fight."""
        f1 = FighterTapeData(name="Champ", is_champion=True)
        f2 = FighterTapeData(name="Challenger")
        
        tape = generate_tale_of_tape(f1, f2, is_title_fight=True)
        
        assert tape.is_title_fight is True
    
    def test_with_weight_class(self):
        """Should include weight class."""
        f1 = FighterTapeData(name="F1")
        f2 = FighterTapeData(name="F2")
        
        tape = generate_tale_of_tape(f1, f2, weight_class="Welterweight")
        
        assert tape.weight_class == "Welterweight"
    
    def test_calculates_advantages(self):
        """Should calculate matchup advantages."""
        f1 = FighterTapeData(name="Striker", stats={
            "boxing": 85, "kicks": 80, "power": 85, "accuracy": 80,
            "wrestling": 50, "bjj": 45
        })
        f2 = FighterTapeData(name="Grappler", stats={
            "boxing": 55, "kicks": 50, "power": 55, "accuracy": 50,
            "wrestling": 85, "bjj": 85
        })
        
        tape = generate_tale_of_tape(f1, f2)
        
        assert tape.striking_advantage == -1  # Striker advantage
        assert tape.grappling_advantage == 1  # Grappler advantage


# ============================================================================
# DISPLAY TESTS
# ============================================================================

class TestFormatTaleOfTape:
    """Test format_tale_of_tape function."""
    
    def test_returns_list_of_strings(self):
        """Should return list of strings."""
        f1 = FighterTapeData(name="F1", stats={"boxing": 70})
        f2 = FighterTapeData(name="F2", stats={"boxing": 65})
        tape = generate_tale_of_tape(f1, f2)
        
        lines = format_tale_of_tape(tape)
        
        assert isinstance(lines, list)
        assert all(isinstance(line, str) for line in lines)
    
    def test_contains_fighter_names(self):
        """Should contain fighter names."""
        f1 = FighterTapeData(name="John Smith")
        f2 = FighterTapeData(name="Mike Jones")
        tape = generate_tale_of_tape(f1, f2)
        
        lines = format_tale_of_tape(tape)
        output = "\n".join(lines)
        
        assert "JOHN SMITH" in output
        assert "MIKE JONES" in output
    
    def test_contains_vs(self):
        """Should contain VS."""
        f1 = FighterTapeData(name="F1")
        f2 = FighterTapeData(name="F2")
        tape = generate_tale_of_tape(f1, f2)
        
        lines = format_tale_of_tape(tape)
        output = "\n".join(lines)
        
        assert "VS" in output
    
    def test_contains_records(self):
        """Should contain fighter records."""
        f1 = FighterTapeData(name="F1", wins=15, losses=3)
        f2 = FighterTapeData(name="F2", wins=12, losses=4)
        tape = generate_tale_of_tape(f1, f2)
        
        lines = format_tale_of_tape(tape)
        output = "\n".join(lines)
        
        assert "15-3" in output
        assert "12-4" in output
    
    def test_shows_champion(self):
        """Should show champion indicator."""
        f1 = FighterTapeData(name="Champion", is_champion=True)
        f2 = FighterTapeData(name="Challenger")
        tape = generate_tale_of_tape(f1, f2)
        
        lines = format_tale_of_tape(tape)
        output = "\n".join(lines)
        
        assert "(C)" in output or "★" in output
    
    def test_shows_rankings(self):
        """Should show rankings."""
        f1 = FighterTapeData(name="Ranked", ranking=3)
        f2 = FighterTapeData(name="Unranked", ranking=0)
        tape = generate_tale_of_tape(f1, f2)
        
        lines = format_tale_of_tape(tape)
        output = "\n".join(lines)
        
        assert "#3" in output


class TestFormatTaleOfTapeCompact:
    """Test format_tale_of_tape_compact function."""
    
    def test_returns_shorter_output(self):
        """Should return fewer lines than full format."""
        f1 = FighterTapeData(name="F1", stats={"boxing": 70})
        f2 = FighterTapeData(name="F2", stats={"boxing": 65})
        tape = generate_tale_of_tape(f1, f2)
        
        full_lines = format_tale_of_tape(tape)
        compact_lines = format_tale_of_tape_compact(tape)
        
        assert len(compact_lines) < len(full_lines)
    
    def test_contains_key_info(self):
        """Should still contain key info."""
        f1 = FighterTapeData(name="Fighter One", wins=10, losses=2)
        f2 = FighterTapeData(name="Fighter Two", wins=8, losses=3)
        tape = generate_tale_of_tape(f1, f2)
        
        lines = format_tale_of_tape_compact(tape)
        output = "\n".join(lines)
        
        assert "Fighter One" in output
        assert "Fighter Two" in output
        assert "10-2" in output


# ============================================================================
# QUICK COMPARISON TESTS
# ============================================================================

class TestGetQuickComparison:
    """Test get_quick_comparison function."""
    
    def test_returns_dict(self):
        """Should return dictionary."""
        f1 = FighterTapeData(name="F1")
        f2 = FighterTapeData(name="F2")
        
        result = get_quick_comparison(f1, f2)
        
        assert isinstance(result, dict)
        assert "fighter1" in result
        assert "fighter2" in result
        assert "favorite" in result
    
    def test_identifies_favorite(self):
        """Should identify favorite."""
        f1 = FighterTapeData(name="Strong", stats={
            "boxing": 85, "kicks": 85, "wrestling": 85, "bjj": 85,
            "cardio": 85, "strength": 85, "speed": 85
        }, wins=20, losses=2)
        f2 = FighterTapeData(name="Weak", stats={
            "boxing": 55, "kicks": 55, "wrestling": 55, "bjj": 55,
            "cardio": 55, "strength": 55, "speed": 55
        }, wins=5, losses=10)
        
        result = get_quick_comparison(f1, f2)
        
        assert result["favorite"] == "Strong"
        assert result["confidence"] == "strong"
    
    def test_even_fight(self):
        """Should detect even fight."""
        f1 = FighterTapeData(name="F1", stats={"boxing": 70})
        f2 = FighterTapeData(name="F2", stats={"boxing": 70})
        
        result = get_quick_comparison(f1, f2)
        
        assert result["favorite"] == "Even"
        assert result["confidence"] == "pick'em"


class TestGetPredictionText:
    """Test get_prediction_text function."""
    
    def test_even_fight_text(self):
        """Should generate even fight text."""
        comp = {"favorite": "Even", "confidence": "pick'em"}
        text = get_prediction_text(comp)
        
        assert "even" in text.lower() or "either way" in text.lower()
    
    def test_strong_favorite_text(self):
        """Should generate strong favorite text."""
        comp = {"favorite": "John", "confidence": "strong"}
        text = get_prediction_text(comp)
        
        assert "John" in text
        assert "significant" in text.lower() or "favored" in text.lower()
    
    def test_slight_favorite_text(self):
        """Should generate slight favorite text."""
        comp = {"favorite": "Mike", "confidence": "slight"}
        text = get_prediction_text(comp)
        
        assert "Mike" in text
        assert "slight" in text.lower() or "edge" in text.lower()


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestCreateFighterTapeData:
    """Test create_fighter_tape_data helper."""
    
    def test_basic_creation(self):
        """Should create with basic info."""
        f = create_fighter_tape_data(
            name="Test Fighter",
            stats={"boxing": 75, "wrestling": 70},
        )
        
        assert f.name == "Test Fighter"
        assert f.stats["boxing"] == 75
    
    def test_with_record(self):
        """Should set record from tuple."""
        f = create_fighter_tape_data(
            name="Test",
            stats={},
            record=(15, 3, 1),
        )
        
        assert f.wins == 15
        assert f.losses == 3
        assert f.draws == 1
    
    def test_with_finishes(self):
        """Should set finishes from tuple."""
        f = create_fighter_tape_data(
            name="Test",
            stats={},
            record=(10, 2, 0),
            finishes=(5, 3),  # 5 KOs, 3 subs
        )
        
        assert f.ko_wins == 5
        assert f.sub_wins == 3
        assert f.dec_wins == 2  # 10 - 5 - 3
    
    def test_with_physical(self):
        """Should set physical attributes."""
        f = create_fighter_tape_data(
            name="Test",
            stats={},
            physical={"age": 32, "height": 73, "weight": 185, "reach": 76},
        )
        
        assert f.age == 32
        assert f.height == 73
        assert f.weight == 185
        assert f.reach == 76
    
    def test_with_kwargs(self):
        """Should pass through kwargs."""
        f = create_fighter_tape_data(
            name="Test",
            stats={},
            nickname="The Destroyer",
            fighting_style="Muay Thai",
            camp_name="Tiger Gym",
        )
        
        assert f.nickname == "The Destroyer"
        assert f.fighting_style == "Muay Thai"
        assert f.camp_name == "Tiger Gym"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestTaleOfTapeIntegration:
    """Integration tests for complete workflows."""
    
    def test_full_workflow(self):
        """Test complete tale of tape workflow."""
        # Create two fighters with different strengths
        striker = create_fighter_tape_data(
            name="Knockout King",
            nickname="KO",
            stats={
                "boxing": 88, "kicks": 82, "power": 90, "accuracy": 85,
                "wrestling": 55, "bjj": 50, "takedown_defense": 60,
                "submissions": 45, "top_control": 50,
                "chin": 75, "cardio": 70, "recovery": 70,
            },
            record=(18, 3, 0),
            finishes=(15, 1),
            physical={"age": 29, "height": 73, "weight": 185, "reach": 76},
            is_champion=True,
            fighting_style="Boxing",
            camp_name="Strike Force",
        )
        
        grappler = create_fighter_tape_data(
            name="Ground Shark",
            nickname="Shark",
            stats={
                "boxing": 58, "kicks": 55, "power": 60, "accuracy": 60,
                "wrestling": 90, "bjj": 92, "takedown_defense": 80,
                "submissions": 88, "top_control": 85,
                "chin": 70, "cardio": 80, "recovery": 75,
            },
            record=(15, 2, 0),
            finishes=(2, 12),
            physical={"age": 31, "height": 71, "weight": 185, "reach": 73},
            ranking=1,
            fighting_style="Brazilian Jiu-Jitsu",
            camp_name="Ground Zero",
        )
        
        # Generate tale of tape
        tape = generate_tale_of_tape(
            striker, grappler,
            is_title_fight=True,
            weight_class="Middleweight"
        )
        
        # Check structure
        assert tape.is_title_fight is True
        assert tape.weight_class == "Middleweight"
        assert tape.fighter1.is_champion is True
        assert tape.fighter2.ranking == 1
        
        # Check advantages
        assert tape.striking_advantage == -1  # Striker has advantage
        assert tape.grappling_advantage == 1  # Grappler has advantage
        
        # Format and check output
        lines = format_tale_of_tape(tape)
        output = "\n".join(lines)
        
        assert "CHAMPIONSHIP" in output
        assert "KNOCKOUT KING" in output
        assert "GROUND SHARK" in output
        assert "18-3" in output
        assert "15-2" in output
        
        # Get prediction
        comparison = get_quick_comparison(striker, grappler)
        prediction = get_prediction_text(comparison)
        
        assert len(prediction) > 0
    
    def test_even_matchup(self):
        """Test evenly matched fighters."""
        f1 = create_fighter_tape_data(
            name="Fighter One",
            stats={
                "boxing": 75, "kicks": 75, "power": 75, "accuracy": 75,
                "wrestling": 75, "bjj": 75, "takedown_defense": 75,
                "submissions": 75, "cardio": 75, "chin": 75,
            },
            record=(10, 3, 0),
        )
        
        f2 = create_fighter_tape_data(
            name="Fighter Two",
            stats={
                "boxing": 75, "kicks": 75, "power": 75, "accuracy": 75,
                "wrestling": 75, "bjj": 75, "takedown_defense": 75,
                "submissions": 75, "cardio": 75, "chin": 75,
            },
            record=(10, 3, 0),
        )
        
        tape = generate_tale_of_tape(f1, f2)
        
        assert tape.striking_advantage == 0
        assert tape.grappling_advantage == 0
        
        lines = format_tale_of_tape(tape)
        output = "\n".join(lines)
        
        assert "evenly matched" in output.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
