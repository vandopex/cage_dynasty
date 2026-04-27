# tests/test_fotn.py
# Tests for Fight of the Night system
# Run: python3 -m pytest tests/test_fotn.py -v

"""
Tests for systems/fotn.py

Covers:
- FOTN score calculation
- FOTN selection from multiple fights
- Basic score fallback
- Excitement tiers
- Edge cases
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from systems.fotn import (
    calculate_fotn_score,
    select_fotn,
    format_fotn_announcement,
    create_fotn_result,
    is_fight_exciting,
    get_excitement_tier,
    FOTNResult,
    FOTN_BONUS,
    MIN_FIGHTS_FOR_FOTN,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def exciting_fight():
    """A very exciting fight with lots of action"""
    return {
        "fighter1_id": "f1",
        "fighter2_id": "f2",
        "fighter1_stats": [
            {"damage_dealt": 80, "knockdowns": 2, "sub_att": 0},
            {"damage_dealt": 70, "knockdowns": 1, "sub_att": 0},
            {"damage_dealt": 90, "knockdowns": 1, "sub_att": 0},
        ],
        "fighter2_stats": [
            {"damage_dealt": 75, "knockdowns": 1, "sub_att": 1},
            {"damage_dealt": 85, "knockdowns": 0, "sub_att": 0},
            {"damage_dealt": 65, "knockdowns": 1, "sub_att": 2},
        ],
        "method": "KO",
        "finish_round": 3,
        "is_title_fight": True,
        "winner_id": "f1",
        "loser_id": "f2",
    }


@pytest.fixture
def boring_fight():
    """A boring fight with minimal action"""
    return {
        "fighter1_id": "f3",
        "fighter2_id": "f4",
        "fighter1_stats": [
            {"damage_dealt": 10, "knockdowns": 0, "sub_att": 0},
            {"damage_dealt": 15, "knockdowns": 0, "sub_att": 0},
            {"damage_dealt": 12, "knockdowns": 0, "sub_att": 0},
        ],
        "fighter2_stats": [
            {"damage_dealt": 8, "knockdowns": 0, "sub_att": 0},
            {"damage_dealt": 10, "knockdowns": 0, "sub_att": 0},
            {"damage_dealt": 5, "knockdowns": 0, "sub_att": 0},
        ],
        "method": "Decision",
        "finish_round": None,
        "is_title_fight": False,
        "winner_id": "f3",
        "loser_id": "f4",
    }


@pytest.fixture
def average_fight():
    """An average fight"""
    return {
        "fighter1_id": "f5",
        "fighter2_id": "f6",
        "fighter1_stats": [
            {"damage_dealt": 40, "knockdowns": 0, "sub_att": 0},
            {"damage_dealt": 35, "knockdowns": 1, "sub_att": 0},
        ],
        "fighter2_stats": [
            {"damage_dealt": 30, "knockdowns": 0, "sub_att": 1},
            {"damage_dealt": 45, "knockdowns": 0, "sub_att": 0},
        ],
        "method": "TKO",
        "finish_round": 2,
        "is_title_fight": False,
        "winner_id": "f5",
        "loser_id": "f6",
    }


@pytest.fixture
def close_decision():
    """A close split decision fight"""
    return {
        "fighter1_id": "f7",
        "fighter2_id": "f8",
        "fighter1_stats": [
            {"damage_dealt": 45, "knockdowns": 0, "sub_att": 0},
            {"damage_dealt": 50, "knockdowns": 0, "sub_att": 0},
            {"damage_dealt": 48, "knockdowns": 0, "sub_att": 0},
        ],
        "fighter2_stats": [
            {"damage_dealt": 47, "knockdowns": 0, "sub_att": 0},
            {"damage_dealt": 46, "knockdowns": 0, "sub_att": 0},
            {"damage_dealt": 52, "knockdowns": 0, "sub_att": 0},
        ],
        "method": "Split Decision",
        "finish_round": None,
        "is_title_fight": False,
        "winner_id": "f7",
        "loser_id": "f8",
    }


# ============================================================================
# SCORE CALCULATION TESTS
# ============================================================================

class TestScoreCalculation:
    def test_exciting_fight_scores_high(self, exciting_fight):
        score = calculate_fotn_score(exciting_fight)
        assert score > 200  # Should be high
    
    def test_boring_fight_scores_low(self, boring_fight):
        score = calculate_fotn_score(boring_fight)
        assert score < 100  # Should be low
    
    def test_knockdowns_add_score(self, average_fight):
        # Get base score
        base_score = calculate_fotn_score(average_fight)
        
        # Add more knockdowns
        fight_with_kd = average_fight.copy()
        fight_with_kd["fighter1_stats"] = [
            {"damage_dealt": 40, "knockdowns": 3, "sub_att": 0},
            {"damage_dealt": 35, "knockdowns": 2, "sub_att": 0},
        ]
        new_score = calculate_fotn_score(fight_with_kd)
        
        assert new_score > base_score
    
    def test_title_fight_multiplier(self, average_fight):
        # Non-title score
        average_fight["is_title_fight"] = False
        non_title_score = calculate_fotn_score(average_fight)
        
        # Title score
        average_fight["is_title_fight"] = True
        title_score = calculate_fotn_score(average_fight)
        
        # Should be ~20% higher
        assert title_score > non_title_score
        assert abs(title_score / non_title_score - 1.2) < 0.01
    
    def test_late_finish_bonus(self):
        early_finish = {
            "fighter1_stats": [{"damage_dealt": 50, "knockdowns": 1, "sub_att": 0}],
            "fighter2_stats": [{"damage_dealt": 40, "knockdowns": 0, "sub_att": 0}],
            "method": "KO",
            "finish_round": 1,
            "is_title_fight": False,
        }
        
        late_finish = {
            "fighter1_stats": [
                {"damage_dealt": 50, "knockdowns": 0, "sub_att": 0},
                {"damage_dealt": 50, "knockdowns": 0, "sub_att": 0},
                {"damage_dealt": 50, "knockdowns": 1, "sub_att": 0},
            ],
            "fighter2_stats": [
                {"damage_dealt": 40, "knockdowns": 0, "sub_att": 0},
                {"damage_dealt": 40, "knockdowns": 0, "sub_att": 0},
                {"damage_dealt": 40, "knockdowns": 0, "sub_att": 0},
            ],
            "method": "KO",
            "finish_round": 3,
            "is_title_fight": False,
        }
        
        early_score = calculate_fotn_score(early_finish)
        late_score = calculate_fotn_score(late_finish)
        
        # Late finish should have bonus even with same KD count
        # (plus more damage from more rounds)
        assert late_score > early_score
    
    def test_close_fight_bonus(self, close_decision):
        score = calculate_fotn_score(close_decision)
        
        # Close split decision should get bonus
        assert score > 100  # Split decision bonus + action
    
    def test_method_bonuses(self):
        base = {
            "fighter1_stats": [{"damage_dealt": 50, "knockdowns": 0, "sub_att": 0}],
            "fighter2_stats": [{"damage_dealt": 50, "knockdowns": 0, "sub_att": 0}],
            "finish_round": 1,
            "is_title_fight": False,
        }
        
        ko_fight = {**base, "method": "KO"}
        tko_fight = {**base, "method": "TKO"}
        sub_fight = {**base, "method": "Submission"}
        dec_fight = {**base, "method": "Decision", "finish_round": None}
        
        ko_score = calculate_fotn_score(ko_fight)
        tko_score = calculate_fotn_score(tko_fight)
        sub_score = calculate_fotn_score(sub_fight)
        dec_score = calculate_fotn_score(dec_fight)
        
        # KO should score highest, then TKO, then SUB, then DEC
        assert ko_score > tko_score
        assert tko_score > sub_score
        assert sub_score > dec_score


class TestBasicScoring:
    def test_basic_score_no_stats(self):
        fight = {
            "method": "KO",
            "finish_round": 2,
            "is_title_fight": False,
        }
        score = calculate_fotn_score(fight)
        assert score > 0
    
    def test_basic_score_split_decision(self):
        fight = {
            "method": "Split Decision",
            "finish_round": None,
            "is_title_fight": False,
        }
        score = calculate_fotn_score(fight)
        assert score > 100  # Split decision bonus


# ============================================================================
# FOTN SELECTION TESTS
# ============================================================================

class TestFOTNSelection:
    def test_select_from_multiple_fights(self, exciting_fight, boring_fight, average_fight):
        fights = [exciting_fight, boring_fight, average_fight]
        winner, score = select_fotn(fights)
        
        assert winner is not None
        assert winner == exciting_fight  # Most exciting should win
        assert score > 0
    
    def test_no_fotn_with_single_fight(self, exciting_fight):
        fights = [exciting_fight]
        winner, score = select_fotn(fights)
        
        # Need minimum fights
        assert winner is None
    
    def test_no_fotn_with_empty_list(self):
        winner, score = select_fotn([])
        assert winner is None
        assert score == 0.0
    
    def test_fotn_returns_highest_scorer(self, close_decision, average_fight):
        # Create two fights with known relative scores
        fights = [average_fight, close_decision]
        
        winner, score = select_fotn(fights)
        assert winner is not None
        assert score > 0


# ============================================================================
# FOTN RESULT TESTS
# ============================================================================

class TestFOTNResult:
    def test_create_fotn_result(self, exciting_fight):
        result = create_fotn_result(exciting_fight, 250.0, "Fighter One", "Fighter Two")
        
        assert result.fighter1_name == "Fighter One"
        assert result.fighter2_name == "Fighter Two"
        assert result.score == 250.0
        assert result.bonus_amount == FOTN_BONUS
    
    def test_fotn_result_serialization(self, exciting_fight):
        result = create_fotn_result(exciting_fight, 250.0, "Fighter One", "Fighter Two")
        
        data = result.to_dict()
        restored = FOTNResult.from_dict(data)
        
        assert restored.fighter1_name == result.fighter1_name
        assert restored.fighter2_name == result.fighter2_name
        assert restored.score == result.score


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================

class TestUtilityFunctions:
    def test_is_fight_exciting_true(self, exciting_fight):
        assert is_fight_exciting(exciting_fight, threshold=100.0) is True
    
    def test_is_fight_exciting_false(self, boring_fight):
        assert is_fight_exciting(boring_fight, threshold=100.0) is False
    
    def test_excitement_tier_instant_classic(self):
        tier = get_excitement_tier(350)
        assert tier == "INSTANT CLASSIC"
    
    def test_excitement_tier_foty_candidate(self):
        tier = get_excitement_tier(250)
        assert tier == "Fight of the Year Candidate"
    
    def test_excitement_tier_excellent(self):
        tier = get_excitement_tier(175)
        assert tier == "Excellent"
    
    def test_excitement_tier_great(self):
        tier = get_excitement_tier(125)
        assert tier == "Great"
    
    def test_excitement_tier_good(self):
        tier = get_excitement_tier(75)
        assert tier == "Good"
    
    def test_excitement_tier_standard(self):
        tier = get_excitement_tier(25)
        assert tier == "Standard"
    
    def test_format_announcement(self, exciting_fight):
        announcement = format_fotn_announcement(
            exciting_fight, 250.0, "John Smith", "Mike Jones"
        )
        
        assert "FIGHT OF THE NIGHT" in announcement
        assert "John Smith" in announcement
        assert "Mike Jones" in announcement
        assert "$50,000" in announcement


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    def test_empty_stats_lists(self):
        fight = {
            "fighter1_stats": [],
            "fighter2_stats": [],
            "method": "KO",
            "finish_round": 1,
            "is_title_fight": False,
        }
        score = calculate_fotn_score(fight)
        assert score > 0  # Should fall back to basic scoring
    
    def test_missing_keys(self):
        fight = {"method": "Decision"}
        score = calculate_fotn_score(fight)
        assert score >= 0
    
    def test_alternative_stat_keys(self):
        # Test with "damage" instead of "damage_dealt"
        fight = {
            "fighter1_stats": [{"damage": 50, "knockdowns": 1, "submission_attempts": 2}],
            "fighter2_stats": [{"damage": 40, "knockdowns": 0, "sub_att": 1}],
            "method": "TKO",
            "finish_round": 1,
            "is_title_fight": False,
        }
        score = calculate_fotn_score(fight)
        assert score > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
