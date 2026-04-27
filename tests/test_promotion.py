# tests/test_promotion.py
# Tests for Module 7: Promotion Entity
# Lines: 324

"""
Comprehensive tests for entities/promotion.py

Run with: python3 -m pytest tests/test_promotion.py -v
"""

import pytest
from core.types import WeightClass, EventType, WEIGHT_CLASS_ORDER
from core.calendar import GameDate
from core.events import event_bus
from entities.promotion import (
    Promotion, create_promotion, create_dfc,
    Division, ScheduledEvent
)


class TestDivision:
    """Tests for Division class"""
    
    def test_creation(self):
        """Division should be created for a weight class"""
        div = Division(WeightClass.LIGHTWEIGHT)
        
        assert div.weight_class == WeightClass.LIGHTWEIGHT
        assert div.name == "Lightweight"
        assert div.champion_id is None
        assert div.has_champion is False
    
    def test_set_champion(self):
        """set_champion should set the champion"""
        div = Division(WeightClass.WELTERWEIGHT)
        previous = div.set_champion("fighter_001")
        
        assert div.champion_id == "fighter_001"
        assert div.has_champion is True
        assert previous is None
    
    def test_set_champion_returns_previous(self):
        """set_champion should return previous champion"""
        div = Division(WeightClass.MIDDLEWEIGHT)
        div.set_champion("fighter_001")
        previous = div.set_champion("fighter_002")
        
        assert div.champion_id == "fighter_002"
        assert previous == "fighter_001"
    
    def test_vacate_title(self):
        """vacate_title should remove champion"""
        div = Division(WeightClass.HEAVYWEIGHT)
        div.set_champion("fighter_001")
        previous = div.vacate_title()
        
        assert div.champion_id is None
        assert div.has_champion is False
        assert previous == "fighter_001"
    
    def test_rankings(self):
        """Should manage rankings"""
        div = Division(WeightClass.FEATHERWEIGHT)
        
        div.set_rank("fighter_001", 1)
        div.set_rank("fighter_002", 2)
        div.set_rank("fighter_003", 3)
        
        assert div.get_rank("fighter_001") == 1
        assert div.get_rank("fighter_002") == 2
        assert div.get_rank("fighter_003") == 3
        assert div.ranked_count == 3
    
    def test_champion_rank_is_zero(self):
        """Champion should have rank 0"""
        div = Division(WeightClass.BANTAMWEIGHT)
        div.set_champion("champ")
        
        assert div.get_rank("champ") == 0
    
    def test_unranked_returns_none(self):
        """Unranked fighter should return None"""
        div = Division(WeightClass.FLYWEIGHT)
        
        assert div.get_rank("unknown") is None
        assert div.is_ranked("unknown") is False
    
    def test_set_champion_removes_from_rankings(self):
        """New champion should be removed from rankings"""
        div = Division(WeightClass.LIGHTWEIGHT)
        div.set_rank("fighter_001", 1)
        div.set_rank("fighter_002", 2)
        
        div.set_champion("fighter_001")
        
        assert div.champion_id == "fighter_001"
        assert "fighter_001" not in div.rankings
        assert div.get_rank("fighter_002") == 1  # Moved up
    
    def test_get_top_contenders(self):
        """Should return top N contenders"""
        div = Division(WeightClass.WELTERWEIGHT)
        for i in range(10):
            div.set_rank(f"fighter_{i}", i + 1)
        
        top5 = div.get_top_contenders(5)
        assert len(top5) == 5
        assert top5[0] == "fighter_0"
    
    def test_remove_from_rankings(self):
        """Should remove fighter from rankings"""
        div = Division(WeightClass.MIDDLEWEIGHT)
        div.set_rank("fighter_001", 1)
        
        result = div.remove_from_rankings("fighter_001")
        
        assert result is True
        assert div.is_ranked("fighter_001") is False
    
    def test_serialization(self):
        """Division should serialize and deserialize"""
        div = Division(WeightClass.HEAVYWEIGHT)
        div.set_champion("champ_001")
        div.set_rank("fighter_001", 1)
        div.set_rank("fighter_002", 2)
        
        data = div.to_dict()
        restored = Division.from_dict(data)
        
        assert restored.weight_class == div.weight_class
        assert restored.champion_id == div.champion_id
        assert restored.rankings == div.rankings


class TestScheduledEvent:
    """Tests for ScheduledEvent class"""
    
    def test_creation(self):
        """Event should be created with correct info"""
        event = ScheduledEvent(
            event_id="evt_001",
            name="DFC 100",
            date=GameDate(2025, 6, 15),
            location="Las Vegas"
        )
        
        assert event.name == "DFC 100"
        assert event.location == "Las Vegas"
        assert event.fight_count == 0
        assert event.is_completed is False
    
    def test_add_fight(self):
        """Should add fights to event"""
        event = ScheduledEvent(
            event_id="evt_001",
            name="DFC 100",
            date=GameDate(2025, 6, 15),
            location="Las Vegas"
        )
        
        event.add_fight("fight_001")
        event.add_fight("fight_002", is_main_event=True)
        
        assert event.fight_count == 2
        assert event.main_event_fight_id == "fight_002"
    
    def test_string_representation(self):
        """String should show name and date"""
        event = ScheduledEvent(
            event_id="evt_001",
            name="DFC 100",
            date=GameDate(2025, 6, 15),
            location="Las Vegas"
        )
        
        result = str(event)
        assert "DFC 100" in result


class TestPromotionCreation:
    """Tests for creating promotions"""
    
    def test_default_creation(self):
        """Should create with default DFC name"""
        promo = create_promotion()
        
        assert promo.name == "Dynasty Fighting Championship"
        assert promo.abbreviation == "DFC"
        assert promo.id is not None
    
    def test_custom_name(self):
        """Should accept custom name"""
        promo = create_promotion(
            name="Custom Fighting League",
            abbreviation="CFL"
        )
        
        assert promo.name == "Custom Fighting League"
        assert promo.abbreviation == "CFL"
    
    def test_create_dfc_helper(self):
        """create_dfc should create default promotion"""
        dfc = create_dfc()
        
        assert dfc.name == "Dynasty Fighting Championship"
        assert dfc.abbreviation == "DFC"
    
    def test_all_divisions_created(self):
        """Should have all weight class divisions"""
        promo = create_promotion()
        
        for wc in WEIGHT_CLASS_ORDER:
            div = promo.get_division(wc)
            assert div is not None
            assert div.weight_class == wc


class TestPromotionDivisions:
    """Tests for division management"""
    
    @pytest.fixture
    def promo(self):
        return create_promotion()
    
    def test_get_division(self, promo):
        """Should retrieve division by weight class"""
        lw = promo.get_division(WeightClass.LIGHTWEIGHT)
        
        assert lw is not None
        assert lw.weight_class == WeightClass.LIGHTWEIGHT
    
    def test_set_champion(self, promo):
        """Should set division champion"""
        promo.set_champion(WeightClass.LIGHTWEIGHT, "fighter_001")
        
        assert promo.get_champion(WeightClass.LIGHTWEIGHT) == "fighter_001"
    
    def test_is_champion(self, promo):
        """is_champion should detect champions"""
        promo.set_champion(WeightClass.WELTERWEIGHT, "fighter_001")
        
        assert promo.is_champion("fighter_001") is True
        assert promo.is_champion("fighter_002") is False
    
    def test_get_all_champions(self, promo):
        """Should get all champions"""
        promo.set_champion(WeightClass.LIGHTWEIGHT, "lw_champ")
        promo.set_champion(WeightClass.WELTERWEIGHT, "ww_champ")
        
        champions = promo.get_all_champions()
        
        assert champions[WeightClass.LIGHTWEIGHT] == "lw_champ"
        assert champions[WeightClass.WELTERWEIGHT] == "ww_champ"
        assert champions[WeightClass.HEAVYWEIGHT] is None
    
    def test_vacate_title(self, promo):
        """Should vacate a title"""
        promo.set_champion(WeightClass.MIDDLEWEIGHT, "fighter_001")
        previous = promo.vacate_title(WeightClass.MIDDLEWEIGHT)
        
        assert previous == "fighter_001"
        assert promo.get_champion(WeightClass.MIDDLEWEIGHT) is None
    
    def test_set_rank(self, promo):
        """Should set fighter rank"""
        promo.set_rank(WeightClass.LIGHTWEIGHT, "fighter_001", 1)
        
        assert promo.get_rank(WeightClass.LIGHTWEIGHT, "fighter_001") == 1
    
    def test_get_rankings(self, promo):
        """Should get division rankings"""
        promo.set_rank(WeightClass.LIGHTWEIGHT, "fighter_001", 1)
        promo.set_rank(WeightClass.LIGHTWEIGHT, "fighter_002", 2)
        
        rankings = promo.get_rankings(WeightClass.LIGHTWEIGHT)
        
        assert len(rankings) == 2
        assert rankings[0] == "fighter_001"


class TestPromotionRoster:
    """Tests for fighter roster management"""
    
    @pytest.fixture
    def promo(self):
        return create_promotion()
    
    def test_empty_roster(self, promo):
        """New promotion should have empty roster"""
        assert promo.roster_size == 0
        assert promo.signed_fighter_ids == []
    
    def test_sign_fighter(self, promo):
        """Should sign fighters"""
        result = promo.sign_fighter("fighter_001")
        
        assert result is True
        assert promo.is_signed("fighter_001") is True
        assert promo.roster_size == 1
    
    def test_cannot_sign_twice(self, promo):
        """Should not sign same fighter twice"""
        promo.sign_fighter("fighter_001")
        result = promo.sign_fighter("fighter_001")
        
        assert result is False
        assert promo.roster_size == 1
    
    def test_release_fighter(self, promo):
        """Should release fighters"""
        promo.sign_fighter("fighter_001")
        result = promo.release_fighter("fighter_001")
        
        assert result is True
        assert promo.is_signed("fighter_001") is False
    
    def test_release_removes_from_rankings(self, promo):
        """Releasing should remove from rankings"""
        promo.sign_fighter("fighter_001")
        promo.set_rank(WeightClass.LIGHTWEIGHT, "fighter_001", 1)
        
        promo.release_fighter("fighter_001")
        
        assert promo.get_rank(WeightClass.LIGHTWEIGHT, "fighter_001") is None
    
    def test_release_vacates_title(self, promo):
        """Releasing champion should vacate title"""
        promo.sign_fighter("fighter_001")
        promo.set_champion(WeightClass.LIGHTWEIGHT, "fighter_001")
        
        promo.release_fighter("fighter_001")
        
        assert promo.get_champion(WeightClass.LIGHTWEIGHT) is None


class TestPromotionEvents:
    """Tests for event scheduling"""
    
    @pytest.fixture
    def promo(self):
        return create_promotion()
    
    def test_schedule_event(self, promo):
        """Should schedule events"""
        event = promo.schedule_event(
            date=GameDate(2025, 6, 15),
            location="Las Vegas"
        )
        
        assert event is not None
        assert event.name == "DFC 1"
        assert len(promo.scheduled_events) == 1
    
    def test_custom_event_name(self, promo):
        """Should accept custom event names"""
        event = promo.schedule_event(
            date=GameDate(2025, 12, 31),
            name="DFC: New Year's Eve",
            is_ppv=True
        )
        
        assert event.name == "DFC: New Year's Eve"
        assert event.is_ppv is True
    
    def test_event_numbering(self, promo):
        """Events should auto-number"""
        promo.schedule_event(GameDate(2025, 1, 1))
        promo.schedule_event(GameDate(2025, 2, 1))
        promo.schedule_event(GameDate(2025, 3, 1))
        
        events = promo.scheduled_events
        assert events[0].name == "DFC 1"
        assert events[1].name == "DFC 2"
        assert events[2].name == "DFC 3"
    
    def test_next_event(self, promo):
        """Should get next scheduled event"""
        promo.schedule_event(GameDate(2025, 6, 15))
        promo.schedule_event(GameDate(2025, 3, 1))  # Earlier
        
        next_event = promo.next_event
        assert next_event.date.month == 3  # Earlier date
    
    def test_complete_event(self, promo):
        """Should complete events"""
        event = promo.schedule_event(GameDate(2025, 1, 1))
        event.add_fight("fight_001")
        event.add_fight("fight_002")
        
        result = promo.complete_event(event.event_id)
        
        assert result is True
        assert promo.total_events == 1
        assert promo.total_fights == 2
        assert len(promo.scheduled_events) == 0


class TestPromotionSerialization:
    """Tests for save/load"""
    
    def test_to_dict_from_dict(self):
        """Promotion should serialize and deserialize"""
        original = create_promotion("Test Promotion", "TP")
        original.sign_fighter("fighter_001")
        original.set_champion(WeightClass.LIGHTWEIGHT, "fighter_001")
        original.set_rank(WeightClass.LIGHTWEIGHT, "fighter_002", 1)
        original.schedule_event(GameDate(2025, 6, 15), "Vegas")
        
        data = original.to_dict()
        restored = Promotion.from_dict(data)
        
        assert restored.name == original.name
        assert restored.abbreviation == original.abbreviation
        assert restored.roster_size == original.roster_size
        assert restored.get_champion(WeightClass.LIGHTWEIGHT) == "fighter_001"
        assert len(restored.scheduled_events) == 1


class TestPromotionEvents_EventBus:
    """Tests for event bus integration"""
    
    def test_set_champion_emits_events(self):
        """Setting champion should emit events"""
        promo = create_promotion()
        events_received = []
        
        def handler(event):
            events_received.append(event.event_type)
        
        h1 = event_bus.subscribe(EventType.TITLE_WON, handler)
        
        promo.set_champion(WeightClass.LIGHTWEIGHT, "fighter_001")
        
        event_bus.unsubscribe(h1)
        
        assert EventType.TITLE_WON in events_received
    
    def test_title_change_emits_both_events(self):
        """Title change should emit won and lost"""
        promo = create_promotion()
        promo.set_champion(WeightClass.LIGHTWEIGHT, "fighter_001")
        
        events_received = []
        
        def handler(event):
            events_received.append(event.event_type)
        
        h1 = event_bus.subscribe(EventType.TITLE_WON, handler)
        h2 = event_bus.subscribe(EventType.TITLE_LOST, handler)
        
        promo.set_champion(WeightClass.LIGHTWEIGHT, "fighter_002")
        
        event_bus.unsubscribe(h1)
        event_bus.unsubscribe(h2)
        
        assert EventType.TITLE_WON in events_received
        assert EventType.TITLE_LOST in events_received


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
