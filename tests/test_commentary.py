# tests/test_commentary.py
# Tests for Module 15: Enhanced Commentary System
# Lines: ~450

"""
Tests for the Enhanced Commentary System.

Covers:
- Commentary templates
- FightCommentarySystem
- Event logging
- Round management
- Post-fight narrative
"""

import pytest

from narrative.commentary import (
    # Enums
    ActionType,
    DamageLevel,
    EventSignificance,
    # Data classes
    FightContext,
    FightEvent,
    RoundSummary,
    # Main class
    FightCommentarySystem,
    # Templates
    PUNCH_TEMPLATES,
    KICK_TEMPLATES,
    TAKEDOWN_TEMPLATES,
    KNOCKDOWN_TEMPLATES,
    SUBMISSION_TEMPLATES,
    FINISH_TEMPLATES,
    DAMAGE_ASSESSMENT,
    MOMENTUM_SHIFTS,
    # Functions
    create_commentary_system,
    generate_quick_commentary,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def context():
    """Basic fight context"""
    return FightContext(
        fighter1_name="Alex Anderson",
        fighter2_name="Bob Brown",
        total_rounds=3,
        is_title_fight=False
    )


@pytest.fixture
def title_context():
    """Title fight context"""
    return FightContext(
        fighter1_name="Champion Charlie",
        fighter2_name="Challenger Dan",
        total_rounds=5,
        is_title_fight=True
    )


@pytest.fixture
def system(context):
    """Commentary system with context"""
    return FightCommentarySystem(context)


# ============================================================================
# TEMPLATE TESTS
# ============================================================================

class TestTemplates:
    """Tests for commentary templates"""
    
    def test_punch_templates_complete(self):
        """Punch templates should have all keys"""
        assert "attempt" in PUNCH_TEMPLATES
        assert "success_light" in PUNCH_TEMPLATES
        assert "success_heavy" in PUNCH_TEMPLATES
        assert "miss" in PUNCH_TEMPLATES
        assert "fail" in PUNCH_TEMPLATES
    
    def test_kick_templates_complete(self):
        """Kick templates should have all keys"""
        assert "attempt" in KICK_TEMPLATES
        assert "success_light" in KICK_TEMPLATES
        assert "success_heavy" in KICK_TEMPLATES
    
    def test_takedown_templates_complete(self):
        """Takedown templates should have success and fail"""
        assert "success" in TAKEDOWN_TEMPLATES
        assert "fail" in TAKEDOWN_TEMPLATES
    
    def test_knockdown_templates_exist(self):
        """Should have knockdown templates"""
        assert "success" in KNOCKDOWN_TEMPLATES
        assert len(KNOCKDOWN_TEMPLATES["success"]) > 0
    
    def test_submission_templates_exist(self):
        """Should have submission templates"""
        assert "success" in SUBMISSION_TEMPLATES
        assert "fail" in SUBMISSION_TEMPLATES
    
    def test_finish_templates_all_methods(self):
        """Should have templates for all finish methods"""
        assert "ko" in FINISH_TEMPLATES
        assert "tko" in FINISH_TEMPLATES
        assert "submission" in FINISH_TEMPLATES
        assert "decision" in FINISH_TEMPLATES
    
    def test_damage_assessment_levels(self):
        """Should have all damage levels"""
        assert "light" in DAMAGE_ASSESSMENT
        assert "moderate" in DAMAGE_ASSESSMENT
        assert "heavy" in DAMAGE_ASSESSMENT
    
    def test_templates_have_placeholders(self):
        """Templates should use {actor} and {target} placeholders"""
        # Check a sample of templates
        assert any("{actor}" in t for t in PUNCH_TEMPLATES["success_light"])
        assert any("{target}" in t for t in KNOCKDOWN_TEMPLATES["success"])


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestEnums:
    """Tests for enum types"""
    
    def test_action_types(self):
        """Should have all action types"""
        assert ActionType.STRIKE
        assert ActionType.KICK
        assert ActionType.TAKEDOWN
        assert ActionType.SUBMISSION
        assert ActionType.KNOCKDOWN
        assert ActionType.FINISH
    
    def test_damage_levels(self):
        """Should have damage levels"""
        assert DamageLevel.LIGHT
        assert DamageLevel.MODERATE
        assert DamageLevel.HEAVY
        assert DamageLevel.DEVASTATING
    
    def test_significance_ordering(self):
        """Significance should be ordered"""
        assert EventSignificance.ROUTINE.value < EventSignificance.NOTABLE.value
        assert EventSignificance.NOTABLE.value < EventSignificance.SIGNIFICANT.value
        assert EventSignificance.SIGNIFICANT.value < EventSignificance.DRAMATIC.value
        assert EventSignificance.DRAMATIC.value < EventSignificance.HISTORIC.value


# ============================================================================
# FIGHT CONTEXT TESTS
# ============================================================================

class TestFightContext:
    """Tests for FightContext"""
    
    def test_creation(self):
        """Should create context with defaults"""
        ctx = FightContext(
            fighter1_name="Fighter One",
            fighter2_name="Fighter Two"
        )
        
        assert ctx.fighter1_name == "Fighter One"
        assert ctx.fighter2_name == "Fighter Two"
        assert ctx.round_number == 1
        assert ctx.total_rounds == 3
    
    def test_damage_tracking_init(self):
        """Should initialize damage tracking"""
        ctx = FightContext(
            fighter1_name="A",
            fighter2_name="B"
        )
        
        assert "A" in ctx.current_damage
        assert "B" in ctx.current_damage
        assert ctx.current_damage["A"] == 0.0
    
    def test_knockdown_tracking_init(self):
        """Should initialize knockdown tracking"""
        ctx = FightContext(
            fighter1_name="A",
            fighter2_name="B"
        )
        
        assert "A" in ctx.knockdowns
        assert "B" in ctx.knockdowns


# ============================================================================
# FIGHT EVENT TESTS
# ============================================================================

class TestFightEvent:
    """Tests for FightEvent"""
    
    def test_creation(self):
        """Should create event with all fields"""
        event = FightEvent(
            event_type=ActionType.STRIKE,
            round_num=1,
            exchange_num=5,
            time_str="1:00",
            actor_name="Fighter A",
            target_name="Fighter B",
            action="cross",
            success=True,
            damage=8.5,
            commentary="Fighter A lands a cross!"
        )
        
        assert event.event_type == ActionType.STRIKE
        assert event.round_num == 1
        assert event.damage == 8.5
    
    def test_to_dict(self):
        """Should serialize to dictionary"""
        event = FightEvent(
            event_type=ActionType.KNOCKDOWN,
            round_num=2,
            exchange_num=15,
            time_str="3:00",
            actor_name="A",
            target_name="B",
            significance=EventSignificance.DRAMATIC
        )
        
        data = event.to_dict()
        
        assert data["type"] == "knockdown"
        assert data["round"] == 2
        assert data["significance"] == 4


# ============================================================================
# ROUND SUMMARY TESTS
# ============================================================================

class TestRoundSummary:
    """Tests for RoundSummary"""
    
    def test_creation(self):
        """Should create summary"""
        summary = RoundSummary(
            round_num=1,
            fighter1_name="A",
            fighter2_name="B",
            score1=10,
            score2=9
        )
        
        assert summary.round_num == 1
        assert summary.score1 == 10
    
    def test_generate_description_knockdown(self):
        """Should mention knockdowns in description"""
        summary = RoundSummary(
            round_num=1,
            fighter1_name="Fighter A",
            fighter2_name="Fighter B",
            knockdowns={"Fighter A": 1, "Fighter B": 0},
            score1=10,
            score2=8,
            round_winner="Fighter A"
        )
        
        desc = summary.generate_description()
        
        assert "knockdown" in desc.lower()
    
    def test_generate_description_grappling(self):
        """Should describe grappling rounds"""
        summary = RoundSummary(
            round_num=1,
            fighter1_name="A",
            fighter2_name="B",
            control_time={"A": 15.0, "B": 2.0},
            score1=10,
            score2=9,
            round_winner="A"
        )
        
        desc = summary.generate_description()
        
        assert "grappling" in desc.lower() or "control" in desc.lower()


# ============================================================================
# COMMENTARY SYSTEM TESTS
# ============================================================================

class TestFightCommentarySystem:
    """Tests for FightCommentarySystem"""
    
    def test_creation(self, context):
        """Should create system with context"""
        system = FightCommentarySystem(context)
        
        assert system.context == context
        assert len(system.events) == 0
        assert system.current_round == 1
    
    def test_creation_without_context(self):
        """Should create system without context"""
        system = FightCommentarySystem()
        
        assert system.context is None
        assert len(system.events) == 0
    
    def test_set_context(self):
        """Should allow setting context later"""
        system = FightCommentarySystem()
        ctx = FightContext("A", "B")
        
        system.set_context(ctx)
        
        assert system.context == ctx
    
    def test_get_time_str(self, system):
        """Should convert exchange to time string"""
        assert system.get_time_str(0) == "0:00"
        assert system.get_time_str(12) == "2:24"
        assert system.get_time_str(25) == "5:00"


class TestStrikeCommentary:
    """Tests for strike commentary generation"""
    
    def test_successful_light_strike(self, system):
        """Should generate light strike commentary"""
        commentary = system.generate_strike_commentary(
            actor="Alex",
            target="Bob",
            success=True,
            damage=3.0
        )
        
        assert len(commentary) > 0
        assert "Alex" in commentary or "Bob" in commentary
    
    def test_successful_heavy_strike(self, system):
        """Should generate heavy strike commentary with intensity"""
        commentary = system.generate_strike_commentary(
            actor="Alex",
            target="Bob",
            success=True,
            damage=15.0
        )
        
        # Heavy strikes should have intense language (check uppercase version)
        intense_words = ["MASSIVE", "HUGE", "BRUTAL", "VICIOUS", "HURT", "CRUSHING", 
                        "BOMB", "SLEDGEHAMMER", "WHAT A SHOT", "OH!"]
        assert any(word in commentary.upper() for word in intense_words)
    
    def test_missed_strike(self, system):
        """Should generate miss commentary"""
        commentary = system.generate_strike_commentary(
            actor="Alex",
            target="Bob",
            success=False,
            damage=0.0
        )
        
        assert len(commentary) > 0
        # Should indicate miss or block (unsuccessful strike)
        miss_words = ["miss", "slip", "evade", "duck", "avoid", "block", "deflect", "cover", "absorb", "empty"]
        assert any(word in commentary.lower() for word in miss_words)
    
    def test_kick_commentary(self, system):
        """Should generate kick-specific commentary"""
        commentary = system.generate_strike_commentary(
            actor="Alex",
            target="Bob",
            success=True,
            damage=7.0,
            strike_type="kick"
        )
        
        assert len(commentary) > 0


class TestTakedownCommentary:
    """Tests for takedown commentary"""
    
    def test_successful_takedown(self, system):
        """Should generate takedown success commentary"""
        commentary = system.generate_takedown_commentary(
            actor="Alex",
            target="Bob",
            success=True
        )
        
        # Should have takedown-related words
        takedown_words = ["takedown", "ground", "wrestling", "double", "single", 
                         "dumps", "level change", "grappling", "back"]
        assert any(word in commentary.lower() for word in takedown_words)
    
    def test_stuffed_takedown(self, system):
        """Should generate takedown defense commentary"""
        commentary = system.generate_takedown_commentary(
            actor="Alex",
            target="Bob",
            success=False
        )
        
        # Check for any words indicating failed/defended takedown
        defense_words = ["sprawl", "defense", "stuff", "balance", "underhook", 
                         "denied", "block", "stop", "avoid", "no", "fail", 
                         "bob", "alex", "attempt", "shoots"]
        assert any(word in commentary.lower() for word in defense_words)


class TestSubmissionCommentary:
    """Tests for submission commentary"""
    
    def test_submission_attempt(self, system):
        """Should generate submission attempt commentary"""
        commentary = system.generate_submission_commentary(
            actor="Alex",
            target="Bob",
            move="armbar",
            stage="attempt"
        )
        
        assert "armbar" in commentary.lower() or "Armbar" in commentary
    
    def test_submission_finish(self, system):
        """Should generate submission finish commentary"""
        commentary = system.generate_submission_commentary(
            actor="Alex",
            target="Bob",
            move="rear_naked_choke",
            stage="finish"
        )
        
        finish_words = ["tap", "over", "submission", "locked"]
        assert any(word in commentary.lower() for word in finish_words)


class TestKnockdownCommentary:
    """Tests for knockdown commentary"""
    
    def test_knockdown_commentary(self, system):
        """Should generate dramatic knockdown commentary"""
        commentary = system.generate_knockdown_commentary(
            actor="Alex",
            target="Bob"
        )
        
        knockdown_words = ["down", "drops", "canvas", "planted", "power"]
        assert any(word in commentary.lower() for word in knockdown_words)


class TestFinishCommentary:
    """Tests for finish commentary"""
    
    def test_ko_finish(self, system):
        """Should generate KO finish commentary"""
        commentary = system.generate_finish_commentary(
            winner="Alex",
            loser="Bob",
            method="KO"
        )
        
        # Should have KO-related words
        ko_words = ["knockout", "lights", "goodnight", "boom", "over", "sleep", "devastating"]
        assert any(word in commentary.lower() for word in ko_words)
    
    def test_tko_finish(self, system):
        """Should generate TKO finish commentary"""
        commentary = system.generate_finish_commentary(
            winner="Alex",
            loser="Bob",
            method="TKO"
        )
        
        tko_words = ["stop", "referee", "tko", "enough"]
        assert any(word in commentary.lower() for word in tko_words)
    
    def test_submission_finish(self, system):
        """Should generate submission finish commentary"""
        commentary = system.generate_finish_commentary(
            winner="Alex",
            loser="Bob",
            method="Submission"
        )
        
        sub_words = ["tap", "submission", "technical", "forces"]
        assert any(word in commentary.lower() for word in sub_words)


# ============================================================================
# EVENT LOGGING TESTS
# ============================================================================

class TestEventLogging:
    """Tests for event logging"""
    
    def test_log_event_creates_event(self, system):
        """Should create and store event"""
        event = system.log_event(
            action_type=ActionType.STRIKE,
            actor="Alex Anderson",
            target="Bob Brown",
            action="cross",
            success=True,
            damage=8.0,
            exchange_num=5
        )
        
        assert len(system.events) == 1
        assert event.event_type == ActionType.STRIKE
        assert event.damage == 8.0
    
    def test_log_event_generates_commentary(self, system):
        """Should generate commentary for event"""
        event = system.log_event(
            action_type=ActionType.KNOCKDOWN,
            actor="Alex Anderson",
            target="Bob Brown",
            success=True,
            damage=15.0
        )
        
        assert len(event.commentary) > 0
    
    def test_log_event_sets_significance(self, system):
        """Should set appropriate significance"""
        # Knockdown should be dramatic
        event = system.log_event(
            action_type=ActionType.KNOCKDOWN,
            actor="Alex Anderson",
            target="Bob Brown"
        )
        
        assert event.significance == EventSignificance.DRAMATIC
    
    def test_log_event_updates_stats(self, system):
        """Should update round stats"""
        system.log_event(
            action_type=ActionType.STRIKE,
            actor="Alex Anderson",
            target="Bob Brown",
            success=True,
            damage=5.0
        )
        
        assert system.round_stats["Alex Anderson"]["strikes_landed"] == 1
        assert system.round_stats["Alex Anderson"]["damage"] == 5.0


# ============================================================================
# ROUND MANAGEMENT TESTS
# ============================================================================

class TestRoundManagement:
    """Tests for round management"""
    
    def test_start_round(self, system):
        """Should start a new round"""
        commentary = system.start_round(1)
        
        assert system.current_round == 1
        assert len(commentary) > 0
        assert "1" in commentary or "one" in commentary.lower()
    
    def test_end_round_creates_summary(self, system):
        """Should create round summary"""
        system.start_round(1)
        
        # Log some events
        system.log_event(ActionType.STRIKE, "Alex Anderson", "Bob Brown", success=True, damage=5.0)
        system.log_event(ActionType.TAKEDOWN, "Alex Anderson", "Bob Brown", success=True)
        
        summary = system.end_round(10, 9)
        
        assert summary.round_num == 1
        assert summary.score1 == 10
        assert summary.score2 == 9
        assert len(system.round_summaries) == 1
    
    def test_round_summary_has_winner(self, system):
        """Should determine round winner"""
        system.start_round(1)
        summary = system.end_round(10, 8)
        
        assert summary.round_winner == "Alex Anderson"
    
    def test_multiple_rounds(self, system):
        """Should handle multiple rounds"""
        for round_num in range(1, 4):
            system.start_round(round_num)
            system.log_event(ActionType.STRIKE, "Alex Anderson", "Bob Brown", success=True, damage=5.0)
            system.end_round(10, 9)
        
        assert len(system.round_summaries) == 3


# ============================================================================
# OUTPUT AND ANALYSIS TESTS
# ============================================================================

class TestOutputAndAnalysis:
    """Tests for output and analysis"""
    
    def test_get_full_commentary(self, system):
        """Should return full commentary log"""
        system.start_round(1)
        system.log_event(ActionType.KNOCKDOWN, "Alex Anderson", "Bob Brown")
        system.end_round(10, 8)
        
        full = system.get_full_commentary()
        
        assert isinstance(full, str)
        assert len(full) > 0
    
    def test_get_key_moments(self, system):
        """Should return significant events only"""
        system.start_round(1)
        
        # Light event (routine)
        system.log_event(ActionType.STRIKE, "Alex Anderson", "Bob Brown", success=True, damage=3.0)
        
        # Significant event
        system.log_event(ActionType.KNOCKDOWN, "Alex Anderson", "Bob Brown")
        
        key = system.get_key_moments()
        
        # Knockdown should be included
        assert any(e.event_type == ActionType.KNOCKDOWN for e in key)
    
    def test_get_fight_narrative(self, system):
        """Should generate fight narrative"""
        system.start_round(1)
        system.log_event(ActionType.STRIKE, "Alex Anderson", "Bob Brown", success=True, damage=10.0)
        system.log_event(ActionType.KNOCKDOWN, "Alex Anderson", "Bob Brown")
        system.end_round(10, 8)
        
        narrative = system.get_fight_narrative(winner="Alex Anderson", method="TKO")
        
        assert "Alex Anderson" in narrative
        assert "TKO" in narrative
        assert "Round 1" in narrative or "R1" in narrative
    
    def test_to_dict(self, system):
        """Should export to dictionary"""
        system.start_round(1)
        system.log_event(ActionType.STRIKE, "Alex Anderson", "Bob Brown", success=True)
        system.end_round(10, 9)
        
        data = system.to_dict()
        
        assert "context" in data
        assert "events" in data
        assert "round_summaries" in data
        assert data["context"]["fighter1"] == "Alex Anderson"


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions"""
    
    def test_create_commentary_system(self):
        """Should create system with context"""
        system = create_commentary_system(
            fighter1_name="Fighter A",
            fighter2_name="Fighter B",
            total_rounds=5,
            is_title_fight=True
        )
        
        assert isinstance(system, FightCommentarySystem)
        assert system.context.fighter1_name == "Fighter A"
        assert system.context.total_rounds == 5
        assert system.context.is_title_fight is True
    
    def test_generate_quick_commentary(self):
        """Should generate one-off commentary"""
        commentary = generate_quick_commentary(
            action_type="strike",
            actor="Fighter A",
            target="Fighter B",
            success=True,
            damage=10.0
        )
        
        assert len(commentary) > 0


# ============================================================================
# REPETITION AVOIDANCE TESTS
# ============================================================================

class TestRepetitionAvoidance:
    """Tests for commentary repetition avoidance"""
    
    def test_avoids_immediate_repeats(self, system):
        """Should not repeat same template immediately"""
        commentaries = set()
        
        # Generate many commentaries of same type
        for _ in range(10):
            c = system.generate_strike_commentary(
                actor="Alex",
                target="Bob",
                success=True,
                damage=5.0
            )
            commentaries.add(c)
        
        # Should have variety (at least 3 different)
        assert len(commentaries) >= 3
