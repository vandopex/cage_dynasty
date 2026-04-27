# tests/test_world.py
# Module 30: World Simulation Tests
# Tests: 55

"""
Tests for the World Simulation module.
"""

import pytest
from simulation.world import (
    # AI Personality
    CampPhilosophy,
    RiskTolerance,
    TalentStrategy,
    NegotiationStyle,
    CampPersonality,
    generate_camp_personality,
    
    # AI Decision Making
    FightOffer,
    CampAI,
    
    # World State
    ScheduledFight,
    ScheduledEvent,
    WeeklyReport,
    
    # World Simulation
    WorldSimulation,
    get_world_simulation,
    reset_world_simulation,
    generate_personality_description,
)


# ============================================================================
# CAMP PHILOSOPHY TESTS
# ============================================================================

class TestCampPhilosophy:
    """Tests for CampPhilosophy enum"""
    
    def test_all_philosophies_defined(self):
        """Should have all expected philosophies"""
        assert CampPhilosophy.STRIKER_FACTORY.value == "striker_factory"
        assert CampPhilosophy.GRAPPLING_ACADEMY.value == "grappling_academy"
        assert CampPhilosophy.WELL_ROUNDED.value == "well_rounded"
        assert CampPhilosophy.CARDIO_KINGS.value == "cardio_kings"
        assert CampPhilosophy.POWER_HOUSE.value == "power_house"


class TestRiskTolerance:
    """Tests for RiskTolerance enum"""
    
    def test_all_tolerances_defined(self):
        """Should have all expected risk tolerances"""
        assert RiskTolerance.CONSERVATIVE.value == "conservative"
        assert RiskTolerance.MODERATE.value == "moderate"
        assert RiskTolerance.AGGRESSIVE.value == "aggressive"
        assert RiskTolerance.RECKLESS.value == "reckless"


class TestTalentStrategy:
    """Tests for TalentStrategy enum"""
    
    def test_all_strategies_defined(self):
        """Should have all expected strategies"""
        assert TalentStrategy.PROSPECT_DEVELOPER.value == "prospect_developer"
        assert TalentStrategy.VETERAN_COLLECTOR.value == "veteran_collector"
        assert TalentStrategy.ELITE_HUNTER.value == "elite_hunter"
        assert TalentStrategy.OPPORTUNIST.value == "opportunist"
        assert TalentStrategy.HOMETOWN_HERO.value == "hometown_hero"


# ============================================================================
# CAMP PERSONALITY TESTS
# ============================================================================

class TestCampPersonality:
    """Tests for CampPersonality dataclass"""
    
    def test_creation(self):
        """Should create personality with correct values"""
        personality = CampPersonality(
            camp_id="camp_1",
            philosophy=CampPhilosophy.STRIKER_FACTORY,
            risk_tolerance=RiskTolerance.AGGRESSIVE,
        )
        
        assert personality.camp_id == "camp_1"
        assert personality.philosophy == CampPhilosophy.STRIKER_FACTORY
        assert personality.risk_tolerance == RiskTolerance.AGGRESSIVE
    
    def test_default_values(self):
        """Should have sensible defaults"""
        personality = CampPersonality(camp_id="test")
        
        assert personality.aggression == 50
        assert personality.patience == 50
        assert personality.loyalty == 50
        assert personality.activity_level == 1.0
    
    def test_fight_acceptance_modifier_aggressive(self):
        """Aggressive camps should accept more fights"""
        aggressive = CampPersonality(
            camp_id="test",
            risk_tolerance=RiskTolerance.AGGRESSIVE,
        )
        conservative = CampPersonality(
            camp_id="test",
            risk_tolerance=RiskTolerance.CONSERVATIVE,
        )
        
        assert aggressive.get_fight_acceptance_modifier(True) > \
               conservative.get_fight_acceptance_modifier(True)
    
    def test_signing_interest_prospect_developer(self):
        """Prospect developers should prefer young fighters"""
        developer = CampPersonality(
            camp_id="test",
            talent_strategy=TalentStrategy.PROSPECT_DEVELOPER,
        )
        
        young_interest = developer.get_signing_interest(22, 60)
        old_interest = developer.get_signing_interest(35, 60)
        
        assert young_interest > old_interest
    
    def test_signing_interest_elite_hunter(self):
        """Elite hunters should prefer high-rated fighters"""
        hunter = CampPersonality(
            camp_id="test",
            talent_strategy=TalentStrategy.ELITE_HUNTER,
        )
        
        elite_interest = hunter.get_signing_interest(28, 85)
        average_interest = hunter.get_signing_interest(28, 55)
        
        assert elite_interest > average_interest
    
    def test_serialization(self):
        """Should serialize and deserialize correctly"""
        personality = CampPersonality(
            camp_id="camp_1",
            philosophy=CampPhilosophy.GRAPPLING_ACADEMY,
            risk_tolerance=RiskTolerance.CONSERVATIVE,
            aggression=70,
            preferred_weight_classes=["Lightweight", "Welterweight"],
        )
        
        data = personality.to_dict()
        restored = CampPersonality.from_dict(data)
        
        assert restored.camp_id == personality.camp_id
        assert restored.philosophy == personality.philosophy
        assert restored.aggression == personality.aggression
        assert restored.preferred_weight_classes == personality.preferred_weight_classes


class TestGenerateCampPersonality:
    """Tests for personality generation"""
    
    def test_generates_unique_personalities(self):
        """Should generate different personalities"""
        personalities = [generate_camp_personality(f"camp_{i}") for i in range(10)]
        
        # Check for variety (not all the same)
        philosophies = set(p.philosophy for p in personalities)
        assert len(philosophies) > 1
    
    def test_generates_valid_traits(self):
        """Should generate valid trait values"""
        for _ in range(20):
            personality = generate_camp_personality("test")
            
            assert 10 <= personality.aggression <= 90
            assert 10 <= personality.patience <= 90
            assert 10 <= personality.loyalty <= 90
            assert 0.6 <= personality.activity_level <= 1.4
    
    def test_preferred_weight_classes(self):
        """Should generate weight class preferences"""
        personality = generate_camp_personality("test")
        
        assert 1 <= len(personality.preferred_weight_classes) <= 3


# ============================================================================
# FIGHT OFFER TESTS
# ============================================================================

class TestFightOffer:
    """Tests for FightOffer dataclass"""
    
    def test_creation(self):
        """Should create offer with correct values"""
        offer = FightOffer(
            opponent_id="opp_1",
            opponent_name="John Doe",
            opponent_rating=75,
            opponent_rank=5,
            is_title_fight=True,
            is_main_event=True,
            weeks_until_fight=8,
            purse=100000,
        )
        
        assert offer.opponent_id == "opp_1"
        assert offer.is_title_fight
        assert offer.purse == 100000
    
    def test_is_favorable(self):
        """Should correctly identify favorable offers"""
        good_offer = FightOffer(
            opponent_id="opp",
            opponent_name="Opp",
            opponent_rating=70,
            opponent_rank=10,
            is_title_fight=False,
            is_main_event=False,
            weeks_until_fight=8,
            purse=50000,
        )
        
        short_notice = FightOffer(
            opponent_id="opp",
            opponent_name="Opp",
            opponent_rating=70,
            opponent_rank=10,
            is_title_fight=False,
            is_main_event=False,
            weeks_until_fight=3,  # Too short
            purse=50000,
        )
        
        assert good_offer.is_favorable
        assert not short_notice.is_favorable


# ============================================================================
# CAMP AI TESTS
# ============================================================================

class TestCampAI:
    """Tests for CampAI decision making"""
    
    @pytest.fixture
    def ai(self):
        """Create a standard AI for testing"""
        personality = CampPersonality(
            camp_id="test",
            risk_tolerance=RiskTolerance.MODERATE,
            ambition=60,
        )
        return CampAI(personality=personality)
    
    @pytest.fixture
    def basic_offer(self):
        """Create a basic fight offer"""
        return FightOffer(
            opponent_id="opp_1",
            opponent_name="Opponent",
            opponent_rating=70,
            opponent_rank=10,
            is_title_fight=False,
            is_main_event=False,
            weeks_until_fight=8,
            purse=50000,
        )
    
    def test_evaluate_favorable_fight(self, ai, basic_offer):
        """Should consider accepting favorable fights"""
        # Run multiple times due to randomness
        accepts = 0
        for _ in range(20):
            accept, reason = ai.evaluate_fight_offer(
                fighter_id="fighter_1",
                fighter_rating=75,  # Higher than opponent
                fighter_rank=8,
                offer=basic_offer,
            )
            if accept:
                accepts += 1
        
        # Should accept at least some favorable fights
        assert accepts > 5
    
    def test_evaluate_title_fight_bonus(self, ai):
        """Title fights should have higher acceptance"""
        title_offer = FightOffer(
            opponent_id="opp",
            opponent_name="Champ",
            opponent_rating=80,
            opponent_rank=0,
            is_title_fight=True,
            is_main_event=True,
            weeks_until_fight=10,
            purse=200000,
        )
        
        accepts = 0
        for _ in range(20):
            accept, reason = ai.evaluate_fight_offer(
                fighter_id="fighter",
                fighter_rating=75,
                fighter_rank=1,
                offer=title_offer,
            )
            if accept:
                accepts += 1
        
        # High acceptance for title shots
        assert accepts > 10
    
    def test_conservative_ai_rejects_tough_fights(self):
        """Conservative AI should reject tough matchups more often"""
        conservative_personality = CampPersonality(
            camp_id="test",
            risk_tolerance=RiskTolerance.CONSERVATIVE,
        )
        conservative_ai = CampAI(personality=conservative_personality)
        
        tough_offer = FightOffer(
            opponent_id="opp",
            opponent_name="Killer",
            opponent_rating=90,  # Much higher
            opponent_rank=2,
            is_title_fight=False,
            is_main_event=False,
            weeks_until_fight=8,
            purse=50000,
        )
        
        accepts = 0
        for _ in range(20):
            accept, _ = conservative_ai.evaluate_fight_offer(
                fighter_id="fighter",
                fighter_rating=65,  # Much lower
                fighter_rank=12,
                offer=tough_offer,
            )
            if accept:
                accepts += 1
        
        # Should reject most tough fights
        assert accepts < 8
    
    def test_evaluate_signing(self, ai):
        """Should evaluate signings based on strategy"""
        sign, offer_amount, reason = ai.evaluate_signing(
            fighter_name="Young Gun",
            fighter_age=22,
            fighter_rating=65,
            asking_price=5000,
            camp_budget=100000,
            current_roster_size=3,
            max_roster_size=10,
        )
        
        # Should return valid response
        assert isinstance(sign, bool)
        assert offer_amount >= 0
        assert len(reason) > 0
    
    def test_signing_respects_roster_limit(self, ai):
        """Should reject if roster full"""
        sign, offer_amount, reason = ai.evaluate_signing(
            fighter_name="Fighter",
            fighter_age=25,
            fighter_rating=70,
            asking_price=5000,
            camp_budget=100000,
            current_roster_size=10,
            max_roster_size=10,
        )
        
        assert not sign
        assert "Roster full" in reason
    
    def test_get_training_focus(self, ai):
        """Should return training focus based on philosophy"""
        focus = ai.get_training_focus({"striking": 60, "grappling": 70})
        
        assert focus in ["striking", "boxing", "kicks", "grappling", 
                         "wrestling", "bjj", "cardio", "strength"]
    
    def test_should_release_fighter(self, ai):
        """Should evaluate fighter releases"""
        release, reason = ai.should_release_fighter(
            fighter_age=40,
            fighter_rating=45,
            recent_record=(0, 4),
            months_without_fight=12,
        )
        
        # High chance of release for old, low-rated, losing fighter
        # But loyalty can save them, so just check it returns valid result
        assert isinstance(release, bool)
        assert len(reason) > 0


# ============================================================================
# SCHEDULED EVENT TESTS
# ============================================================================

class TestScheduledFight:
    """Tests for ScheduledFight dataclass"""
    
    def test_creation(self):
        """Should create fight with correct values"""
        fight = ScheduledFight(
            fighter1_id="f1",
            fighter2_id="f2",
            fighter1_name="Fighter One",
            fighter2_name="Fighter Two",
            weight_class="Lightweight",
            is_title_fight=True,
            rounds=5,
        )
        
        assert fight.fighter1_id == "f1"
        assert fight.is_title_fight
        assert fight.rounds == 5
    
    def test_to_dict(self):
        """Should serialize correctly"""
        fight = ScheduledFight(
            fighter1_id="f1",
            fighter2_id="f2",
            fighter1_name="One",
            fighter2_name="Two",
            weight_class="Welterweight",
        )
        
        data = fight.to_dict()
        assert data["fighter1_id"] == "f1"
        assert data["weight_class"] == "Welterweight"


class TestScheduledEvent:
    """Tests for ScheduledEvent dataclass"""
    
    def test_creation(self):
        """Should create event with correct values"""
        event = ScheduledEvent(
            event_id="evt_1",
            event_name="DFC 100",
            date="2025-06-15",
            location="Las Vegas",
        )
        
        assert event.event_id == "evt_1"
        assert event.fight_count == 0
        assert not event.has_title_fight
    
    def test_add_fight(self):
        """Should add fights to event"""
        event = ScheduledEvent(
            event_id="evt_1",
            event_name="DFC 100",
            date="2025-06-15",
            location="Las Vegas",
        )
        
        fight = ScheduledFight(
            fighter1_id="f1",
            fighter2_id="f2",
            fighter1_name="One",
            fighter2_name="Two",
            weight_class="Lightweight",
            is_title_fight=True,
        )
        
        event.add_fight(fight)
        
        assert event.fight_count == 1
        assert event.has_title_fight
    
    def test_get_main_event(self):
        """Should return main event fight"""
        event = ScheduledEvent(
            event_id="evt_1",
            event_name="DFC 100",
            date="2025-06-15",
            location="Las Vegas",
        )
        
        prelim = ScheduledFight(
            fighter1_id="f1", fighter2_id="f2",
            fighter1_name="A", fighter2_name="B",
            weight_class="Flyweight",
        )
        main = ScheduledFight(
            fighter1_id="f3", fighter2_id="f4",
            fighter1_name="C", fighter2_name="D",
            weight_class="Heavyweight",
            is_main_event=True,
        )
        
        event.add_fight(prelim)
        event.add_fight(main)
        
        assert event.get_main_event() == main


# ============================================================================
# WEEKLY REPORT TESTS
# ============================================================================

class TestWeeklyReport:
    """Tests for WeeklyReport dataclass"""
    
    def test_creation(self):
        """Should create report with correct values"""
        report = WeeklyReport(
            week_number=10,
            date="2025-03-15",
        )
        
        assert report.week_number == 10
        assert report.fights_completed == 0
    
    def test_to_dict(self):
        """Should serialize correctly"""
        report = WeeklyReport(
            week_number=10,
            date="2025-03-15",
            fights_completed=12,
            knockouts=3,
        )
        
        data = report.to_dict()
        assert data["week_number"] == 10
        assert data["fights_completed"] == 12
        assert data["knockouts"] == 3


# ============================================================================
# WORLD SIMULATION TESTS
# ============================================================================

class TestWorldSimulation:
    """Tests for WorldSimulation class"""
    
    @pytest.fixture
    def world(self):
        """Fresh world simulation for each test"""
        return WorldSimulation()
    
    def test_creation(self, world):
        """Should create world with initial state"""
        assert world.week_number == 0
        assert len(world.fighter_ids) == 0
        assert len(world.camp_ids) == 0
    
    def test_register_fighter(self, world):
        """Should register fighters"""
        world.register_fighter("fighter_1")
        
        assert "fighter_1" in world.fighter_ids
        assert "fighter_1" in world.free_agent_ids
    
    def test_register_fighter_with_camp(self, world):
        """Should register fighter with camp"""
        world.register_fighter("fighter_1", camp_id="camp_1")
        
        assert "fighter_1" in world.fighter_ids
        assert "fighter_1" not in world.free_agent_ids
    
    def test_register_camp(self, world):
        """Should register camp with personality"""
        world.register_camp("camp_1")
        
        assert "camp_1" in world.camp_ids
        assert "camp_1" in world.camp_personalities
        assert "camp_1" in world.camp_ais
    
    def test_advance_week(self, world):
        """Should advance week and return report"""
        report = world.advance_week()
        
        assert world.week_number == 1
        assert report.week_number == 1
    
    def test_advance_multiple_weeks(self, world):
        """Should advance multiple weeks"""
        reports = world.advance_weeks(4)
        
        assert world.week_number == 4
        assert len(reports) == 4
    
    def test_schedule_event(self, world):
        """Should schedule events"""
        event = world.schedule_event(weeks_from_now=4)
        
        assert event is not None
        assert len(world.upcoming_events) == 1
        assert world.event_counter == 1
    
    def test_book_fight(self, world):
        """Should book fights on events"""
        world.register_fighter("f1")
        world.register_fighter("f2")
        
        event = world.schedule_event(weeks_from_now=4)
        
        success = world.book_fight(
            event_id=event.event_id,
            fighter1_id="f1",
            fighter2_id="f2",
            fighter1_name="Fighter One",
            fighter2_name="Fighter Two",
            weight_class="Lightweight",
        )
        
        assert success
        assert "f1" in world.booked_fighters
        assert "f2" in world.booked_fighters
        assert event.fight_count == 1
    
    def test_cannot_double_book(self, world):
        """Should prevent double booking"""
        world.register_fighter("f1")
        world.register_fighter("f2")
        world.register_fighter("f3")
        
        event = world.schedule_event(weeks_from_now=4)
        
        world.book_fight(
            event_id=event.event_id,
            fighter1_id="f1",
            fighter2_id="f2",
            fighter1_name="One",
            fighter2_name="Two",
            weight_class="Lightweight",
        )
        
        # Try to book f1 again
        success = world.book_fight(
            event_id=event.event_id,
            fighter1_id="f1",
            fighter2_id="f3",
            fighter1_name="One",
            fighter2_name="Three",
            weight_class="Welterweight",
        )
        
        assert not success
    
    def test_injured_fighter_unavailable(self, world):
        """Injured fighters should not be available"""
        world.register_fighter("f1")
        world.injure_fighter("f1", weeks=8)
        
        assert not world.is_fighter_available("f1")
        assert "f1" in world.injured_ids
    
    def test_injury_healing(self, world):
        """Injuries should heal over time"""
        world.register_fighter("f1")
        world.injure_fighter("f1", weeks=2)
        
        world.advance_week()
        assert "f1" in world.injured_ids
        
        world.advance_week()
        assert "f1" not in world.injured_ids
        assert world.is_fighter_available("f1")
    
    def test_retire_fighter(self, world):
        """Should retire fighters"""
        world.register_fighter("f1")
        world.retire_fighter("f1")
        
        assert "f1" in world.retired_ids
        assert "f1" not in world.fighter_ids
        assert not world.is_fighter_available("f1")
    
    def test_get_next_event(self, world):
        """Should get next scheduled event"""
        world.schedule_event(weeks_from_now=4, event_name="Second")
        world.schedule_event(weeks_from_now=2, event_name="First")
        
        next_event = world.get_next_event()
        assert next_event.event_name == "First"
    
    def test_get_available_fighters(self, world):
        """Should return available fighters"""
        world.register_fighter("f1")
        world.register_fighter("f2")
        world.register_fighter("f3")
        
        world.injure_fighter("f2", weeks=4)
        
        available = world.get_available_fighters()
        
        assert "f1" in available
        assert "f2" not in available
        assert "f3" in available
    
    def test_get_world_stats(self, world):
        """Should return world statistics"""
        world.register_fighter("f1")
        world.register_fighter("f2")
        world.register_camp("camp_1")
        
        stats = world.get_world_stats()
        
        assert stats["total_fighters"] == 2
        assert stats["active_camps"] == 1
        assert stats["week_number"] == 0
    
    def test_get_camp_personality_summary(self, world):
        """Should return personality summary"""
        world.register_camp("camp_1")
        
        summary = world.get_camp_personality_summary("camp_1")
        
        assert summary is not None
        assert "philosophy" in summary
        assert "risk_tolerance" in summary
        assert "key_traits" in summary
    
    def test_serialization(self, world):
        """Should serialize and deserialize correctly"""
        world.register_fighter("f1")
        world.register_camp("camp_1")
        world.schedule_event(weeks_from_now=4)
        world.advance_week()
        
        data = world.to_dict()
        restored = WorldSimulation.from_dict(data)
        
        assert restored.week_number == 1
        assert "f1" in restored.fighter_ids
        assert "camp_1" in restored.camp_ids
        assert len(restored.upcoming_events) == 1


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions"""
    
    def test_get_world_simulation_singleton(self):
        """Should return same instance"""
        reset_world_simulation()
        w1 = get_world_simulation()
        w2 = get_world_simulation()
        
        assert w1 is w2
    
    def test_reset_world_simulation(self):
        """Should create fresh instance"""
        w1 = get_world_simulation()
        w1.register_fighter("test")
        
        reset_world_simulation()
        w2 = get_world_simulation()
        
        assert "test" not in w2.fighter_ids
    
    def test_generate_personality_description(self):
        """Should generate readable description"""
        personality = CampPersonality(
            camp_id="test",
            philosophy=CampPhilosophy.STRIKER_FACTORY,
            risk_tolerance=RiskTolerance.AGGRESSIVE,
            ambition=80,
            loyalty=25,
        )
        
        desc = generate_personality_description(personality)
        
        assert "striker" in desc.lower()
        assert "challenge" in desc.lower() or "risk" in desc.lower()
        assert "title" in desc.lower() or "glory" in desc.lower()
