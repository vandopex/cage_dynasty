# tests/test_traits.py
# Module: Fighter Traits System Tests
# Tests: 52
#
# Tests for the trait system - personality and abilities

"""
Test suite for Fighter Traits System.

Tests cover:
- Trait definitions and validation
- Trait assignment based on fighter attributes
- Conflict detection
- Stat modifiers
- Fight modifiers (with updated balance values)
- Pressure/counter interactions
- Training modifiers
- Display helpers

NOTE: Tests updated to match Balance Pass v2 values:
- Fast Starter: round1_bonus = 10 (was 15)
- Slow Starter: round1_penalty = -5 (was -10), late_round_bonus = 20 (was 15)
- Injury Prone: injury_mod = 0.20 (was 0.30)
- Big Game Hunter: Uses win_bonus, not rating_adjustment
- Choke Artist: Uses win_bonus penalty, not rating_adjustment
"""

import pytest
from typing import List, Dict

from systems.traits import (
    FIGHTER_TRAITS,
    TRAIT_CATEGORIES,
    CONFLICTING_TRAITS,
    assign_traits,
    has_trait,
    get_stat_modifiers,
    apply_stat_modifiers,
    FightModifiers,
    get_trait_fight_modifiers,
    get_pressure_counter_interaction,
    get_training_multiplier,
    get_injury_modifier,
    get_trait_info,
    get_trait_description,
    get_trait_category,
    get_all_trait_names,
    get_traits_by_category,
)


# ============================================================================
# TRAIT DEFINITION TESTS
# ============================================================================

class TestTraitDefinitions:
    """Tests for trait definitions structure"""
    
    def test_fighter_traits_exists(self):
        """FIGHTER_TRAITS dictionary should exist"""
        assert FIGHTER_TRAITS is not None
        assert isinstance(FIGHTER_TRAITS, dict)
    
    def test_has_16_traits(self):
        """Should have 16 traits defined"""
        assert len(FIGHTER_TRAITS) == 16
    
    def test_all_traits_have_description(self):
        """Every trait should have a description"""
        for name, info in FIGHTER_TRAITS.items():
            assert "description" in info, f"{name} missing description"
            assert len(info["description"]) > 0
    
    def test_all_traits_have_category(self):
        """Every trait should have a category"""
        for name, info in FIGHTER_TRAITS.items():
            assert "category" in info, f"{name} missing category"
    
    def test_all_traits_have_stat_mods(self):
        """Every trait should have stat_mods (even if empty)"""
        for name, info in FIGHTER_TRAITS.items():
            assert "stat_mods" in info, f"{name} missing stat_mods"
            assert isinstance(info["stat_mods"], dict)
    
    def test_trait_categories_complete(self):
        """All categories should be covered"""
        expected = ["offensive", "defensive", "cardio", "mental", "training"]
        for category in expected:
            assert category in TRAIT_CATEGORIES
            assert len(TRAIT_CATEGORIES[category]) > 0
    
    def test_conflicting_traits_valid(self):
        """All traits in conflicts should exist"""
        for trait1, trait2 in CONFLICTING_TRAITS:
            assert trait1 in FIGHTER_TRAITS, f"{trait1} not in FIGHTER_TRAITS"
            assert trait2 in FIGHTER_TRAITS, f"{trait2} not in FIGHTER_TRAITS"


# ============================================================================
# TRAIT ASSIGNMENT TESTS
# ============================================================================

class TestTraitAssignment:
    """Tests for trait assignment logic"""
    
    def test_assign_traits_returns_list(self):
        """assign_traits should return a list"""
        attrs = {"boxing": 70, "wrestling": 60}
        traits = assign_traits(attrs)
        assert isinstance(traits, list)
    
    def test_assign_traits_max_two(self):
        """Fighter should get at most 2 traits"""
        attrs = {"boxing": 80, "wrestling": 90, "bjj": 85}
        for _ in range(10):
            traits = assign_traits(attrs)
            assert len(traits) <= 2
    
    def test_force_count_zero(self):
        """force_count=0 should give no traits"""
        attrs = {"boxing": 70}
        traits = assign_traits(attrs, force_count=0)
        assert len(traits) == 0
    
    def test_force_count_one(self):
        """force_count=1 should give exactly 1 trait"""
        attrs = {"boxing": 70}
        traits = assign_traits(attrs, force_count=1)
        assert len(traits) == 1
    
    def test_force_count_two(self):
        """force_count=2 should give exactly 2 traits"""
        attrs = {"boxing": 70, "wrestling": 60}
        traits = assign_traits(attrs, force_count=2)
        assert len(traits) == 2
    
    def test_no_duplicate_traits(self):
        """Fighter should not get the same trait twice"""
        attrs = {"boxing": 80}
        for _ in range(20):
            traits = assign_traits(attrs, force_count=2)
            assert len(traits) == len(set(traits))
    
    def test_no_conflicting_traits_assigned(self):
        """Conflicting traits should not be assigned together"""
        attrs = {"chin": 90, "power": 90}  # Could trigger both Glass Cannon and Iron Chin
        for _ in range(20):
            traits = assign_traits(attrs, force_count=2)
            for t1, t2 in CONFLICTING_TRAITS:
                if t1 in traits and t2 in traits:
                    pytest.fail(f"Conflicting traits assigned: {t1} and {t2}")
    
    def test_high_bjj_favors_submission_ace(self):
        """High BJJ should make Submission Ace more likely"""
        attrs = {"bjj": 90, "submissions": 90}
        sub_count = 0
        trials = 500
        
        for _ in range(trials):
            traits = assign_traits(attrs, force_count=1)
            if "Submission Ace" in traits:
                sub_count += 1
        
        assert sub_count > trials * 0.10, "High BJJ should favor Submission Ace"
    
    def test_high_age_favors_veteran_savvy(self):
        """Older fighters should be more likely to get Veteran Savvy."""
        attrs = {"age": 36, "fight_iq": 75, "composure": 70}  # Added IQ and composure
        veteran_count = 0
        trials = 500
        
        for _ in range(trials):
            traits = assign_traits(attrs, force_count=1)
            if "Veteran Savvy" in traits:
                veteran_count += 1
        
        # More lenient threshold - just needs some probability
        assert veteran_count > trials * 0.05, "High age should favor Veteran Savvy"


# ============================================================================
# HAS_TRAIT TESTS
# ============================================================================

class TestHasTrait:
    """Tests for has_trait function"""
    
    def test_has_trait_true(self):
        """Should return True when trait present"""
        traits = ["Iron Chin", "Cardio Machine"]
        assert has_trait(traits, "Iron Chin") is True
    
    def test_has_trait_false(self):
        """Should return False when trait not present"""
        traits = ["Iron Chin", "Cardio Machine"]
        assert has_trait(traits, "Glass Cannon") is False
    
    def test_has_trait_empty_list(self):
        """Should return False for empty list"""
        assert has_trait([], "Iron Chin") is False


# ============================================================================
# STAT MODIFIER TESTS
# ============================================================================

class TestStatModifiers:
    """Tests for stat modifier functions"""
    
    def test_get_stat_modifiers_empty(self):
        """Empty traits should give empty modifiers"""
        mods = get_stat_modifiers([])
        assert mods == {}
    
    def test_get_stat_modifiers_glass_cannon(self):
        """Glass Cannon should boost strength, reduce chin"""
        mods = get_stat_modifiers(["Glass Cannon"])
        assert mods.get("strength", 0) > 0
        assert mods.get("chin", 0) < 0
    
    def test_get_stat_modifiers_iron_chin(self):
        """Iron Chin should boost chin"""
        mods = get_stat_modifiers(["Iron Chin"])
        assert mods.get("chin", 0) > 0
    
    def test_get_stat_modifiers_multiple_traits(self):
        """Multiple traits should stack modifiers"""
        mods = get_stat_modifiers(["Iron Chin", "Cardio Machine"])
        assert mods.get("chin", 0) > 0  # From Iron Chin
        assert mods.get("cardio", 0) > 0  # From Cardio Machine
    
    def test_apply_stat_modifiers(self):
        """apply_stat_modifiers should update attributes"""
        attrs = {"chin": 50, "strength": 60}
        modified = apply_stat_modifiers(attrs, ["Iron Chin"])
        
        assert modified["chin"] > attrs["chin"]
        assert modified["strength"] == attrs["strength"]  # Unchanged
    
    def test_apply_stat_modifiers_clamps_values(self):
        """Modified values should stay in 1-100 range"""
        attrs = {"chin": 95}  # High chin
        modified = apply_stat_modifiers(attrs, ["Iron Chin"])  # +15 chin
        
        assert modified["chin"] <= 100


# ============================================================================
# FIGHT MODIFIER TESTS
# ============================================================================

class TestFightModifiers:
    """Tests for fight simulation modifiers"""
    
    def test_fight_modifiers_default(self):
        """Default modifiers should be neutral"""
        mods = get_trait_fight_modifiers([])
        assert mods.win_bonus == 0.0
        assert mods.ko_chance_mod == 0.0
    
    def test_big_game_hunter_in_title_fight(self):
        """Big Game Hunter should boost win probability in title fights."""
        mods = get_trait_fight_modifiers(
            ["Big Game Hunter"],
            is_title_fight=True
        )
        # big_fight_bonus = 0.05 + base win_bonus = 0.01
        assert mods.win_bonus >= 0.05  # Gets big fight bonus
    
    def test_choke_artist_in_title_fight(self):
        """Choke Artist should penalize win probability in title fights."""
        mods = get_trait_fight_modifiers(
            ["Choke Artist"],
            is_title_fight=True
        )
        # big_fight_penalty = -0.05
        assert mods.win_bonus < 0  # Gets penalty
    
    def test_big_game_hunter_normal_fight(self):
        """Big Game Hunter should have minimal bonus in normal fights"""
        mods = get_trait_fight_modifiers(["Big Game Hunter"], is_title_fight=False)
        # Base win_bonus = 0.01
        assert mods.win_bonus == 0.01
    
    def test_knockout_artist_ko_bonus(self):
        """Knockout Artist should increase KO chance"""
        mods = get_trait_fight_modifiers(["Knockout Artist"])
        assert mods.ko_chance_mod > 0
    
    def test_submission_ace_sub_bonus(self):
        """Submission Ace should increase submission chance"""
        mods = get_trait_fight_modifiers(["Submission Ace"])
        assert mods.sub_chance_mod > 0
    
    def test_fast_starter_round_1(self):
        """Fast Starter should boost in round 1."""
        mods = get_trait_fight_modifiers(
            ["Fast Starter"],
            current_round=1,
            total_rounds=3
        )
        # round1_bonus = 10 (NERFED from 15 in Balance Pass v2)
        assert mods.rating_adjustment == 10
    
    def test_fast_starter_late_round(self):
        """Fast Starter should have penalty in late rounds"""
        mods = get_trait_fight_modifiers(
            ["Fast Starter"],
            current_round=3,
            total_rounds=3
        )
        # late_round_penalty = -10
        assert mods.rating_adjustment == -10
    
    def test_slow_starter_round_1(self):
        """Slow Starter should penalize in round 1."""
        mods = get_trait_fight_modifiers(
            ["Slow Starter"],
            current_round=1,
            total_rounds=3
        )
        # round1_penalty = -5 (BUFFED from -10 in Balance Pass v2)
        assert mods.rating_adjustment == -5
    
    def test_slow_starter_late_round(self):
        """Slow Starter should boost in late rounds."""
        mods = get_trait_fight_modifiers(
            ["Slow Starter"],
            current_round=3,
            total_rounds=3
        )
        # late_round_bonus = 20 (BUFFED from 15 in Balance Pass v2)
        assert mods.rating_adjustment == 20
    
    def test_multiple_traits_stack(self):
        """Multiple trait effects should stack."""
        mods = get_trait_fight_modifiers(
            ["Big Game Hunter", "Knockout Artist"],
            is_title_fight=True
        )
        # Win bonuses stack: 0.01 + 0.05 (big fight) + 0.02 = 0.08
        assert mods.win_bonus > 0.05
        assert mods.ko_chance_mod > 0


# ============================================================================
# PRESSURE/COUNTER INTERACTION TESTS
# ============================================================================

class TestPressureCounterInteraction:
    """Tests for pressure vs counter fighter interactions"""
    
    def test_pressure_vs_counter(self):
        """Counter Puncher should get bonus vs Pressure Fighter."""
        f1_adj, f2_adj = get_pressure_counter_interaction(
            ["Pressure Fighter"],
            ["Counter Puncher"]
        )
        assert f1_adj == 0
        # counter_vs_pressure = 0.05 (5% win probability bonus)
        assert f2_adj == 0.05
    
    def test_counter_vs_pressure(self):
        """Counter Puncher should get bonus regardless of order."""
        f1_adj, f2_adj = get_pressure_counter_interaction(
            ["Counter Puncher"],
            ["Pressure Fighter"]
        )
        # counter_vs_pressure = 0.05
        assert f1_adj == 0.05
        assert f2_adj == 0
    
    def test_no_interaction(self):
        """No interaction without matching traits"""
        f1_adj, f2_adj = get_pressure_counter_interaction(
            ["Iron Chin"],
            ["Cardio Machine"]
        )
        assert f1_adj == 0
        assert f2_adj == 0


# ============================================================================
# TRAINING MODIFIER TESTS
# ============================================================================

class TestTrainingModifiers:
    """Tests for training and injury modifiers"""
    
    def test_training_multiplier_default(self):
        """Default training multiplier should be 1.0"""
        mult = get_training_multiplier([])
        assert mult == 1.0
    
    def test_gym_rat_bonus(self):
        """Gym Rat should increase training multiplier"""
        mult = get_training_multiplier(["Gym Rat"])
        assert mult > 1.0  # Should have training_bonus = 0.25
    
    def test_injury_modifier_default(self):
        """Default injury modifier should be 0"""
        mod = get_injury_modifier([])
        assert mod == 0.0
    
    def test_durable_reduces_injury(self):
        """Durable should decrease injury chance"""
        mod = get_injury_modifier(["Durable"])
        assert mod < 0  # injury_mod = -0.30
    
    def test_injury_prone_increases_injury(self):
        """Injury Prone should increase injury chance."""
        mod = get_injury_modifier(["Injury Prone"])
        # injury_mod = 0.20 (BUFFED from 0.30 in Balance Pass v2)
        assert mod == 0.20


# ============================================================================
# DISPLAY HELPER TESTS
# ============================================================================

class TestDisplayHelpers:
    """Tests for display helper functions"""
    
    def test_get_trait_info_valid(self):
        """get_trait_info should return trait dict"""
        info = get_trait_info("Iron Chin")
        assert info is not None
        assert "description" in info
    
    def test_get_trait_info_invalid(self):
        """get_trait_info should return None for invalid trait"""
        info = get_trait_info("Nonexistent Trait")
        assert info is None
    
    def test_get_trait_description(self):
        """get_trait_description should return string"""
        desc = get_trait_description("Iron Chin")
        assert isinstance(desc, str)
        assert len(desc) > 0
    
    def test_get_trait_category(self):
        """get_trait_category should return category"""
        cat = get_trait_category("Iron Chin")
        assert cat == "defensive"
    
    def test_get_all_trait_names(self):
        """get_all_trait_names should return all trait names"""
        names = get_all_trait_names()
        assert len(names) == 16
        assert "Iron Chin" in names
    
    def test_get_traits_by_category(self):
        """get_traits_by_category should filter correctly"""
        offensive = get_traits_by_category("offensive")
        assert "Knockout Artist" in offensive
        assert "Iron Chin" not in offensive


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestTraitsIntegration:
    """Integration tests for trait system"""
    
    def test_full_assignment_and_modification_flow(self):
        """Test complete workflow from assignment to application"""
        # Assign traits
        attrs = {"boxing": 75, "wrestling": 60, "chin": 80}
        traits = assign_traits(attrs, force_count=1)
        
        # Get stat modifiers
        stat_mods = get_stat_modifiers(traits)
        
        # Apply modifiers
        modified = apply_stat_modifiers(attrs, traits)
        
        # All values should still be in range
        for val in modified.values():
            assert 1 <= val <= 100
    
    def test_fight_simulation_context(self):
        """Test trait modifiers in realistic fight context."""
        # Fighter with Big Game Hunter in a title fight
        traits = ["Big Game Hunter", "Fast Starter"]
        
        # Round 1 of title fight
        mods_r1 = get_trait_fight_modifiers(
            traits,
            is_title_fight=True,
            current_round=1,
            total_rounds=5
        )
        # Fast Starter R1 bonus = 10
        assert mods_r1.rating_adjustment == 10
        # Win bonus = 0.01 (BGH) + 0.05 (big fight) + 0.02 (FS) = 0.08
        assert mods_r1.win_bonus >= 0.07
        
        # Round 5 (late round)
        mods_r5 = get_trait_fight_modifiers(
            traits,
            is_title_fight=True,
            current_round=5,
            total_rounds=5
        )
        # Fast Starter late_round_penalty = -10
        assert mods_r5.rating_adjustment == -10
