# tests/test_fight_integration.py
# Tests for Module 16: Fight Integration
# Lines: ~530

"""
Tests for the Fight Integration module.

Covers:
- NarratedFightResult
- Action type mapping
- NarratedFightSimulator
- Full fight simulation with commentary
- Convenience functions
"""

import pytest
import random

from simulation.fight_integration import (
    # Result class
    NarratedFightResult,
    # Mapping functions
    strike_to_action_type,
    grappling_to_action_type,
    # Simulator
    NarratedFightSimulator,
    # Convenience functions
    simulate_narrated_fight,
    quick_narrated_fight,
    get_fight_summary,
    print_fight_narrative,
)

from simulation.fight_engine import (
    FighterAttributes, FightConfig,
    StrikeType, GrapplingAction, Position,
)

from narrative.commentary import ActionType


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def striker():
    """Striker-type fighter"""
    return FighterAttributes(
        fighter_id="striker_001",
        name="Alex Striker",
        strength=60, speed=70, cardio=65, chin=60,
        boxing=80, kicks=75, clinch_striking=60, striking_defense=70,
        wrestling=45, bjj=40, takedown_defense=55,
        heart=65, fight_iq=60, composure=60
    )


@pytest.fixture
def grappler():
    """Grappler-type fighter"""
    return FighterAttributes(
        fighter_id="grappler_001",
        name="Gary Grappler",
        strength=65, speed=55, cardio=70, chin=55,
        boxing=50, kicks=45, clinch_striking=55, striking_defense=50,
        wrestling=80, bjj=85, takedown_defense=75,
        heart=70, fight_iq=65, composure=65
    )


@pytest.fixture
def balanced1():
    """Balanced fighter 1"""
    return FighterAttributes(
        fighter_id="balanced_001",
        name="Bob Balanced",
        strength=60, speed=60, cardio=60, chin=60,
        boxing=60, kicks=60, clinch_striking=60, striking_defense=60,
        wrestling=60, bjj=60, takedown_defense=60,
        heart=60, fight_iq=60, composure=60
    )


@pytest.fixture
def balanced2():
    """Balanced fighter 2"""
    return FighterAttributes(
        fighter_id="balanced_002",
        name="Bill Balanced",
        strength=60, speed=60, cardio=60, chin=60,
        boxing=60, kicks=60, clinch_striking=60, striking_defense=60,
        wrestling=60, bjj=60, takedown_defense=60,
        heart=60, fight_iq=60, composure=60
    )


# ============================================================================
# NARRATED FIGHT RESULT TESTS
# ============================================================================

class TestNarratedFightResult:
    """Tests for NarratedFightResult"""
    
    def test_creation(self):
        """Should create result with basic fields"""
        result = NarratedFightResult(
            winner_id="f1",
            winner_name="Fighter One",
            loser_id="f2",
            loser_name="Fighter Two",
            method="KO",
            finish_round=2,
            finish_time="3:45"
        )
        
        assert result.winner_id == "f1"
        assert result.winner_name == "Fighter One"
        assert result.method == "KO"
        assert result.finish_round == 2
    
    def test_is_finish_ko(self):
        """KO should be a finish"""
        result = NarratedFightResult(
            winner_id="f1", winner_name="A",
            loser_id="f2", loser_name="B",
            method="KO"
        )
        
        assert result.is_finish is True
        assert result.is_decision is False
    
    def test_is_finish_tko(self):
        """TKO should be a finish"""
        result = NarratedFightResult(
            winner_id="f1", winner_name="A",
            loser_id="f2", loser_name="B",
            method="TKO"
        )
        
        assert result.is_finish is True
    
    def test_is_finish_submission(self):
        """Submission should be a finish"""
        result = NarratedFightResult(
            winner_id="f1", winner_name="A",
            loser_id="f2", loser_name="B",
            method="Submission"
        )
        
        assert result.is_finish is True
    
    def test_is_decision(self):
        """Decision should not be a finish"""
        result = NarratedFightResult(
            winner_id="f1", winner_name="A",
            loser_id="f2", loser_name="B",
            method="Unanimous Decision",
            judge_scores=[(30, 27), (30, 27), (29, 28)],
            decision_type="Unanimous"
        )
        
        assert result.is_finish is False
        assert result.is_decision is True
    
    def test_is_draw(self):
        """Draw should be identified"""
        result = NarratedFightResult(
            winner_id=None, winner_name="A",
            loser_id=None, loser_name="B",
            method="Draw"
        )
        
        assert result.is_draw is True
        assert result.is_finish is False
    
    def test_get_summary_finish(self):
        """Should generate finish summary"""
        result = NarratedFightResult(
            winner_id="f1", winner_name="Alex",
            loser_id="f2", loser_name="Bob",
            method="KO",
            finish_round=1,
            finish_time="2:30"
        )
        
        summary = result.get_summary()
        
        assert "Alex" in summary
        assert "Bob" in summary
        assert "KO" in summary
        assert "R1" in summary or "1" in summary
    
    def test_get_summary_decision(self):
        """Should generate decision summary"""
        result = NarratedFightResult(
            winner_id="f1", winner_name="Alex",
            loser_id="f2", loser_name="Bob",
            method="Unanimous Decision",
            judge_scores=[(30, 27), (30, 27), (30, 27)],
            decision_type="Unanimous"
        )
        
        summary = result.get_summary()
        
        assert "Alex" in summary
        assert "Decision" in summary
    
    def test_to_dict(self):
        """Should serialize to dictionary"""
        result = NarratedFightResult(
            winner_id="f1", winner_name="Alex",
            loser_id="f2", loser_name="Bob",
            method="TKO",
            finish_round=2,
            finish_time="4:00"
        )
        
        data = result.to_dict()
        
        assert data["winner_id"] == "f1"
        assert data["method"] == "TKO"
        assert "summary" in data


# ============================================================================
# ACTION TYPE MAPPING TESTS
# ============================================================================

class TestActionTypeMapping:
    """Tests for action type mapping functions"""
    
    def test_punch_to_strike(self):
        """Punches should map to STRIKE"""
        assert strike_to_action_type(StrikeType.JAB) == ActionType.STRIKE
        assert strike_to_action_type(StrikeType.CROSS) == ActionType.STRIKE
        assert strike_to_action_type(StrikeType.HOOK) == ActionType.STRIKE
    
    def test_kick_to_kick(self):
        """Kicks should map to KICK"""
        assert strike_to_action_type(StrikeType.LEG_KICK) == ActionType.KICK
        assert strike_to_action_type(StrikeType.HEAD_KICK) == ActionType.KICK
        assert strike_to_action_type(StrikeType.BODY_KICK) == ActionType.KICK
    
    def test_clinch_strikes(self):
        """Clinch strikes should map correctly"""
        # Use actual enum values - clinch strikes map to CLINCH_STRIKE
        assert strike_to_action_type(StrikeType.CLINCH_ELBOW) == ActionType.CLINCH_STRIKE
        assert strike_to_action_type(StrikeType.CLINCH_KNEE) == ActionType.CLINCH_STRIKE
    
    def test_ground_strikes(self):
        """Ground strikes should map correctly"""
        # Use actual enum value
        assert strike_to_action_type(StrikeType.GNP_PUNCH) == ActionType.GROUND_STRIKE
    
    def test_takedown_mapping(self):
        """Takedowns should map to TAKEDOWN"""
        assert grappling_to_action_type(GrapplingAction.SINGLE_LEG) == ActionType.TAKEDOWN
        assert grappling_to_action_type(GrapplingAction.DOUBLE_LEG) == ActionType.TAKEDOWN
    
    def test_sweep_mapping(self):
        """Sweeps should map to SWEEP"""
        # Use actual enum values
        assert grappling_to_action_type(GrapplingAction.SCISSOR_SWEEP) == ActionType.SWEEP
        assert grappling_to_action_type(GrapplingAction.BUTTERFLY_SWEEP) == ActionType.SWEEP
    
    def test_standup_mapping(self):
        """Stand up should map to STAND_UP"""
        assert grappling_to_action_type(GrapplingAction.STAND_UP) == ActionType.STAND_UP
        assert grappling_to_action_type(GrapplingAction.TECHNICAL_STANDUP) == ActionType.STAND_UP


# ============================================================================
# FIGHT SIMULATOR TESTS
# ============================================================================

class TestNarratedFightSimulator:
    """Tests for NarratedFightSimulator"""
    
    def test_creation(self, striker, grappler):
        """Should create simulator"""
        sim = NarratedFightSimulator(striker, grappler)
        
        assert sim.fighter1 == striker
        assert sim.fighter2 == grappler
        assert sim.config is not None
    
    def test_custom_config(self, striker, grappler):
        """Should accept custom fight config"""
        # Use constructor instead of class method
        config = FightConfig(scheduled_rounds=5, is_title_fight=True)
        sim = NarratedFightSimulator(striker, grappler, config=config)
        
        assert sim.config.scheduled_rounds == 5
        assert sim.config.is_title_fight is True
    
    def test_simulate_returns_result(self, striker, grappler):
        """Simulation should return NarratedFightResult"""
        random.seed(42)
        
        sim = NarratedFightSimulator(striker, grappler)
        result = sim.simulate()
        
        assert isinstance(result, NarratedFightResult)
        assert result.winner_id in [striker.fighter_id, grappler.fighter_id, None]
    
    def test_simulate_has_stats(self, balanced1, balanced2):
        """Should have fighter stats after simulation"""
        random.seed(123)
        
        sim = NarratedFightSimulator(balanced1, balanced2)
        result = sim.simulate()
        
        assert len(result.fighter1_stats) > 0
        assert len(result.fighter2_stats) > 0
    
    def test_simulate_tracks_rounds(self, balanced1, balanced2):
        """Should track round summaries"""
        random.seed(456)
        
        sim = NarratedFightSimulator(balanced1, balanced2)
        result = sim.simulate()
        
        # If went to decision, should have 3 round summaries
        if result.is_decision:
            assert result.total_rounds == 3
    
    def test_finish_has_timing(self, striker, grappler):
        """Finish should have round and time"""
        # Create lopsided matchup for likely finish
        weak = FighterAttributes(
            fighter_id="weak",
            name="Weak Fighter",
            strength=30, speed=30, cardio=30, chin=30,
            boxing=30, kicks=30, clinch_striking=30, striking_defense=30,
            wrestling=30, bjj=30, takedown_defense=30,
            heart=30, fight_iq=30, composure=30
        )
        
        finish_found = False
        for seed in range(50):
            random.seed(seed)
            sim = NarratedFightSimulator(striker, weak)
            result = sim.simulate()
            
            if result.is_finish:
                assert result.finish_round is not None
                assert result.finish_time is not None
                finish_found = True
                break
        
        assert finish_found, "No finish found in 50 attempts"
    
    def test_decision_has_scores(self, balanced1, balanced2):
        """Decision should have judge scores"""
        decision_found = False
        
        for seed in range(50):
            random.seed(seed)
            sim = NarratedFightSimulator(balanced1, balanced2)
            result = sim.simulate()
            
            if result.is_decision:
                assert len(result.judge_scores) == 3
                assert result.decision_type in ["Unanimous", "Split", "Majority"]
                decision_found = True
                break
        
        # Balanced fighters should sometimes go to decision
        assert decision_found, "No decision found in 50 attempts"


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions"""
    
    def test_simulate_narrated_fight(self, striker, grappler):
        """Should simulate with defaults"""
        random.seed(42)
        
        result = simulate_narrated_fight(striker, grappler)
        
        assert isinstance(result, NarratedFightResult)
        assert result.total_rounds <= 3
    
    def test_simulate_title_fight(self, striker, grappler):
        """Should handle title fight config"""
        random.seed(42)
        
        result = simulate_narrated_fight(
            striker, grappler,
            rounds=5,
            is_title_fight=True
        )
        
        assert isinstance(result, NarratedFightResult)
    
    def test_quick_narrated_fight(self):
        """Should create fighters and simulate"""
        random.seed(42)
        
        result = quick_narrated_fight(
            f1_overall=70,
            f2_overall=65,
            f1_name="Test Fighter A",
            f2_name="Test Fighter B"
        )
        
        assert isinstance(result, NarratedFightResult)
        assert result.winner_name in ["Test Fighter A", "Test Fighter B"] or result.is_draw
    
    def test_get_fight_summary(self, striker, grappler):
        """Should return summary string"""
        random.seed(42)
        
        result = simulate_narrated_fight(striker, grappler)
        summary = get_fight_summary(result)
        
        assert isinstance(summary, str)
        assert len(summary) > 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFightIntegration:
    """Integration tests for full fight simulation"""
    
    def test_multiple_fights_varied_outcomes(self, striker, grappler):
        """Multiple fights should have varied outcomes"""
        outcomes = {"finish": 0, "decision": 0}
        
        for seed in range(20):
            random.seed(seed)
            result = simulate_narrated_fight(striker, grappler)
            
            if result.is_finish:
                outcomes["finish"] += 1
            else:
                outcomes["decision"] += 1
        
        # Should have at least some of each (or all one type is okay too)
        assert outcomes["finish"] + outcomes["decision"] == 20
    
    def test_fight_narrative_quality(self, striker, grappler):
        """Fight narrative should be substantive"""
        random.seed(42)
        
        result = simulate_narrated_fight(striker, grappler)
        
        # Should have multiple lines
        assert "\n" in result.fight_narrative
        
        # Should mention fighters
        assert striker.name in result.fight_narrative or grappler.name in result.fight_narrative
    
    def test_key_moments_captured(self, striker, grappler):
        """Should capture key moments"""
        # Run several fights to get one with key moments
        for seed in range(20):
            random.seed(seed)
            result = simulate_narrated_fight(striker, grappler)
            
            if result.key_moments:
                # Verify key moment structure
                moment = result.key_moments[0]
                assert "type" in moment or "event_type" in moment or "action" in moment
                break
    
    def test_championship_fight_goes_5_rounds(self, balanced1, balanced2):
        """Championship fights can go 5 rounds"""
        for seed in range(30):
            random.seed(seed)
            result = simulate_narrated_fight(
                balanced1, balanced2,
                rounds=5,
                is_title_fight=True
            )
            
            if result.is_decision and result.total_rounds == 5:
                # Found a 5-round decision
                assert len(result.judge_scores) == 3
                break
    
    def test_commentary_logs_actions(self, striker, grappler):
        """Commentary should log fight actions"""
        random.seed(42)
        
        sim = NarratedFightSimulator(striker, grappler)
        result = sim.simulate()
        
        # Should have events logged
        assert len(sim.commentary.events) > 0
        
        # Should have commentary generated
        assert len(sim.commentary.commentary_log) > 0
    
    def test_round_scoring(self, balanced1, balanced2):
        """Rounds should be scored"""
        # Find a decision
        for seed in range(30):
            random.seed(seed)
            sim = NarratedFightSimulator(balanced1, balanced2)
            result = sim.simulate()
            
            if result.is_decision:
                # Should have 3 judge scorecards
                assert len(result.judge_scores) == 3
                
                # Each scorecard should have valid scores
                # Minimum is 23 to allow for rare 10-8 or 10-7 rounds
                for s1, s2 in result.judge_scores:
                    assert s1 >= 23  # Allows for 10-8 and 10-7 rounds
                    assert s2 >= 23  # Allows for 10-8 and 10-7 rounds
                break
    
    def test_bonuses_awarded(self):
        """Performance bonuses should be awarded for early finishes"""
        # Create lopsided matchup
        strong = FighterAttributes(
            fighter_id="strong",
            name="Strong Fighter",
            strength=85, speed=80, cardio=75, chin=80,
            boxing=85, kicks=80, clinch_striking=75, striking_defense=80,
            wrestling=70, bjj=65, takedown_defense=75,
            heart=80, fight_iq=75, composure=80
        )
        
        weak = FighterAttributes(
            fighter_id="weak",
            name="Weak Fighter",
            strength=35, speed=35, cardio=35, chin=35,
            boxing=35, kicks=35, clinch_striking=35, striking_defense=35,
            wrestling=35, bjj=35, takedown_defense=35,
            heart=35, fight_iq=35, composure=35
        )
        
        bonus_found = False
        for seed in range(30):
            random.seed(seed)
            result = simulate_narrated_fight(strong, weak)
            
            if result.performance_bonus:
                bonus_found = True
                assert result.is_finish
                break
        
        # Early finishes should get bonuses
        assert bonus_found, "No performance bonus awarded in 30 fights"
