# systems/watchlist.py
# Module: Fighter Watchlist System
# Lines: ~750
#
# Track and organize fighters with categories, priorities, notes, alerts.

"""
Cage Dynasty - Watchlist System

Inspired by BBGM's flag system and Leather's traffic light priorities.
Enhanced with MMA-specific features for scouting and tracking.

FEATURES:
    - Watch Categories: SIGN_TARGET, OPPONENT, RIVAL, PROSPECT, THREAT, etc.
    - Priority Levels: HIGH (🔴), MEDIUM (🟡), LOW (🟢), NONE (⚪)
    - Personal Notes: Add timestamped notes to any watched fighter
    - Smart Alerts: Get notified of important events
    - Auto-Watch Rules: Automatically track fighters matching criteria
    - Tags: Custom organization with user-defined tags
"""

from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


# ============================================================================
# ENUMS
# ============================================================================

class WatchCategory(Enum):
    """Categories for watching fighters."""
    SIGN_TARGET = "SIGN_TARGET"      # Want to sign this fighter
    OPPONENT = "OPPONENT"            # Potential/upcoming opponent
    RIVAL = "RIVAL"                  # Camp or personal rival
    PROSPECT = "PROSPECT"            # Young talent to monitor
    THREAT = "THREAT"                # Dangerous fighter to prepare for
    SCOUT = "SCOUT"                  # General scouting interest
    AVOID = "AVOID"                  # Fighters to avoid
    FAVORITE = "FAVORITE"            # Personal favorites


class WatchPriority(Enum):
    """Priority levels using traffic light system."""
    HIGH = "HIGH"        # 🔴 Red - Urgent attention
    MEDIUM = "MEDIUM"    # 🟡 Yellow - Monitor closely  
    LOW = "LOW"          # 🟢 Green - Casual observation
    NONE = "NONE"        # ⚪ White - No priority set


class AlertType(Enum):
    """Types of alerts for watched fighters."""
    FIGHT_WIN = "FIGHT_WIN"
    FIGHT_LOSS = "FIGHT_LOSS"
    BECAME_FREE_AGENT = "BECAME_FREE_AGENT"
    SIGNED_CONTRACT = "SIGNED_CONTRACT"
    INJURED = "INJURED"
    RECOVERED = "RECOVERED"
    RETIRED = "RETIRED"
    RANKED_UP = "RANKED_UP"
    RANKED_DOWN = "RANKED_DOWN"
    BECAME_CHAMPION = "BECAME_CHAMPION"
    LOST_TITLE = "LOST_TITLE"
    SCHEDULED_FIGHT = "SCHEDULED_FIGHT"


# ============================================================================
# CONSTANTS
# ============================================================================

PRIORITY_SYMBOLS = {
    WatchPriority.HIGH: "🔴",
    WatchPriority.MEDIUM: "🟡",
    WatchPriority.LOW: "🟢",
    WatchPriority.NONE: "⚪",
}

PRIORITY_TEXT = {
    WatchPriority.HIGH: "[!!!]",
    WatchPriority.MEDIUM: "[!!]",
    WatchPriority.LOW: "[!]",
    WatchPriority.NONE: "[-]",
}

CATEGORY_INFO = {
    WatchCategory.SIGN_TARGET: {"name": "Sign Target", "icon": "📝", "description": "Fighters you want to sign"},
    WatchCategory.OPPONENT: {"name": "Opponent", "icon": "⚔️", "description": "Potential opponents"},
    WatchCategory.RIVAL: {"name": "Rival", "icon": "👊", "description": "Camp or personal rivals"},
    WatchCategory.PROSPECT: {"name": "Prospect", "icon": "⭐", "description": "Young talent to monitor"},
    WatchCategory.THREAT: {"name": "Threat", "icon": "⚠️", "description": "Dangerous fighters"},
    WatchCategory.SCOUT: {"name": "Scout", "icon": "🔍", "description": "General scouting"},
    WatchCategory.AVOID: {"name": "Avoid", "icon": "🚫", "description": "Fighters to avoid"},
    WatchCategory.FAVORITE: {"name": "Favorite", "icon": "❤️", "description": "Personal favorites"},
}

DEFAULT_ALERT_SETTINGS = {
    AlertType.FIGHT_WIN: True,
    AlertType.FIGHT_LOSS: True,
    AlertType.BECAME_FREE_AGENT: True,
    AlertType.SIGNED_CONTRACT: True,
    AlertType.INJURED: False,
    AlertType.RECOVERED: False,
    AlertType.RETIRED: True,
    AlertType.RANKED_UP: False,
    AlertType.RANKED_DOWN: False,
    AlertType.BECAME_CHAMPION: True,
    AlertType.LOST_TITLE: True,
    AlertType.SCHEDULED_FIGHT: False,
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class WatchEntry:
    """A single entry on the watchlist."""
    fighter_id: str
    fighter_name: str
    category: WatchCategory
    priority: WatchPriority = WatchPriority.NONE
    added_date: str = ""
    last_updated: str = ""
    notes: List[str] = field(default_factory=list)
    weight_class: str = ""
    record: str = ""
    camp_name: str = ""
    ranking: int = 0
    is_champion: bool = False
    is_free_agent: bool = False
    age: int = 0
    fights_since_added: int = 0
    last_fight_result: str = ""
    tags: List[str] = field(default_factory=list)
    
    def add_note(self, note: str) -> None:
        """Add a timestamped note."""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        self.notes.append(f"[{timestamp}] {note}")
        self.last_updated = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id, "fighter_name": self.fighter_name,
            "category": self.category.value, "priority": self.priority.value,
            "added_date": self.added_date, "last_updated": self.last_updated,
            "notes": self.notes, "weight_class": self.weight_class,
            "record": self.record, "camp_name": self.camp_name,
            "ranking": self.ranking, "is_champion": self.is_champion,
            "is_free_agent": self.is_free_agent, "age": self.age,
            "fights_since_added": self.fights_since_added,
            "last_fight_result": self.last_fight_result, "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WatchEntry":
        return cls(
            fighter_id=data["fighter_id"], fighter_name=data["fighter_name"],
            category=WatchCategory(data["category"]),
            priority=WatchPriority(data.get("priority", "NONE")),
            added_date=data.get("added_date", ""),
            last_updated=data.get("last_updated", ""),
            notes=data.get("notes", []), weight_class=data.get("weight_class", ""),
            record=data.get("record", ""), camp_name=data.get("camp_name", ""),
            ranking=data.get("ranking", 0), is_champion=data.get("is_champion", False),
            is_free_agent=data.get("is_free_agent", False), age=data.get("age", 0),
            fights_since_added=data.get("fights_since_added", 0),
            last_fight_result=data.get("last_fight_result", ""),
            tags=data.get("tags", []),
        )


@dataclass
class WatchAlert:
    """An alert about a watched fighter."""
    fighter_id: str
    fighter_name: str
    alert_type: AlertType
    message: str
    date: str
    read: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id, "fighter_name": self.fighter_name,
            "alert_type": self.alert_type.value, "message": self.message,
            "date": self.date, "read": self.read,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WatchAlert":
        return cls(
            fighter_id=data["fighter_id"], fighter_name=data["fighter_name"],
            alert_type=AlertType(data["alert_type"]), message=data["message"],
            date=data["date"], read=data.get("read", False),
        )


@dataclass
class AutoWatchRule:
    """Rule for automatically adding fighters to watchlist."""
    rule_id: str
    name: str
    description: str
    category: WatchCategory
    priority: WatchPriority
    enabled: bool = True
    min_ranking: Optional[int] = None
    weight_classes: List[str] = field(default_factory=list)
    is_free_agent: Optional[bool] = None
    min_win_streak: Optional[int] = None
    max_age: Optional[int] = None
    min_wins: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id, "name": self.name,
            "description": self.description, "category": self.category.value,
            "priority": self.priority.value, "enabled": self.enabled,
            "min_ranking": self.min_ranking, "weight_classes": self.weight_classes,
            "is_free_agent": self.is_free_agent, "min_win_streak": self.min_win_streak,
            "max_age": self.max_age, "min_wins": self.min_wins,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutoWatchRule":
        return cls(
            rule_id=data["rule_id"], name=data["name"],
            description=data["description"],
            category=WatchCategory(data["category"]),
            priority=WatchPriority(data.get("priority", "NONE")),
            enabled=data.get("enabled", True),
            min_ranking=data.get("min_ranking"),
            weight_classes=data.get("weight_classes", []),
            is_free_agent=data.get("is_free_agent"),
            min_win_streak=data.get("min_win_streak"),
            max_age=data.get("max_age"), min_wins=data.get("min_wins"),
        )


# ============================================================================
# WATCHLIST CLASS
# ============================================================================

class Watchlist:
    """Main watchlist manager."""
    
    def __init__(self, max_entries: int = 100):
        self.max_entries = max_entries
        self._entries: Dict[str, WatchEntry] = {}
        self._alerts: List[WatchAlert] = []
        self._auto_rules: Dict[str, AutoWatchRule] = {}
        self._alert_settings: Dict[AlertType, bool] = dict(DEFAULT_ALERT_SETTINGS)
        self._by_category: Dict[WatchCategory, Set[str]] = {cat: set() for cat in WatchCategory}
        self._by_priority: Dict[WatchPriority, Set[str]] = {pri: set() for pri in WatchPriority}
    
    def add(self, fighter_id: str, fighter_name: str, category: WatchCategory,
            priority: WatchPriority = WatchPriority.NONE, note: Optional[str] = None,
            **fighter_info) -> Tuple[bool, str]:
        """Add a fighter to the watchlist."""
        if len(self._entries) >= self.max_entries and fighter_id not in self._entries:
            return False, f"Watchlist full ({self.max_entries} max)"
        if fighter_id in self._entries:
            return False, f"{fighter_name} is already on your watchlist"
        
        now = datetime.now().isoformat()
        entry = WatchEntry(
            fighter_id=fighter_id, fighter_name=fighter_name,
            category=category, priority=priority, added_date=now, last_updated=now,
            weight_class=fighter_info.get("weight_class", ""),
            record=fighter_info.get("record", ""),
            camp_name=fighter_info.get("camp_name", ""),
            ranking=fighter_info.get("ranking", 0),
            is_champion=fighter_info.get("is_champion", False),
            is_free_agent=fighter_info.get("is_free_agent", False),
            age=fighter_info.get("age", 0),
        )
        if note:
            entry.add_note(note)
        
        self._entries[fighter_id] = entry
        self._by_category[category].add(fighter_id)
        self._by_priority[priority].add(fighter_id)
        return True, f"Added {fighter_name} to watchlist as {category.value}"
    
    def remove(self, fighter_id: str) -> Tuple[bool, str]:
        """Remove a fighter from the watchlist."""
        if fighter_id not in self._entries:
            return False, "Fighter not on watchlist"
        entry = self._entries[fighter_id]
        name = entry.fighter_name
        self._by_category[entry.category].discard(fighter_id)
        self._by_priority[entry.priority].discard(fighter_id)
        del self._entries[fighter_id]
        return True, f"Removed {name} from watchlist"
    
    def get(self, fighter_id: str) -> Optional[WatchEntry]:
        return self._entries.get(fighter_id)
    
    def contains(self, fighter_id: str) -> bool:
        return fighter_id in self._entries
    
    def count(self) -> int:
        return len(self._entries)
    
    def update_category(self, fighter_id: str, new_category: WatchCategory) -> Tuple[bool, str]:
        if fighter_id not in self._entries:
            return False, "Fighter not on watchlist"
        entry = self._entries[fighter_id]
        old_category = entry.category
        self._by_category[old_category].discard(fighter_id)
        self._by_category[new_category].add(fighter_id)
        entry.category = new_category
        entry.last_updated = datetime.now().isoformat()
        return True, f"Changed {entry.fighter_name} to {new_category.value}"
    
    def update_priority(self, fighter_id: str, new_priority: WatchPriority) -> Tuple[bool, str]:
        if fighter_id not in self._entries:
            return False, "Fighter not on watchlist"
        entry = self._entries[fighter_id]
        old_priority = entry.priority
        self._by_priority[old_priority].discard(fighter_id)
        self._by_priority[new_priority].add(fighter_id)
        entry.priority = new_priority
        entry.last_updated = datetime.now().isoformat()
        return True, f"Set {entry.fighter_name} to {PRIORITY_SYMBOLS[new_priority]} {new_priority.value}"
    
    def add_note(self, fighter_id: str, note: str) -> Tuple[bool, str]:
        if fighter_id not in self._entries:
            return False, "Fighter not on watchlist"
        self._entries[fighter_id].add_note(note)
        return True, f"Added note"
    
    def add_tag(self, fighter_id: str, tag: str) -> Tuple[bool, str]:
        if fighter_id not in self._entries:
            return False, "Fighter not on watchlist"
        entry = self._entries[fighter_id]
        tag = tag.lower().strip()
        if tag not in entry.tags:
            entry.tags.append(tag)
            entry.last_updated = datetime.now().isoformat()
        return True, f"Added tag '{tag}'"
    
    def remove_tag(self, fighter_id: str, tag: str) -> Tuple[bool, str]:
        if fighter_id not in self._entries:
            return False, "Fighter not on watchlist"
        entry = self._entries[fighter_id]
        tag = tag.lower().strip()
        if tag in entry.tags:
            entry.tags.remove(tag)
            return True, f"Removed tag '{tag}'"
        return False, f"Tag '{tag}' not found"
    
    def update_fighter_info(self, fighter_id: str, **info) -> bool:
        if fighter_id not in self._entries:
            return False
        entry = self._entries[fighter_id]
        for key in ["record", "ranking", "is_champion", "is_free_agent", "camp_name", "age"]:
            if key in info:
                setattr(entry, key, info[key])
        if "last_fight_result" in info:
            entry.last_fight_result = info["last_fight_result"]
            entry.fights_since_added += 1
        entry.last_updated = datetime.now().isoformat()
        return True
    
    def get_all(self) -> List[WatchEntry]:
        return list(self._entries.values())
    
    def get_by_category(self, category: WatchCategory) -> List[WatchEntry]:
        return [self._entries[fid] for fid in self._by_category[category] if fid in self._entries]
    
    def get_by_priority(self, priority: WatchPriority) -> List[WatchEntry]:
        return [self._entries[fid] for fid in self._by_priority[priority] if fid in self._entries]
    
    def get_by_weight_class(self, weight_class: str) -> List[WatchEntry]:
        return [e for e in self._entries.values() if e.weight_class.lower() == weight_class.lower()]
    
    def get_by_tag(self, tag: str) -> List[WatchEntry]:
        tag = tag.lower().strip()
        return [e for e in self._entries.values() if tag in e.tags]
    
    def get_free_agents(self) -> List[WatchEntry]:
        return [e for e in self._entries.values() if e.is_free_agent]
    
    def get_high_priority(self) -> List[WatchEntry]:
        return self.get_by_priority(WatchPriority.HIGH)
    
    def search(self, query: str) -> List[WatchEntry]:
        query = query.lower()
        results = []
        for entry in self._entries.values():
            if query in entry.fighter_name.lower():
                results.append(entry)
            elif any(query in note.lower() for note in entry.notes):
                results.append(entry)
            elif query in entry.tags:
                results.append(entry)
        return results
    
    def get_sorted(self, sort_by: str = "priority", reverse: bool = True) -> List[WatchEntry]:
        entries = list(self._entries.values())
        if sort_by == "priority":
            order = {WatchPriority.HIGH: 0, WatchPriority.MEDIUM: 1, WatchPriority.LOW: 2, WatchPriority.NONE: 3}
            entries.sort(key=lambda e: order[e.priority], reverse=not reverse)
        elif sort_by == "name":
            entries.sort(key=lambda e: e.fighter_name.lower(), reverse=reverse)
        elif sort_by == "added":
            entries.sort(key=lambda e: e.added_date, reverse=reverse)
        elif sort_by == "ranking":
            entries.sort(key=lambda e: (e.ranking if e.ranking > 0 else 999), reverse=not reverse)
        return entries
    
    # Alert operations
    def create_alert(self, fighter_id: str, alert_type: AlertType, message: str) -> Optional[WatchAlert]:
        if fighter_id not in self._entries:
            return None
        if not self._alert_settings.get(alert_type, False):
            return None
        entry = self._entries[fighter_id]
        alert = WatchAlert(fighter_id=fighter_id, fighter_name=entry.fighter_name,
                          alert_type=alert_type, message=message, date=datetime.now().isoformat())
        self._alerts.append(alert)
        return alert
    
    def get_unread_alerts(self) -> List[WatchAlert]:
        return [a for a in self._alerts if not a.read]
    
    def get_alerts(self, limit: int = 50) -> List[WatchAlert]:
        return self._alerts[-limit:]
    
    def mark_alert_read(self, index: int) -> bool:
        if 0 <= index < len(self._alerts):
            self._alerts[index].read = True
            return True
        return False
    
    def mark_all_read(self) -> int:
        count = sum(1 for a in self._alerts if not a.read)
        for a in self._alerts:
            a.read = True
        return count
    
    def set_alert_setting(self, alert_type: AlertType, enabled: bool) -> None:
        self._alert_settings[alert_type] = enabled
    
    def get_alert_settings(self) -> Dict[AlertType, bool]:
        return dict(self._alert_settings)
    
    # Auto-watch rules
    def add_auto_rule(self, rule: AutoWatchRule) -> bool:
        self._auto_rules[rule.rule_id] = rule
        return True
    
    def remove_auto_rule(self, rule_id: str) -> bool:
        if rule_id in self._auto_rules:
            del self._auto_rules[rule_id]
            return True
        return False
    
    def get_auto_rules(self) -> List[AutoWatchRule]:
        return list(self._auto_rules.values())
    
    def check_auto_rules(self, fighter_id: str, fighter_name: str, fighter_data: Dict[str, Any]) -> Optional[WatchEntry]:
        if fighter_id in self._entries:
            return None
        for rule in self._auto_rules.values():
            if not rule.enabled:
                continue
            if self._matches_rule(rule, fighter_data):
                success, _ = self.add(fighter_id, fighter_name, rule.category, rule.priority,
                                     note=f"Auto-added: {rule.name}", **fighter_data)
                if success:
                    return self._entries[fighter_id]
        return None
    
    def _matches_rule(self, rule: AutoWatchRule, data: Dict[str, Any]) -> bool:
        if rule.min_ranking is not None:
            ranking = data.get("ranking", 0)
            if ranking == 0 or ranking > rule.min_ranking:
                return False
        if rule.weight_classes:
            if data.get("weight_class", "").lower() not in [wc.lower() for wc in rule.weight_classes]:
                return False
        if rule.is_free_agent is not None:
            if data.get("is_free_agent", False) != rule.is_free_agent:
                return False
        if rule.min_win_streak is not None:
            if data.get("win_streak", 0) < rule.min_win_streak:
                return False
        if rule.max_age is not None:
            if data.get("age", 0) > rule.max_age:
                return False
        if rule.min_wins is not None:
            if data.get("wins", 0) < rule.min_wins:
                return False
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total": len(self._entries), "max": self.max_entries,
            "by_category": {cat.value: len(self._by_category[cat]) for cat in WatchCategory},
            "by_priority": {pri.value: len(self._by_priority[pri]) for pri in WatchPriority},
            "free_agents": len(self.get_free_agents()),
            "unread_alerts": len(self.get_unread_alerts()),
            "auto_rules": len(self._auto_rules),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_entries": self.max_entries,
            "entries": [e.to_dict() for e in self._entries.values()],
            "alerts": [a.to_dict() for a in self._alerts],
            "auto_rules": [r.to_dict() for r in self._auto_rules.values()],
            "alert_settings": {k.value: v for k, v in self._alert_settings.items()},
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Watchlist":
        watchlist = cls(max_entries=data.get("max_entries", 100))
        for entry_data in data.get("entries", []):
            entry = WatchEntry.from_dict(entry_data)
            watchlist._entries[entry.fighter_id] = entry
            watchlist._by_category[entry.category].add(entry.fighter_id)
            watchlist._by_priority[entry.priority].add(entry.fighter_id)
        for alert_data in data.get("alerts", []):
            watchlist._alerts.append(WatchAlert.from_dict(alert_data))
        for rule_data in data.get("auto_rules", []):
            rule = AutoWatchRule.from_dict(rule_data)
            watchlist._auto_rules[rule.rule_id] = rule
        for key, value in data.get("alert_settings", {}).items():
            try:
                watchlist._alert_settings[AlertType(key)] = value
            except ValueError:
                pass
        return watchlist


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_watchlist(max_entries: int = 100) -> Watchlist:
    """Create a new empty watchlist."""
    return Watchlist(max_entries=max_entries)


def create_watchlist_with_defaults(max_entries: int = 100) -> Watchlist:
    """Create watchlist with default auto-watch rules."""
    watchlist = Watchlist(max_entries=max_entries)
    watchlist.add_auto_rule(AutoWatchRule(
        rule_id="top_free_agents", name="Top Free Agents",
        description="Watch ranked free agents",
        category=WatchCategory.SIGN_TARGET, priority=WatchPriority.HIGH,
        min_ranking=15, is_free_agent=True,
    ))
    watchlist.add_auto_rule(AutoWatchRule(
        rule_id="hot_prospects", name="Hot Prospects",
        description="Young fighters on winning streaks",
        category=WatchCategory.PROSPECT, priority=WatchPriority.MEDIUM,
        max_age=25, min_win_streak=3, enabled=False,
    ))
    return watchlist


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def format_watch_entry(entry: WatchEntry, use_emoji: bool = True, show_notes: bool = False) -> str:
    """Format a watch entry for display."""
    priority = PRIORITY_SYMBOLS[entry.priority] if use_emoji else PRIORITY_TEXT[entry.priority]
    cat_info = CATEGORY_INFO[entry.category]
    category = cat_info["icon"] if use_emoji else f"[{entry.category.value[:4]}]"
    status = "(C) " if entry.is_champion else (f"#{entry.ranking} " if entry.ranking > 0 else "")
    fa = " [FA]" if entry.is_free_agent else ""
    line = f"{priority} {category} {status}{entry.fighter_name}{fa}"
    if entry.record:
        line += f" ({entry.record})"
    if entry.weight_class:
        line += f" - {entry.weight_class}"
    if entry.tags:
        line += f" [{', '.join(entry.tags)}]"
    if show_notes and entry.notes:
        line += f"\n    Last note: {entry.notes[-1]}"
    return line


def format_watchlist_summary(watchlist: Watchlist) -> List[str]:
    """Format watchlist summary for display."""
    stats = watchlist.get_stats()
    lines = [
        "═" * 40,
        "         WATCHLIST SUMMARY         ".center(40),
        "═" * 40,
        f"  Total Watched: {stats['total']}/{stats['max']}",
        "",
        "  By Category:",
    ]
    for cat in WatchCategory:
        count = stats["by_category"][cat.value]
        if count > 0:
            info = CATEGORY_INFO[cat]
            lines.append(f"    {info['icon']} {info['name']}: {count}")
    lines.extend(["", "  By Priority:"])
    for pri in WatchPriority:
        count = stats["by_priority"][pri.value]
        if count > 0:
            lines.append(f"    {PRIORITY_SYMBOLS[pri]} {pri.value}: {count}")
    if stats["free_agents"] > 0:
        lines.extend(["", f"  📝 Free Agents: {stats['free_agents']}"])
    if stats["unread_alerts"] > 0:
        lines.extend(["", f"  🔔 Unread Alerts: {stats['unread_alerts']}"])
    lines.append("═" * 40)
    return lines


def format_alert(alert: WatchAlert, use_emoji: bool = True) -> str:
    """Format an alert for display."""
    marker = "● " if not alert.read else ""
    date = alert.date[:10] if len(alert.date) >= 10 else alert.date
    return f"{marker}[{date}] {alert.fighter_name}: {alert.message}"


def get_category_options() -> List[Tuple[str, WatchCategory]]:
    """Get (display_name, category) list for menus."""
    return [(f"{CATEGORY_INFO[cat]['icon']} {CATEGORY_INFO[cat]['name']}", cat) for cat in WatchCategory]


def get_priority_options() -> List[Tuple[str, WatchPriority]]:
    """Get (display_name, priority) list for menus."""
    return [(f"{PRIORITY_SYMBOLS[pri]} {pri.value}", pri) for pri in WatchPriority]


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "WatchCategory", "WatchPriority", "AlertType",
    "WatchEntry", "WatchAlert", "AutoWatchRule", "Watchlist",
    "create_watchlist", "create_watchlist_with_defaults",
    "format_watch_entry", "format_watchlist_summary", "format_alert",
    "get_category_options", "get_priority_options",
    "PRIORITY_SYMBOLS", "PRIORITY_TEXT", "CATEGORY_INFO", "DEFAULT_ALERT_SETTINGS",
]
