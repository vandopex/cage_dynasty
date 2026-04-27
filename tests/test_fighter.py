# tests/test_fighter.py
# Module 5: Fighter Entity Tests
# Tests: 43
#
# Tests for the Fighter entity - the core of the game.

"""
Test suite for Fighter entity.

Tests cover:
- Fighter creation and identity
- Attribute management
- Fight records and statistics
- Injuries and recovery
- Morale system
- Win/loss streaks
- Serialization
"""

import pytest
from dataclasses import asdict
from datetime import date

from entities.fighter import (
    Fighter, FightHistoryEntry, InjuryRecord,
    create_fighter
)
from core.types import (
    WeightClass, FightOutcome, FighterStatus, InjuryType,
    FightingStyle, FightRecord, AttributeSet
)
from core.calendar import GameDate, calendar


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def basic_fighter():
    """Create a basic test fighter"""
    return create_fighter(
        first_name="Test",
        last_name="Fighter",
        weight_class=WeightClass.LIGHTWEIGHT,
        birth_date=GameDate(1990, 6, 15),
        nationality="USA"
    )


@pytest.fixture
def configured_fighter():
    """Create a fighter with specific attributes"""
    return create_fighter(
        first_name="Configured",
        last_name="Test",
        weight_class=WeightClass.MIDDLEWEIGHT,
        birth_date=GameDate(1992, 3, 10),
        nationality="Brazil",
        attributes={
            "boxing": 75,
            "kicks": 80,
            "wrestling": 65,
            "bjj": 70,
            "cardio": 85
        }
    )


# ============================================================================
# FIGHTER CREATION TESTS
# ============================================================================

class TestFighterCreation:
    """Tests for creating fighters"""
    
    def test_basic_creation(self, basic_fighter):
        """Fighter should be created with basic info"""
        assert basic_fighter.first_name == "Test"
        assert basic_fighter.last_name == "Fighter"
        assert basic_fighter.weight_class == WeightClass.LIGHTWEIGHT
        assert basic_fighter.nationality == "USA"
    
    def test_factory_function(self, basic_fighter):
        """create_fighter should work"""
        assert isinstance(basic_fighter, Fighter)
    
    def test_custom_attributes(self, configured_fighter):
        """Custom attributes should be set"""
        assert configured_fighter.get_attribute("boxing") == 75
        assert configured_fighter.get_attribute("kicks") == 80
        assert configured_fighter.get_attribute("wrestling") == 65
    
    def test_default_attributes(self, basic_fighter):
        """Default attributes should be reasonable"""
        boxing = basic_fighter.get_attribute("boxing")
        assert 30 <= boxing <= 100
    
    def test_unique_ids(self):
        """Each fighter should have unique ID"""
        f1 = create_fighter("A", "B", WeightClass.FLYWEIGHT, GameDate(1990, 1, 1), "USA")
        f2 = create_fighter("C", "D", WeightClass.FLYWEIGHT, GameDate(1990, 1, 1), "USA")
        assert f1.id != f2.id


# ============================================================================
# FIGHTER IDENTITY TESTS
# ============================================================================

class TestFighterIdentity:
    """Tests for fighter name and identity"""
    
    def test_full_name(self, basic_fighter):
        """full_name should combine first and last"""
        assert basic_fighter.full_name == "Test Fighter"
    
    def test_display_name_without_nickname(self, basic_fighter):
        """display_name without nickname should be full name"""
        assert basic_fighter.display_name == "Test Fighter"
    
    def test_display_name_with_nickname(self, basic_fighter):
        """display_name with nickname should include it"""
        basic_fighter.nickname = "The Destroyer"
        assert '"The Destroyer"' in basic_fighter.display_name
    
    def test_string_representation(self, basic_fighter):
        """String should include name and weight class"""
        s = str(basic_fighter)
        assert "Test Fighter" in s
        assert "Lightweight" in s


# ============================================================================
# FIGHTER AGE TESTS
# ============================================================================

class TestFighterAge:
    """Tests for fighter age calculation"""
    
    def test_age_calculation(self, basic_fighter):
        """age should be calculated from birth date"""
        # Born June 15, 1990
        # Current calendar date determines age
        age = basic_fighter.age
        assert age >= 0  # Basic sanity check
    
    def test_age_on_specific_date(self, basic_fighter):
        """age_on_date should work for future dates"""
        future = GameDate(2030, 1, 1)
        age = basic_fighter.age_on_date(future)
        assert age == 39  # Born 1990, so 39 years old in 2030


# ============================================================================
# FIGHTER ATTRIBUTES TESTS
# ============================================================================

class TestFighterAttributes:
    """Tests for attribute management"""
    
    def test_get_attribute(self, configured_fighter):
        """get_attribute should return correct value"""
        assert configured_fighter.get_attribute("boxing") == 75
    
    def test_set_attribute(self, configured_fighter):
        """set_attribute should update value"""
        configured_fighter.set_attribute("boxing", 90)
        assert configured_fighter.get_attribute("boxing") == 90
    
    def test_modify_attribute(self, configured_fighter):
        """modify_attribute should add/subtract"""
        initial = configured_fighter.get_attribute("boxing")
        configured_fighter.modify_attribute("boxing", 5)
        assert configured_fighter.get_attribute("boxing") == initial + 5
    
    def test_modify_attribute_clamps(self, configured_fighter):
        """modify_attribute should clamp to 1-100"""
        configured_fighter.set_attribute("boxing", 95)
        configured_fighter.modify_attribute("boxing", 20)
        assert configured_fighter.get_attribute("boxing") == 100
    
    def test_overall_rating(self, configured_fighter):
        """overall_rating should be an average"""
        rating = configured_fighter.overall_rating
        assert 30 <= rating <= 100
    
    def test_striking_overall(self, configured_fighter):
        """striking_overall should calculate from striking attributes"""
        striking = configured_fighter.striking_overall
        assert 30 <= striking <= 100
    
    def test_grappling_overall(self, configured_fighter):
        """grappling_overall should calculate from grappling attributes"""
        grappling = configured_fighter.grappling_overall
        assert 30 <= grappling <= 100


# ============================================================================
# FIGHTER RECORD TESTS
# ============================================================================

@pytest.fixture
def record_fighter():
    """Fighter for record tests"""
    return create_fighter(
        first_name="Record",
        last_name="Test",
        weight_class=WeightClass.MIDDLEWEIGHT,
        birth_date=GameDate(1990, 1, 1),
        nationality="USA"
    )


class TestFighterRecord:
    """Tests for fight record management"""
    
    def test_initial_record(self, record_fighter):
        """New fighter should have 0-0-0 record"""
        assert record_fighter.record.wins == 0
        assert record_fighter.record.losses == 0
        assert record_fighter.record.draws == 0
    
    def test_add_win(self, record_fighter):
        """add_win should update record"""
        record_fighter.add_win(
            method=FightOutcome.KO,
            opponent_name="Opponent One",
            round_finished=2,
            time_in_round="3:45"
        )
        
        assert record_fighter.record.wins == 1
        assert record_fighter.record.losses == 0
    
    def test_add_loss(self, record_fighter):
        """add_loss should update record"""
        record_fighter.add_loss(
            method=FightOutcome.DECISION_UNANIMOUS,
            opponent_name="Opponent Two",
            round_finished=3
        )
        
        assert record_fighter.record.losses == 1
        assert record_fighter.record.wins == 0
    
    def test_add_draw(self, record_fighter):
        """add_draw should update record"""
        record_fighter.add_draw(opponent_name="Opponent Three")
        
        assert record_fighter.record.draws == 1
    
    def test_fight_history(self, record_fighter):
        """Fight history should track all fights"""
        record_fighter.add_win(
            method=FightOutcome.KO,
            opponent_name="Opp1",
            round_finished=1,
            time_in_round="2:30"
        )
        record_fighter.add_loss(
            method=FightOutcome.DECISION_UNANIMOUS,
            opponent_name="Opp2",
            round_finished=3
        )
        
        history = record_fighter.fight_history
        assert len(history) == 2
    
    def test_ko_wins_tracked(self, record_fighter):
        """KO/TKO wins should be counted"""
        record_fighter.add_win(
            method=FightOutcome.KO,
            opponent_name="A",
            round_finished=1,
            time_in_round="1:00"
        )
        record_fighter.add_win(
            method=FightOutcome.TKO,
            opponent_name="B",
            round_finished=2,
            time_in_round="2:00"
        )
        
        assert record_fighter.ko_wins == 2
    
    def test_submission_wins_tracked(self, record_fighter):
        """Submission wins should be counted"""
        record_fighter.add_win(
            method=FightOutcome.SUBMISSION,
            opponent_name="A",
            round_finished=2,
            time_in_round="3:30"
        )
        record_fighter.add_win(
            method=FightOutcome.SUBMISSION,
            opponent_name="B",
            round_finished=1,
            time_in_round="4:00"
        )
        
        assert record_fighter.submission_wins == 2
    
    def test_finish_rate(self, record_fighter):
        """finish_rate should calculate correctly"""
        record_fighter.add_win(
            method=FightOutcome.KO,
            opponent_name="A",
            round_finished=1,
            time_in_round="1:00"
        )
        record_fighter.add_win(
            method=FightOutcome.DECISION_UNANIMOUS,
            opponent_name="B",
            round_finished=3,
            time_in_round="5:00"
        )
        
        # 1 finish out of 2 wins = 50%
        assert record_fighter.finish_rate == 50.0


# ============================================================================
# WIN/LOSS STREAK TESTS
# ============================================================================

@pytest.fixture
def streak_fighter():
    """Fighter for streak tests"""
    return create_fighter(
        first_name="Streak",
        last_name="Test",
        weight_class=WeightClass.LIGHTWEIGHT,
        birth_date=GameDate(1990, 1, 1),
        nationality="USA"
    )


class TestWinLossStreaks:
    """Tests for win/loss streak tracking"""
    
    def test_win_streak(self, streak_fighter):
        """Should track consecutive wins"""
        streak_fighter.add_win(
            method=FightOutcome.KO,
            opponent_name="A",
            round_finished=1,
            time_in_round="1:00"
        )
        streak_fighter.add_win(
            method=FightOutcome.DECISION_UNANIMOUS,
            opponent_name="B",
            round_finished=3,
            time_in_round="5:00"
        )
        
        assert streak_fighter.win_streak >= 2
    
    def test_loss_breaks_win_streak(self, streak_fighter):
        """Loss should reset win streak"""
        streak_fighter.add_win(
            method=FightOutcome.KO,
            opponent_name="A",
            round_finished=1,
            time_in_round="1:00"
        )
        streak_fighter.add_loss(
            method=FightOutcome.KO,
            opponent_name="B",
            round_finished=1,
            time_in_round="2:00"
        )
        
        assert streak_fighter.win_streak == 0
    
    def test_lose_streak(self, streak_fighter):
        """Should track consecutive losses"""
        streak_fighter.add_loss(
            method=FightOutcome.KO,
            opponent_name="A",
            round_finished=1,
            time_in_round="1:00"
        )
        streak_fighter.add_loss(
            method=FightOutcome.DECISION_UNANIMOUS,
            opponent_name="B",
            round_finished=3,
            time_in_round="5:00"
        )
        
        assert streak_fighter.loss_streak >= 2


# ============================================================================
# FIGHTER STATUS TESTS
# ============================================================================

class TestFighterStatus:
    """Tests for fighter status"""
    
    def test_default_status(self, basic_fighter):
        """New fighter should be active or free agent"""
        assert basic_fighter.status in (FighterStatus.ACTIVE, FighterStatus.FREE_AGENT)
    
    def test_camp_assignment(self, basic_fighter):
        """camp_id should be settable"""
        basic_fighter.camp_id = "camp-123"
        assert basic_fighter.camp_id == "camp-123"
    
    def test_rank_properties(self, basic_fighter):
        """Ranking properties should work"""
        basic_fighter.rank = 5
        assert basic_fighter.rank == 5
        assert basic_fighter.is_ranked is True


# ============================================================================
# FIGHTER INJURY TESTS
# ============================================================================

@pytest.fixture
def injury_fighter():
    """Fighter for injury tests"""
    return create_fighter(
        first_name="Injury",
        last_name="Test",
        weight_class=WeightClass.FEATHERWEIGHT,
        birth_date=GameDate(1990, 1, 1),
        nationality="USA"
    )


class TestFighterInjuries:
    """Tests for injury system"""
    
    def test_no_injury_by_default(self, injury_fighter):
        """New fighter should have no injuries"""
        assert len(injury_fighter.injuries) == 0
    
    def test_add_injury(self, injury_fighter):
        """add_injury should create injury"""
        injury_fighter.add_injury(
            injury_type=InjuryType.MODERATE,
            description="Sprained ankle",
            recovery_weeks=6
        )
        
        assert len(injury_fighter.injuries) == 1
        assert injury_fighter.status == FighterStatus.INJURED
    
    def test_heal_injuries(self, injury_fighter):
        """heal_injuries should reduce recovery time"""
        injury_fighter.add_injury(InjuryType.MINOR, "Cut", 2)
        
        initial = injury_fighter.injuries[0].weeks_remaining
        injury_fighter.heal_injuries(weeks=1)
        
        assert injury_fighter.injuries[0].weeks_remaining == initial - 1
    
    def test_is_active_with_injury(self, injury_fighter):
        """Injured fighter should not be active"""
        # Check is_available property instead of is_active if that doesn't exist
        assert injury_fighter.status != FighterStatus.INJURED
        
        injury_fighter.add_injury(InjuryType.MINOR, "Cut", 2)
        assert injury_fighter.status == FighterStatus.INJURED


# ============================================================================
# FIGHTER MORALE TESTS
# ============================================================================

@pytest.fixture
def morale_fighter():
    """Fighter for morale tests"""
    return create_fighter(
        first_name="Morale",
        last_name="Test",
        weight_class=WeightClass.BANTAMWEIGHT,
        birth_date=GameDate(1990, 1, 1),
        nationality="USA"
    )


class TestFighterMorale:
    """Tests for morale system"""
    
    def test_default_morale(self, morale_fighter):
        """Default morale should be positive"""
        assert morale_fighter.morale >= 50
    
    def test_win_boosts_morale(self, morale_fighter):
        """Winning should increase morale"""
        initial = morale_fighter.morale
        morale_fighter.add_win(
            method=FightOutcome.KO,
            opponent_name="Opponent",
            round_finished=1,
            time_in_round="2:00"
        )
        
        assert morale_fighter.morale > initial
    
    def test_loss_hurts_morale(self, morale_fighter):
        """Losing should decrease morale"""
        initial = morale_fighter.morale
        morale_fighter.add_loss(
            method=FightOutcome.KO,
            opponent_name="Opponent",
            round_finished=1,
            time_in_round="1:00"
        )
        
        assert morale_fighter.morale < initial
    
    def test_morale_clamped(self, morale_fighter):
        """Morale should stay in 0-100 range"""
        morale_fighter.morale = 150
        assert morale_fighter.morale <= 100
        
        morale_fighter.morale = -50
        assert morale_fighter.morale >= 0


# ============================================================================
# SERIALIZATION TESTS
# ============================================================================

class TestFighterSerialization:
    """Tests for saving and loading fighters"""
    
    def test_to_dict_from_dict(self):
        """Fighter should serialize and deserialize"""
        original = create_fighter(
            first_name="Serialize",
            last_name="Test",
            weight_class=WeightClass.WELTERWEIGHT,
            birth_date=GameDate(1994, 9, 9),
            nationality="Canada",
            attributes={"boxing": 80, "wrestling": 70}
        )
        original.nickname = "The Serializer"
        original.rank = 5
        original.add_win(
            method=FightOutcome.KO,
            opponent_name="Opponent",
            round_finished=1,
            time_in_round="2:30"
        )
        
        # Serialize
        data = original.to_dict()
        
        # Deserialize
        restored = Fighter.from_dict(data)
        
        # Verify
        assert restored.first_name == "Serialize"
        assert restored.last_name == "Test"
        assert restored.nickname == "The Serializer"
        assert restored.weight_class == WeightClass.WELTERWEIGHT
        assert restored.rank == 5
        assert restored.record.wins == 1


# ============================================================================
# FIGHT HISTORY ENTRY TESTS
# ============================================================================

class TestFightHistoryEntry:
    """Tests for fight history entries"""
    
    def test_win_string(self):
        """Win entry should show W"""
        entry = FightHistoryEntry(
            date=GameDate(2024, 1, 1),
            opponent_name="Opponent",
            result="W",
            method=FightOutcome.KO,
            round_finished=1,
            time_in_round="2:30",
            weight_class=WeightClass.LIGHTWEIGHT
        )
        
        s = str(entry)
        assert "W" in s
    
    def test_loss_string(self):
        """Loss entry should show L"""
        entry = FightHistoryEntry(
            date=GameDate(2024, 1, 1),
            opponent_name="Opponent",
            result="L",
            method=FightOutcome.KO,
            round_finished=1,
            time_in_round="2:30",
            weight_class=WeightClass.LIGHTWEIGHT
        )
        
        s = str(entry)
        assert "L" in s
