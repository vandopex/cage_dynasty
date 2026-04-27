# tests/test_training_enhanced.py
# Tests for Enhanced Training System
# Lines: ~700
#
# Tests training events, sparring bonuses, private lessons, and camp journal

"""
Tests for the enhanced training system:
- 37 training events with context-based probability
- Automatic sparring bonus calculation
- Private lesson assignment system
- Camp Journal tracking
- Coach specialty matching
- Full training calculation with all modifiers
"""

import pytest
import random
from typing import Dict, List

# Import training module - try multiple paths for flexibility
try:
    from systems.training import (
        TrainingFocus, TrainingIntensity, TrainingEventType, CoachSpecialty,
        TrainingCamp, TrainingEvent, TrainingSystem,
        calculate_training_gain, calculate_diminishing_returns,
        calculate_age_modifier, calculate_camp_tier_bonus,
        calculate_coach_quality_bonus, coach_specialty_matches_focus,
        SPECIALTY_TO_FOCUS, calculate_sparring_bonus,
        calculate_private_lesson_score, get_private_lesson_assignments,
        should_trigger_event, generate_training_event, TRAINING_EVENTS,
        FOCUS_ATTRIBUTES, FOCUS_DESCRIPTIONS,
        INTENSITY_MULTIPLIERS, INTENSITY_FATIGUE, INTENSITY_INJURY_RISK,
    )
    from systems.training_camp import (
        CampJournal, CampJournalEntry, JournalEntryType,
        FighterTrainingInfo, TrainingWeekResult, ActiveTrainingCamp,
        format_camp_journal, format_camp_summary, format_camp_status,
        EVENT_ICONS,
    )
except ImportError:
    # Fallback for flat structure
    from training import (
        TrainingFocus, TrainingIntensity, TrainingEventType, CoachSpecialty,
        TrainingCamp, TrainingEvent, TrainingSystem,
        calculate_training_gain, calculate_diminishing_returns,
        calculate_age_modifier, calculate_camp_tier_bonus,
        calculate_coach_quality_bonus, coach_specialty_matches_focus,
        SPECIALTY_TO_FOCUS, calculate_sparring_bonus,
        calculate_private_lesson_score, get_private_lesson_assignments,
        should_trigger_event, generate_training_event, TRAINING_EVENTS,
        FOCUS_ATTRIBUTES, FOCUS_DESCRIPTIONS,
        INTENSITY_MULTIPLIERS, INTENSITY_FATIGUE, INTENSITY_INJURY_RISK,
    )
    from training_camp import (
        CampJournal, CampJournalEntry, JournalEntryType,
        FighterTrainingInfo, TrainingWeekResult, ActiveTrainingCamp,
        format_camp_journal, format_camp_summary, format_camp_status,
        EVENT_ICONS,
    )


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def young_fighter():
    """A young prospect fighter."""
    return {
        "fighter_id": "f_young",
        "name": "Young Prospect",
        "age": 22,
        "attributes": {
            "boxing": 60, "kicks": 55, "wrestling": 58,
            "bjj": 52, "cardio": 65, "power": 58,
            "speed": 62, "chin": 60, "composure": 55,
        },
        "traits": ["Gym Rat"],
        "overall": 58,
        "fighting_style": "Striker",
        "potential": 85,
    }


@pytest.fixture
def veteran_fighter():
    """An experienced veteran fighter."""
    return {
        "fighter_id": "f_veteran",
        "name": "Old Veteran",
        "age": 35,
        "attributes": {
            "boxing": 78, "kicks": 72, "wrestling": 75,
            "bjj": 70, "cardio": 68, "power": 74,
            "speed": 68, "chin": 72, "composure": 80,
        },
        "traits": ["Veteran Savvy"],
        "overall": 73,
        "fighting_style": "MMA Fighter",
    }


@pytest.fixture
def quality_coach():
    """A high quality coach."""
    return {
        "coach_id": "c_quality",
        "name": "Master Coach",
        "quality": 4,
        "specialty": "Striking",
        "traits": ["Diamond Polisher", "Analytical"],
    }


@pytest.fixture
def average_coach():
    """An average quality coach."""
    return {
        "coach_id": "c_average",
        "name": "Average Joe",
        "quality": 3,
        "specialty": "Wrestling",
        "traits": [],
    }


@pytest.fixture
def training_context():
    """Context dict for event generation."""
    return {
        "age": 25,
        "chemistry": 60,
        "focus": TrainingFocus.STRIKING,
        "intensity": TrainingIntensity.MODERATE,
        "fatigue": 20,
        "coach_quality": 4,
        "coach_is_analytical": True,
        "specialty_matches": True,
        "weeks_completed": 3,
        "camp_fighter_count": 3,
        "is_injury_prone": False,
        "lost_last_fight": False,
        "weeks_until_fight": 5,
        "fight_iq": 65,
    }


# ============================================================================
# TRAINING FOCUS TESTS
# ============================================================================

class TestTrainingFocus:
    """Tests for training focus configuration."""
    
    def test_all_focuses_have_attributes(self):
        """Each focus should map to attributes."""
        for focus in TrainingFocus:
            if focus != TrainingFocus.FIGHT_SPECIFIC:
                attrs = FOCUS_ATTRIBUTES.get(focus, [])
                assert len(attrs) > 0, f"{focus} has no attributes"
    
    def test_all_focuses_have_descriptions(self):
        """Each focus should have a description."""
        for focus in TrainingFocus:
            assert focus in FOCUS_DESCRIPTIONS, f"{focus} has no description"
    
    def test_striking_focus_attributes(self):
        """Striking focus should improve striking stats."""
        attrs = FOCUS_ATTRIBUTES[TrainingFocus.STRIKING]
        assert "boxing" in attrs or "kicks" in attrs


# ============================================================================
# COACH SPECIALTY MATCHING TESTS
# ============================================================================

class TestCoachSpecialtyMatching:
    """Tests for coach specialty to training focus matching."""
    
    def test_striking_specialty_matches_striking_focus(self):
        """Striking specialty should match striking focus."""
        assert coach_specialty_matches_focus("Striking", TrainingFocus.STRIKING)
        assert coach_specialty_matches_focus("STRIKING", TrainingFocus.STRIKING)
    
    def test_wrestling_specialty_matches_wrestling_focus(self):
        """Wrestling specialty should match wrestling focus."""
        assert coach_specialty_matches_focus("Wrestling", TrainingFocus.WRESTLING)
    
    def test_jiujitsu_specialty_matches_jiujitsu_focus(self):
        """Jiu-Jitsu specialty should match jiu-jitsu focus."""
        assert coach_specialty_matches_focus("Jiu-Jitsu", TrainingFocus.JIUJITSU)
    
    def test_specialty_mismatch(self):
        """Non-matching specialties should return False."""
        assert not coach_specialty_matches_focus("Striking", TrainingFocus.WRESTLING)
        assert not coach_specialty_matches_focus("Wrestling", TrainingFocus.STRIKING)
    
    def test_none_specialty(self):
        """None specialty should not match anything."""
        assert not coach_specialty_matches_focus(None, TrainingFocus.STRIKING)
    
    def test_cornering_specialty(self):
        """Cornering specialty doesn't match any training focus."""
        assert not coach_specialty_matches_focus("Cornering", TrainingFocus.STRIKING)
        assert not coach_specialty_matches_focus("Cornering", TrainingFocus.WRESTLING)


# ============================================================================
# SPARRING BONUS TESTS
# ============================================================================

class TestSparringBonus:
    """Tests for automatic sparring bonus calculation."""
    
    def test_no_sparring_with_one_fighter(self):
        """Solo fighter gets no sparring bonus."""
        fighters = [{"overall": 70, "fighting_style": "Striker"}]
        bonus, desc = calculate_sparring_bonus(fighters)
        assert bonus == 0.0
        assert "No sparring partners" in desc
    
    def test_base_sparring_bonus_with_two_fighters(self):
        """Two fighters get base sparring bonus."""
        fighters = [
            {"overall": 60, "fighting_style": "Striker"},
            {"overall": 60, "fighting_style": "Wrestler"},
        ]
        bonus, desc = calculate_sparring_bonus(fighters)
        assert bonus > 0
        assert bonus <= 0.15  # Capped at 15%
    
    def test_elite_sparring_partners(self):
        """Elite partners give higher bonus."""
        elite_fighters = [
            {"overall": 85, "fighting_style": "Striker"},
            {"overall": 82, "fighting_style": "Wrestler"},
            {"overall": 80, "fighting_style": "Grappler"},
        ]
        decent_fighters = [
            {"overall": 55, "fighting_style": "Striker"},
            {"overall": 52, "fighting_style": "Wrestler"},
            {"overall": 50, "fighting_style": "Grappler"},
        ]
        
        elite_bonus, _ = calculate_sparring_bonus(elite_fighters)
        decent_bonus, _ = calculate_sparring_bonus(decent_fighters)
        
        assert elite_bonus > decent_bonus
    
    def test_style_diversity_bonus(self):
        """Diverse styles give bonus."""
        diverse = [
            {"overall": 70, "fighting_style": "Striker"},
            {"overall": 70, "fighting_style": "Wrestler"},
            {"overall": 70, "fighting_style": "BJJ"},
        ]
        same_style = [
            {"overall": 70, "fighting_style": "Striker"},
            {"overall": 70, "fighting_style": "Striker"},
            {"overall": 70, "fighting_style": "Striker"},
        ]
        
        diverse_bonus, diverse_desc = calculate_sparring_bonus(diverse)
        same_bonus, same_desc = calculate_sparring_bonus(same_style)
        
        assert diverse_bonus > same_bonus
        assert "Diverse" in diverse_desc
    
    def test_iron_sharpener_bonus(self):
        """Iron Sharpener trait increases sparring bonus."""
        fighters = [
            {"overall": 70, "fighting_style": "Striker"},
            {"overall": 70, "fighting_style": "Wrestler"},
        ]
        
        normal_bonus, _ = calculate_sparring_bonus(fighters, coach_has_iron_sharpener=False)
        iron_bonus, _ = calculate_sparring_bonus(fighters, coach_has_iron_sharpener=True)
        
        assert iron_bonus > normal_bonus
    
    def test_diminishing_returns_large_camp(self):
        """Large camps have diminishing returns."""
        large_camp = [{"overall": 70, "fighting_style": f"Style{i}"} for i in range(8)]
        medium_camp = [{"overall": 70, "fighting_style": f"Style{i}"} for i in range(4)]
        
        large_bonus, _ = calculate_sparring_bonus(large_camp)
        medium_bonus, _ = calculate_sparring_bonus(medium_camp)
        
        # Large camp should not have proportionally higher bonus
        assert large_bonus < medium_bonus * 2
    
    def test_sparring_bonus_capped_at_15_percent(self):
        """Sparring bonus should never exceed 15%."""
        perfect_camp = [
            {"overall": 95, "fighting_style": f"Style{i}"} for i in range(6)
        ]
        bonus, _ = calculate_sparring_bonus(perfect_camp, coach_has_iron_sharpener=True)
        assert bonus <= 0.15


# ============================================================================
# PRIVATE LESSON TESTS
# ============================================================================

class TestPrivateLessons:
    """Tests for private lesson assignment system."""
    
    def test_low_quality_coach_no_private_lessons(self):
        """Quality 2 coaches don't give private lessons."""
        score = calculate_private_lesson_score(
            coach_quality=2,
            coach_traits=[],
            fighter_age=25,
            fighter_potential=80,
            chemistry=70,
            has_scheduled_fight=True,
            weeks_until_fight=4,
        )
        assert score == 0
    
    def test_upcoming_fight_highest_priority(self):
        """Fighters with upcoming fights get priority."""
        fight_score = calculate_private_lesson_score(
            coach_quality=4,
            coach_traits=[],
            fighter_age=25,
            fighter_potential=70,
            chemistry=50,
            has_scheduled_fight=True,
            weeks_until_fight=3,
        )
        no_fight_score = calculate_private_lesson_score(
            coach_quality=4,
            coach_traits=[],
            fighter_age=25,
            fighter_potential=70,
            chemistry=50,
            has_scheduled_fight=False,
            weeks_until_fight=99,
        )
        assert fight_score > no_fight_score
        assert fight_score >= 60  # Should hit 60 point threshold
    
    def test_high_chemistry_bonus(self):
        """High chemistry increases score."""
        high_chem_score = calculate_private_lesson_score(
            coach_quality=4,
            coach_traits=[],
            fighter_age=25,
            fighter_potential=70,
            chemistry=85,
            has_scheduled_fight=False,
            weeks_until_fight=99,
        )
        low_chem_score = calculate_private_lesson_score(
            coach_quality=4,
            coach_traits=[],
            fighter_age=25,
            fighter_potential=70,
            chemistry=30,
            has_scheduled_fight=False,
            weeks_until_fight=99,
        )
        assert high_chem_score > low_chem_score
    
    def test_diamond_polisher_young_fighter(self):
        """Diamond Polisher trait + young fighter = bonus."""
        dp_young_score = calculate_private_lesson_score(
            coach_quality=4,
            coach_traits=["Diamond Polisher"],
            fighter_age=22,
            fighter_potential=85,
            chemistry=50,
            has_scheduled_fight=False,
            weeks_until_fight=99,
        )
        no_dp_score = calculate_private_lesson_score(
            coach_quality=4,
            coach_traits=[],
            fighter_age=22,
            fighter_potential=85,
            chemistry=50,
            has_scheduled_fight=False,
            weeks_until_fight=99,
        )
        assert dp_young_score > no_dp_score
    
    def test_veterans_touch_old_fighter(self):
        """Veteran's Touch trait + veteran fighter = bonus."""
        vt_old_score = calculate_private_lesson_score(
            coach_quality=4,
            coach_traits=["Veteran's Touch"],
            fighter_age=35,
            fighter_potential=70,
            chemistry=50,
            has_scheduled_fight=False,
            weeks_until_fight=99,
        )
        no_vt_score = calculate_private_lesson_score(
            coach_quality=4,
            coach_traits=[],
            fighter_age=35,
            fighter_potential=70,
            chemistry=50,
            has_scheduled_fight=False,
            weeks_until_fight=99,
        )
        assert vt_old_score > no_vt_score
    
    def test_private_lesson_assignments(self):
        """Test assignment of private lessons to fighters."""
        coaches = [
            {"coach_id": "c1", "quality": 4, "traits": ["Diamond Polisher"]},
            {"coach_id": "c2", "quality": 3, "traits": []},
        ]
        fighters = [
            {"fighter_id": "f1", "age": 22, "potential": 85, "chemistry": 70, 
             "has_scheduled_fight": True, "weeks_until_fight": 4},
            {"fighter_id": "f2", "age": 28, "potential": 70, "chemistry": 50,
             "has_scheduled_fight": False, "weeks_until_fight": 99},
        ]
        
        assignments = get_private_lesson_assignments(coaches, fighters)
        
        # Fighter with fight should get priority
        assert "c1" in assignments
        assert assignments["c1"] == "f1"  # Fight in 4 weeks = top priority
    
    def test_threshold_for_private_lessons(self):
        """Score must reach 40 to trigger private lessons."""
        coaches = [{"coach_id": "c1", "quality": 3, "traits": []}]
        # Fighter with low scores shouldn't trigger lessons
        fighters = [
            {"fighter_id": "f1", "age": 28, "potential": 60, "chemistry": 30,
             "has_scheduled_fight": False, "weeks_until_fight": 99},
        ]
        
        assignments = get_private_lesson_assignments(coaches, fighters)
        # Low scores shouldn't reach threshold
        assert len(assignments) == 0 or assignments.get("c1") is None


# ============================================================================
# TRAINING EVENT TESTS
# ============================================================================

class TestTrainingEvents:
    """Tests for training event generation."""
    
    def test_event_definitions_complete(self):
        """All event types should have definitions."""
        for event_type in TrainingEventType:
            assert event_type in TRAINING_EVENTS, f"Missing definition for {event_type}"
    
    def test_event_has_required_fields(self):
        """Each event should have required fields."""
        required = ["base_chance", "category", "headline"]
        for event_type, data in TRAINING_EVENTS.items():
            for field in required:
                assert field in data, f"{event_type} missing {field}"
    
    def test_event_categories(self):
        """Events should be categorized correctly."""
        categories = set()
        for event_type, data in TRAINING_EVENTS.items():
            categories.add(data["category"])
        
        assert "positive" in categories
        assert "negative" in categories
        assert "neutral" in categories
    
    def test_should_trigger_event_base_chance(self):
        """Base event chance should be around 18%."""
        random.seed(42)
        triggers = 0
        trials = 1000
        
        for _ in range(trials):
            if should_trigger_event(
                fighter_age=28,
                weeks_completed=3,
                total_weeks=8,
                intensity=TrainingIntensity.MODERATE,
                chemistry=50,
                fatigue=20,
            ):
                triggers += 1
        
        # Should be around 18% (+/- 5%)
        trigger_rate = triggers / trials
        assert 0.10 < trigger_rate < 0.30
    
    def test_high_intensity_increases_event_chance(self):
        """Extreme intensity should increase event chance."""
        random.seed(123)
        
        moderate_triggers = sum(
            1 for _ in range(500)
            if should_trigger_event(25, 3, 8, TrainingIntensity.MODERATE, 50, 20)
        )
        
        random.seed(123)
        extreme_triggers = sum(
            1 for _ in range(500)
            if should_trigger_event(25, 3, 8, TrainingIntensity.EXTREME, 50, 20)
        )
        
        assert extreme_triggers > moderate_triggers
    
    def test_generate_training_event(self, training_context):
        """Should generate valid training events."""
        random.seed(42)
        
        event = generate_training_event(
            fighter_name="Test Fighter",
            coach_name="Test Coach",
            context=training_context,
        )
        
        # Event might be None (low chance), but if generated should be valid
        if event:
            assert isinstance(event, TrainingEvent)
            assert event.event_type in TrainingEventType
            assert event.category in ["positive", "negative", "neutral"]
            assert event.headline
    
    def test_chemistry_affects_event_type(self, training_context):
        """Good chemistry should favor positive events."""
        random.seed(42)
        
        # High chemistry context
        high_chem = training_context.copy()
        high_chem["chemistry"] = 85
        
        # Low chemistry context
        low_chem = training_context.copy()
        low_chem["chemistry"] = 25
        
        high_positive = 0
        low_positive = 0
        
        for i in range(100):
            random.seed(i)
            event = generate_training_event("Fighter", "Coach", high_chem)
            if event and event.category == "positive":
                high_positive += 1
            
            random.seed(i)
            event = generate_training_event("Fighter", "Coach", low_chem)
            if event and event.category == "positive":
                low_positive += 1
        
        # High chemistry should have more positive events
        assert high_positive >= low_positive


# ============================================================================
# CAMP JOURNAL TESTS
# ============================================================================

class TestCampJournal:
    """Tests for camp journal functionality."""
    
    def test_create_camp_journal(self):
        """Should create a journal with basic info."""
        journal = CampJournal(
            fighter_id="f1",
            fighter_name="Test Fighter",
            camp_start_week=10,
            focus="STRIKING",
            coach_name="Test Coach",
        )
        
        assert journal.fighter_name == "Test Fighter"
        assert journal.camp_start_week == 10
        assert len(journal.entries) == 0
    
    def test_add_training_entry(self):
        """Should add training entries with gains."""
        journal = CampJournal(
            fighter_id="f1",
            fighter_name="Test Fighter",
            camp_start_week=10,
            focus="STRIKING",
            coach_name="Test Coach",
        )
        
        gains = {"boxing": 2, "kicks": 1, "power": 1}
        entry = journal.add_training_entry(
            week_number=1,
            game_week=10,
            gains=gains,
        )
        
        assert len(journal.entries) == 1
        assert entry.entry_type == JournalEntryType.TRAINING
        assert journal.total_gains["boxing"] == 2
    
    def test_add_event_entry(self):
        """Should add event entries."""
        journal = CampJournal(
            fighter_id="f1",
            fighter_name="Test Fighter",
            camp_start_week=10,
            focus="STRIKING",
            coach_name="Test Coach",
        )
        
        entry = journal.add_event_entry(
            week_number=2,
            game_week=11,
            headline="Breakthrough!",
            description="Something clicked.",
            category="positive",
            stat_changes={"boxing": 2},
        )
        
        assert len(journal.entries) == 1
        assert journal.positive_events == 1
        assert journal.total_events == 1
        assert journal.total_gains["boxing"] == 2
    
    def test_add_injury_entry(self):
        """Should add injury entries."""
        journal = CampJournal(
            fighter_id="f1",
            fighter_name="Test Fighter",
            camp_start_week=10,
            focus="STRIKING",
            coach_name="Test Coach",
        )
        
        entry = journal.add_injury_entry(
            week_number=3,
            game_week=12,
            injury_description="Minor muscle strain",
        )
        
        assert journal.injuries == 1
        assert entry.entry_type == JournalEntryType.INJURY
    
    def test_add_transaction_entry(self):
        """Should track income and expenses."""
        journal = CampJournal(
            fighter_id="f1",
            fighter_name="Test Fighter",
            camp_start_week=10,
            focus="STRIKING",
            coach_name="Test Coach",
        )
        
        journal.add_transaction_entry(1, 10, "Sponsorship", 5000)
        journal.add_transaction_entry(2, 11, "Camp fees", -1000)
        
        assert journal.money_earned == 5000
        assert journal.money_spent == 1000
    
    def test_camp_rating_calculation(self):
        """Should calculate camp rating based on gains and events."""
        journal = CampJournal(
            fighter_id="f1",
            fighter_name="Test Fighter",
            camp_start_week=10,
            focus="STRIKING",
            coach_name="Test Coach",
        )
        
        # Add good gains
        for week in range(1, 9):
            journal.add_training_entry(week, 9 + week, {"boxing": 3, "kicks": 2})
        
        # Add positive events
        journal.add_event_entry(3, 12, "Breakthrough", "Great", "positive")
        journal.add_event_entry(5, 14, "Perfect week", "Amazing", "positive")
        
        rating, stars = journal.get_camp_rating()
        assert stars >= 4  # Should be good rating with high gains
    
    def test_journal_serialization(self):
        """Journal should serialize and deserialize correctly."""
        journal = CampJournal(
            fighter_id="f1",
            fighter_name="Test Fighter",
            camp_start_week=10,
            focus="STRIKING",
            coach_name="Test Coach",
        )
        
        journal.add_training_entry(1, 10, {"boxing": 2})
        journal.add_event_entry(2, 11, "Event", "Desc", "positive")
        
        # Serialize and deserialize
        data = journal.to_dict()
        restored = CampJournal.from_dict(data)
        
        assert restored.fighter_name == journal.fighter_name
        assert len(restored.entries) == len(journal.entries)
        assert restored.positive_events == journal.positive_events


# ============================================================================
# TRAINING CALCULATION TESTS
# ============================================================================

class TestTrainingCalculations:
    """Tests for training gain calculations."""
    
    def test_diminishing_returns_low_stat(self):
        """Low stats should have bonus to improvement."""
        mult = calculate_diminishing_returns(40)
        assert mult > 1.0
    
    def test_diminishing_returns_high_stat(self):
        """High stats should be harder to improve."""
        mult = calculate_diminishing_returns(85)
        assert mult < 1.0
    
    def test_diminishing_returns_elite_stat(self):
        """Elite stats should be very hard to improve."""
        mult = calculate_diminishing_returns(95)
        assert mult <= 0.2
    
    def test_age_modifier_young(self):
        """Young fighters learn faster."""
        mult = calculate_age_modifier(21)
        assert mult > 1.0
    
    def test_age_modifier_prime(self):
        """Prime age should be baseline."""
        mult = calculate_age_modifier(28)
        assert mult == 1.0
    
    def test_age_modifier_old(self):
        """Old fighters learn slower."""
        mult = calculate_age_modifier(37)
        assert mult < 1.0
    
    def test_coach_quality_bonus(self):
        """Higher quality coaches give better bonuses."""
        bonus_1 = calculate_coach_quality_bonus(1)
        bonus_3 = calculate_coach_quality_bonus(3)
        bonus_5 = calculate_coach_quality_bonus(5)
        
        assert bonus_1 < bonus_3 < bonus_5
    
    def test_full_training_gain_calculation(self):
        """Test full training gain with all modifiers."""
        # Good situation
        try:
            from systems.training import CampTier
        except ImportError:
            from training import CampTier
        
        gain = calculate_training_gain(
            base_gain=1.5,
            current_value=60,
            age=24,
            camp_tier=CampTier.NATIONAL,
            coach_quality=4,
            intensity=TrainingIntensity.MODERATE,
            is_focus_attribute=True,
            coach_specialty_matches=True,
            chemistry_multiplier=1.2,
            sparring_bonus=0.10,
            private_lessons=True,
        )
        
        # Should be a good gain with all bonuses
        assert gain >= 2


# ============================================================================
# TRAINING SYSTEM TESTS
# ============================================================================

class TestTrainingSystem:
    """Tests for the TrainingSystem class."""
    
    def test_start_camp(self):
        """Should start a training camp."""
        system = TrainingSystem()
        
        camp = system.start_camp(
            fighter_id="f1",
            camp_id="camp1",
            focus=TrainingFocus.STRIKING,
            intensity=TrainingIntensity.MODERATE,
            weeks=8,
        )
        
        assert camp.fighter_id == "f1"
        assert camp.focus == TrainingFocus.STRIKING
        assert camp.total_weeks == 8
        assert system.has_active_camp("f1")
    
    def test_get_camp(self):
        """Should retrieve active camp."""
        system = TrainingSystem()
        system.start_camp("f1", "camp1", TrainingFocus.WRESTLING)
        
        camp = system.get_camp("f1")
        assert camp is not None
        assert camp.focus == TrainingFocus.WRESTLING
        
        # Non-existent camp
        assert system.get_camp("f999") is None
    
    def test_cancel_camp(self):
        """Should cancel active camp."""
        system = TrainingSystem()
        system.start_camp("f1", "camp1")
        
        assert system.has_active_camp("f1")
        result = system.cancel_camp("f1")
        
        assert result is True
        assert not system.has_active_camp("f1")
    
    def test_system_serialization(self):
        """System should serialize and deserialize."""
        system = TrainingSystem()
        system.start_camp("f1", "camp1", TrainingFocus.STRIKING)
        system.start_camp("f2", "camp2", TrainingFocus.WRESTLING)
        
        data = system.to_dict()
        restored = TrainingSystem.from_dict(data)
        
        assert restored.has_active_camp("f1")
        assert restored.has_active_camp("f2")
        assert restored.get_camp("f1").focus == TrainingFocus.STRIKING


# ============================================================================
# DISPLAY FORMATTING TESTS
# ============================================================================

class TestDisplayFormatting:
    """Tests for display formatting functions."""
    
    def test_format_camp_journal(self):
        """Should format journal for display."""
        journal = CampJournal(
            fighter_id="f1",
            fighter_name="Test Fighter",
            camp_start_week=10,
            focus="STRIKING",
            coach_name="Test Coach",
        )
        
        journal.add_training_entry(1, 10, {"boxing": 2, "kicks": 1})
        journal.add_event_entry(1, 10, "Great day!", "Everything clicked.", "positive")
        
        lines = format_camp_journal(journal)
        
        assert len(lines) > 0
        assert "Test Fighter" in "\n".join(lines)
        assert "WEEK 1" in "\n".join(lines)
    
    def test_format_camp_summary(self):
        """Should format camp summary for display."""
        try:
            from systems.training_camp import ActiveTrainingCamp, TrainingFocus as TCFocus, TrainingIntensity as TCIntensity
        except ImportError:
            from training_camp import ActiveTrainingCamp, TrainingFocus as TCFocus, TrainingIntensity as TCIntensity
        
        camp = ActiveTrainingCamp(
            camp_id="c1",
            fighter_id="f1",
            fighter_name="Test Fighter",
            focus=TCFocus.STRIKING,
            intensity=TCIntensity.MODERATE,
            facility_tier="REGIONAL",
            total_weeks=8,
            weeks_completed=8,
            total_gains={"boxing": 8, "kicks": 6, "power": 4},
        )
        
        lines = format_camp_summary(camp)
        
        assert len(lines) > 0
        assert "COMPLETE" in "\n".join(lines)
        assert "Test Fighter" in "\n".join(lines)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for the full training system."""
    
    def test_full_camp_simulation(self):
        """Simulate a complete training camp."""
        try:
            from systems.training import CampTier
        except ImportError:
            from training import CampTier
        
        system = TrainingSystem()
        camp = system.start_camp(
            fighter_id="f1",
            camp_id="camp1",
            focus=TrainingFocus.STRIKING,
            intensity=TrainingIntensity.MODERATE,
            weeks=8,
        )
        
        attributes = {
            "boxing": 60, "kicks": 58, "clinch_striking": 55,
            "striking_defense": 52, "cardio": 65,
        }
        
        total_gains = {}
        events_triggered = 0
        
        for week in range(8):
            gains, event = system.process_training_week(
                fighter_id="f1",
                current_attributes=attributes,
                age=25,
                camp_tier=CampTier.REGIONAL,
                coach_quality=4,
                fatigue=week * 5,
                coach_specialty="Striking",
                chemistry=70,
                fighter_name="Test Fighter",
                coach_name="Test Coach",
            )
            
            # Apply gains
            for attr, gain in gains.items():
                attributes[attr] = attributes.get(attr, 50) + gain
                total_gains[attr] = total_gains.get(attr, 0) + gain
            
            if event:
                events_triggered += 1
        
        # Should have made progress
        total_points = sum(total_gains.values())
        assert total_points > 0
        
        # Camp should be complete
        assert camp.is_complete


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
