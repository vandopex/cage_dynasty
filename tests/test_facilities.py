# tests/test_facilities.py
# Tests for the Facility Caps System
# Run: python3 -m pytest tests/test_facilities.py -v

"""
Tests for systems/facilities.py

Tests cover:
- Stat cap definitions
- Cap enforcement during training
- Tier progression
- Upgrade costs and requirements
- Roster limits
- Display helpers
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from systems.facilities import (
    CampStats,
    FACILITY_TIERS,
    FACILITY_STAT_CAPS,
    TIER_ORDER,
    MAX_FIGHTERS,
    UPGRADE_COSTS,
    MONTHLY_COSTS,
    MAINTENANCE_COSTS,
    TRAINING_EFFICIENCY,
    UPGRADE_REQUIREMENTS,
    CAPPED_STATS,
    UNCAPPED_STATS,
    get_stat_cap,
    get_tier_index,
    get_next_tier,
    is_stat_capped,
    can_improve_stat,
    get_effective_training_gain,
    apply_facility_cap,
    calculate_training_gain,
    apply_training_with_caps,
    get_capped_stats,
    get_stats_near_cap,
    get_max_fighters,
    can_sign_fighter,
    get_roster_status,
    get_upgrade_cost,
    get_upgrade_requirements,
    can_upgrade,
    perform_upgrade,
    can_afford_upgrade,
    get_monthly_cost,
    get_maintenance_cost,
    get_training_efficiency,
    get_tier_display_name,
    get_tier_description,
    get_facility_description,
    format_cap_warning,
    format_upgrade_requirements,
)


# ============================================================================
# CONSTANT TESTS
# ============================================================================

class TestConstants:
    """Test constant definitions."""
    
    def test_facility_stat_caps_exists(self):
        """FACILITY_STAT_CAPS should be defined."""
        assert FACILITY_STAT_CAPS is not None
        assert isinstance(FACILITY_STAT_CAPS, dict)
    
    def test_facility_tiers_list(self):
        """FACILITY_TIERS should be a list of tier names."""
        assert FACILITY_TIERS == ["GARAGE", "LOCAL", "REGIONAL", "NATIONAL", "ELITE"]
    
    def test_has_five_tiers(self):
        """Should have exactly 5 tiers."""
        assert len(FACILITY_STAT_CAPS) == 5
        assert len(TIER_ORDER) == 5
    
    def test_tier_order_matches_caps(self):
        """All tiers in order should have caps defined."""
        for tier in TIER_ORDER:
            assert tier in FACILITY_STAT_CAPS
    
    def test_caps_increase_with_tier(self):
        """Higher tiers should have higher caps."""
        prev_cap = 0
        for tier in TIER_ORDER:
            cap = FACILITY_STAT_CAPS[tier]
            assert cap > prev_cap, f"{tier} cap should be higher than previous"
            prev_cap = cap
    
    def test_specific_cap_values(self):
        """Verify specific cap values."""
        assert FACILITY_STAT_CAPS["GARAGE"] == 65
        assert FACILITY_STAT_CAPS["LOCAL"] == 72
        assert FACILITY_STAT_CAPS["REGIONAL"] == 80
        assert FACILITY_STAT_CAPS["NATIONAL"] == 90
        assert FACILITY_STAT_CAPS["ELITE"] == 100
    
    def test_max_fighters_defined(self):
        """All tiers should have max fighters defined."""
        for tier in TIER_ORDER:
            assert tier in MAX_FIGHTERS
            assert MAX_FIGHTERS[tier] > 0
    
    def test_upgrade_costs_defined(self):
        """All tiers should have upgrade costs."""
        for tier in TIER_ORDER:
            assert tier in UPGRADE_COSTS
    
    def test_upgrade_costs_increase(self):
        """Upgrade costs should increase with tier."""
        prev_cost = -1
        for tier in TIER_ORDER:
            cost = UPGRADE_COSTS[tier]
            assert cost > prev_cost, f"{tier} upgrade cost should be higher"
            prev_cost = cost
    
    def test_maintenance_costs_defined(self):
        """All tiers should have maintenance costs."""
        for tier in TIER_ORDER:
            assert tier in MAINTENANCE_COSTS
    
    def test_monthly_costs_defined(self):
        """All tiers should have monthly costs."""
        for tier in TIER_ORDER:
            assert tier in MONTHLY_COSTS
    
    def test_training_efficiency_defined(self):
        """All tiers should have training efficiency."""
        for tier in TIER_ORDER:
            assert tier in TRAINING_EFFICIENCY
            assert TRAINING_EFFICIENCY[tier] >= 1.0
    
    def test_capped_stats_not_empty(self):
        """Should have stats that are capped."""
        assert len(CAPPED_STATS) > 0
    
    def test_uncapped_stats_not_empty(self):
        """Should have stats that are uncapped."""
        assert len(UNCAPPED_STATS) > 0
    
    def test_no_overlap_capped_uncapped(self):
        """Capped and uncapped stats should not overlap."""
        capped_set = set(s.lower() for s in CAPPED_STATS)
        uncapped_set = set(s.lower() for s in UNCAPPED_STATS)
        overlap = capped_set & uncapped_set
        assert len(overlap) == 0, f"Overlap found: {overlap}"


# ============================================================================
# CAMP STATS TESTS
# ============================================================================

class TestCampStats:
    """Test CampStats dataclass."""
    
    def test_default_values(self):
        """Should have default values of 0."""
        stats = CampStats()
        assert stats.money == 0
        assert stats.wins == 0
        assert stats.title_wins == 0
    
    def test_custom_values(self):
        """Should accept custom values."""
        stats = CampStats(money=50000, wins=10, title_wins=2)
        assert stats.money == 50000
        assert stats.wins == 10
        assert stats.title_wins == 2


# ============================================================================
# CORE FUNCTION TESTS
# ============================================================================

class TestGetStatCap:
    """Test get_stat_cap function."""
    
    def test_garage_cap(self):
        """GARAGE should have cap of 65."""
        assert get_stat_cap("GARAGE") == 65
    
    def test_elite_cap(self):
        """ELITE should have cap of 100."""
        assert get_stat_cap("ELITE") == 100
    
    def test_case_insensitive(self):
        """Should handle different cases."""
        assert get_stat_cap("garage") == 65
        assert get_stat_cap("Garage") == 65
        assert get_stat_cap("GARAGE") == 65
    
    def test_unknown_tier_defaults(self):
        """Unknown tier should default to 65."""
        assert get_stat_cap("UNKNOWN") == 65


class TestTierIndex:
    """Test tier index functions."""
    
    def test_garage_is_first(self):
        """GARAGE should be index 0."""
        assert get_tier_index("GARAGE") == 0
    
    def test_elite_is_last(self):
        """ELITE should be index 4."""
        assert get_tier_index("ELITE") == 4
    
    def test_regional_is_middle(self):
        """REGIONAL should be index 2."""
        assert get_tier_index("REGIONAL") == 2
    
    def test_unknown_tier_returns_zero(self):
        """Unknown tier should return 0."""
        assert get_tier_index("UNKNOWN") == 0


class TestNextTier:
    """Test get_next_tier function."""
    
    def test_garage_to_local(self):
        """GARAGE -> LOCAL."""
        assert get_next_tier("GARAGE") == "LOCAL"
    
    def test_local_to_regional(self):
        """LOCAL -> REGIONAL."""
        assert get_next_tier("LOCAL") == "REGIONAL"
    
    def test_regional_to_national(self):
        """REGIONAL -> NATIONAL."""
        assert get_next_tier("REGIONAL") == "NATIONAL"
    
    def test_national_to_elite(self):
        """NATIONAL -> ELITE."""
        assert get_next_tier("NATIONAL") == "ELITE"
    
    def test_elite_has_no_next(self):
        """ELITE should return None."""
        assert get_next_tier("ELITE") is None


class TestIsStatCapped:
    """Test is_stat_capped function."""
    
    def test_boxing_is_capped(self):
        """Boxing should be capped."""
        assert is_stat_capped("boxing") is True
    
    def test_wrestling_is_capped(self):
        """Wrestling should be capped."""
        assert is_stat_capped("wrestling") is True
    
    def test_chin_is_uncapped(self):
        """Chin should be uncapped."""
        assert is_stat_capped("chin") is False
    
    def test_heart_is_uncapped(self):
        """Heart should be uncapped."""
        assert is_stat_capped("heart") is False
    
    def test_case_insensitive(self):
        """Should be case insensitive."""
        assert is_stat_capped("Boxing") is True
        assert is_stat_capped("BOXING") is True


class TestCanImproveStat:
    """Test can_improve_stat function."""
    
    def test_below_cap_can_improve(self):
        """Stat below cap should be improvable."""
        assert can_improve_stat("boxing", 60, "GARAGE") is True
    
    def test_at_cap_cannot_improve(self):
        """Stat at cap should not be improvable."""
        assert can_improve_stat("boxing", 65, "GARAGE") is False
    
    def test_above_cap_cannot_improve(self):
        """Stat above cap should not be improvable."""
        assert can_improve_stat("boxing", 70, "GARAGE") is False
    
    def test_higher_tier_allows_improvement(self):
        """Higher tier should allow improvement past lower cap."""
        assert can_improve_stat("boxing", 70, "REGIONAL") is True
    
    def test_uncapped_stat_always_improvable(self):
        """Uncapped stats should always be improvable up to 100."""
        assert can_improve_stat("chin", 65, "GARAGE") is True
        assert can_improve_stat("chin", 90, "GARAGE") is True
        assert can_improve_stat("chin", 100, "GARAGE") is False


# ============================================================================
# TRAINING GAIN TESTS
# ============================================================================

class TestEffectiveTrainingGain:
    """Test get_effective_training_gain function."""
    
    def test_normal_gain_below_cap(self):
        """Full gain should apply when well below cap."""
        gain = get_effective_training_gain(
            current_value=50,
            raw_gain=5,
            camp_tier="GARAGE"
        )
        assert gain == 5
    
    def test_gain_capped_at_limit(self):
        """Gain should be limited when approaching cap."""
        gain = get_effective_training_gain(
            current_value=63,
            raw_gain=5,
            camp_tier="GARAGE"  # Cap is 65
        )
        assert gain == 2  # 65 - 63 = 2
    
    def test_no_gain_at_cap(self):
        """No gain when already at cap."""
        gain = get_effective_training_gain(
            current_value=65,
            raw_gain=5,
            camp_tier="GARAGE"
        )
        assert gain == 0
    
    def test_no_gain_above_cap(self):
        """No gain when already above cap."""
        gain = get_effective_training_gain(
            current_value=70,
            raw_gain=5,
            camp_tier="GARAGE"
        )
        assert gain == 0
    
    def test_higher_tier_allows_more_gain(self):
        """Higher tier allows gains past lower caps."""
        gain = get_effective_training_gain(
            current_value=70,
            raw_gain=5,
            camp_tier="REGIONAL"  # Cap is 80
        )
        assert gain == 5
    
    def test_zero_raw_gain(self):
        """Zero raw gain should return zero."""
        gain = get_effective_training_gain(
            current_value=50,
            raw_gain=0,
            camp_tier="GARAGE"
        )
        assert gain == 0
    
    def test_negative_raw_gain(self):
        """Negative raw gain should return zero."""
        gain = get_effective_training_gain(
            current_value=50,
            raw_gain=-5,
            camp_tier="GARAGE"
        )
        assert gain == 0
    
    def test_uncapped_stat_full_gain(self):
        """Uncapped stats should get full gain up to 100."""
        gain = get_effective_training_gain(
            current_value=90,
            raw_gain=5,
            camp_tier="GARAGE",
            stat_name="chin"
        )
        assert gain == 5


class TestApplyFacilityCap:
    """Test apply_facility_cap function."""
    
    def test_returns_tuple(self):
        """Should return (new_value, actual_gain, was_capped)."""
        result = apply_facility_cap(50, 5, "GARAGE")
        assert isinstance(result, tuple)
        assert len(result) == 3
    
    def test_normal_gain(self):
        """Full gain when below cap."""
        new_val, gain, capped = apply_facility_cap(50, 5, "GARAGE")
        assert new_val == 55
        assert gain == 5
        assert capped is False
    
    def test_capped_gain(self):
        """Partial gain when approaching cap."""
        new_val, gain, capped = apply_facility_cap(63, 5, "GARAGE")
        assert new_val == 65
        assert gain == 2
        assert capped is True
    
    def test_no_gain_at_cap(self):
        """No gain when at cap."""
        new_val, gain, capped = apply_facility_cap(65, 5, "GARAGE")
        assert new_val == 65
        assert gain == 0
        assert capped is True


class TestCalculateTrainingGain:
    """Test calculate_training_gain function."""
    
    def test_applies_efficiency(self):
        """Should apply efficiency multiplier."""
        # ELITE has 1.25 efficiency
        new_val, gain, capped = calculate_training_gain(4, "ELITE", 50)
        # 4 * 1.25 = 5
        assert gain == 5
        assert new_val == 55
    
    def test_respects_cap(self):
        """Should still respect caps after efficiency."""
        new_val, gain, capped = calculate_training_gain(10, "GARAGE", 60)
        # 10 * 1.0 = 10, but capped at 65
        assert new_val == 65
        assert capped is True


class TestApplyTrainingWithCaps:
    """Test apply_training_with_caps function."""
    
    def test_applies_gains_correctly(self):
        """Should apply gains and return new stats."""
        stats = {"boxing": 50, "wrestling": 60}
        gains = {"boxing": 3, "wrestling": 2}
        
        new_stats, actual = apply_training_with_caps(stats, gains, "REGIONAL")
        
        assert new_stats["boxing"] == 53
        assert new_stats["wrestling"] == 62
        assert actual["boxing"] == 3
        assert actual["wrestling"] == 2
    
    def test_respects_caps(self):
        """Should respect facility caps."""
        stats = {"boxing": 63, "wrestling": 64}
        gains = {"boxing": 5, "wrestling": 5}
        
        new_stats, actual = apply_training_with_caps(stats, gains, "GARAGE")  # Cap 65
        
        assert new_stats["boxing"] == 65
        assert new_stats["wrestling"] == 65
        assert actual["boxing"] == 2
        assert actual["wrestling"] == 1
    
    def test_original_not_modified(self):
        """Original stats dict should not be modified."""
        stats = {"boxing": 50}
        gains = {"boxing": 5}
        
        new_stats, _ = apply_training_with_caps(stats, gains, "GARAGE")
        
        assert stats["boxing"] == 50  # Original unchanged
        assert new_stats["boxing"] == 55


# ============================================================================
# CAP STATUS TESTS
# ============================================================================

class TestGetCappedStats:
    """Test get_capped_stats function."""
    
    def test_returns_capped_stats(self):
        """Should return stats at or above cap."""
        stats = {
            "boxing": 65,      # At cap
            "wrestling": 60,  # Below cap
            "bjj": 70,        # Above cap
        }
        
        capped = get_capped_stats(stats, "GARAGE")  # Cap is 65
        
        assert "boxing" in capped
        assert "bjj" in capped
        assert "wrestling" not in capped
    
    def test_empty_when_none_capped(self):
        """Should return empty list when nothing at cap."""
        stats = {"boxing": 50, "wrestling": 55}
        capped = get_capped_stats(stats, "ELITE")  # Cap is 100
        assert len(capped) == 0
    
    def test_ignores_uncapped_stats(self):
        """Should ignore uncapped stats even if high."""
        stats = {"chin": 90}  # Uncapped stat
        capped = get_capped_stats(stats, "GARAGE")
        assert len(capped) == 0


class TestGetStatsNearCap:
    """Test get_stats_near_cap function."""
    
    def test_finds_stats_near_cap(self):
        """Should find stats within threshold of cap."""
        stats = {
            "boxing": 63,     # 2 from cap (65), within threshold 3
            "wrestling": 60,  # 5 from cap, outside threshold
            "bjj": 64,        # 1 from cap, within threshold
        }
        
        near = get_stats_near_cap(stats, "GARAGE", threshold=3)
        
        stat_names = [s[0] for s in near]
        assert "boxing" in stat_names
        assert "bjj" in stat_names
        assert "wrestling" not in stat_names
    
    def test_excludes_already_capped(self):
        """Should exclude stats already at cap."""
        stats = {"boxing": 65}  # Already at cap
        near = get_stats_near_cap(stats, "GARAGE")
        assert len(near) == 0
    
    def test_returns_correct_tuple_format(self):
        """Should return (name, current, cap) tuples."""
        stats = {"boxing": 63}
        near = get_stats_near_cap(stats, "GARAGE")
        
        assert len(near) == 1
        name, current, cap = near[0]
        assert name == "boxing"
        assert current == 63
        assert cap == 65


# ============================================================================
# ROSTER TESTS
# ============================================================================

class TestRosterFunctions:
    """Test roster-related functions."""
    
    def test_get_max_fighters(self):
        """Should return correct max fighters per tier."""
        assert get_max_fighters("GARAGE") == 3
        assert get_max_fighters("ELITE") == 20
    
    def test_can_sign_fighter_yes(self):
        """Should allow signing when under limit."""
        can_sign, reason = can_sign_fighter("GARAGE", 2)
        assert can_sign is True
        assert reason == ""
    
    def test_can_sign_fighter_no(self):
        """Should prevent signing when at limit."""
        can_sign, reason = can_sign_fighter("GARAGE", 3)
        assert can_sign is False
        assert "full" in reason.lower()
    
    def test_get_roster_status(self):
        """Should format roster status correctly."""
        status = get_roster_status("GARAGE", 2)
        assert status == "2/3"


# ============================================================================
# UPGRADE TESTS
# ============================================================================

class TestUpgradeFunctions:
    """Test upgrade-related functions."""
    
    def test_get_upgrade_cost_garage(self):
        """GARAGE to LOCAL should cost $25k."""
        cost = get_upgrade_cost("GARAGE")
        assert cost == 25_000
    
    def test_get_upgrade_cost_national(self):
        """NATIONAL to ELITE should cost $2M."""
        cost = get_upgrade_cost("NATIONAL")
        assert cost == 2_000_000
    
    def test_get_upgrade_cost_elite(self):
        """ELITE has no upgrade, should return None."""
        cost = get_upgrade_cost("ELITE")
        assert cost is None
    
    def test_get_upgrade_requirements(self):
        """Should return requirements dict."""
        reqs = get_upgrade_requirements("GARAGE")
        assert "money" in reqs
        assert "wins" in reqs
    
    def test_get_upgrade_requirements_elite(self):
        """ELITE has no upgrade, should return None."""
        reqs = get_upgrade_requirements("ELITE")
        assert reqs is None
    
    def test_can_upgrade_success(self):
        """Should succeed when all requirements met."""
        stats = CampStats(money=30000, wins=5)
        can_up, missing = can_upgrade("GARAGE", stats)
        assert can_up is True
        assert len(missing) == 0
    
    def test_can_upgrade_fail_money(self):
        """Should fail when money insufficient."""
        stats = CampStats(money=10000, wins=5)
        can_up, missing = can_upgrade("GARAGE", stats)
        assert can_up is False
        assert any("$25,000" in m for m in missing)
    
    def test_can_upgrade_fail_wins(self):
        """Should fail when wins insufficient."""
        stats = CampStats(money=30000, wins=1)
        can_up, missing = can_upgrade("GARAGE", stats)
        assert can_up is False
        assert any("wins" in m.lower() for m in missing)
    
    def test_perform_upgrade_success(self):
        """Should return success when requirements met."""
        stats = CampStats(money=30000, wins=5)
        success, msg, cost = perform_upgrade("GARAGE", stats)
        assert success is True
        assert "Local Gym" in msg
        assert cost == 25000
    
    def test_perform_upgrade_fail(self):
        """Should return failure when requirements not met."""
        stats = CampStats(money=1000, wins=0)
        success, msg, cost = perform_upgrade("GARAGE", stats)
        assert success is False
        assert cost == 0
    
    def test_get_monthly_cost(self):
        """Should return correct monthly costs."""
        assert get_monthly_cost("GARAGE") == 2000
        assert get_monthly_cost("ELITE") == 200000
    
    def test_get_maintenance_cost(self):
        """Should return correct maintenance costs."""
        assert get_maintenance_cost("GARAGE") == 500
        assert get_maintenance_cost("ELITE") == 50_000
    
    def test_get_training_efficiency(self):
        """Should return correct efficiency multipliers."""
        assert get_training_efficiency("GARAGE") == 1.0
        assert get_training_efficiency("ELITE") == 1.25
    
    def test_can_afford_upgrade_true(self):
        """Should return True when funds sufficient."""
        assert can_afford_upgrade("GARAGE", 30_000) is True
    
    def test_can_afford_upgrade_false(self):
        """Should return False when funds insufficient."""
        assert can_afford_upgrade("GARAGE", 20_000) is False
    
    def test_can_afford_upgrade_elite(self):
        """ELITE cannot be upgraded."""
        assert can_afford_upgrade("ELITE", 10_000_000) is False


# ============================================================================
# DISPLAY HELPER TESTS
# ============================================================================

class TestDisplayHelpers:
    """Test display helper functions."""
    
    def test_get_tier_display_name(self):
        """Should return friendly tier names."""
        assert get_tier_display_name("GARAGE") == "Garage Gym"
        assert get_tier_display_name("ELITE") == "Elite Complex"
    
    def test_get_tier_description(self):
        """Should return tier descriptions."""
        desc = get_tier_description("GARAGE")
        assert len(desc) > 0
        assert "Basic" in desc
    
    def test_get_facility_description(self):
        """Should be alias for get_tier_description."""
        assert get_facility_description("GARAGE") == get_tier_description("GARAGE")
    
    def test_format_cap_warning_at_cap(self):
        """Should format message for stat at cap."""
        msg = format_cap_warning("boxing", 65, 65)
        assert "MAXED" in msg
        assert "65" in msg
    
    def test_format_cap_warning_near_cap(self):
        """Should format message for stat near cap."""
        msg = format_cap_warning("boxing", 63, 65)
        assert "2 points" in msg
        assert "65" in msg
    
    def test_format_upgrade_requirements(self):
        """Should format requirements as string."""
        formatted = format_upgrade_requirements("GARAGE")
        assert "$25,000" in formatted
        assert "wins" in formatted.lower()
    
    def test_format_upgrade_requirements_elite(self):
        """ELITE should return max tier message."""
        formatted = format_upgrade_requirements("ELITE")
        assert "Maximum" in formatted


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFacilitiesIntegration:
    """Integration tests for complete workflows."""
    
    def test_training_progression_across_tiers(self):
        """Test that training caps work across tier progression."""
        stats = {"boxing": 50}
        
        # Train at GARAGE (cap 65)
        for _ in range(10):
            gains = {"boxing": 3}
            stats, _ = apply_training_with_caps(stats, gains, "GARAGE")
        
        assert stats["boxing"] == 65  # Stopped at GARAGE cap
        
        # Upgrade to LOCAL (cap 72) and train more
        for _ in range(10):
            gains = {"boxing": 3}
            stats, _ = apply_training_with_caps(stats, gains, "LOCAL")
        
        assert stats["boxing"] == 72  # Stopped at LOCAL cap
        
        # Upgrade to ELITE (cap 100) and train to max
        for _ in range(20):
            gains = {"boxing": 3}
            stats, _ = apply_training_with_caps(stats, gains, "ELITE")
        
        assert stats["boxing"] == 100  # Can reach maximum
    
    def test_upgrade_path_requirements(self):
        """Test that upgrade requirements increase appropriately."""
        # Check each tier's requirements increase
        garage_reqs = get_upgrade_requirements("GARAGE")
        local_reqs = get_upgrade_requirements("LOCAL")
        regional_reqs = get_upgrade_requirements("REGIONAL")
        
        assert local_reqs["money"] > garage_reqs["money"]
        assert regional_reqs["money"] > local_reqs["money"]
        
        assert local_reqs["wins"] > garage_reqs["wins"]
        assert regional_reqs["wins"] > local_reqs["wins"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
