# tests/test_cli_data.py
# Tests for interface/cli_data.py
# Lines: 324

"""Tests for CLI data classes module."""

import pytest
from interface.cli_data import (
    FighterFullData,
    FightResult,
    CompletedEvent,
    NewsItem,
    FightOffer,
)


# ============================================================================
# FIGHTER FULL DATA TESTS
# ============================================================================

class TestFighterFullDataCreation:
    """Test FighterFullData creation."""
    
    def test_basic_creation(self):
        """Create fighter with required fields."""
        fighter = FighterFullData(
            fighter_id="f1",
            name="Test Fighter"
        )
        assert fighter.fighter_id == "f1"
        assert fighter.name == "Test Fighter"
    
    def test_default_values(self):
        """Check default attribute values."""
        fighter = FighterFullData(fighter_id="f1", name="Test")
        assert fighter.country == "United States"
        assert fighter.age == 25
        assert fighter.weight_class == "Lightweight"
        assert fighter.strength == 50
        assert fighter.wins == 0
        assert fighter.traits == []
    
    def test_custom_attributes(self):
        """Create fighter with custom attributes."""
        fighter = FighterFullData(
            fighter_id="f1",
            name="Test Fighter",
            country="Brazil",
            boxing=85,
            wrestling=90,
            wins=15,
            ko_wins=10,
        )
        assert fighter.country == "Brazil"
        assert fighter.boxing == 85
        assert fighter.wrestling == 90
        assert fighter.wins == 15


class TestFighterFullDataProperties:
    """Test FighterFullData computed properties."""
    
    def test_overall_rating(self):
        """Overall rating should be calculated from attributes."""
        fighter = FighterFullData(
            fighter_id="f1",
            name="Test",
            boxing=80,
            kicks=70,
            clinch_striking=70,
            wrestling=75,
            bjj=80,
            takedown_defense=70,
            chin=75,
            cardio=80,
            heart=85,
        )
        assert 70 <= fighter.overall_rating <= 85
    
    def test_striking_rating(self):
        """Striking rating calculation."""
        fighter = FighterFullData(
            fighter_id="f1",
            name="Test",
            boxing=80,
            kicks=60,
            clinch_striking=60,
            striking_defense=80,
        )
        assert 60 <= fighter.striking_rating <= 80
    
    def test_grappling_rating(self):
        """Grappling rating calculation."""
        fighter = FighterFullData(
            fighter_id="f1",
            name="Test",
            wrestling=70,
            bjj=90,
            takedown_defense=80,
        )
        assert 75 <= fighter.grappling_rating <= 85
    
    def test_record_no_draws(self):
        """Record string without draws."""
        fighter = FighterFullData(fighter_id="f1", name="Test", wins=10, losses=2)
        assert fighter.record == "10-2"
    
    def test_record_with_draws(self):
        """Record string with draws."""
        fighter = FighterFullData(fighter_id="f1", name="Test", wins=10, losses=2, draws=1)
        assert fighter.record == "10-2-1"
    
    def test_height_display(self):
        """Height conversion to feet/inches."""
        fighter = FighterFullData(fighter_id="f1", name="Test", height_cm=183)
        assert "'" in fighter.height_display
        assert '"' in fighter.height_display
    
    def test_reach_display(self):
        """Reach conversion to inches."""
        fighter = FighterFullData(fighter_id="f1", name="Test", reach_cm=188)
        assert '"' in fighter.reach_display
    
    def test_finish_rate_with_wins(self):
        """Finish rate with wins."""
        fighter = FighterFullData(
            fighter_id="f1",
            name="Test",
            wins=10,
            ko_wins=5,
            sub_wins=3,
        )
        assert fighter.finish_rate == 0.8
    
    def test_finish_rate_no_wins(self):
        """Finish rate with no wins."""
        fighter = FighterFullData(fighter_id="f1", name="Test", wins=0)
        assert fighter.finish_rate == 0.0
    
    def test_is_injured_false(self):
        """Fighter without injuries."""
        fighter = FighterFullData(fighter_id="f1", name="Test")
        assert fighter.is_injured is False
    
    def test_is_injured_true(self):
        """Fighter with injuries."""
        fighter = FighterFullData(
            fighter_id="f1",
            name="Test",
            injuries=[{"type": "cut", "weeks": 2}]
        )
        assert fighter.is_injured is True


class TestFighterFullDataSerialization:
    """Test FighterFullData serialization."""
    
    def test_to_dict(self):
        """Serialize to dictionary."""
        fighter = FighterFullData(
            fighter_id="f1",
            name="Test Fighter",
            wins=10,
            boxing=80,
        )
        data = fighter.to_dict()
        assert data["fighter_id"] == "f1"
        assert data["name"] == "Test Fighter"
        assert data["wins"] == 10
        assert data["boxing"] == 80
    
    def test_from_dict(self):
        """Deserialize from dictionary."""
        data = {
            "fighter_id": "f1",
            "name": "Test Fighter",
            "wins": 15,
            "ko_wins": 8,
        }
        fighter = FighterFullData.from_dict(data)
        assert fighter.fighter_id == "f1"
        assert fighter.wins == 15
        assert fighter.ko_wins == 8
    
    def test_round_trip(self):
        """Serialize and deserialize."""
        original = FighterFullData(
            fighter_id="f1",
            name="Test",
            boxing=85,
            wins=20,
            traits=["Glass Cannon"],
        )
        data = original.to_dict()
        restored = FighterFullData.from_dict(data)
        assert restored.fighter_id == original.fighter_id
        assert restored.boxing == original.boxing
        assert restored.traits == original.traits


# ============================================================================
# FIGHT RESULT TESTS
# ============================================================================

class TestFightResultCreation:
    """Test FightResult creation."""
    
    def test_basic_creation(self):
        """Create fight result."""
        result = FightResult(
            fight_id="fight1",
            event_id="event1",
            event_name="DFC 100",
            week=10,
            fighter1_id="f1",
            fighter1_name="Fighter A",
            fighter2_id="f2",
            fighter2_name="Fighter B",
            winner_id="f1",
            winner_name="Fighter A",
            loser_id="f2",
            loser_name="Fighter B",
            method="KO",
            round_finished=2,
        )
        assert result.fight_id == "fight1"
        assert result.winner_id == "f1"
        assert result.method == "KO"


class TestFightResultProperties:
    """Test FightResult computed properties."""
    
    def test_is_finish_ko(self):
        """KO is a finish."""
        result = FightResult(
            fight_id="f1", event_id="e1", event_name="DFC", week=1,
            fighter1_id="a", fighter1_name="A", fighter2_id="b", fighter2_name="B",
            winner_id="a", winner_name="A", loser_id="b", loser_name="B",
            method="KO", round_finished=1,
        )
        assert result.is_finish is True
    
    def test_is_finish_tko(self):
        """TKO is a finish."""
        result = FightResult(
            fight_id="f1", event_id="e1", event_name="DFC", week=1,
            fighter1_id="a", fighter1_name="A", fighter2_id="b", fighter2_name="B",
            winner_id="a", winner_name="A", loser_id="b", loser_name="B",
            method="TKO", round_finished=3,
        )
        assert result.is_finish is True
    
    def test_is_finish_sub(self):
        """Submission is a finish."""
        result = FightResult(
            fight_id="f1", event_id="e1", event_name="DFC", week=1,
            fighter1_id="a", fighter1_name="A", fighter2_id="b", fighter2_name="B",
            winner_id="a", winner_name="A", loser_id="b", loser_name="B",
            method="SUB", round_finished=2,
        )
        assert result.is_finish is True
    
    def test_is_decision(self):
        """Decision is not a finish."""
        result = FightResult(
            fight_id="f1", event_id="e1", event_name="DFC", week=1,
            fighter1_id="a", fighter1_name="A", fighter2_id="b", fighter2_name="B",
            winner_id="a", winner_name="A", loser_id="b", loser_name="B",
            method="DEC", round_finished=3,
        )
        assert result.is_finish is False
        assert result.is_decision is True
    
    def test_headline_finish(self):
        """Headline for finish."""
        result = FightResult(
            fight_id="f1", event_id="e1", event_name="DFC", week=1,
            fighter1_id="a", fighter1_name="Fighter A", fighter2_id="b", fighter2_name="Fighter B",
            winner_id="a", winner_name="Fighter A", loser_id="b", loser_name="Fighter B",
            method="KO", round_finished=1,
        )
        headline = result.headline
        assert "Fighter A" in headline
        assert "Fighter B" in headline
        assert "KO" in headline
        assert "R1" in headline
    
    def test_headline_decision(self):
        """Headline for decision."""
        result = FightResult(
            fight_id="f1", event_id="e1", event_name="DFC", week=1,
            fighter1_id="a", fighter1_name="Fighter A", fighter2_id="b", fighter2_name="Fighter B",
            winner_id="a", winner_name="Fighter A", loser_id="b", loser_name="Fighter B",
            method="DEC", round_finished=3,
        )
        headline = result.headline
        assert "Decision" in headline


class TestFightResultSerialization:
    """Test FightResult serialization."""
    
    def test_to_dict(self):
        """Serialize to dictionary."""
        result = FightResult(
            fight_id="f1", event_id="e1", event_name="DFC", week=1,
            fighter1_id="a", fighter1_name="A", fighter2_id="b", fighter2_name="B",
            winner_id="a", winner_name="A", loser_id="b", loser_name="B",
            method="KO", round_finished=1,
            fighter1_strikes=50,
        )
        data = result.to_dict()
        assert data["fight_id"] == "f1"
        assert data["method"] == "KO"
        assert data["fighter1_strikes"] == 50
    
    def test_from_dict(self):
        """Deserialize from dictionary."""
        data = {
            "fight_id": "f1", "event_id": "e1", "event_name": "DFC", "week": 1,
            "fighter1_id": "a", "fighter1_name": "A", "fighter2_id": "b", "fighter2_name": "B",
            "winner_id": "a", "winner_name": "A", "loser_id": "b", "loser_name": "B",
            "method": "SUB", "round_finished": 2,
            "judge_scores": [[29, 28], [29, 28], [28, 29]],
        }
        result = FightResult.from_dict(data)
        assert result.method == "SUB"
        assert result.judge_scores[0] == (29, 28)


# ============================================================================
# COMPLETED EVENT TESTS
# ============================================================================

class TestCompletedEvent:
    """Test CompletedEvent class."""
    
    def test_creation(self):
        """Create event."""
        event = CompletedEvent(
            event_id="e1",
            event_name="DFC 100",
            week=10,
        )
        assert event.event_id == "e1"
        assert event.total_fights == 0
    
    def test_add_fight(self):
        """Add fights to event."""
        event = CompletedEvent(event_id="e1", event_name="DFC", week=1)
        fight = FightResult(
            fight_id="f1", event_id="e1", event_name="DFC", week=1,
            fighter1_id="a", fighter1_name="A", fighter2_id="b", fighter2_name="B",
            winner_id="a", winner_name="A", loser_id="b", loser_name="B",
            method="KO", round_finished=1,
        )
        event.add_fight(fight)
        assert event.total_fights == 1
    
    def test_knockouts_count(self):
        """Count knockouts."""
        event = CompletedEvent(event_id="e1", event_name="DFC", week=1)
        for method in ["KO", "TKO", "SUB", "DEC"]:
            fight = FightResult(
                fight_id=f"f_{method}", event_id="e1", event_name="DFC", week=1,
                fighter1_id="a", fighter1_name="A", fighter2_id="b", fighter2_name="B",
                winner_id="a", winner_name="A", loser_id="b", loser_name="B",
                method=method, round_finished=1,
            )
            event.add_fight(fight)
        assert event.knockouts == 2
        assert event.submissions == 1
        assert event.decisions == 1


# ============================================================================
# NEWS ITEM TESTS
# ============================================================================

class TestNewsItem:
    """Test NewsItem class."""
    
    def test_creation(self):
        """Create news item."""
        news = NewsItem(headline="Big Fight Announced!")
        assert news.headline == "Big Fight Announced!"
        assert news.category == "general"
    
    def test_icon(self):
        """Get icon for category."""
        assert NewsItem(headline="", category="fight").icon == "[FIGHT]"
        assert NewsItem(headline="", category="title").icon == "[TITLE]"
        assert NewsItem(headline="", category="injury").icon == "[INJ]"
    
    def test_serialization(self):
        """Serialize and deserialize."""
        news = NewsItem(headline="Test", category="fight", week=5)
        data = news.to_dict()
        restored = NewsItem.from_dict(data)
        assert restored.headline == "Test"
        assert restored.category == "fight"


# ============================================================================
# FIGHT OFFER TESTS
# ============================================================================

class TestFightOffer:
    """Test FightOffer class."""
    
    def test_creation(self):
        """Create fight offer."""
        offer = FightOffer(
            offer_id="o1",
            fighter_id="f1",
            fighter_name="Fighter A",
            opponent_id="f2",
            opponent_name="Fighter B",
            weight_class="Lightweight",
        )
        assert offer.offer_id == "o1"
        assert offer.opponent_name == "Fighter B"
    
    def test_short_notice(self):
        """Short notice detection."""
        short = FightOffer(
            offer_id="o1", fighter_id="f1", fighter_name="A",
            opponent_id="f2", opponent_name="B", weight_class="LW",
            weeks_notice=2,
        )
        long = FightOffer(
            offer_id="o2", fighter_id="f1", fighter_name="A",
            opponent_id="f2", opponent_name="B", weight_class="LW",
            weeks_notice=8,
        )
        assert short.is_short_notice is True
        assert long.is_short_notice is False
    
    def test_summary(self):
        """Generate summary."""
        offer = FightOffer(
            offer_id="o1", fighter_id="f1", fighter_name="A",
            opponent_id="f2", opponent_name="Fighter B", weight_class="LW",
            opponent_record="10-2",
            is_title_fight=True,
        )
        summary = offer.summary
        assert "Fighter B" in summary
        assert "10-2" in summary
        assert "[TITLE]" in summary
    
    def test_serialization(self):
        """Serialize and deserialize."""
        offer = FightOffer(
            offer_id="o1", fighter_id="f1", fighter_name="A",
            opponent_id="f2", opponent_name="B", weight_class="LW",
            purse=50000,
        )
        data = offer.to_dict()
        restored = FightOffer.from_dict(data)
        assert restored.purse == 50000
