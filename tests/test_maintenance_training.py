# tests/test_maintenance_training.py
# Tests for Coach Maintenance Training & Stat Decay System
# Lines: ~450

"""
Tests for the Maintenance Training system.

Covers:
- StatActivity tracking
- Coach boost calculations
- Stat decay mechanics
- MaintenanceTrainingSystem
- Integration scenarios
"""

import pytest
import random

from systems.maintenance_training import (
    # Constants
    DECAY_THRESHOLD_START,
    DECAY_THRESHOLD_MODERATE,
    DECAY_THRESHOLD_HIGH,
    DECAY_THRESHOLD_SEVERE,
    MIN_STAT_VALUE,
    MAX_STAT_VALUE,
    ALL_STATS,
    PHYSICAL_STATS,
    MENTAL_STATS,
    COACH_BOOST_BASE_CHANCE,
    COACH_BOOST_AMOUNT,
    
    # Data classes
    StatActivity,
    MaintenanceBoost,
    StatDecay,
    DecayWarning,
    
    # System
    MaintenanceTrainingSystem,
    
    # Functions
    check_stat_decay,
    get_decay_tier,
    get_decay_multiplier,
    check_coach_specialty_match,
    select_boost_stat,
    calculate_boost_amount,
    format_maintenance_summary,
    get_stat_category,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def system():
    """Fresh maintenance training system."""
    return MaintenanceTrainingSystem()


@pytest.fixture
def sample_fighter():
    """Sample fighter data."""
    return {
        "id": "fighter_001",
        "name": "John Smith",
        "age": 28,
        "attributes": {
            "strength": 70,
            "speed": 68,
            "cardio": 72,
            "chin": 65,
            "recovery": 70,
            "boxing": 75,
            "kicks": 70,
            "clinch_striking": 65,
            "striking_defense": 68,
            "wrestling": 60,
            "bjj": 55,
            "takedown_defense": 62,
            "top_control": 58,
            "submissions": 50,
            "heart": 72,
            "fight_iq": 68,
            "composure": 70,
        }
    }


@pytest.fixture
def sample_coach():
    """Sample coach data."""
    return {
        "id": "coach_001",
        "name": "Mike Johnson",
        "quality": 4,
        "specialty": "Striking",
        "traits": ["Motivator"],
    }


@pytest.fixture
def elite_coach():
    """Elite 5-star coach."""
    return {
        "id": "coach_002",
        "name": "Elite Coach",
        "quality": 5,
        "specialty": "Wrestling",
        "traits": ["Diamond Polisher", "Technical Genius"],
    }


@pytest.fixture
def low_quality_coach():
    """Low quality 1-star coach."""
    return {
        "id": "coach_003",
        "name": "Budget Coach",
        "quality": 1,
        "specialty": "Conditioning",
        "traits": [],
    }


# ============================================================================
# STAT ACTIVITY TESTS
# ============================================================================

class TestStatActivity:
    """Tests for StatActivity tracking."""
    
    def test_creation(self):
        """Should create empty activity tracker."""
        activity = StatActivity()
        assert activity.last_activity_week == {}
    
    def test_record_activity(self):
        """Should record activity for a stat."""
        activity = StatActivity()
        activity.record_activity("boxing", 100)
        assert activity.last_activity_week["boxing"] == 100
    
    def test_record_multiple(self):
        """Should record activity for multiple stats."""
        activity = StatActivity()
        activity.record_multiple(["boxing", "kicks", "cardio"], 50)
        
        assert activity.last_activity_week["boxing"] == 50
        assert activity.last_activity_week["kicks"] == 50
        assert activity.last_activity_week["cardio"] == 50
    
    def test_weeks_since_activity(self):
        """Should calculate weeks since last activity."""
        activity = StatActivity()
        activity.record_activity("boxing", 90)
        
        assert activity.weeks_since_activity("boxing", 100) == 10
        assert activity.weeks_since_activity("boxing", 90) == 0
    
    def test_weeks_since_never_trained(self):
        """Should return high value for never-trained stats."""
        activity = StatActivity()
        assert activity.weeks_since_activity("boxing", 100) == 999
    
    def test_get_idle_stats(self):
        """Should return stats idle longer than threshold."""
        activity = StatActivity()
        activity.record_activity("boxing", 80)  # 20 weeks ago
        activity.record_activity("wrestling", 95)  # 5 weeks ago
        
        idle = activity.get_idle_stats(100, threshold=15)
        assert "boxing" in idle
        assert "wrestling" not in idle
    
    def test_serialization(self):
        """Should serialize and deserialize."""
        activity = StatActivity()
        activity.record_activity("boxing", 50)
        activity.record_activity("wrestling", 60)
        
        data = activity.to_dict()
        restored = StatActivity.from_dict(data)
        
        assert restored.last_activity_week["boxing"] == 50
        assert restored.last_activity_week["wrestling"] == 60


# ============================================================================
# DECAY TIER TESTS
# ============================================================================

class TestDecayTier:
    """Tests for decay tier calculation."""
    
    def test_no_decay_below_threshold(self):
        """Should return None below start threshold."""
        assert get_decay_tier(10) is None
        assert get_decay_tier(DECAY_THRESHOLD_START - 1) is None
    
    def test_start_tier(self):
        """Should return 'start' tier at threshold."""
        assert get_decay_tier(DECAY_THRESHOLD_START) == "start"
        assert get_decay_tier(DECAY_THRESHOLD_MODERATE - 1) == "start"
    
    def test_moderate_tier(self):
        """Should return 'moderate' tier."""
        assert get_decay_tier(DECAY_THRESHOLD_MODERATE) == "moderate"
    
    def test_high_tier(self):
        """Should return 'high' tier."""
        assert get_decay_tier(DECAY_THRESHOLD_HIGH) == "high"
    
    def test_severe_tier(self):
        """Should return 'severe' tier."""
        assert get_decay_tier(DECAY_THRESHOLD_SEVERE) == "severe"
        assert get_decay_tier(100) == "severe"  # Very high idle time


# ============================================================================
# DECAY MULTIPLIER TESTS
# ============================================================================

class TestDecayMultiplier:
    """Tests for decay rate multipliers."""
    
    def test_physical_stats_decay_faster(self):
        """Physical stats should have higher decay multiplier."""
        for stat in PHYSICAL_STATS:
            assert get_decay_multiplier(stat) > 1.0
    
    def test_mental_stats_decay_slower(self):
        """Mental stats should have lower decay multiplier."""
        for stat in MENTAL_STATS:
            assert get_decay_multiplier(stat) < 1.0
    
    def test_other_stats_normal_decay(self):
        """Other stats should have 1.0 multiplier."""
        assert get_decay_multiplier("boxing") == 1.0
        assert get_decay_multiplier("wrestling") == 1.0


# ============================================================================
# COACH SPECIALTY MATCH TESTS
# ============================================================================

class TestCoachSpecialtyMatch:
    """Tests for coach specialty matching."""
    
    def test_striking_coach_matches_striking(self):
        """Striking coach should match striking stats."""
        assert check_coach_specialty_match("Striking", "boxing") is True
        assert check_coach_specialty_match("Striking", "kicks") is True
        assert check_coach_specialty_match("Striking", "wrestling") is False
    
    def test_wrestling_coach_matches_grappling(self):
        """Wrestling coach should match grappling stats."""
        assert check_coach_specialty_match("Wrestling", "wrestling") is True
        assert check_coach_specialty_match("Wrestling", "bjj") is True
        assert check_coach_specialty_match("Wrestling", "boxing") is False
    
    def test_unknown_specialty(self):
        """Unknown specialty should not match anything."""
        assert check_coach_specialty_match("Unknown", "boxing") is False


# ============================================================================
# STAT DECAY TESTS
# ============================================================================

class TestStatDecay:
    """Tests for stat decay mechanics."""
    
    def test_no_decay_below_threshold(self):
        """Should not decay below threshold."""
        should_decay, amount = check_stat_decay("boxing", 70, 10)
        assert should_decay is False
        assert amount == 0
    
    def test_no_decay_at_minimum(self):
        """Should not decay below minimum stat value."""
        should_decay, amount = check_stat_decay("boxing", MIN_STAT_VALUE, 50)
        assert should_decay is False
        assert amount == 0
    
    def test_decay_at_threshold(self):
        """Should have chance to decay at threshold."""
        random.seed(42)
        
        decay_count = 0
        for _ in range(100):
            should_decay, amount = check_stat_decay("boxing", 70, DECAY_THRESHOLD_START)
            if should_decay:
                decay_count += 1
                assert amount >= 1
        
        # Should decay some but not all (8% base chance)
        assert 2 <= decay_count <= 25
    
    def test_higher_decay_at_severe(self):
        """Should have higher decay chance at severe tier."""
        random.seed(42)
        
        decay_count = 0
        for _ in range(100):
            should_decay, _ = check_stat_decay("boxing", 70, DECAY_THRESHOLD_SEVERE)
            if should_decay:
                decay_count += 1
        
        # Should decay more often at severe (40% base)
        assert decay_count >= 20


# ============================================================================
# BOOST CALCULATION TESTS
# ============================================================================

class TestBoostCalculation:
    """Tests for coach boost calculations."""
    
    def test_boost_amount_by_quality(self):
        """Higher quality coaches should give bigger boosts."""
        random.seed(42)
        
        q1_boosts = [calculate_boost_amount(1, False, 28, 60) for _ in range(20)]
        q5_boosts = [calculate_boost_amount(5, False, 28, 60) for _ in range(20)]
        
        assert sum(q5_boosts) > sum(q1_boosts)
    
    def test_specialty_match_bonus(self):
        """Specialty match should increase boost."""
        random.seed(42)
        
        no_match = [calculate_boost_amount(3, False, 28, 60) for _ in range(20)]
        with_match = [calculate_boost_amount(3, True, 28, 60) for _ in range(20)]
        
        assert sum(with_match) > sum(no_match)
    
    def test_diminishing_returns_at_high_stat(self):
        """Boosts should be smaller at high stat values."""
        random.seed(42)
        
        low_stat_boosts = [calculate_boost_amount(4, True, 28, 50) for _ in range(20)]
        high_stat_boosts = [calculate_boost_amount(4, True, 28, 90) for _ in range(20)]
        
        # High stat boosts should average lower
        assert sum(high_stat_boosts) <= sum(low_stat_boosts)
    
    def test_boost_respects_max_stat(self):
        """Boost should not exceed max stat value."""
        boost = calculate_boost_amount(5, True, 22, 98)
        assert 98 + boost <= MAX_STAT_VALUE


# ============================================================================
# MAINTENANCE TRAINING SYSTEM TESTS
# ============================================================================

class TestMaintenanceTrainingSystem:
    """Tests for the main system."""
    
    def test_creation(self, system):
        """Should create system."""
        assert system is not None
        assert system._fighter_activity == {}
    
    def test_initialize_fighter(self, system):
        """Should initialize fighter activity."""
        system.initialize_fighter("fighter_001", 100)
        
        activity = system.get_fighter_activity("fighter_001")
        for stat in ALL_STATS:
            assert stat in activity.last_activity_week
    
    def test_record_training_camp(self, system):
        """Should record training camp activity."""
        system.initialize_fighter("fighter_001", 50)
        system.record_training_camp_activity(
            "fighter_001",
            ["boxing", "kicks", "cardio"],
            100
        )
        
        activity = system.get_fighter_activity("fighter_001")
        assert activity.last_activity_week["boxing"] == 100
        assert activity.last_activity_week["kicks"] == 100
        assert activity.last_activity_week["cardio"] == 100
    
    def test_process_week_with_coaches(self, system, sample_fighter, sample_coach):
        """Should process weekly maintenance with coach boosts."""
        random.seed(42)
        
        fighters = [sample_fighter]
        camp_assignments = {"fighter_001": "camp_001"}
        camp_coaches = {"camp_001": [sample_coach]}
        
        # Run many weeks to get some boosts
        all_boosts = []
        for week in range(100, 200):
            boosts, decays, warnings = system.process_week(
                fighters, [], camp_assignments, camp_coaches, week
            )
            all_boosts.extend(boosts)
        
        # Should have gotten some boosts
        assert len(all_boosts) > 0
        
        # Check boost structure
        if all_boosts:
            boost = all_boosts[0]
            assert boost.fighter_id == "fighter_001"
            assert boost.coach_id == "coach_001"
            assert boost.stat in ALL_STATS
            assert boost.amount >= 1
    
    def test_no_boost_for_fighters_in_camp(self, system, sample_fighter, sample_coach):
        """Fighters in active camps should not get maintenance boosts."""
        random.seed(42)
        
        fighters = [sample_fighter]
        camp_assignments = {"fighter_001": "camp_001"}
        camp_coaches = {"camp_001": [sample_coach]}
        fighters_in_camp = {"fighter_001"}
        
        boosts, decays, warnings = system.process_week(
            fighters, [], camp_assignments, camp_coaches, 100,
            fighters_in_camp=fighters_in_camp
        )
        
        # Should not have boosts (fighter is in camp)
        assert len(boosts) == 0
    
    def test_decay_for_idle_fighters(self, system, sample_fighter):
        """Idle fighters should experience stat decay."""
        random.seed(42)
        
        # Initialize fighter way in the past
        system.initialize_fighter("fighter_001", 10)
        
        fighters = [sample_fighter]
        camp_assignments = {}  # No camp
        camp_coaches = {}
        
        # Process at week 100 (90 weeks of idleness)
        boosts, decays, warnings = system.process_week(
            fighters, [], camp_assignments, camp_coaches, 100
        )
        
        # Should have some decays after 90 weeks idle
        assert len(decays) > 0
    
    def test_decay_risk_assessment(self, system):
        """Should assess decay risk for fighter."""
        system.initialize_fighter("fighter_001", 80)
        
        activity = system.get_fighter_activity("fighter_001")
        activity.record_activity("boxing", 96)  # 4 weeks ago - safely OK
        activity.record_activity("wrestling", 70)  # 30 weeks ago - decaying
        
        risk = system.get_fighter_decay_risk("fighter_001", 100)
        
        # 4 weeks idle = OK (threshold is 16, caution starts at 8)
        assert risk["boxing"]["risk_level"] == "OK"
        # 30 weeks idle = DECAYING (past threshold of 16)
        assert risk["wrestling"]["risk_level"] == "DECAYING"
    
    def test_serialization(self, system, sample_fighter, sample_coach):
        """Should serialize and restore state."""
        random.seed(42)
        
        system.initialize_fighter("fighter_001", 100)
        
        fighters = [sample_fighter]
        camp_assignments = {"fighter_001": "camp_001"}
        camp_coaches = {"camp_001": [sample_coach]}
        
        # Generate some activity
        for week in range(100, 150):
            system.process_week(fighters, [], camp_assignments, camp_coaches, week)
        
        # Serialize
        data = system.to_dict()
        
        # Restore
        restored = MaintenanceTrainingSystem.from_dict(data)
        
        # Verify
        assert "fighter_001" in restored._fighter_activity
        assert len(restored._boost_history) == len(system._boost_history)


# ============================================================================
# DATA CLASS TESTS
# ============================================================================

class TestDataClasses:
    """Tests for data classes."""
    
    def test_maintenance_boost_headline(self):
        """Should generate appropriate headlines."""
        boost = MaintenanceBoost(
            fighter_id="f1",
            fighter_name="John Smith",
            coach_id="c1",
            coach_name="Coach Mike",
            stat="boxing",
            amount=3,
            week=100,
            specialty_match=True
        )
        
        headline = boost.headline
        assert "John Smith" in headline
        assert "Coach Mike" in headline
    
    def test_stat_decay_headline(self):
        """Should generate appropriate headlines."""
        decay = StatDecay(
            fighter_id="f1",
            fighter_name="John Smith",
            stat="cardio",
            amount=2,
            weeks_idle=25,
            week=100
        )
        
        headline = decay.headline
        assert "John Smith" in headline
        assert "cardio" in headline
    
    def test_decay_warning_message(self):
        """Should generate appropriate warning."""
        warning = DecayWarning(
            fighter_id="f1",
            fighter_name="John Smith",
            stat="wrestling",
            weeks_idle=14,
            weeks_until_decay=2
        )
        
        message = warning.message
        assert "John Smith" in message
        assert "wrestling" in message


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for realistic scenarios."""
    
    def test_elite_coach_vs_budget_coach(self, system, sample_fighter, elite_coach, low_quality_coach):
        """Elite coaches should produce more/better boosts than budget coaches."""
        random.seed(42)
        
        # Test with elite coach
        elite_boosts = []
        system_elite = MaintenanceTrainingSystem()
        for week in range(100, 200):
            boosts, _, _ = system_elite.process_week(
                [sample_fighter], [],
                {"fighter_001": "camp_001"},
                {"camp_001": [elite_coach]},
                week
            )
            elite_boosts.extend(boosts)
        
        # Test with budget coach
        budget_boosts = []
        system_budget = MaintenanceTrainingSystem()
        for week in range(100, 200):
            boosts, _, _ = system_budget.process_week(
                [sample_fighter], [],
                {"fighter_001": "camp_001"},
                {"camp_001": [low_quality_coach]},
                week
            )
            budget_boosts.extend(boosts)
        
        # Elite should have more boosts
        assert len(elite_boosts) > len(budget_boosts)
        
        # Elite should have higher total gains
        elite_total = sum(b.amount for b in elite_boosts)
        budget_total = sum(b.amount for b in budget_boosts)
        assert elite_total > budget_total
    
    def test_long_term_no_coaching(self, system, sample_fighter):
        """Fighter without coaches should decay over time."""
        random.seed(42)
        
        system.initialize_fighter("fighter_001", 1)
        
        total_decay = 0
        for week in range(1, 100):
            boosts, decays, warnings = system.process_week(
                [sample_fighter], [],
                {},  # No camp
                {},  # No coaches
                week
            )
            total_decay += sum(d.amount for d in decays)
        
        # Should have significant decay after ~100 weeks without coaching
        assert total_decay > 0
    
    def test_training_camp_resets_decay_timer(self, system, sample_fighter):
        """Recording training camp activity should reset decay timer."""
        system.initialize_fighter("fighter_001", 1)
        
        # Check initial activity
        activity = system.get_fighter_activity("fighter_001")
        initial_week = activity.last_activity_week.get("boxing", 0)
        
        # Record training camp at week 50
        system.record_training_camp_activity("fighter_001", ["boxing", "kicks"], 50)
        
        # Check updated activity
        assert activity.last_activity_week["boxing"] == 50
        assert activity.last_activity_week["kicks"] == 50
        
        # Check decay risk at week 54 (only 4 weeks since camp - safely OK)
        risk = system.get_fighter_decay_risk("fighter_001", 54)
        # 4 weeks idle = OK (threshold 16, caution starts at 8 weeks before)
        assert risk["boxing"]["risk_level"] == "OK"
        assert risk["kicks"]["risk_level"] == "OK"


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_get_stat_category(self):
        """Should return correct category for stats."""
        assert get_stat_category("strength") == "Physical"
        assert get_stat_category("boxing") == "Striking"
        assert get_stat_category("wrestling") == "Grappling"
        assert get_stat_category("heart") == "Mental"
        assert get_stat_category("unknown") == "Unknown"
    
    def test_format_maintenance_summary(self):
        """Should format summary for display."""
        boosts = [
            MaintenanceBoost("f1", "John", "c1", "Coach", "boxing", 2, 100, True)
        ]
        decays = [
            StatDecay("f1", "John", "cardio", 1, 20, 100)
        ]
        warnings = [
            DecayWarning("f1", "John", "wrestling", 14, 2)
        ]
        
        lines = format_maintenance_summary(boosts, decays, warnings, {"f1"})
        
        assert len(lines) > 0
        text = "\n".join(lines)
        assert "John" in text
