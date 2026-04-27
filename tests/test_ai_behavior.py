# tests/test_ai_behavior.py
# Tests for the AI Behavior System
# Run: python3 -m pytest tests/test_ai_behavior.py -v

"""
Tests for simulation/ai_behavior.py

Covers:
- Personality generation and variance
- Fight offer decisions with all modifiers
- Training intensity selection
- Retirement decisions
- Target selection
- Activity level decisions
- Decision breakdown logging
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation.ai_behavior import (
    # Enums
    FighterMentality, ActivityPreference, RiskProfile,
    FinishingInstinct, TrainingDedication,
    # Data classes
    FighterPersonality, DecisionBreakdown,
    # Engine
    AIDecisionEngine, create_ai_engine,
    # Generation
    generate_fighter_personality,
    # Archetypes
    create_warrior_personality, create_businessman_personality,
    create_glory_seeker_personality, create_journeyman_personality,
    # Display
    format_personality, format_decision_breakdown, describe_mentality,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def warrior():
    """Create a warrior personality."""
    return create_warrior_personality("warrior_1")


@pytest.fixture
def businessman():
    """Create a businessman personality."""
    return create_businessman_personality("business_1")


@pytest.fixture
def glory_seeker():
    """Create a glory seeker personality."""
    return create_glory_seeker_personality("glory_1")


@pytest.fixture
def journeyman():
    """Create a journeyman personality."""
    return create_journeyman_personality("journey_1")


@pytest.fixture
def engine():
    """Create an AI decision engine."""
    return create_ai_engine()


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestEnums:
    def test_fighter_mentality_values(self):
        assert FighterMentality.WARRIOR.value == "warrior"
        assert FighterMentality.BUSINESSMAN.value == "businessman"
        assert FighterMentality.GLORY_SEEKER.value == "glory_seeker"
    
    def test_activity_preference_values(self):
        assert ActivityPreference.VERY_ACTIVE.value == "very_active"
        assert ActivityPreference.INACTIVE.value == "inactive"
    
    def test_risk_profile_values(self):
        assert RiskProfile.RECKLESS.value == "reckless"
        assert RiskProfile.COWARDLY.value == "cowardly"
    
    def test_finishing_instinct_values(self):
        assert FinishingInstinct.KILLER_INSTINCT.value == "killer"
        assert FinishingInstinct.POINT_FIGHTER.value == "point_fighter"
    
    def test_training_dedication_values(self):
        assert TrainingDedication.OBSESSED.value == "obsessed"
        assert TrainingDedication.LAZY.value == "lazy"


# ============================================================================
# PERSONALITY GENERATION TESTS
# ============================================================================

class TestPersonalityGeneration:
    def test_generate_unique_personalities(self):
        """Generate 100 personalities and verify variance."""
        personalities = [
            generate_fighter_personality(f"fighter_{i}")
            for i in range(100)
        ]
        
        # Check we get variety in mentalities
        mentalities = set(p.mentality for p in personalities)
        assert len(mentalities) >= 4  # Should have multiple types
        
        # Check confidence varies
        confidences = [p.confidence for p in personalities]
        assert min(confidences) < 40  # Some low confidence
        assert max(confidences) > 60  # Some high confidence
    
    def test_champion_gets_confidence_boost(self):
        """Champions should have higher confidence."""
        regular_fighters = [
            generate_fighter_personality(f"reg_{i}", is_champion=False)
            for i in range(50)
        ]
        champions = [
            generate_fighter_personality(f"champ_{i}", is_champion=True)
            for i in range(50)
        ]
        
        avg_regular = sum(p.confidence for p in regular_fighters) / 50
        avg_champion = sum(p.confidence for p in champions) / 50
        
        # Champions should average higher confidence
        assert avg_champion > avg_regular
    
    def test_personality_serialization(self, warrior):
        """Test personality serialization."""
        data = warrior.to_dict()
        restored = FighterPersonality.from_dict(data)
        
        assert restored.fighter_id == warrior.fighter_id
        assert restored.mentality == warrior.mentality
        assert restored.confidence == warrior.confidence


class TestArchetypes:
    def test_warrior_archetype(self, warrior):
        assert warrior.mentality == FighterMentality.WARRIOR
        assert warrior.activity == ActivityPreference.VERY_ACTIVE
        assert warrior.risk_profile == RiskProfile.RECKLESS
        assert warrior.short_notice_fighter is True
        assert warrior.heart >= 80
    
    def test_businessman_archetype(self, businessman):
        assert businessman.mentality == FighterMentality.BUSINESSMAN
        assert businessman.risk_profile == RiskProfile.CAUTIOUS
        assert businessman.intelligence >= 70
        assert businessman.will_fight_down is False
    
    def test_glory_seeker_archetype(self, glory_seeker):
        assert glory_seeker.mentality == FighterMentality.GLORY_SEEKER
        assert glory_seeker.wants_title is True
        assert glory_seeker.ego >= 80
    
    def test_journeyman_archetype(self, journeyman):
        assert journeyman.mentality == FighterMentality.JOURNEYMAN
        assert journeyman.activity == ActivityPreference.ACTIVE
        assert journeyman.wants_title is False


# ============================================================================
# FIGHT OFFER DECISION TESTS
# ============================================================================

class TestFightOfferDecisions:
    def test_warrior_accepts_more(self, engine, warrior, businessman):
        """Warriors should accept more fights than businessmen."""
        warrior_accepts = 0
        businessman_accepts = 0
        
        for _ in range(100):
            result, _ = engine.evaluate_fight_offer(
                personality=warrior,
                fighter_rating=75,
                fighter_rank=5,
                is_champion=False,
                wins=10, losses=3,
                win_streak=0, lose_streak=0,
                weeks_since_fight=12,
                opponent_rating=75,
                opponent_rank=6,
                opponent_id="opp1",
                is_title_fight=False,
                is_main_event=False,
                weeks_out=8,
                purse=50000,
            )
            if result:
                warrior_accepts += 1
        
        for _ in range(100):
            result, _ = engine.evaluate_fight_offer(
                personality=businessman,
                fighter_rating=75,
                fighter_rank=5,
                is_champion=False,
                wins=10, losses=3,
                win_streak=0, lose_streak=0,
                weeks_since_fight=12,
                opponent_rating=75,
                opponent_rank=6,
                opponent_id="opp1",
                is_title_fight=False,
                is_main_event=False,
                weeks_out=8,
                purse=50000,
            )
            if result:
                businessman_accepts += 1
        
        # Warrior should accept significantly more
        assert warrior_accepts > businessman_accepts
    
    def test_title_fight_increases_acceptance(self, engine, glory_seeker):
        """Title fights should increase acceptance rate."""
        non_title_accepts = 0
        title_accepts = 0
        
        for _ in range(100):
            result, _ = engine.evaluate_fight_offer(
                personality=glory_seeker,
                fighter_rating=80,
                fighter_rank=3,
                is_champion=False,
                wins=15, losses=2,
                win_streak=3, lose_streak=0,
                weeks_since_fight=10,
                opponent_rating=85,
                opponent_rank=0,  # Champion
                opponent_id="champ",
                is_title_fight=False,
                is_main_event=False,
                weeks_out=8,
                purse=100000,
            )
            if result:
                non_title_accepts += 1
        
        for _ in range(100):
            result, _ = engine.evaluate_fight_offer(
                personality=glory_seeker,
                fighter_rating=80,
                fighter_rank=3,
                is_champion=False,
                wins=15, losses=2,
                win_streak=3, lose_streak=0,
                weeks_since_fight=10,
                opponent_rating=85,
                opponent_rank=0,
                opponent_id="champ",
                is_title_fight=True,  # Title fight!
                is_main_event=True,
                weeks_out=8,
                purse=100000,
            )
            if result:
                title_accepts += 1
        
        assert title_accepts > non_title_accepts
    
    def test_short_notice_affects_acceptance(self, engine, businessman):
        """Short notice should decrease acceptance (except for short notice fighters)."""
        standard_accepts = 0
        short_notice_accepts = 0
        
        for _ in range(100):
            result, _ = engine.evaluate_fight_offer(
                personality=businessman,
                fighter_rating=75,
                fighter_rank=8,
                is_champion=False,
                wins=10, losses=3,
                win_streak=1, lose_streak=0,
                weeks_since_fight=12,
                opponent_rating=72,
                opponent_rank=10,
                opponent_id="opp1",
                is_title_fight=False,
                is_main_event=False,
                weeks_out=8,  # Standard notice
                purse=50000,
            )
            if result:
                standard_accepts += 1
        
        for _ in range(100):
            result, _ = engine.evaluate_fight_offer(
                personality=businessman,
                fighter_rating=75,
                fighter_rank=8,
                is_champion=False,
                wins=10, losses=3,
                win_streak=1, lose_streak=0,
                weeks_since_fight=12,
                opponent_rating=72,
                opponent_rank=10,
                opponent_id="opp1",
                is_title_fight=False,
                is_main_event=False,
                weeks_out=2,  # Short notice!
                purse=50000,
            )
            if result:
                short_notice_accepts += 1
        
        assert standard_accepts > short_notice_accepts
    
    def test_decision_breakdown_logged(self, engine, warrior):
        """Decisions should be logged with breakdown."""
        result, breakdown = engine.evaluate_fight_offer(
            personality=warrior,
            fighter_rating=75,
            fighter_rank=5,
            is_champion=False,
            wins=10, losses=3,
            win_streak=2, lose_streak=0,
            weeks_since_fight=12,
            opponent_rating=70,
            opponent_rank=8,
            opponent_id="opp1",
            is_title_fight=False,
            is_main_event=False,
            weeks_out=8,
            purse=50000,
        )
        
        assert breakdown is not None
        assert breakdown.decision_type == "Fight Offer"
        assert breakdown.base_probability == 0.50
        assert len(breakdown.modifiers) > 0
        assert 0 <= breakdown.final_probability <= 1


# ============================================================================
# TRAINING INTENSITY TESTS
# ============================================================================

class TestTrainingIntensity:
    def test_obsessed_trains_harder(self, engine):
        """Obsessed fighters should train more intensely."""
        obsessed = FighterPersonality(
            fighter_id="obsessed",
            dedication=TrainingDedication.OBSESSED,
        )
        lazy = FighterPersonality(
            fighter_id="lazy",
            dedication=TrainingDedication.LAZY,
        )
        
        obsessed_intense = 0
        lazy_intense = 0
        
        for _ in range(100):
            intensity, _ = engine.select_training_intensity(
                personality=obsessed,
                weeks_until_fight=8,
                current_fatigue=20,
                age=28,
                coming_off_loss=False,
                coming_off_ko_loss=False,
            )
            if intensity in ["INTENSE", "EXTREME"]:
                obsessed_intense += 1
        
        for _ in range(100):
            intensity, _ = engine.select_training_intensity(
                personality=lazy,
                weeks_until_fight=8,
                current_fatigue=20,
                age=28,
                coming_off_loss=False,
                coming_off_ko_loss=False,
            )
            if intensity in ["INTENSE", "EXTREME"]:
                lazy_intense += 1
        
        assert obsessed_intense > lazy_intense
    
    def test_taper_before_fight(self, engine, warrior):
        """Should select lighter training close to fight."""
        light_near_fight = 0
        light_far_fight = 0
        
        for _ in range(100):
            intensity, _ = engine.select_training_intensity(
                personality=warrior,
                weeks_until_fight=2,  # Close to fight
                current_fatigue=20,
                age=28,
                coming_off_loss=False,
                coming_off_ko_loss=False,
            )
            if intensity == "LIGHT":
                light_near_fight += 1
        
        for _ in range(100):
            intensity, _ = engine.select_training_intensity(
                personality=warrior,
                weeks_until_fight=8,  # Far from fight
                current_fatigue=20,
                age=28,
                coming_off_loss=False,
                coming_off_ko_loss=False,
            )
            if intensity == "LIGHT":
                light_far_fight += 1
        
        assert light_near_fight > light_far_fight


# ============================================================================
# RETIREMENT DECISION TESTS
# ============================================================================

class TestRetirementDecisions:
    def test_older_fighters_retire_more(self, engine, businessman):
        """Older fighters should consider retirement more."""
        young_retires = 0
        old_retires = 0
        
        for _ in range(100):
            result, _ = engine.consider_retirement(
                personality=businessman,
                age=28,
                wins=15, losses=5,
                recent_record=(2, 3),
                is_champion=False,
                ko_losses_career=1,
                months_since_last_win=6,
            )
            if result:
                young_retires += 1
        
        for _ in range(100):
            result, _ = engine.consider_retirement(
                personality=businessman,
                age=38,
                wins=15, losses=5,
                recent_record=(2, 3),
                is_champion=False,
                ko_losses_career=1,
                months_since_last_win=6,
            )
            if result:
                old_retires += 1
        
        assert old_retires > young_retires
    
    def test_warriors_dont_quit(self, engine, warrior, businessman):
        """Warriors should retire less than businessmen."""
        warrior_retires = 0
        businessman_retires = 0
        
        for _ in range(100):
            result, _ = engine.consider_retirement(
                personality=warrior,
                age=36,
                wins=20, losses=10,
                recent_record=(1, 4),
                is_champion=False,
                ko_losses_career=3,
                months_since_last_win=12,
            )
            if result:
                warrior_retires += 1
        
        for _ in range(100):
            result, _ = engine.consider_retirement(
                personality=businessman,
                age=36,
                wins=20, losses=10,
                recent_record=(1, 4),
                is_champion=False,
                ko_losses_career=3,
                months_since_last_win=12,
                money_secure=True,
            )
            if result:
                businessman_retires += 1
        
        assert warrior_retires < businessman_retires
    
    def test_title_shot_delays_retirement(self, engine, businessman):
        """Pending title shot should delay retirement."""
        without_shot = 0
        with_shot = 0
        
        for _ in range(100):
            result, _ = engine.consider_retirement(
                personality=businessman,
                age=36,
                wins=18, losses=6,
                recent_record=(2, 3),
                is_champion=False,
                ko_losses_career=2,
                months_since_last_win=8,
                has_title_shot_coming=False,
            )
            if result:
                without_shot += 1
        
        for _ in range(100):
            result, _ = engine.consider_retirement(
                personality=businessman,
                age=36,
                wins=18, losses=6,
                recent_record=(2, 3),
                is_champion=False,
                ko_losses_career=2,
                months_since_last_win=8,
                has_title_shot_coming=True,
            )
            if result:
                with_shot += 1
        
        assert without_shot > with_shot


# ============================================================================
# TARGET SELECTION TESTS
# ============================================================================

class TestTargetSelection:
    def test_selects_from_available(self, engine, warrior):
        """Should select from available opponents."""
        opponents = [
            {"fighter_id": "opp1", "name": "Fighter 1", "rank": 3, "rating": 80},
            {"fighter_id": "opp2", "name": "Fighter 2", "rank": 5, "rating": 75},
            {"fighter_id": "opp3", "name": "Fighter 3", "rank": 10, "rating": 70},
        ]
        
        selected, breakdown = engine.select_target(
            personality=warrior,
            fighter_rank=4,
            is_champion=False,
            available_opponents=opponents,
            rival_ids=[],
            lost_to_ids=[],
        )
        
        assert selected in ["opp1", "opp2", "opp3"]
    
    def test_revenge_driven_targets_losses(self, engine):
        """Revenge-driven fighters should target people they lost to."""
        revenge_fighter = FighterPersonality(
            fighter_id="revenge",
            revenge_driven=True,
            mentality=FighterMentality.WARRIOR,
        )
        
        opponents = [
            {"fighter_id": "opp1", "name": "Fighter 1", "rank": 3, "rating": 80},
            {"fighter_id": "nemesis", "name": "Nemesis", "rank": 5, "rating": 75},
        ]
        
        nemesis_count = 0
        for _ in range(200):  # More iterations for statistical stability
            selected, _ = engine.select_target(
                personality=revenge_fighter,
                fighter_rank=4,
                is_champion=False,
                available_opponents=opponents,
                rival_ids=[],
                lost_to_ids=["nemesis"],  # Lost to this person
            )
            if selected == "nemesis":
                nemesis_count += 1
        
        # Should target nemesis more often (revenge bonus +30)
        # With 200 samples, expect ~55-60% nemesis selections
        assert nemesis_count >= 80  # At least 45% to account for variance


# ============================================================================
# ACTIVITY LEVEL TESTS
# ============================================================================

class TestActivityLevel:
    def test_very_active_seeks_more_fights(self, engine, warrior, businessman):
        """Very active fighters should seek fights more often."""
        warrior_seeks = 0
        businessman_seeks = 0
        
        for _ in range(100):
            result, _ = engine.should_seek_fight(
                personality=warrior,  # VERY_ACTIVE
                weeks_since_last_fight=8,
                has_scheduled_fight=False,
                is_injured=False,
                is_in_camp=False,
                current_fatigue=20,
                age=28,
            )
            if result:
                warrior_seeks += 1
        
        for _ in range(100):
            # Create selective fighter
            selective = FighterPersonality(
                fighter_id="selective",
                activity=ActivityPreference.SELECTIVE,
            )
            result, _ = engine.should_seek_fight(
                personality=selective,
                weeks_since_last_fight=8,
                has_scheduled_fight=False,
                is_injured=False,
                is_in_camp=False,
                current_fatigue=20,
                age=28,
            )
            if result:
                businessman_seeks += 1
        
        assert warrior_seeks > businessman_seeks
    
    def test_injured_never_seeks(self, engine, warrior):
        """Injured fighters should never seek fights."""
        result, breakdown = engine.should_seek_fight(
            personality=warrior,
            weeks_since_last_fight=30,
            has_scheduled_fight=False,
            is_injured=True,
            is_in_camp=False,
            current_fatigue=0,
            age=25,
        )
        
        assert result is False
        assert "injured" in breakdown.result_reason.lower()
    
    def test_scheduled_never_seeks(self, engine, warrior):
        """Fighters with scheduled fights shouldn't seek more."""
        result, breakdown = engine.should_seek_fight(
            personality=warrior,
            weeks_since_last_fight=30,
            has_scheduled_fight=True,
            is_injured=False,
            is_in_camp=False,
            current_fatigue=0,
            age=25,
        )
        
        assert result is False


# ============================================================================
# DECISION BREAKDOWN TESTS
# ============================================================================

class TestDecisionBreakdown:
    def test_breakdown_explanation(self, engine, warrior):
        """Breakdown should generate readable explanation."""
        result, breakdown = engine.evaluate_fight_offer(
            personality=warrior,
            fighter_rating=80,
            fighter_rank=3,
            is_champion=False,
            wins=15, losses=2,
            win_streak=5, lose_streak=0,
            weeks_since_fight=12,
            opponent_rating=78,
            opponent_rank=5,
            opponent_id="opp1",
            is_title_fight=True,
            is_main_event=True,
            weeks_out=8,
            purse=100000,
        )
        
        explanation = breakdown.to_explanation()
        
        assert len(explanation) > 0
        assert any("Base probability" in line for line in explanation)
        assert any("Modifiers" in line for line in explanation)
        assert any("Final probability" in line for line in explanation)
    
    def test_decision_log(self, engine, warrior):
        """Engine should log all decisions."""
        engine.clear_log()
        
        engine.evaluate_fight_offer(
            personality=warrior,
            fighter_rating=75, fighter_rank=5, is_champion=False,
            wins=10, losses=3, win_streak=0, lose_streak=0,
            weeks_since_fight=12, opponent_rating=70, opponent_rank=8,
            opponent_id="opp1", is_title_fight=False, is_main_event=False,
            weeks_out=8, purse=50000,
        )
        
        engine.select_training_intensity(
            personality=warrior,
            weeks_until_fight=8,
            current_fatigue=20,
            age=28,
            coming_off_loss=False,
            coming_off_ko_loss=False,
        )
        
        log = engine.get_recent_decisions()
        assert len(log) == 2


# ============================================================================
# DISPLAY HELPER TESTS
# ============================================================================

class TestDisplayHelpers:
    def test_format_personality(self, warrior):
        lines = format_personality(warrior)
        
        assert len(lines) > 0
        assert any("WARRIOR" in line for line in lines)
        assert any("Confidence" in line for line in lines)
    
    def test_describe_mentality(self):
        desc = describe_mentality(FighterMentality.WARRIOR)
        assert "fight" in desc.lower()
        
        desc = describe_mentality(FighterMentality.BUSINESSMAN)
        assert "career" in desc.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
