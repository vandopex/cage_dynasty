# tests/test_week_advancement.py
# Tests for the Week Advancement System (Core Game Loop)
# Run: python3 -m pytest tests/test_week_advancement.py -v

"""
Tests for core/week_advancement.py

Covers:
- Fighter state management
- Fight scheduling
- Week advancement core loop
- Training processing
- Fight execution
- Injury recovery
- Offer generation
- News/headlines
- Display helpers
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.week_advancement import (
    # Enums
    EventType, HeadlineCategory,
    # Data classes
    WeekEvent, FightResult, TrainingProgress, InjuryUpdate,
    OfferUpdate, WeekSummary, FighterWeekState, ScheduledFight,
    # System
    WeekAdvancementSystem, create_week_system,
    # Display
    format_week_summary, format_upcoming_fights,
    format_injury_report, format_training_report,
    # Constants
    FATIGUE_RECOVERY_PER_WEEK,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def fighter1():
    """Create first test fighter."""
    return FighterWeekState(
        fighter_id="f1",
        name="Champion Charlie",
        age=28,
        camp_id="camp_player",
        is_player_fighter=True,
        is_active=True,
        wins=15,
        losses=2,
        win_streak=5,
    )


@pytest.fixture
def fighter2():
    """Create second test fighter."""
    return FighterWeekState(
        fighter_id="f2",
        name="Challenger Chris",
        age=26,
        camp_id="camp_ai",
        is_player_fighter=False,
        is_active=True,
        wins=12,
        losses=3,
        win_streak=3,
    )


@pytest.fixture
def injured_fighter():
    """Create an injured fighter."""
    return FighterWeekState(
        fighter_id="f3",
        name="Injured Ivan",
        age=30,
        camp_id="camp_ai",
        is_player_fighter=False,
        is_active=True,
        is_injured=True,
        injury_type="Broken hand",
        injury_weeks_remaining=4,
    )


@pytest.fixture
def training_fighter():
    """Create a fighter in training."""
    return FighterWeekState(
        fighter_id="f4",
        name="Training Tom",
        age=24,
        camp_id="camp_player",
        is_player_fighter=True,
        is_active=True,
        in_training_camp=True,
        fatigue=20,
    )


@pytest.fixture
def system(fighter1, fighter2, injured_fighter, training_fighter):
    """Create system with fighters registered."""
    sys = create_week_system()
    sys.set_player_camp("camp_player")
    sys.register_fighter(fighter1)
    sys.register_fighter(fighter2)
    sys.register_fighter(injured_fighter)
    sys.register_fighter(training_fighter)
    return sys


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestEnums:
    def test_event_types(self):
        assert EventType.FIGHT_COMPLETED.value == "fight_completed"
        assert EventType.TRAINING_PROGRESS.value == "training_progress"
        assert EventType.INJURY_OCCURRED.value == "injury_occurred"
    
    def test_headline_categories(self):
        assert HeadlineCategory.FIGHT_RESULT.value == "fight_result"
        assert HeadlineCategory.TITLE_NEWS.value == "title_news"


# ============================================================================
# DATA CLASS TESTS
# ============================================================================

class TestFighterWeekState:
    def test_create_fighter(self, fighter1):
        assert fighter1.fighter_id == "f1"
        assert fighter1.name == "Champion Charlie"
        assert fighter1.is_player_fighter is True
    
    def test_to_dict(self, fighter1):
        data = fighter1.to_dict()
        assert data["fighter_id"] == "f1"
        assert data["name"] == "Champion Charlie"
    
    def test_injured_state(self, injured_fighter):
        assert injured_fighter.is_injured is True
        assert injured_fighter.injury_weeks_remaining == 4


class TestScheduledFight:
    def test_create_fight(self):
        fight = ScheduledFight(
            fight_id="fight1",
            fighter1_id="f1",
            fighter1_name="Fighter One",
            fighter2_id="f2",
            fighter2_name="Fighter Two",
            weight_class="Welterweight",
            scheduled_week=10,
            scheduled_date="Week 10",
        )
        assert fight.fight_id == "fight1"
        assert fight.involves_player is False
    
    def test_serialization(self):
        fight = ScheduledFight(
            fight_id="fight1",
            fighter1_id="f1",
            fighter1_name="One",
            fighter2_id="f2",
            fighter2_name="Two",
            weight_class="Welterweight",
            scheduled_week=10,
            scheduled_date="Week 10",
            is_title_fight=True,
        )
        
        data = fight.to_dict()
        restored = ScheduledFight.from_dict(data)
        
        assert restored.fight_id == "fight1"
        assert restored.is_title_fight is True


class TestFightResult:
    def test_headline_regular(self):
        result = FightResult(
            fight_id="f1",
            winner_id="w1",
            winner_name="Winner",
            loser_id="l1",
            loser_name="Loser",
            method="DEC",
            round_finished=3,
            time_finished="5:00",
            weight_class="Welterweight",
        )
        assert "Winner" in result.headline
        assert "Loser" in result.headline
    
    def test_headline_ko(self):
        result = FightResult(
            fight_id="f1",
            winner_id="w1",
            winner_name="KO King",
            loser_id="l1",
            loser_name="Victim",
            method="KO",
            round_finished=1,
            time_finished="2:30",
            weight_class="Welterweight",
        )
        assert "💥" in result.headline
        assert "KO" in result.headline
    
    def test_headline_title_change(self):
        result = FightResult(
            fight_id="f1",
            winner_id="w1",
            winner_name="New Champ",
            loser_id="l1",
            loser_name="Old Champ",
            method="TKO",
            round_finished=4,
            time_finished="3:45",
            weight_class="Welterweight",
            was_title_fight=True,
            title_changed=True,
        )
        assert "CHAMPION" in result.headline
        assert "👑" in result.headline


class TestWeekSummary:
    def test_create_summary(self):
        summary = WeekSummary(
            week_number=1,
            year=2025,
            month=1,
            day=1,
            date_string="Week 1, Year 2025",
        )
        assert summary.fights_completed == 0
        assert summary.headlines == []
    
    def test_add_event(self):
        summary = WeekSummary(
            week_number=1,
            year=2025,
            month=1,
            day=1,
            date_string="Week 1",
        )
        
        event = WeekEvent(
            event_type=EventType.FIGHT_COMPLETED,
            description="Test fight",
            headline="Test headline",
            is_player_relevant=True,
        )
        
        summary.add_event(event)
        
        assert len(summary.events) == 1
        assert "Test headline" in summary.headlines
        assert "Test headline" in summary.player_headlines
    
    def test_has_player_events(self):
        summary = WeekSummary(
            week_number=1, year=2025, month=1, day=1, date_string="Week 1"
        )
        assert summary.has_player_events is False
        
        summary.player_headlines.append("Test")
        assert summary.has_player_events is True


# ============================================================================
# WEEK ADVANCEMENT SYSTEM TESTS
# ============================================================================

class TestWeekAdvancementSystem:
    def test_create_system(self):
        sys = create_week_system()
        assert sys is not None
    
    def test_register_fighter(self, system, fighter1):
        fighter = system.get_fighter(fighter1.fighter_id)
        assert fighter is not None
        assert fighter.name == fighter1.name
    
    def test_update_fighter(self, system, fighter1):
        success = system.update_fighter(fighter1.fighter_id, wins=20)
        assert success is True
        
        fighter = system.get_fighter(fighter1.fighter_id)
        assert fighter.wins == 20
    
    def test_set_player_camp(self, system):
        system.set_player_camp("new_camp")
        assert system._player_camp_id == "new_camp"


class TestFightScheduling:
    def test_schedule_fight(self, system, fighter1, fighter2):
        fight = system.schedule_fight(
            fighter1.fighter_id,
            fighter2.fighter_id,
            weeks_from_now=8,
        )
        
        assert fight is not None
        assert fight.fighter1_name == fighter1.name
        assert fight.fighter2_name == fighter2.name
        assert fight.involves_player is True  # fighter1 is player
    
    def test_schedule_title_fight(self, system, fighter1, fighter2):
        fight = system.schedule_fight(
            fighter1.fighter_id,
            fighter2.fighter_id,
            weeks_from_now=8,
            is_title_fight=True,
        )
        
        assert fight.is_title_fight is True
    
    def test_get_scheduled_fights(self, system, fighter1, fighter2):
        system.schedule_fight(fighter1.fighter_id, fighter2.fighter_id, weeks_from_now=5)
        
        # Current week is 1, fight at week 6
        fights = system.get_scheduled_fights(week=6)
        assert len(fights) == 1
    
    def test_get_player_scheduled_fights(self, system, fighter1, fighter2):
        system.schedule_fight(fighter1.fighter_id, fighter2.fighter_id, weeks_from_now=4)
        
        player_fights = system.get_player_scheduled_fights()
        assert len(player_fights) == 1


class TestWeekAdvancement:
    def test_advance_week_basic(self, system):
        summary = system.advance_week()
        
        assert summary is not None
        # After first advance, we're at week 2 (started at week 1)
        assert summary.week_number == 2
        assert isinstance(summary.headlines, list)
    
    def test_advance_week_increments_date(self, system):
        initial_date = system.get_current_date()
        system.advance_week()
        new_date = system.get_current_date()
        
        assert new_date["week"] == initial_date["week"] + 1
    
    def test_advance_multiple_weeks(self, system):
        summaries = system.advance_weeks(4)
        
        assert len(summaries) == 4
        date = system.get_current_date()
        assert date["week"] == 5  # Started at 1, advanced 4


class TestRecoveryPhase:
    def test_injury_recovery(self, system, injured_fighter):
        initial_weeks = injured_fighter.injury_weeks_remaining
        
        system.advance_week()
        
        fighter = system.get_fighter(injured_fighter.fighter_id)
        assert fighter.injury_weeks_remaining == initial_weeks - 1
    
    def test_injury_healed(self, system):
        # Create fighter with 1 week injury
        short_injury = FighterWeekState(
            fighter_id="short",
            name="Short Injury",
            age=25,
            is_injured=True,
            injury_type="Minor cut",
            injury_weeks_remaining=1,
        )
        system.register_fighter(short_injury)
        
        summary = system.advance_week()
        
        fighter = system.get_fighter("short")
        assert fighter.is_injured is False
        assert summary.injuries_healed == 1
    
    def test_fatigue_recovery(self, system):
        fatigued = FighterWeekState(
            fighter_id="tired",
            name="Tired Fighter",
            age=27,
            fatigue=50,
            in_training_camp=False,
        )
        system.register_fighter(fatigued)
        
        system.advance_week()
        
        fighter = system.get_fighter("tired")
        assert fighter.fatigue == 50 - FATIGUE_RECOVERY_PER_WEEK


class TestFightExecution:
    def test_fight_executes_on_scheduled_week(self, system, fighter1, fighter2):
        # Schedule fight for next week
        system.schedule_fight(
            fighter1.fighter_id,
            fighter2.fighter_id,
            weeks_from_now=1,
        )
        
        # Advance to fight week
        summary = system.advance_week()
        
        assert summary.fights_completed == 1
        assert len(summary.fight_results) == 1
    
    def test_fight_updates_records(self, system, fighter1, fighter2):
        initial_f1_wins = fighter1.wins
        initial_f2_wins = fighter2.wins
        
        system.schedule_fight(
            fighter1.fighter_id,
            fighter2.fighter_id,
            weeks_from_now=1,
        )
        
        summary = system.advance_week()
        result = summary.fight_results[0]
        
        # Winner should have +1 win
        winner = system.get_fighter(result.winner_id)
        loser = system.get_fighter(result.loser_id)
        
        if result.winner_id == fighter1.fighter_id:
            assert winner.wins == initial_f1_wins + 1
        else:
            assert winner.wins == initial_f2_wins + 1
    
    def test_injured_fight_cancelled(self, system, fighter1, injured_fighter):
        system.schedule_fight(
            fighter1.fighter_id,
            injured_fighter.fighter_id,
            weeks_from_now=1,
        )
        
        summary = system.advance_week()
        
        # Fight should be cancelled
        assert summary.fights_completed == 0
        # Should have cancellation headline
        assert any("cancelled" in h.lower() for h in summary.headlines)


class TestQueries:
    def test_get_upcoming_fights(self, system, fighter1, fighter2):
        system.schedule_fight(fighter1.fighter_id, fighter2.fighter_id, weeks_from_now=3)
        
        upcoming = system.get_upcoming_fights(weeks_ahead=5)
        assert len(upcoming) == 1
    
    def test_get_injured_fighters(self, system, injured_fighter):
        injured = system.get_injured_fighters()
        assert len(injured) >= 1
        assert any(f.fighter_id == injured_fighter.fighter_id for f in injured)
    
    def test_get_available_fighters(self, system, fighter1, fighter2, injured_fighter):
        available = system.get_available_fighters()
        
        # Injured fighter should not be available
        assert not any(f.fighter_id == injured_fighter.fighter_id for f in available)
    
    def test_get_week_history(self, system):
        system.advance_weeks(5)
        
        history = system.get_week_history(num_weeks=3)
        assert len(history) == 3


class TestSerialization:
    def test_to_dict(self, system, fighter1, fighter2):
        system.schedule_fight(fighter1.fighter_id, fighter2.fighter_id, weeks_from_now=4)
        
        data = system.to_dict()
        
        assert "current_week" in data
        assert "fighters" in data
        assert "scheduled_fights" in data
    
    def test_from_dict(self):
        data = {
            "current_week": 10,
            "current_year": 2026,
            "current_month": 3,
            "current_day": 15,
            "player_camp_id": "player",
            "fight_counter": 5,
            "fighters": {
                "f1": {
                    "fighter_id": "f1",
                    "name": "Test Fighter",
                    "age": 28,
                    "is_active": True,
                    "is_injured": False,
                    "injury_type": "",
                    "injury_weeks_remaining": 0,
                    "in_training_camp": False,
                    "scheduled_fight_date": None,
                    "scheduled_fight_weeks": 0,
                    "fatigue": 0,
                }
            },
            "scheduled_fights": {},
        }
        
        system = WeekAdvancementSystem.from_dict(data)
        
        assert system._current_week == 10
        assert system._current_year == 2026
        assert "f1" in system._fighters


# ============================================================================
# DISPLAY HELPER TESTS
# ============================================================================

class TestDisplayHelpers:
    def test_format_week_summary(self):
        summary = WeekSummary(
            week_number=5,
            year=2025,
            month=2,
            day=1,
            date_string="Week 5, Year 2025",
            fights_completed=2,
            training_sessions=3,
        )
        summary.headlines = ["Fight 1 result", "Fight 2 result"]
        
        lines = format_week_summary(summary)
        
        assert len(lines) > 0
        assert any("WEEK 5" in line for line in lines)
        assert any("2 fights" in line for line in lines)
    
    def test_format_upcoming_fights(self):
        fights = [
            ScheduledFight(
                fight_id="f1",
                fighter1_id="a",
                fighter1_name="Fighter A",
                fighter2_id="b",
                fighter2_name="Fighter B",
                weight_class="Welterweight",
                scheduled_week=10,
                scheduled_date="Week 10",
                involves_player=True,
            )
        ]
        
        lines = format_upcoming_fights(fights, current_week=8)
        
        assert any("Fighter A" in line for line in lines)
        assert any("Fighter B" in line for line in lines)
    
    def test_format_injury_report(self):
        injuries = [
            InjuryUpdate(
                fighter_id="f1",
                fighter_name="Hurt Harry",
                injury_type="Broken hand",
                weeks_remaining=4,
            )
        ]
        
        lines = format_injury_report(injuries)
        
        assert any("Hurt Harry" in line for line in lines)
        assert any("Broken hand" in line for line in lines)
    
    def test_format_training_report(self):
        progress = [
            TrainingProgress(
                fighter_id="f1",
                fighter_name="Training Tom",
                gains={"boxing": 2, "kicks": 1},
                total_gains=3,
                week_number=3,
            )
        ]
        
        lines = format_training_report(progress)
        
        assert any("Training Tom" in line for line in lines)
        assert any("+3" in line for line in lines)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    def test_full_week_cycle(self, system, fighter1, fighter2):
        """Test a complete week with all phases."""
        # Schedule a fight
        system.schedule_fight(
            fighter1.fighter_id,
            fighter2.fighter_id,
            weeks_from_now=1,
        )
        
        # Advance to fight week
        summary = system.advance_week()
        
        # Should have fight result
        assert summary.fights_completed == 1
        
        # Should have headlines
        assert len(summary.headlines) > 0
        
        # Should be in history
        history = system.get_week_history(1)
        assert len(history) == 1
    
    def test_multi_week_progression(self, system, fighter1, fighter2, injured_fighter):
        """Test progression over multiple weeks."""
        # Schedule fight
        system.schedule_fight(
            fighter1.fighter_id,
            fighter2.fighter_id,
            weeks_from_now=3,
        )
        
        # Advance 5 weeks
        summaries = system.advance_weeks(5)
        
        assert len(summaries) == 5
        
        # Fight should have happened when we reach week 4 (1 + 3)
        # After 3 advances from week 1, we're at week 4
        fight_week = summaries[2]  # Third advance reaches week 4
        assert fight_week.fights_completed == 1
        
        # Injured fighter should be healing
        fighter = system.get_fighter(injured_fighter.fighter_id)
        assert fighter.injury_weeks_remaining < 4  # Was 4, should decrease
    
    def test_callbacks_fire(self, system, fighter1, fighter2):
        """Test that callbacks are triggered."""
        fight_results = []
        
        def on_fight(result):
            fight_results.append(result)
        
        system.add_fight_callback(on_fight)
        
        system.schedule_fight(
            fighter1.fighter_id,
            fighter2.fighter_id,
            weeks_from_now=1,
        )
        
        system.advance_week()
        
        assert len(fight_results) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
