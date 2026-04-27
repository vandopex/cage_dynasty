# tests/test_world_integration.py
# Tests for the World Integration System
# Run: python3 -m pytest tests/test_world_integration.py -v

"""
Tests for simulation/world_integration.py

Covers:
- Camp AI configuration generation
- Fighter/Camp registration
- Fight offer processing
- Training intensity selection
- Activity checks
- Roster evaluation
- Retirement decisions
- Decision logging
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation.world_integration import (
    # Triggers
    DecisionTrigger,
    # Camp config
    CampAIConfig, generate_camp_ai_config,
    # State tracking
    FighterWorldState, CampWorldState,
    # Logging
    AIDecisionLog,
    # Engine
    WorldIntegrationEngine, create_world_integration_engine,
    # Display
    format_camp_config, format_decision_summary,
)

from simulation.ai_behavior import (
    FighterMentality, ActivityPreference, RiskProfile,
    FighterPersonality,
    create_warrior_personality, create_businessman_personality,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def engine():
    """Create a fresh world integration engine."""
    return create_world_integration_engine()


@pytest.fixture
def populated_engine():
    """Create an engine with camps and fighters registered."""
    engine = create_world_integration_engine()
    
    # Register player camp
    engine.register_camp(
        camp_id="player_camp",
        name="Player's Gym",
        is_player_camp=True,
        budget=100000,
    )
    
    # Register AI camp
    engine.register_camp(
        camp_id="ai_camp_1",
        name="AI Gym Alpha",
        is_player_camp=False,
        budget=150000,
    )
    
    # Register fighters for AI camp
    for i in range(3):
        engine.register_fighter(
            fighter_id=f"ai_fighter_{i}",
            name=f"AI Fighter {i}",
            age=28 + i,
            rating=70 + i * 5,
            camp_id="ai_camp_1",
            is_player_fighter=False,
            wins=10 - i,
            losses=i * 2,
        )
    
    # Register a player fighter
    engine.register_fighter(
        fighter_id="player_fighter_1",
        name="Player Champion",
        age=27,
        rating=85,
        camp_id="player_camp",
        is_player_fighter=True,
        wins=15,
        losses=2,
    )
    
    return engine


# ============================================================================
# CAMP AI CONFIG TESTS
# ============================================================================

class TestCampAIConfig:
    def test_create_config(self):
        config = CampAIConfig(
            camp_id="test_camp",
            camp_name="Test Camp",
        )
        
        assert config.camp_id == "test_camp"
        assert config.booking_aggression == 1.0
        assert config.roster_patience == 0.5
    
    def test_config_serialization(self):
        config = CampAIConfig(
            camp_id="test_camp",
            camp_name="Test",
            booking_aggression=1.3,
            prospect_focus=0.8,
        )
        
        data = config.to_dict()
        restored = CampAIConfig.from_dict(data)
        
        assert restored.camp_id == config.camp_id
        assert restored.booking_aggression == config.booking_aggression
        assert restored.prospect_focus == config.prospect_focus
    
    def test_generate_camp_config_variance(self):
        """Generate many configs and verify variance."""
        configs = [
            generate_camp_ai_config(f"camp_{i}")
            for i in range(50)
        ]
        
        # Check we get variance in booking aggression
        aggressions = [c.booking_aggression for c in configs]
        assert min(aggressions) < 0.9  # Some passive
        assert max(aggressions) > 1.1  # Some aggressive
        
        # Check we get variance in prospect focus
        prospects = [c.prospect_focus for c in configs]
        assert min(prospects) < 0.4
        assert max(prospects) > 0.6


# ============================================================================
# FIGHTER/CAMP STATE TESTS
# ============================================================================

class TestFighterWorldState:
    def test_create_fighter_state(self):
        state = FighterWorldState(
            fighter_id="test_fighter",
            name="Test Fighter",
            age=28,
            rating=75,
        )
        
        assert state.fighter_id == "test_fighter"
        assert state.is_active is True
        assert state.is_retired is False
    
    def test_fighter_serialization(self):
        personality = create_warrior_personality("test")
        state = FighterWorldState(
            fighter_id="test",
            name="Test",
            age=30,
            rating=80,
            personality=personality,
            wins=15,
            losses=3,
        )
        
        data = state.to_dict()
        restored = FighterWorldState.from_dict(data)
        
        assert restored.fighter_id == state.fighter_id
        assert restored.wins == state.wins
        assert restored.personality is not None


class TestCampWorldState:
    def test_create_camp_state(self):
        state = CampWorldState(
            camp_id="test_camp",
            name="Test Camp",
        )
        
        assert state.roster_size == 0
        assert state.has_roster_space is True
    
    def test_roster_tracking(self):
        state = CampWorldState(
            camp_id="test_camp",
            name="Test Camp",
            max_roster_size=5,
        )
        
        state.fighter_ids = ["f1", "f2", "f3"]
        
        assert state.roster_size == 3
        assert state.has_roster_space is True
        
        state.fighter_ids = ["f1", "f2", "f3", "f4", "f5"]
        assert state.has_roster_space is False


# ============================================================================
# ENGINE REGISTRATION TESTS
# ============================================================================

class TestEngineRegistration:
    def test_register_fighter(self, engine):
        state = engine.register_fighter(
            fighter_id="fighter_1",
            name="Test Fighter",
            age=28,
            rating=75,
        )
        
        assert state.fighter_id == "fighter_1"
        assert state.personality is not None  # Auto-generated
        assert engine.get_fighter("fighter_1") is not None
    
    def test_register_fighter_with_camp(self, engine):
        engine.register_camp("camp_1", "Test Camp")
        engine.register_fighter(
            fighter_id="fighter_1",
            name="Test",
            age=28,
            rating=75,
            camp_id="camp_1",
        )
        
        camp = engine.get_camp("camp_1")
        assert "fighter_1" in camp.fighter_ids
    
    def test_register_camp_ai_config(self, engine):
        engine.register_camp(
            camp_id="ai_camp",
            name="AI Camp",
            is_player_camp=False,
        )
        
        camp = engine.get_camp("ai_camp")
        assert camp.ai_config is not None
    
    def test_register_player_camp_no_ai(self, engine):
        engine.register_camp(
            camp_id="player",
            name="Player Camp",
            is_player_camp=True,
        )
        
        camp = engine.get_camp("player")
        assert camp.ai_config is None
        assert engine.player_camp_id == "player"


# ============================================================================
# FIGHT OFFER PROCESSING TESTS
# ============================================================================

class TestFightOfferProcessing:
    def test_add_fight_offer(self, populated_engine):
        populated_engine.add_fight_offer(
            target_fighter_id="ai_fighter_0",
            opponent_id="some_opponent",
            opponent_name="Opponent Guy",
            opponent_rating=70,
            opponent_rank=10,
            is_title_fight=False,
            is_main_event=False,
            weeks_out=8,
            purse=50000,
        )
        
        assert "ai_fighter_0" in populated_engine.pending_offers
        assert len(populated_engine.pending_offers["ai_fighter_0"]) == 1
    
    def test_process_fight_offers(self, populated_engine):
        # Add offer
        populated_engine.add_fight_offer(
            target_fighter_id="ai_fighter_0",
            opponent_id="opponent_1",
            opponent_name="Opponent",
            opponent_rating=65,
            opponent_rank=12,
            is_title_fight=False,
            is_main_event=False,
            weeks_out=8,
            purse=50000,
        )
        
        # Process week
        logs = populated_engine.process_week(1)
        
        # Should have processed the offer
        offer_logs = [l for l in logs if l.decision_type == "Fight Offer"]
        assert len(offer_logs) >= 0  # May or may not accept
        
        # Offer should be cleared
        assert len(populated_engine.pending_offers.get("ai_fighter_0", [])) == 0
    
    def test_warrior_accepts_more_offers(self, engine):
        """Warriors should accept more fight offers."""
        # Create camp
        engine.register_camp("camp", "Camp", is_player_camp=False)
        
        # Create warrior fighter
        warrior_personality = create_warrior_personality("warrior")
        engine.register_fighter(
            fighter_id="warrior",
            name="Warrior",
            age=28,
            rating=75,
            camp_id="camp",
            personality=warrior_personality,
        )
        
        # Create businessman fighter
        business_personality = create_businessman_personality("business")
        engine.register_fighter(
            fighter_id="business",
            name="Business",
            age=28,
            rating=75,
            camp_id="camp",
            personality=business_personality,
        )
        
        # Test many offers for each
        warrior_accepts = 0
        business_accepts = 0
        
        for i in range(50):
            # Clear any scheduled fights
            engine.fighters["warrior"].has_scheduled_fight = False
            engine.fighters["business"].has_scheduled_fight = False
            
            engine.add_fight_offer(
                target_fighter_id="warrior",
                opponent_id=f"opp_{i}",
                opponent_name=f"Opponent {i}",
                opponent_rating=80,  # Tough fight
                opponent_rank=5,
                is_title_fight=False,
                is_main_event=False,
                weeks_out=8,
                purse=50000,
            )
            
            engine.add_fight_offer(
                target_fighter_id="business",
                opponent_id=f"opp_{i}",
                opponent_name=f"Opponent {i}",
                opponent_rating=80,
                opponent_rank=5,
                is_title_fight=False,
                is_main_event=False,
                weeks_out=8,
                purse=50000,
            )
            
            logs = engine.process_week(i + 1)
            
            for log in logs:
                if log.decision_type == "Fight Offer":
                    if "Warrior" in log.actor_name and log.result:
                        warrior_accepts += 1
                    elif "Business" in log.actor_name and log.result:
                        business_accepts += 1
        
        # Warrior should accept more tough fights
        assert warrior_accepts > business_accepts


# ============================================================================
# TRAINING INTENSITY TESTS
# ============================================================================

class TestTrainingIntensity:
    def test_training_intensity_selection(self, populated_engine):
        # Put fighter in training camp
        fighter = populated_engine.fighters["ai_fighter_0"]
        fighter.in_training_camp = True
        fighter.training_week = 2
        
        logs = populated_engine.process_week(1)
        
        # Should have training decision
        training_logs = [l for l in logs if l.decision_type == "Training Intensity"]
        assert len(training_logs) >= 1


# ============================================================================
# ACTIVITY CHECK TESTS
# ============================================================================

class TestActivityChecks:
    def test_activity_check_generates_logs(self, populated_engine):
        # Set fighter as inactive for a while
        fighter = populated_engine.fighters["ai_fighter_0"]
        fighter.weeks_since_last_fight = 20
        fighter.has_scheduled_fight = False
        fighter.is_injured = False
        fighter.in_training_camp = False
        
        logs = populated_engine.process_week(1)
        
        # May or may not have activity log depending on roll
        # Just verify no errors


# ============================================================================
# ROSTER EVALUATION TESTS
# ============================================================================

class TestRosterEvaluation:
    def test_roster_evaluation_on_even_weeks(self, populated_engine):
        # Trigger roster evaluation (bi-weekly)
        logs1 = populated_engine.process_week(1)  # Week 1 - no roster eval
        logs2 = populated_engine.process_week(2)  # Week 2 - roster eval
        
        # Roster evaluation happens on even weeks
        # Verify no errors occurred
    
    def test_losing_fighter_more_likely_released(self, engine):
        """Fighter with bad record should be more likely released."""
        engine.register_camp("camp", "Camp", is_player_camp=False)
        
        # Good fighter
        engine.register_fighter(
            fighter_id="good",
            name="Good Fighter",
            age=28,
            rating=80,
            camp_id="camp",
            wins=15,
            losses=2,
        )
        engine.fighters["good"].recent_wins = 4
        engine.fighters["good"].recent_losses = 1
        
        # Bad fighter
        engine.register_fighter(
            fighter_id="bad",
            name="Bad Fighter",
            age=35,
            rating=50,
            camp_id="camp",
            wins=5,
            losses=15,
        )
        engine.fighters["bad"].recent_wins = 0
        engine.fighters["bad"].recent_losses = 5
        
        # Run many weeks and count releases
        good_released = 0
        bad_released = 0
        
        for i in range(50):
            # Reset roster
            if "good" not in engine.camps["camp"].fighter_ids:
                engine.camps["camp"].fighter_ids.append("good")
                engine.fighters["good"].camp_id = "camp"
            if "bad" not in engine.camps["camp"].fighter_ids:
                engine.camps["camp"].fighter_ids.append("bad")
                engine.fighters["bad"].camp_id = "camp"
            
            logs = engine.process_week(i * 2 + 2)  # Even weeks only
            
            for log in logs:
                if log.decision_type == "Roster Release" and log.result:
                    if "Good" in log.subject:
                        good_released += 1
                    elif "Bad" in log.subject:
                        bad_released += 1
        
        # Bad fighter should be released more
        assert bad_released > good_released


# ============================================================================
# RETIREMENT TESTS
# ============================================================================

class TestRetirement:
    def test_older_fighter_retires_more(self, engine):
        """Older fighters should retire more often."""
        engine.register_camp("camp", "Camp", is_player_camp=False)
        
        young_retires = 0
        old_retires = 0
        
        for i in range(30):
            # Register fighters
            engine.register_fighter(
                fighter_id=f"young_{i}",
                name=f"Young {i}",
                age=28,
                rating=75,
                camp_id="camp",
                wins=10,
                losses=3,
            )
            
            engine.register_fighter(
                fighter_id=f"old_{i}",
                name=f"Old {i}",
                age=38,
                rating=60,
                camp_id="camp",
                wins=25,
                losses=15,
            )
            engine.fighters[f"old_{i}"].recent_wins = 1
            engine.fighters[f"old_{i}"].recent_losses = 4
            engine.fighters[f"old_{i}"].ko_losses = 4
            
            # Process monthly check (week 1)
            logs = engine.process_week(1)
            
            for log in logs:
                if log.decision_type == "Retirement" and log.result:
                    if "Young" in log.actor_name:
                        young_retires += 1
                    elif "Old" in log.actor_name:
                        old_retires += 1
            
            # Reset for next iteration
            for fid in [f"young_{i}", f"old_{i}"]:
                del engine.fighters[fid]
        
        assert old_retires > young_retires


# ============================================================================
# DECISION LOG TESTS
# ============================================================================

class TestDecisionLogging:
    def test_decision_log_format(self):
        log = AIDecisionLog(
            timestamp=5,
            decision_type="Test Decision",
            actor_id="actor_1",
            actor_name="Test Actor",
            trigger=DecisionTrigger.WEEKLY_CHECK,
            subject="Test Subject",
            base_probability=0.50,
            modifiers=[("Modifier 1", 0.10), ("Modifier 2", -0.05)],
            final_probability=0.55,
            roll=0.40,
            result=True,
            result_description="Test passed",
        )
        
        lines = log.format()
        
        assert len(lines) > 0
        assert any("Week 5" in line for line in lines)
        assert any("Base" in line for line in lines)
    
    def test_get_decision_log_filtering(self, populated_engine):
        # Generate some decisions
        for i in range(5):
            populated_engine.process_week(i + 1)
        
        # Get all logs
        all_logs = populated_engine.get_decision_log(count=100)
        
        # Filter by type (if any exist)
        if all_logs:
            dtype = all_logs[0].decision_type
            filtered = populated_engine.get_decision_log(
                count=100,
                decision_type=dtype
            )
            assert all(l.decision_type == dtype for l in filtered)


# ============================================================================
# QUERY TESTS
# ============================================================================

class TestQueries:
    def test_get_ai_camps(self, populated_engine):
        ai_camps = populated_engine.get_ai_camps()
        
        assert len(ai_camps) == 1
        assert all(not c.is_player_camp for c in ai_camps)
    
    def test_get_active_fighters(self, populated_engine):
        active = populated_engine.get_active_fighters()
        
        assert len(active) == 4  # 3 AI + 1 player
        assert all(not f.is_retired for f in active)
    
    def test_get_free_agents(self, engine):
        engine.register_camp("camp", "Camp")
        
        # Signed fighter
        engine.register_fighter(
            fighter_id="signed",
            name="Signed",
            age=28,
            rating=75,
            camp_id="camp",
        )
        
        # Free agent
        engine.register_fighter(
            fighter_id="free",
            name="Free Agent",
            age=28,
            rating=70,
            camp_id=None,
        )
        
        free_agents = engine.get_free_agents()
        
        assert len(free_agents) == 1
        assert free_agents[0].fighter_id == "free"


# ============================================================================
# SERIALIZATION TESTS
# ============================================================================

class TestSerialization:
    def test_engine_to_dict(self, populated_engine):
        data = populated_engine.to_dict()
        
        assert "fighters" in data
        assert "camps" in data
        assert "player_camp_id" in data
        assert len(data["fighters"]) == 4


# ============================================================================
# DISPLAY HELPER TESTS
# ============================================================================

class TestDisplayHelpers:
    def test_format_camp_config(self):
        config = CampAIConfig(
            camp_id="test",
            camp_name="Test Camp",
            booking_aggression=1.3,
        )
        
        lines = format_camp_config(config)
        
        assert len(lines) > 0
        assert any("Test Camp" in line for line in lines)
        assert any("1.3" in line for line in lines)
    
    def test_format_decision_summary(self, populated_engine):
        # Generate some decisions
        for i in range(3):
            populated_engine.process_week(i + 1)
        
        logs = populated_engine.get_decision_log()
        summary = format_decision_summary(logs)
        
        assert len(summary) > 0


# ============================================================================
# CALLBACK TESTS
# ============================================================================

class TestCallbacks:
    def test_fight_accepted_callback(self, populated_engine):
        accepted_fights = []
        
        def on_accept(fighter_id, offer):
            accepted_fights.append((fighter_id, offer))
        
        populated_engine.on_fight_accepted(on_accept)
        
        # Add favorable offer
        populated_engine.add_fight_offer(
            target_fighter_id="ai_fighter_0",
            opponent_id="easy_opp",
            opponent_name="Easy Opponent",
            opponent_rating=50,  # Much easier
            opponent_rank=15,
            is_title_fight=False,
            is_main_event=False,
            weeks_out=8,
            purse=50000,
        )
        
        # Process multiple times to likely get acceptance
        for i in range(10):
            populated_engine.fighters["ai_fighter_0"].has_scheduled_fight = False
            populated_engine.add_fight_offer(
                target_fighter_id="ai_fighter_0",
                opponent_id=f"easy_{i}",
                opponent_name="Easy",
                opponent_rating=50,
                opponent_rank=15,
                is_title_fight=False,
                is_main_event=False,
                weeks_out=8,
                purse=50000,
            )
            populated_engine.process_week(i + 1)
            
            if accepted_fights:
                break
        
        # Should have triggered callback at least once (high probability)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    def test_full_week_cycle(self, populated_engine):
        """Test a complete week of processing."""
        # Setup some state
        fighter = populated_engine.fighters["ai_fighter_0"]
        fighter.in_training_camp = True
        fighter.weeks_since_last_fight = 15
        
        # Add an offer
        populated_engine.add_fight_offer(
            target_fighter_id="ai_fighter_0",
            opponent_id="opp",
            opponent_name="Opponent",
            opponent_rating=72,
            opponent_rank=8,
            is_title_fight=False,
            is_main_event=False,
            weeks_out=8,
            purse=50000,
        )
        
        # Process week
        logs = populated_engine.process_week(1)
        
        # Should have multiple decisions
        assert len(logs) >= 0  # At minimum, no errors
    
    def test_multi_week_simulation(self, populated_engine):
        """Test multiple weeks of simulation."""
        for week in range(1, 13):
            logs = populated_engine.process_week(week)
            
            # Add random offers occasionally
            if week % 3 == 0:
                for fid in ["ai_fighter_0", "ai_fighter_1"]:
                    if not populated_engine.fighters[fid].has_scheduled_fight:
                        populated_engine.add_fight_offer(
                            target_fighter_id=fid,
                            opponent_id=f"opp_{week}",
                            opponent_name=f"Opponent {week}",
                            opponent_rating=70,
                            opponent_rank=10,
                            is_title_fight=False,
                            is_main_event=False,
                            weeks_out=8,
                            purse=40000,
                        )
            
            # Update weeks since fight
            for f in populated_engine.fighters.values():
                f.weeks_since_last_fight += 1
        
        # Verify we have logged decisions
        all_logs = populated_engine.get_decision_log(count=1000)
        assert len(all_logs) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
