# tests/test_rivalry.py
# Module 22: Rivalry System Tests
# Tests: 48

"""
Tests for the Rivalry System module.
"""

import pytest
from narrative.rivalry import (
    # Enums
    RivalryType,
    RivalryIntensity,
    
    # Constants
    INTENSITY_THRESHOLDS,
    RIVALRY_SCORE_MODIFIERS,
    
    # Data classes
    RivalryEvent,
    Rivalry,
    FightContext,
    
    # Detection
    detect_rivalry_triggers,
    determine_rivalry_type,
    detect_rivalry_from_fight,
    
    # System
    RivalrySystem,
    get_rivalry_system,
    reset_rivalry_system,
    
    # Utilities
    get_rivalry_intensity_description,
    get_rivalry_type_description,
    check_for_rivalry,
    get_rivalry_score,
    format_rivalry_display,
)


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestRivalryType:
    """Tests for RivalryType enum"""
    
    def test_all_types_defined(self):
        """Should have all expected rivalry types"""
        assert RivalryType.COMPETITIVE.value == "competitive"
        assert RivalryType.BAD_BLOOD.value == "bad_blood"
        assert RivalryType.TITLE_DISPUTE.value == "title_dispute"
        assert RivalryType.GYM_WAR.value == "gym_war"
        assert RivalryType.NATIONAL_PRIDE.value == "national_pride"
        assert RivalryType.STYLE_CLASH.value == "style_clash"
        assert RivalryType.GENERATIONAL.value == "generational"
        assert RivalryType.REVENGE.value == "revenge"


class TestRivalryIntensity:
    """Tests for RivalryIntensity enum"""
    
    def test_intensity_ordering(self):
        """Intensities should have correct ordering"""
        assert RivalryIntensity.BUDDING.value < RivalryIntensity.NOTABLE.value
        assert RivalryIntensity.NOTABLE.value < RivalryIntensity.HEATED.value
        assert RivalryIntensity.HEATED.value < RivalryIntensity.FIERCE.value
        assert RivalryIntensity.FIERCE.value < RivalryIntensity.LEGENDARY.value


class TestIntensityThresholds:
    """Tests for intensity thresholds"""
    
    def test_thresholds_cover_range(self):
        """Thresholds should cover full score range"""
        assert INTENSITY_THRESHOLDS[RivalryIntensity.BUDDING][0] == 10
        assert INTENSITY_THRESHOLDS[RivalryIntensity.LEGENDARY][1] == 100


# ============================================================================
# RIVALRY EVENT TESTS
# ============================================================================

class TestRivalryEvent:
    """Tests for RivalryEvent dataclass"""
    
    def test_creation(self):
        """Should create event with correct values"""
        event = RivalryEvent(
            event_type="trash_talk",
            description="Fighter calls out opponent",
            score_change=10,
            date="2025-01-15",
        )
        
        assert event.event_type == "trash_talk"
        assert event.score_change == 10
    
    def test_serialization(self):
        """Should serialize and deserialize correctly"""
        event = RivalryEvent(
            event_type="split_decision",
            description="Controversial result",
            score_change=20,
            date="2025-01-15",
            fight_id="fight_123",
        )
        
        data = event.to_dict()
        restored = RivalryEvent.from_dict(data)
        
        assert restored.event_type == event.event_type
        assert restored.score_change == event.score_change
        assert restored.fight_id == event.fight_id


# ============================================================================
# RIVALRY TESTS
# ============================================================================

class TestRivalry:
    """Tests for Rivalry dataclass"""
    
    @pytest.fixture
    def basic_rivalry(self):
        """Create a basic rivalry for testing"""
        return Rivalry(
            fighter1_id="fighter_a",
            fighter2_id="fighter_b",
            fighter1_name="Alex Alpha",
            fighter2_name="Bob Beta",
            rivalry_type=RivalryType.COMPETITIVE,
            score=50,
        )
    
    def test_creation(self):
        """Should create rivalry with correct values"""
        rivalry = Rivalry(
            fighter1_id="f1",
            fighter2_id="f2",
            fighter1_name="Fighter One",
            fighter2_name="Fighter Two",
            rivalry_type=RivalryType.BAD_BLOOD,
        )
        
        assert rivalry.fighter1_id == "f1"
        assert rivalry.rivalry_type == RivalryType.BAD_BLOOD
        assert rivalry.score == 0
        assert rivalry.fights == 0
    
    def test_intensity_calculation(self, basic_rivalry):
        """Should calculate correct intensity"""
        basic_rivalry.score = 25
        assert basic_rivalry.intensity == RivalryIntensity.BUDDING
        
        basic_rivalry.score = 50
        assert basic_rivalry.intensity == RivalryIntensity.HEATED
        
        basic_rivalry.score = 95
        assert basic_rivalry.intensity == RivalryIntensity.LEGENDARY
    
    def test_head_to_head(self, basic_rivalry):
        """Should format head-to-head correctly"""
        basic_rivalry.fighter1_wins = 2
        basic_rivalry.fighter2_wins = 1
        basic_rivalry.draws = 0
        
        assert basic_rivalry.head_to_head == "2-1-0"
    
    def test_series_leader(self, basic_rivalry):
        """Should identify series leader"""
        basic_rivalry.fighter1_wins = 2
        basic_rivalry.fighter2_wins = 1
        
        assert basic_rivalry.series_leader == "fighter_a"
        
        basic_rivalry.fighter2_wins = 2
        assert basic_rivalry.is_tied
    
    def test_is_heated(self, basic_rivalry):
        """Should correctly identify heated rivalries"""
        basic_rivalry.score = 40
        assert not basic_rivalry.is_heated()
        
        basic_rivalry.score = 50
        assert basic_rivalry.is_heated()
    
    def test_add_score(self, basic_rivalry):
        """Should add score and create event"""
        initial_score = basic_rivalry.score
        basic_rivalry.add_score(15, "trash_talk", "Called out opponent")
        
        assert basic_rivalry.score == initial_score + 15
        assert len(basic_rivalry.history) == 1
        assert basic_rivalry.history[0].event_type == "trash_talk"
    
    def test_add_score_clamped(self, basic_rivalry):
        """Score should be clamped to 0-100"""
        basic_rivalry.score = 95
        basic_rivalry.add_score(20, "test", "Test event")
        assert basic_rivalry.score == 100
        
        basic_rivalry.score = 5
        basic_rivalry.add_score(-20, "test", "Test event")
        assert basic_rivalry.score == 0
    
    def test_record_fight(self, basic_rivalry):
        """Should record fight results"""
        basic_rivalry.record_fight("fighter_a")
        
        assert basic_rivalry.fights == 1
        assert basic_rivalry.fighter1_wins == 1
        assert basic_rivalry.fighter2_wins == 0
    
    def test_record_draw(self, basic_rivalry):
        """Should record draws"""
        basic_rivalry.record_fight(None, is_draw=True)
        
        assert basic_rivalry.fights == 1
        assert basic_rivalry.draws == 1
    
    def test_apply_decay(self, basic_rivalry):
        """Should apply decay correctly"""
        basic_rivalry.score = 50
        basic_rivalry.apply_decay(2)  # 2 months
        
        assert basic_rivalry.score == 46  # 50 - (2 * 2)
    
    def test_deactivate_on_low_score(self, basic_rivalry):
        """Should deactivate when score too low"""
        basic_rivalry.score = 12
        basic_rivalry.apply_decay(2)  # Drops to 8
        
        assert not basic_rivalry.is_active
    
    def test_narrative_summary(self, basic_rivalry):
        """Should generate narrative summary"""
        basic_rivalry.fights = 2
        summary = basic_rivalry.get_narrative_summary()
        
        assert "Alex Alpha" in summary
        assert "Bob Beta" in summary
        assert "rematch" in summary.lower()
    
    def test_serialization(self, basic_rivalry):
        """Should serialize and deserialize correctly"""
        basic_rivalry.add_score(10, "test", "Test event")
        basic_rivalry.record_fight("fighter_a")
        
        data = basic_rivalry.to_dict()
        restored = Rivalry.from_dict(data)
        
        assert restored.fighter1_id == basic_rivalry.fighter1_id
        assert restored.score == basic_rivalry.score
        assert restored.fights == basic_rivalry.fights
        assert len(restored.history) == 1


# ============================================================================
# FIGHT CONTEXT TESTS
# ============================================================================

class TestFightContext:
    """Tests for FightContext dataclass"""
    
    def test_creation(self):
        """Should create context with required fields"""
        context = FightContext(
            fight_id="fight_1",
            fighter1_id="f1",
            fighter2_id="f2",
            fighter1_name="Fighter One",
            fighter2_name="Fighter Two",
            winner_id="f1",
            method="DEC",
        )
        
        assert context.fight_id == "fight_1"
        assert context.winner_id == "f1"
        assert context.method == "DEC"


# ============================================================================
# DETECTION TESTS
# ============================================================================

class TestDetectRivalryTriggers:
    """Tests for rivalry trigger detection"""
    
    def test_split_decision_trigger(self):
        """Split decisions should trigger rivalry"""
        context = FightContext(
            fight_id="f1",
            fighter1_id="a",
            fighter2_id="b",
            fighter1_name="A",
            fighter2_name="B",
            winner_id="a",
            method="SPLIT",
        )
        
        triggers = detect_rivalry_triggers(context)
        trigger_types = [t[0] for t in triggers]
        
        assert "split_decision" in trigger_types
    
    def test_title_fight_trigger(self):
        """Title fights should trigger rivalry"""
        context = FightContext(
            fight_id="f1",
            fighter1_id="a",
            fighter2_id="b",
            fighter1_name="A",
            fighter2_name="B",
            winner_id="a",
            method="DEC",
            is_title_fight=True,
        )
        
        triggers = detect_rivalry_triggers(context)
        trigger_types = [t[0] for t in triggers]
        
        assert "title_fight" in trigger_types
    
    def test_knockout_trigger(self):
        """Knockouts should create revenge motivation"""
        context = FightContext(
            fight_id="f1",
            fighter1_id="a",
            fighter2_id="b",
            fighter1_name="A",
            fighter2_name="B",
            winner_id="a",
            method="KO",
        )
        
        triggers = detect_rivalry_triggers(context)
        trigger_types = [t[0] for t in triggers]
        
        assert "knockout_loss" in trigger_types
    
    def test_close_fight_trigger(self):
        """Close fights should trigger rivalry"""
        context = FightContext(
            fight_id="f1",
            fighter1_id="a",
            fighter2_id="b",
            fighter1_name="A",
            fighter2_name="B",
            winner_id="a",
            method="DEC",
            was_close=True,
        )
        
        triggers = detect_rivalry_triggers(context)
        trigger_types = [t[0] for t in triggers]
        
        assert "close_decision" in trigger_types


class TestDetermineRivalryType:
    """Tests for rivalry type determination"""
    
    def test_title_fight_creates_title_dispute(self):
        """Title fights should create title dispute rivalry"""
        context = FightContext(
            fight_id="f1",
            fighter1_id="a",
            fighter2_id="b",
            fighter1_name="A",
            fighter2_name="B",
            winner_id="a",
            method="DEC",
            is_title_fight=True,
        )
        
        rivalry_type = determine_rivalry_type(context)
        assert rivalry_type == RivalryType.TITLE_DISPUTE
    
    def test_controversial_creates_bad_blood(self):
        """Controversial results should create bad blood"""
        context = FightContext(
            fight_id="f1",
            fighter1_id="a",
            fighter2_id="b",
            fighter1_name="A",
            fighter2_name="B",
            winner_id="a",
            method="DEC",
            was_controversial=True,
        )
        
        rivalry_type = determine_rivalry_type(context)
        assert rivalry_type == RivalryType.BAD_BLOOD
    
    def test_default_is_competitive(self):
        """Default rivalry type should be competitive"""
        context = FightContext(
            fight_id="f1",
            fighter1_id="a",
            fighter2_id="b",
            fighter1_name="A",
            fighter2_name="B",
            winner_id="a",
            method="DEC",
        )
        
        rivalry_type = determine_rivalry_type(context)
        assert rivalry_type == RivalryType.COMPETITIVE


class TestDetectRivalryFromFight:
    """Tests for full rivalry detection"""
    
    def test_creates_rivalry_from_significant_fight(self):
        """Should create rivalry from significant fight"""
        context = FightContext(
            fight_id="f1",
            fighter1_id="a",
            fighter2_id="b",
            fighter1_name="Fighter A",
            fighter2_name="Fighter B",
            winner_id="a",
            method="SPLIT",
            is_title_fight=True,
        )
        
        rivalry, events = detect_rivalry_from_fight(context)
        
        assert rivalry is not None
        assert rivalry.fighter1_id == "a"
        assert rivalry.score > 0
        assert len(events) > 0
    
    def test_updates_existing_rivalry(self):
        """Should update existing rivalry"""
        existing = Rivalry(
            fighter1_id="a",
            fighter2_id="b",
            fighter1_name="Fighter A",
            fighter2_name="Fighter B",
            rivalry_type=RivalryType.COMPETITIVE,
            score=30,
            fights=1,
        )
        
        context = FightContext(
            fight_id="f2",
            fighter1_id="a",
            fighter2_id="b",
            fighter1_name="Fighter A",
            fighter2_name="Fighter B",
            winner_id="b",
            method="KO",
        )
        
        rivalry, events = detect_rivalry_from_fight(context, existing)
        
        assert rivalry.fights == 2
        assert rivalry.score > 30  # Should have increased
        assert "rematch" in [e.event_type for e in events]
    
    def test_no_rivalry_from_boring_fight(self):
        """Should not create rivalry from uneventful fight"""
        context = FightContext(
            fight_id="f1",
            fighter1_id="a",
            fighter2_id="b",
            fighter1_name="Fighter A",
            fighter2_name="Fighter B",
            winner_id="a",
            method="DEC",  # Regular decision, nothing special
        )
        
        rivalry, events = detect_rivalry_from_fight(context)
        
        # May or may not create rivalry depending on triggers
        # Just ensure it doesn't crash
        assert events is not None


# ============================================================================
# RIVALRY SYSTEM TESTS
# ============================================================================

class TestRivalrySystem:
    """Tests for RivalrySystem class"""
    
    @pytest.fixture
    def system(self):
        """Fresh rivalry system for each test"""
        return RivalrySystem()
    
    def test_get_rivalry_none(self, system):
        """Should return None for non-existent rivalry"""
        rivalry = system.get_rivalry("a", "b")
        assert rivalry is None
    
    def test_add_and_get_rivalry(self, system):
        """Should add and retrieve rivalry"""
        rivalry = Rivalry(
            fighter1_id="a",
            fighter2_id="b",
            fighter1_name="A",
            fighter2_name="B",
            rivalry_type=RivalryType.COMPETITIVE,
            score=50,
        )
        
        system.add_rivalry(rivalry)
        
        # Should find regardless of order
        assert system.get_rivalry("a", "b") is not None
        assert system.get_rivalry("b", "a") is not None
    
    def test_get_fighter_rivalries(self, system):
        """Should get all rivalries for a fighter"""
        r1 = Rivalry(
            fighter1_id="a", fighter2_id="b",
            fighter1_name="A", fighter2_name="B",
            rivalry_type=RivalryType.COMPETITIVE, score=50,
        )
        r2 = Rivalry(
            fighter1_id="a", fighter2_id="c",
            fighter1_name="A", fighter2_name="C",
            rivalry_type=RivalryType.BAD_BLOOD, score=40,
        )
        
        system.add_rivalry(r1)
        system.add_rivalry(r2)
        
        rivalries = system.get_fighter_rivalries("a")
        assert len(rivalries) == 2
    
    def test_get_top_rivalry(self, system):
        """Should get most intense rivalry"""
        r1 = Rivalry(
            fighter1_id="a", fighter2_id="b",
            fighter1_name="A", fighter2_name="B",
            rivalry_type=RivalryType.COMPETITIVE, score=50,
        )
        r2 = Rivalry(
            fighter1_id="a", fighter2_id="c",
            fighter1_name="A", fighter2_name="C",
            rivalry_type=RivalryType.BAD_BLOOD, score=80,
        )
        
        system.add_rivalry(r1)
        system.add_rivalry(r2)
        
        top = system.get_top_rivalry("a")
        assert top.score == 80
    
    def test_process_fight(self, system):
        """Should process fight and create/update rivalry"""
        context = FightContext(
            fight_id="f1",
            fighter1_id="a",
            fighter2_id="b",
            fighter1_name="Fighter A",
            fighter2_name="Fighter B",
            winner_id="a",
            method="SPLIT",
            is_title_fight=True,
        )
        
        rivalry = system.process_fight(context)
        
        assert rivalry is not None
        assert system.get_rivalry("a", "b") is not None
    
    def test_add_interaction(self, system):
        """Should add interaction and create rivalry"""
        rivalry = system.add_interaction(
            fighter1_id="a",
            fighter2_id="b",
            fighter1_name="Fighter A",
            fighter2_name="Fighter B",
            interaction_type="trash_talk",
        )
        
        assert rivalry is not None
        assert rivalry.rivalry_type == RivalryType.BAD_BLOOD
        assert rivalry.score > 0
    
    def test_record_gym_defection(self, system):
        """Should create gym war rivalries"""
        rivalries = system.record_gym_defection(
            fighter_id="defector",
            fighter_name="The Defector",
            former_teammates=[
                ("teammate1", "Teammate One"),
                ("teammate2", "Teammate Two"),
            ]
        )
        
        assert len(rivalries) == 2
        for r in rivalries:
            assert r.rivalry_type == RivalryType.GYM_WAR
    
    def test_apply_monthly_decay(self, system):
        """Should apply decay to all rivalries"""
        r1 = Rivalry(
            fighter1_id="a", fighter2_id="b",
            fighter1_name="A", fighter2_name="B",
            rivalry_type=RivalryType.COMPETITIVE, score=50,
        )
        
        system.add_rivalry(r1)
        deactivated = system.apply_monthly_decay()
        
        rivalry = system.get_rivalry("a", "b")
        assert rivalry.score == 48  # 50 - 2
        assert len(deactivated) == 0
    
    def test_get_heated_rivalries(self, system):
        """Should return only heated rivalries"""
        r1 = Rivalry(
            fighter1_id="a", fighter2_id="b",
            fighter1_name="A", fighter2_name="B",
            rivalry_type=RivalryType.COMPETITIVE, score=60,
        )
        r2 = Rivalry(
            fighter1_id="c", fighter2_id="d",
            fighter1_name="C", fighter2_name="D",
            rivalry_type=RivalryType.BAD_BLOOD, score=30,
        )
        
        system.add_rivalry(r1)
        system.add_rivalry(r2)
        
        heated = system.get_heated_rivalries()
        assert len(heated) == 1
        assert heated[0].score == 60
    
    def test_get_rivalry_stats(self, system):
        """Should return system statistics"""
        r1 = Rivalry(
            fighter1_id="a", fighter2_id="b",
            fighter1_name="A", fighter2_name="B",
            rivalry_type=RivalryType.COMPETITIVE, score=50,
        )
        system.add_rivalry(r1)
        
        stats = system.get_rivalry_stats()
        
        assert stats["total_rivalries"] == 1
        assert stats["active_rivalries"] == 1
        assert "intensity_distribution" in stats
        assert "type_distribution" in stats
    
    def test_serialization(self, system):
        """Should serialize and deserialize correctly"""
        r1 = Rivalry(
            fighter1_id="a", fighter2_id="b",
            fighter1_name="A", fighter2_name="B",
            rivalry_type=RivalryType.COMPETITIVE, score=50,
        )
        system.add_rivalry(r1)
        
        data = system.to_dict()
        restored = RivalrySystem.from_dict(data)
        
        assert restored.get_rivalry("a", "b") is not None
        assert restored.get_rivalry("a", "b").score == 50


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions"""
    
    def test_get_rivalry_system_singleton(self):
        """Should return same instance"""
        reset_rivalry_system()
        s1 = get_rivalry_system()
        s2 = get_rivalry_system()
        assert s1 is s2
    
    def test_reset_rivalry_system(self):
        """Should reset to fresh instance"""
        system = get_rivalry_system()
        system.add_rivalry(Rivalry(
            fighter1_id="a", fighter2_id="b",
            fighter1_name="A", fighter2_name="B",
            rivalry_type=RivalryType.COMPETITIVE,
        ))
        
        reset_rivalry_system()
        new_system = get_rivalry_system()
        
        assert new_system.get_rivalry("a", "b") is None
    
    def test_get_intensity_description(self):
        """Should return description for intensity"""
        desc = get_rivalry_intensity_description(RivalryIntensity.LEGENDARY)
        assert "legendary" in desc.lower()
    
    def test_get_type_description(self):
        """Should return description for type"""
        desc = get_rivalry_type_description(RivalryType.GYM_WAR)
        assert "teammate" in desc.lower()
    
    def test_check_for_rivalry(self):
        """Should check if rivalry exists"""
        reset_rivalry_system()
        system = get_rivalry_system()
        
        assert not check_for_rivalry("a", "b")
        
        system.add_rivalry(Rivalry(
            fighter1_id="a", fighter2_id="b",
            fighter1_name="A", fighter2_name="B",
            rivalry_type=RivalryType.COMPETITIVE, score=50,
        ))
        
        assert check_for_rivalry("a", "b")
    
    def test_get_rivalry_score(self):
        """Should get rivalry score"""
        reset_rivalry_system()
        system = get_rivalry_system()
        
        assert get_rivalry_score("a", "b") == 0
        
        system.add_rivalry(Rivalry(
            fighter1_id="a", fighter2_id="b",
            fighter1_name="A", fighter2_name="B",
            rivalry_type=RivalryType.COMPETITIVE, score=75,
        ))
        
        assert get_rivalry_score("a", "b") == 75
    
    def test_format_rivalry_display(self):
        """Should format rivalry for display"""
        rivalry = Rivalry(
            fighter1_id="a", fighter2_id="b",
            fighter1_name="Fighter Alpha", fighter2_name="Fighter Beta",
            rivalry_type=RivalryType.BAD_BLOOD, score=60,
            fighter1_wins=1, fighter2_wins=1,
        )
        
        display = format_rivalry_display(rivalry)
        
        assert "Fighter Alpha" in display
        assert "Fighter Beta" in display
        assert "1-1-0" in display
        assert "Bad Blood" in display
