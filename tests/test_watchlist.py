# tests/test_watchlist.py
# Tests for the Watchlist System
# Run: python3 -m pytest tests/test_watchlist.py -v

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from systems.watchlist import (
    WatchCategory, WatchPriority, AlertType,
    WatchEntry, WatchAlert, AutoWatchRule, Watchlist,
    create_watchlist, create_watchlist_with_defaults,
    format_watch_entry, format_watchlist_summary, format_alert,
    get_category_options, get_priority_options,
    PRIORITY_SYMBOLS, PRIORITY_TEXT, CATEGORY_INFO,
)


class TestEnums:
    def test_watch_categories_exist(self):
        expected = ["SIGN_TARGET", "OPPONENT", "RIVAL", "PROSPECT", "THREAT", "SCOUT", "AVOID", "FAVORITE"]
        for cat in expected:
            assert hasattr(WatchCategory, cat)
    
    def test_watch_priorities_exist(self):
        for pri in ["HIGH", "MEDIUM", "LOW", "NONE"]:
            assert hasattr(WatchPriority, pri)
    
    def test_alert_types_exist(self):
        for alert in ["FIGHT_WIN", "FIGHT_LOSS", "BECAME_FREE_AGENT", "BECAME_CHAMPION", "RETIRED"]:
            assert hasattr(AlertType, alert)


class TestConstants:
    def test_priority_symbols_defined(self):
        for pri in WatchPriority:
            assert pri in PRIORITY_SYMBOLS
    
    def test_priority_text_defined(self):
        for pri in WatchPriority:
            assert pri in PRIORITY_TEXT
    
    def test_category_info_defined(self):
        for cat in WatchCategory:
            assert cat in CATEGORY_INFO
            assert "name" in CATEGORY_INFO[cat]
            assert "icon" in CATEGORY_INFO[cat]


class TestWatchEntry:
    def test_creation(self):
        entry = WatchEntry(fighter_id="f1", fighter_name="Test Fighter", category=WatchCategory.SIGN_TARGET)
        assert entry.fighter_id == "f1"
        assert entry.category == WatchCategory.SIGN_TARGET
        assert entry.priority == WatchPriority.NONE
    
    def test_add_note(self):
        entry = WatchEntry(fighter_id="f1", fighter_name="Test", category=WatchCategory.SCOUT)
        entry.add_note("Good wrestler")
        assert len(entry.notes) == 1
        assert "Good wrestler" in entry.notes[0]
    
    def test_to_dict(self):
        entry = WatchEntry(fighter_id="f1", fighter_name="Test", category=WatchCategory.PROSPECT, priority=WatchPriority.HIGH, ranking=5)
        data = entry.to_dict()
        assert data["fighter_id"] == "f1"
        assert data["category"] == "PROSPECT"
        assert data["priority"] == "HIGH"
    
    def test_from_dict(self):
        data = {"fighter_id": "f2", "fighter_name": "Another", "category": "RIVAL", "priority": "MEDIUM", "is_champion": True}
        entry = WatchEntry.from_dict(data)
        assert entry.category == WatchCategory.RIVAL
        assert entry.is_champion is True
    
    def test_round_trip(self):
        original = WatchEntry(fighter_id="f1", fighter_name="Test", category=WatchCategory.THREAT, priority=WatchPriority.HIGH, tags=["dangerous"])
        original.add_note("Watch out")
        restored = WatchEntry.from_dict(original.to_dict())
        assert restored.fighter_id == original.fighter_id
        assert restored.tags == original.tags


class TestWatchAlert:
    def test_creation(self):
        alert = WatchAlert(fighter_id="f1", fighter_name="Test", alert_type=AlertType.FIGHT_WIN, message="Won by KO", date="2025-01-15")
        assert alert.alert_type == AlertType.FIGHT_WIN
        assert alert.read is False
    
    def test_serialization(self):
        alert = WatchAlert(fighter_id="f1", fighter_name="Test", alert_type=AlertType.BECAME_CHAMPION, message="Won title", date="2025-01-15", read=True)
        restored = WatchAlert.from_dict(alert.to_dict())
        assert restored.alert_type == AlertType.BECAME_CHAMPION
        assert restored.read is True


class TestAutoWatchRule:
    def test_creation(self):
        rule = AutoWatchRule(rule_id="test", name="Test", description="A test", category=WatchCategory.PROSPECT, priority=WatchPriority.MEDIUM, max_age=25)
        assert rule.max_age == 25
        assert rule.enabled is True
    
    def test_serialization(self):
        rule = AutoWatchRule(rule_id="rule1", name="FA Watch", description="Watch FAs", category=WatchCategory.SIGN_TARGET, priority=WatchPriority.HIGH, is_free_agent=True, min_ranking=10)
        restored = AutoWatchRule.from_dict(rule.to_dict())
        assert restored.is_free_agent is True
        assert restored.min_ranking == 10


class TestWatchlistAdd:
    def test_add_fighter(self):
        wl = create_watchlist()
        success, msg = wl.add("f1", "John Smith", WatchCategory.SIGN_TARGET)
        assert success is True
        assert wl.count() == 1
    
    def test_add_with_priority(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.THREAT, WatchPriority.HIGH)
        assert wl.get("f1").priority == WatchPriority.HIGH
    
    def test_add_with_note(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.SCOUT, note="Great prospect")
        assert len(wl.get("f1").notes) == 1
    
    def test_add_with_info(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.OPPONENT, weight_class="Welterweight", record="15-3")
        entry = wl.get("f1")
        assert entry.weight_class == "Welterweight"
        assert entry.record == "15-3"
    
    def test_add_duplicate_fails(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.SCOUT)
        success, msg = wl.add("f1", "Test", WatchCategory.RIVAL)
        assert success is False
    
    def test_add_respects_max(self):
        wl = create_watchlist(max_entries=2)
        wl.add("f1", "One", WatchCategory.SCOUT)
        wl.add("f2", "Two", WatchCategory.SCOUT)
        success, msg = wl.add("f3", "Three", WatchCategory.SCOUT)
        assert success is False


class TestWatchlistRemove:
    def test_remove_fighter(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.SCOUT)
        success, _ = wl.remove("f1")
        assert success is True
        assert wl.count() == 0
    
    def test_remove_nonexistent(self):
        wl = create_watchlist()
        success, _ = wl.remove("fake")
        assert success is False


class TestWatchlistUpdate:
    def test_update_category(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.SCOUT)
        wl.update_category("f1", WatchCategory.SIGN_TARGET)
        assert wl.get("f1").category == WatchCategory.SIGN_TARGET
    
    def test_update_priority(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.SCOUT)
        wl.update_priority("f1", WatchPriority.HIGH)
        assert wl.get("f1").priority == WatchPriority.HIGH
    
    def test_add_note(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.SCOUT)
        wl.add_note("f1", "Looking good")
        assert len(wl.get("f1").notes) == 1
    
    def test_add_tag(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.SCOUT)
        wl.add_tag("f1", "striker")
        assert "striker" in wl.get("f1").tags
    
    def test_remove_tag(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.SCOUT)
        wl.add_tag("f1", "striker")
        wl.remove_tag("f1", "striker")
        assert "striker" not in wl.get("f1").tags
    
    def test_update_fighter_info(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.SCOUT)
        wl.update_fighter_info("f1", record="16-3", ranking=3, is_champion=True)
        entry = wl.get("f1")
        assert entry.record == "16-3"
        assert entry.is_champion is True


class TestWatchlistQueries:
    def test_get_all(self):
        wl = create_watchlist()
        wl.add("f1", "One", WatchCategory.SCOUT)
        wl.add("f2", "Two", WatchCategory.RIVAL)
        assert len(wl.get_all()) == 2
    
    def test_get_by_category(self):
        wl = create_watchlist()
        wl.add("f1", "One", WatchCategory.SCOUT)
        wl.add("f2", "Two", WatchCategory.RIVAL)
        wl.add("f3", "Three", WatchCategory.SCOUT)
        assert len(wl.get_by_category(WatchCategory.SCOUT)) == 2
    
    def test_get_by_priority(self):
        wl = create_watchlist()
        wl.add("f1", "One", WatchCategory.SCOUT, WatchPriority.HIGH)
        wl.add("f2", "Two", WatchCategory.SCOUT, WatchPriority.LOW)
        assert len(wl.get_by_priority(WatchPriority.HIGH)) == 1
    
    def test_get_by_weight_class(self):
        wl = create_watchlist()
        wl.add("f1", "One", WatchCategory.SCOUT, weight_class="Welterweight")
        wl.add("f2", "Two", WatchCategory.SCOUT, weight_class="Middleweight")
        assert len(wl.get_by_weight_class("Welterweight")) == 1
    
    def test_get_by_tag(self):
        wl = create_watchlist()
        wl.add("f1", "One", WatchCategory.SCOUT)
        wl.add_tag("f1", "striker")
        assert len(wl.get_by_tag("striker")) == 1
    
    def test_get_free_agents(self):
        wl = create_watchlist()
        wl.add("f1", "One", WatchCategory.SCOUT, is_free_agent=True)
        wl.add("f2", "Two", WatchCategory.SCOUT, is_free_agent=False)
        assert len(wl.get_free_agents()) == 1
    
    def test_search_by_name(self):
        wl = create_watchlist()
        wl.add("f1", "John Smith", WatchCategory.SCOUT)
        wl.add("f2", "Mike Jones", WatchCategory.SCOUT)
        assert len(wl.search("john")) == 1
    
    def test_get_sorted_by_priority(self):
        wl = create_watchlist()
        wl.add("f1", "One", WatchCategory.SCOUT, WatchPriority.LOW)
        wl.add("f2", "Two", WatchCategory.SCOUT, WatchPriority.HIGH)
        sorted_entries = wl.get_sorted(sort_by="priority")
        assert sorted_entries[0].priority == WatchPriority.HIGH


class TestWatchlistAlerts:
    def test_create_alert(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.SCOUT)
        alert = wl.create_alert("f1", AlertType.FIGHT_WIN, "Won by KO")
        assert alert is not None
    
    def test_alert_disabled(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.SCOUT)
        wl.set_alert_setting(AlertType.INJURED, False)
        alert = wl.create_alert("f1", AlertType.INJURED, "Hurt")
        assert alert is None
    
    def test_get_unread_alerts(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.SCOUT)
        wl.create_alert("f1", AlertType.FIGHT_WIN, "Won")
        assert len(wl.get_unread_alerts()) == 1
    
    def test_mark_all_read(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.SCOUT)
        wl.create_alert("f1", AlertType.FIGHT_WIN, "Won")
        wl.mark_all_read()
        assert len(wl.get_unread_alerts()) == 0


class TestAutoWatchRules:
    def test_add_rule(self):
        wl = create_watchlist()
        rule = AutoWatchRule(rule_id="test", name="Test", description="Desc", category=WatchCategory.PROSPECT, priority=WatchPriority.MEDIUM)
        wl.add_auto_rule(rule)
        assert len(wl.get_auto_rules()) == 1
    
    def test_check_rules_matches(self):
        wl = create_watchlist()
        wl.add_auto_rule(AutoWatchRule(rule_id="young", name="Young", description="Under 25", category=WatchCategory.PROSPECT, priority=WatchPriority.MEDIUM, max_age=25))
        entry = wl.check_auto_rules("f1", "Young Gun", {"age": 22})
        assert entry is not None
        assert entry.category == WatchCategory.PROSPECT
    
    def test_check_rules_no_match(self):
        wl = create_watchlist()
        wl.add_auto_rule(AutoWatchRule(rule_id="young", name="Young", description="Under 25", category=WatchCategory.PROSPECT, priority=WatchPriority.MEDIUM, max_age=25))
        entry = wl.check_auto_rules("f1", "Old Vet", {"age": 35})
        assert entry is None
    
    def test_check_rules_disabled(self):
        wl = create_watchlist()
        wl.add_auto_rule(AutoWatchRule(rule_id="test", name="Test", description="Desc", category=WatchCategory.PROSPECT, priority=WatchPriority.MEDIUM, max_age=25, enabled=False))
        entry = wl.check_auto_rules("f1", "Young Gun", {"age": 22})
        assert entry is None


class TestWatchlistSerialization:
    def test_to_dict(self):
        wl = create_watchlist()
        wl.add("f1", "Test", WatchCategory.SCOUT, WatchPriority.HIGH)
        data = wl.to_dict()
        assert "entries" in data
        assert len(data["entries"]) == 1
    
    def test_from_dict(self):
        data = {"max_entries": 50, "entries": [{"fighter_id": "f1", "fighter_name": "Test", "category": "SCOUT", "priority": "HIGH"}], "alerts": [], "auto_rules": [], "alert_settings": {}}
        wl = Watchlist.from_dict(data)
        assert wl.max_entries == 50
        assert wl.count() == 1
    
    def test_round_trip(self):
        original = create_watchlist()
        original.add("f1", "One", WatchCategory.RIVAL, WatchPriority.HIGH)
        original.add_tag("f1", "dangerous")
        restored = Watchlist.from_dict(original.to_dict())
        assert restored.count() == 1
        assert "dangerous" in restored.get("f1").tags


class TestFactoryFunctions:
    def test_create_watchlist(self):
        wl = create_watchlist()
        assert wl.count() == 0
        assert wl.max_entries == 100
    
    def test_create_with_max(self):
        wl = create_watchlist(max_entries=50)
        assert wl.max_entries == 50
    
    def test_create_with_defaults(self):
        wl = create_watchlist_with_defaults()
        assert len(wl.get_auto_rules()) >= 1


class TestDisplayHelpers:
    def test_format_watch_entry(self):
        entry = WatchEntry(fighter_id="f1", fighter_name="John Smith", category=WatchCategory.SIGN_TARGET, priority=WatchPriority.HIGH, record="15-3", weight_class="Welterweight")
        formatted = format_watch_entry(entry)
        assert "John Smith" in formatted
        assert "15-3" in formatted
    
    def test_format_entry_champion(self):
        entry = WatchEntry(fighter_id="f1", fighter_name="Champ", category=WatchCategory.RIVAL, is_champion=True)
        assert "(C)" in format_watch_entry(entry)
    
    def test_format_entry_ranking(self):
        entry = WatchEntry(fighter_id="f1", fighter_name="Ranked", category=WatchCategory.OPPONENT, ranking=5)
        assert "#5" in format_watch_entry(entry)
    
    def test_format_watchlist_summary(self):
        wl = create_watchlist()
        wl.add("f1", "One", WatchCategory.SCOUT, WatchPriority.HIGH)
        lines = format_watchlist_summary(wl)
        assert len(lines) > 0
    
    def test_format_alert(self):
        alert = WatchAlert(fighter_id="f1", fighter_name="Test", alert_type=AlertType.FIGHT_WIN, message="Won by sub", date="2025-01-15")
        assert "Test" in format_alert(alert)
    
    def test_get_category_options(self):
        options = get_category_options()
        assert len(options) == len(WatchCategory)
    
    def test_get_priority_options(self):
        options = get_priority_options()
        assert len(options) == len(WatchPriority)


class TestWatchlistIntegration:
    def test_full_workflow(self):
        wl = create_watchlist()
        wl.add("f1", "Rising Star", WatchCategory.PROSPECT, WatchPriority.HIGH, note="Undefeated", age=22, weight_class="Lightweight")
        wl.add("f2", "Veteran", WatchCategory.THREAT, WatchPriority.MEDIUM, record="25-5", ranking=3)
        wl.add("f3", "Free Agent", WatchCategory.SIGN_TARGET, WatchPriority.HIGH, is_free_agent=True)
        wl.add_tag("f1", "striker")
        wl.create_alert("f1", AlertType.FIGHT_WIN, "Won by KO")
        
        assert len(wl.get_high_priority()) == 2
        assert len(wl.get_free_agents()) == 1
        assert len(wl.get_by_tag("striker")) == 1
        
        wl.update_category("f1", WatchCategory.SIGN_TARGET)
        assert wl.get("f1").category == WatchCategory.SIGN_TARGET
        
        stats = wl.get_stats()
        assert stats["total"] == 3
        
        restored = Watchlist.from_dict(wl.to_dict())
        assert restored.count() == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
