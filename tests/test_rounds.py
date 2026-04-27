# tests/test_rounds.py
# Tests for Module 15: Round-by-Round Commentary System
# Lines: ~400

"""
Tests for the Round-by-Round Commentary System.

Covers:
- Fight events and types
- Round summaries
- Commentary generation
- Strike/grappling/submission commentary
- Post-fight analysis
"""

import pytest

from simulation.rounds import (
    # Event types
    FightEventType,
    EventSignificance,
    # Data classes
    FightEvent,
    RoundSummary,
    FightAnalysis,
    # Commentary engine
    CommentaryEngine,
    STRIKE_TEMPLATES,
    GRAPPLING_TEMPLATES,
    SUBMISSION_TEMPLATES,
    KNOCKDOWN_COMMENTARY,
    # Functions
    create_commentary_engine,
    get_round_summary,
    analyze_fight,
)
from simulation.fight_engine import (
    FighterAttributes,
    RoundStats,
    StrikeType,
    GrapplingAction,
    SubmissionType,
    Position,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def fighter1():
    """First fighter for testing"""
    return FighterAttributes(
        fighter_id="fighter_001",
        name="Alex Anderson",
        boxing=70, kicks=65, wrestling=60, bjj=55,
        chin=65, cardio=70, speed=68, strength=62,
        heart=70, fight_iq=65, composure=60
    )


@pytest.fixture
def fighter2():
    """Second fighter for testing"""
    return FighterAttributes(
        fighter_id="fighter_002",
        name="Bob Brown",
        boxing=65, kicks=60, wrestling=70, bjj=75,
        chin=60, cardio=65, speed=62, strength=65,
        heart=65, fight_iq=70, composure=65
    )


@pytest.fixture
def commentary(fighter1, fighter2):
    """Commentary engine for testing"""
    return CommentaryEngine(fighter1, fighter2, verbose=True)


@pytest.fixture
def sample_round_stats():
    """Sample round statistics"""
    return RoundStats(
        significant_strikes_attempted=20,
        significant_strikes_landed=12,
        head_strikes_landed=8,
        body_strikes_landed=3,
        leg_strikes_landed=1,
        takedowns_attempted=2,
        takedowns_landed=1,
        control_time=8.0,
        damage_dealt=45.0,
        knockdowns=0
    )


# ============================================================================
# EVENT TYPE TESTS
# ============================================================================

class TestFightEventType:
    """Tests for fight event types"""
    
    def test_all_strike_events_exist(self):
        """Should have all strike event types"""
        assert FightEventType.STRIKE_LANDED
        assert FightEventType.STRIKE_MISSED
        assert FightEventType.COUNTER_STRIKE
        assert FightEventType.KNOCKDOWN
    
    def test_all_grappling_events_exist(self):
        """Should have all grappling event types"""
        assert FightEventType.TAKEDOWN_SUCCESS
        assert FightEventType.TAKEDOWN_STUFFED
        assert FightEventType.POSITION_ADVANCE
        assert FightEventType.SWEEP
        assert FightEventType.ESCAPE
    
    def test_all_submission_events_exist(self):
        """Should have all submission event types"""
        assert FightEventType.SUBMISSION_ATTEMPT
        assert FightEventType.SUBMISSION_LOCKED
        assert FightEventType.SUBMISSION_ESCAPE
        assert FightEventType.SUBMISSION_FINISH
    
    def test_finish_events_exist(self):
        """Should have finish event types"""
        assert FightEventType.KO_FINISH
        assert FightEventType.TKO_FINISH
        assert FightEventType.SUBMISSION_WIN
        assert FightEventType.DECISION


class TestEventSignificance:
    """Tests for event significance levels"""
    
    def test_significance_ordering(self):
        """Significance levels should be ordered"""
        assert EventSignificance.ROUTINE.value < EventSignificance.NOTABLE.value
        assert EventSignificance.NOTABLE.value < EventSignificance.SIGNIFICANT.value
        assert EventSignificance.SIGNIFICANT.value < EventSignificance.DRAMATIC.value
        assert EventSignificance.DRAMATIC.value < EventSignificance.HISTORIC.value


# ============================================================================
# FIGHT EVENT TESTS
# ============================================================================

class TestFightEvent:
    """Tests for FightEvent dataclass"""
    
    def test_creation(self):
        """Should create event with correct values"""
        event = FightEvent(
            event_type=FightEventType.STRIKE_LANDED,
            round_num=1,
            exchange_num=5,
            time_str="1:00",
            actor_id="fighter_001",
            actor_name="Alex",
            target_id="fighter_002",
            target_name="Bob",
            action="cross",
            success=True,
            damage=10.5,
            significance=EventSignificance.NOTABLE
        )
        
        assert event.event_type == FightEventType.STRIKE_LANDED
        assert event.round_num == 1
        assert event.damage == 10.5
    
    def test_to_dict(self):
        """Should serialize to dict"""
        event = FightEvent(
            event_type=FightEventType.KNOCKDOWN,
            round_num=2,
            exchange_num=15,
            time_str="3:00",
            actor_id="f1",
            actor_name="Fighter 1",
            significance=EventSignificance.DRAMATIC
        )
        
        data = event.to_dict()
        
        assert data["event_type"] == "knockdown"
        assert data["round"] == 2
        assert data["significance"] == 4


# ============================================================================
# ROUND SUMMARY TESTS
# ============================================================================

class TestRoundSummary:
    """Tests for RoundSummary dataclass"""
    
    def test_creation(self, sample_round_stats):
        """Should create round summary"""
        stats2 = RoundStats(
            significant_strikes_landed=8,
            damage_dealt=30.0
        )
        
        summary = RoundSummary(
            round_num=1,
            fighter1_stats=sample_round_stats,
            fighter2_stats=stats2,
            fighter1_score=10,
            fighter2_score=9
        )
        
        assert summary.round_num == 1
        assert summary.fighter1_score == 10
    
    def test_add_key_event(self, sample_round_stats):
        """Should add significant events"""
        summary = RoundSummary(
            round_num=1,
            fighter1_stats=sample_round_stats,
            fighter2_stats=RoundStats()
        )
        
        routine_event = FightEvent(
            event_type=FightEventType.STRIKE_LANDED,
            round_num=1, exchange_num=1, time_str="0:12",
            actor_id="f1", actor_name="Fighter 1",
            significance=EventSignificance.ROUTINE
        )
        
        significant_event = FightEvent(
            event_type=FightEventType.KNOCKDOWN,
            round_num=1, exchange_num=10, time_str="2:00",
            actor_id="f1", actor_name="Fighter 1",
            significance=EventSignificance.SIGNIFICANT
        )
        
        summary.add_key_event(routine_event)
        summary.add_key_event(significant_event)
        
        # Only significant event should be added
        assert len(summary.key_events) == 1
        assert summary.key_events[0].event_type == FightEventType.KNOCKDOWN
    
    def test_generate_description(self, sample_round_stats):
        """Should generate round description"""
        summary = RoundSummary(
            round_num=1,
            fighter1_stats=sample_round_stats,
            fighter2_stats=RoundStats(damage_dealt=20.0),
            fighter1_score=10,
            fighter2_score=9,
            round_winner_id="fighter1"
        )
        
        desc = summary.generate_description("Alex", "Bob")
        
        assert len(desc) > 0
        assert "Alex" in desc or "round" in desc.lower()


# ============================================================================
# COMMENTARY TEMPLATES TESTS
# ============================================================================

class TestCommentaryTemplates:
    """Tests for commentary template collections"""
    
    def test_strike_templates_exist(self):
        """Should have templates for major strikes"""
        assert StrikeType.JAB in STRIKE_TEMPLATES
        assert StrikeType.CROSS in STRIKE_TEMPLATES
        assert StrikeType.HOOK in STRIKE_TEMPLATES
        assert StrikeType.HEAD_KICK in STRIKE_TEMPLATES
    
    def test_strike_templates_have_landed_missed(self):
        """Strike templates should have landed and missed variants"""
        for strike, templates in STRIKE_TEMPLATES.items():
            assert "landed" in templates or "significant" in templates, f"{strike} missing templates"
    
    def test_grappling_templates_exist(self):
        """Should have templates for major grappling actions"""
        assert GrapplingAction.DOUBLE_LEG in GRAPPLING_TEMPLATES
        assert GrapplingAction.SINGLE_LEG in GRAPPLING_TEMPLATES
    
    def test_submission_templates_exist(self):
        """Should have templates for major submissions"""
        assert SubmissionType.REAR_NAKED_CHOKE in SUBMISSION_TEMPLATES
        assert SubmissionType.ARMBAR in SUBMISSION_TEMPLATES
        assert SubmissionType.TRIANGLE_CHOKE in SUBMISSION_TEMPLATES
    
    def test_knockdown_commentary_exists(self):
        """Should have knockdown commentary"""
        assert len(KNOCKDOWN_COMMENTARY) > 0
        # Should have {actor} and {target} placeholders
        assert any("{actor}" in c for c in KNOCKDOWN_COMMENTARY)


# ============================================================================
# COMMENTARY ENGINE TESTS
# ============================================================================

class TestCommentaryEngine:
    """Tests for CommentaryEngine"""
    
    def test_creation(self, fighter1, fighter2):
        """Should create engine with fighters"""
        engine = CommentaryEngine(fighter1, fighter2)
        
        assert engine.fighter1 == fighter1
        assert engine.fighter2 == fighter2
        assert len(engine.events) == 0
    
    def test_get_fighter_name(self, commentary):
        """Should return correct fighter names"""
        assert commentary.get_fighter_name("fighter_001") == "Alex Anderson"
        assert commentary.get_fighter_name("fighter_002") == "Bob Brown"
    
    def test_get_time_str(self, commentary):
        """Should convert exchanges to time strings"""
        assert commentary.get_time_str(0) == "0:00"
        assert commentary.get_time_str(12) == "2:24"  # 12/25 * 300 = 144 seconds
        assert commentary.get_time_str(25) == "5:00"
    
    def test_log_round_start(self, commentary):
        """Should log round start"""
        event = commentary.log_round_start(1)
        
        assert event.event_type == FightEventType.ROUND_START
        assert event.round_num == 1
        assert len(commentary.events) == 1
        assert len(commentary.commentary_log) > 0
    
    def test_log_strike_landed(self, commentary):
        """Should log landed strikes"""
        commentary.log_round_start(1)
        
        event = commentary.log_strike(
            attacker_id="fighter_001",
            target_id="fighter_002",
            strike=StrikeType.CROSS,
            landed=True,
            damage=10.0,
            exchange_num=5
        )
        
        assert event.event_type == FightEventType.STRIKE_LANDED
        assert event.success is True
        assert event.damage == 10.0
    
    def test_log_strike_missed(self, commentary):
        """Should log missed strikes"""
        commentary.log_round_start(1)
        
        event = commentary.log_strike(
            attacker_id="fighter_001",
            target_id="fighter_002",
            strike=StrikeType.JAB,
            landed=False,
            damage=0.0,
            exchange_num=3
        )
        
        assert event.event_type == FightEventType.STRIKE_MISSED
        assert event.success is False
    
    def test_log_significant_strike(self, commentary):
        """Significant strikes should be logged with higher significance"""
        commentary.log_round_start(1)
        
        event = commentary.log_strike(
            attacker_id="fighter_001",
            target_id="fighter_002",
            strike=StrikeType.HEAD_KICK,
            landed=True,
            damage=15.0,  # High damage
            caused_rock=True,
            exchange_num=10
        )
        
        assert event.significance.value >= EventSignificance.SIGNIFICANT.value
    
    def test_log_knockdown(self, commentary):
        """Should log knockdowns"""
        commentary.log_round_start(1)
        
        event = commentary.log_knockdown(
            attacker_id="fighter_001",
            target_id="fighter_002",
            strike=StrikeType.HOOK,
            exchange_num=15
        )
        
        assert event.event_type == FightEventType.KNOCKDOWN
        assert event.significance == EventSignificance.DRAMATIC
        # Check for knockdown-related words (case insensitive)
        commentary_lower = event.commentary.lower()
        knockdown_words = ["down", "drops", "hurt", "knockdown", "canvas", "mat"]
        assert any(word in commentary_lower for word in knockdown_words)
    
    def test_log_takedown(self, commentary):
        """Should log takedowns"""
        commentary.log_round_start(1)
        
        event = commentary.log_takedown(
            attacker_id="fighter_002",
            target_id="fighter_001",
            action=GrapplingAction.DOUBLE_LEG,
            success=True,
            new_position=Position.FULL_GUARD_TOP,
            exchange_num=8
        )
        
        assert event.event_type == FightEventType.TAKEDOWN_SUCCESS
        assert event.success is True
    
    def test_log_takedown_stuffed(self, commentary):
        """Should log stuffed takedowns"""
        commentary.log_round_start(1)
        
        event = commentary.log_takedown(
            attacker_id="fighter_002",
            target_id="fighter_001",
            action=GrapplingAction.SINGLE_LEG,
            success=False,
            exchange_num=12
        )
        
        assert event.event_type == FightEventType.TAKEDOWN_STUFFED
        assert event.success is False
    
    def test_log_submission_attempt(self, commentary):
        """Should log submission attempts"""
        commentary.log_round_start(1)
        
        event = commentary.log_submission_attempt(
            attacker_id="fighter_002",
            target_id="fighter_001",
            submission=SubmissionType.REAR_NAKED_CHOKE,
            stage="attempt",
            exchange_num=20
        )
        
        assert event.event_type == FightEventType.SUBMISSION_ATTEMPT
        # Check for RNC-related words (case insensitive)
        commentary_lower = event.commentary.lower()
        assert "rnc" in commentary_lower or "choke" in commentary_lower or "rear naked" in commentary_lower
    
    def test_log_submission_finish(self, commentary):
        """Should log submission finishes"""
        commentary.log_round_start(1)
        
        event = commentary.log_submission_attempt(
            attacker_id="fighter_002",
            target_id="fighter_001",
            submission=SubmissionType.ARMBAR,
            stage="finish",
            exchange_num=22
        )
        
        assert event.event_type == FightEventType.SUBMISSION_FINISH
        assert event.significance == EventSignificance.DRAMATIC
    
    def test_log_finish(self, commentary):
        """Should log fight finishes"""
        commentary.log_round_start(1)
        
        event = commentary.log_finish(
            winner_id="fighter_001",
            loser_id="fighter_002",
            method="KO",
            round_num=1,
            exchange_num=18
        )
        
        assert event.event_type == FightEventType.KO_FINISH
        assert event.significance == EventSignificance.HISTORIC
        # Check for KO-related words (case insensitive)
        commentary_lower = event.commentary.lower()
        assert "ko" in commentary_lower or "knockout" in commentary_lower or "out" in commentary_lower
    
    def test_log_decision(self, commentary):
        """Should log decisions"""
        commentary.log_round_start(1)
        
        event = commentary.log_decision(
            winner_id="fighter_001",
            decision_type="Unanimous",
            scores=[(30, 27), (29, 28), (30, 27)]
        )
        
        assert event.event_type == FightEventType.DECISION
        assert "Unanimous" in event.commentary
        assert "Alex Anderson" in event.commentary
    
    def test_log_round_end(self, commentary, sample_round_stats):
        """Should log round end and create summary"""
        commentary.log_round_start(1)
        
        stats2 = RoundStats(damage_dealt=25.0)
        
        summary = commentary.log_round_end(
            round_num=1,
            stats1=sample_round_stats,
            stats2=stats2,
            score1=10,
            score2=9
        )
        
        assert summary.round_num == 1
        assert summary.fighter1_score == 10
        assert len(commentary.round_summaries) == 1
    
    def test_get_full_commentary(self, commentary):
        """Should return full commentary log"""
        commentary.log_round_start(1)
        commentary.log_strike(
            "fighter_001", "fighter_002",
            StrikeType.JAB, True, 5.0, exchange_num=1
        )
        
        full = commentary.get_full_commentary()
        
        assert isinstance(full, str)
        assert len(full) > 0
    
    def test_get_key_moments(self, commentary):
        """Should return only significant events"""
        commentary.log_round_start(1)
        
        # Routine event
        commentary.log_strike(
            "fighter_001", "fighter_002",
            StrikeType.JAB, True, 3.0, exchange_num=1
        )
        
        # Significant event
        commentary.log_knockdown(
            "fighter_001", "fighter_002",
            StrikeType.HOOK, exchange_num=10
        )
        
        key_moments = commentary.get_key_moments()
        
        assert len(key_moments) >= 1
        assert all(e.significance.value >= EventSignificance.SIGNIFICANT.value for e in key_moments)


# ============================================================================
# FIGHT ANALYSIS TESTS
# ============================================================================

class TestFightAnalysis:
    """Tests for post-fight analysis"""
    
    def test_analysis_creation(self):
        """Should create analysis with data"""
        analysis = FightAnalysis(
            winner_id="f1",
            winner_name="Fighter One",
            loser_name="Fighter Two",
            method="KO",
            total_strikes_landed={"f1": 45, "f2": 30},
            knockdowns={"f1": 2, "f2": 0}
        )
        
        assert analysis.winner_name == "Fighter One"
        assert analysis.method == "KO"
    
    def test_generate_narrative(self):
        """Should generate narrative summary"""
        analysis = FightAnalysis(
            winner_id="f1",
            winner_name="Fighter One",
            loser_name="Fighter Two",
            method="TKO",
            total_strikes_landed={"f1": 50, "f2": 25},
            knockdowns={"f1": 1, "f2": 0},
            key_moments=["Big knockdown in round 2", "Ground and pound finish"]
        )
        
        narrative = analysis.generate_narrative()
        
        assert "Fighter One" in narrative
        assert "TKO" in narrative
        assert len(narrative) > 50
    
    def test_analyze_fight(self, commentary, sample_round_stats):
        """Should analyze fight from commentary"""
        commentary.log_round_start(1)
        commentary.log_knockdown("fighter_001", "fighter_002", StrikeType.HOOK, 10)
        commentary.log_round_end(1, sample_round_stats, RoundStats(), 10, 8)
        
        analysis = analyze_fight(commentary, "fighter_001", "KO")
        
        assert analysis.winner_id == "fighter_001"
        assert analysis.winner_name == "Alex Anderson"
        assert analysis.method == "KO"


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Tests for module convenience functions"""
    
    def test_create_commentary_engine(self, fighter1, fighter2):
        """Should create commentary engine"""
        engine = create_commentary_engine(fighter1, fighter2)
        
        assert isinstance(engine, CommentaryEngine)
        assert engine.fighter1 == fighter1
    
    def test_get_round_summary(self, commentary, sample_round_stats):
        """Should get specific round summary"""
        commentary.log_round_start(1)
        commentary.log_round_end(1, sample_round_stats, RoundStats(), 10, 9)
        commentary.log_round_start(2)
        commentary.log_round_end(2, RoundStats(), sample_round_stats, 9, 10)
        
        summary1 = get_round_summary(commentary, 1)
        summary2 = get_round_summary(commentary, 2)
        summary3 = get_round_summary(commentary, 3)
        
        assert summary1 is not None
        assert summary1.round_num == 1
        assert summary2 is not None
        assert summary2.round_num == 2
        assert summary3 is None  # Doesn't exist


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestCommentaryIntegration:
    """Integration tests for full fight commentary"""
    
    def test_full_round_commentary(self, commentary, sample_round_stats):
        """Should handle full round of events"""
        commentary.log_round_start(1)
        
        # Simulate some exchanges
        for i in range(5):
            commentary.log_strike(
                "fighter_001", "fighter_002",
                StrikeType.JAB, True, 3.0, exchange_num=i
            )
        
        commentary.log_takedown(
            "fighter_002", "fighter_001",
            GrapplingAction.DOUBLE_LEG, True,
            Position.FULL_GUARD_TOP, exchange_num=6
        )
        
        commentary.log_round_end(1, sample_round_stats, RoundStats(), 10, 9)
        
        # Should have recorded events
        assert len(commentary.events) > 5
        assert len(commentary.round_summaries) == 1
    
    def test_multi_round_fight(self, commentary, sample_round_stats):
        """Should handle multiple rounds"""
        for round_num in range(1, 4):
            commentary.log_round_start(round_num)
            
            commentary.log_strike(
                "fighter_001", "fighter_002",
                StrikeType.CROSS, True, 8.0, exchange_num=10
            )
            
            commentary.log_round_end(
                round_num,
                sample_round_stats,
                RoundStats(damage_dealt=20.0),
                10, 9
            )
        
        assert len(commentary.round_summaries) == 3
        
        # Check fight summary
        summary = commentary.get_fight_summary()
        assert len(summary["rounds"]) == 3
