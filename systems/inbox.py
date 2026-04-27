"""
Inbox System for Cage Dynasty
Centralizes all player notifications: fight offers, scout reports, alerts, and more.

Author: Cage Dynasty Team
Version: 1.0.0
Lines: ~650
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
import random
import uuid


# =============================================================================
# ENUMS
# =============================================================================

class NotificationType(Enum):
    """Types of inbox notifications."""
    FIGHT_OFFER = "fight_offer"
    INCOMING_CHALLENGE = "incoming_challenge"
    SCOUT_REPORT = "scout_report"
    CONTRACT_ALERT = "contract_alert"
    INJURY_UPDATE = "injury_update"
    TITLE_OPPORTUNITY = "title_opportunity"
    RIVALRY_UPDATE = "rivalry_update"
    FINANCIAL_ALERT = "financial_alert"
    RANKING_CHANGE = "ranking_change"
    TRAINING_COMPLETE = "training_complete"
    SYSTEM_MESSAGE = "system"


class NotificationPriority(Enum):
    """Priority levels for notifications."""
    CRITICAL = 4  # Red - immediate action needed
    HIGH = 3      # Orange - important
    MEDIUM = 2    # Yellow - notable
    LOW = 1       # Dim - informational


# Icon and color mapping for each notification type
NOTIFICATION_ICONS = {
    NotificationType.FIGHT_OFFER: "🥊",
    NotificationType.INCOMING_CHALLENGE: "⚔️",
    NotificationType.SCOUT_REPORT: "🔍",
    NotificationType.CONTRACT_ALERT: "📋",
    NotificationType.INJURY_UPDATE: "🏥",
    NotificationType.TITLE_OPPORTUNITY: "🏆",
    NotificationType.RIVALRY_UPDATE: "🔥",
    NotificationType.FINANCIAL_ALERT: "💰",
    NotificationType.RANKING_CHANGE: "📊",
    NotificationType.TRAINING_COMPLETE: "💪",
    NotificationType.SYSTEM_MESSAGE: "📢",
}

# Priority colors (ANSI codes)
PRIORITY_COLORS = {
    NotificationPriority.CRITICAL: "\033[91m",  # Red
    NotificationPriority.HIGH: "\033[93m",      # Orange/Yellow
    NotificationPriority.MEDIUM: "\033[33m",    # Yellow
    NotificationPriority.LOW: "\033[2m",        # Dim
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Notification:
    """A single inbox notification."""
    notification_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    title: str
    body: str
    week_created: int
    
    # Optional context
    fighter_id: Optional[str] = None
    opponent_id: Optional[str] = None
    expires_week: Optional[int] = None  # None = never expires
    
    # State
    is_read: bool = False
    is_dismissed: bool = False
    is_actionable: bool = False  # Can player take action on this?
    
    # Extra data for actions
    action_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.notification_id:
            self.notification_id = f"notif_{uuid.uuid4().hex[:8]}"
    
    @property
    def icon(self) -> str:
        """Get icon for this notification type."""
        return NOTIFICATION_ICONS.get(self.notification_type, "📌")
    
    @property
    def is_expired(self) -> bool:
        """Check if notification has expired."""
        if self.expires_week is None:
            return False
        return False  # Expiry check done in InboxSystem with current week
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize notification to dict."""
        return {
            "notification_id": self.notification_id,
            "notification_type": self.notification_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "body": self.body,
            "week_created": self.week_created,
            "fighter_id": self.fighter_id,
            "opponent_id": self.opponent_id,
            "expires_week": self.expires_week,
            "is_read": self.is_read,
            "is_dismissed": self.is_dismissed,
            "is_actionable": self.is_actionable,
            "action_data": self.action_data,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Deserialize notification from dict."""
        return cls(
            notification_id=data.get("notification_id", ""),
            notification_type=NotificationType(data.get("notification_type", "system")),
            priority=NotificationPriority(data.get("priority", 1)),
            title=data.get("title", ""),
            body=data.get("body", ""),
            week_created=data.get("week_created", 0),
            fighter_id=data.get("fighter_id"),
            opponent_id=data.get("opponent_id"),
            expires_week=data.get("expires_week"),
            is_read=data.get("is_read", False),
            is_dismissed=data.get("is_dismissed", False),
            is_actionable=data.get("is_actionable", False),
            action_data=data.get("action_data", {}),
        )


@dataclass
class FightOfferData:
    """Data structure for fight offer notifications."""
    offer_id: str
    fighter_id: str
    fighter_name: str
    opponent_id: str
    opponent_name: str
    opponent_rank: Optional[int]
    opponent_record: str
    opponent_rating: int
    opponent_style: str
    weight_class: str
    weeks_until: int
    purse: int
    win_bonus: int
    is_title_fight: bool
    is_main_event: bool
    matchup_quality: str  # "competitive", "step_up", "step_down"
    accept_chance: int  # AI acceptance probability %
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "opponent_id": self.opponent_id,
            "opponent_name": self.opponent_name,
            "opponent_rank": self.opponent_rank,
            "opponent_record": self.opponent_record,
            "opponent_rating": self.opponent_rating,
            "opponent_style": self.opponent_style,
            "weight_class": self.weight_class,
            "weeks_until": self.weeks_until,
            "purse": self.purse,
            "win_bonus": self.win_bonus,
            "is_title_fight": self.is_title_fight,
            "is_main_event": self.is_main_event,
            "matchup_quality": self.matchup_quality,
            "accept_chance": self.accept_chance,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FightOfferData':
        return cls(
            offer_id=data.get("offer_id", ""),
            fighter_id=data.get("fighter_id", ""),
            fighter_name=data.get("fighter_name", ""),
            opponent_id=data.get("opponent_id", ""),
            opponent_name=data.get("opponent_name", ""),
            opponent_rank=data.get("opponent_rank"),
            opponent_record=data.get("opponent_record", "0-0"),
            opponent_rating=data.get("opponent_rating", 50),
            opponent_style=data.get("opponent_style", "Balanced"),
            weight_class=data.get("weight_class", ""),
            weeks_until=data.get("weeks_until", 8),
            purse=data.get("purse", 5000),
            win_bonus=data.get("win_bonus", 2500),
            is_title_fight=data.get("is_title_fight", False),
            is_main_event=data.get("is_main_event", False),
            matchup_quality=data.get("matchup_quality", "competitive"),
            accept_chance=data.get("accept_chance", 50),
        )


@dataclass
class ScoutReportData:
    """Data structure for scout report notifications."""
    fighter_id: str
    fighter_name: str
    age: int
    weight_class: str
    overall_rating: int
    potential: str  # "Elite", "High", "Average", "Limited"
    ceiling: int
    fighting_style: str
    region: str
    record: str
    notable_traits: List[str]
    reason: str  # Why this fighter was scouted
    scout_source: str  # "coach", "watchlist", "tournament", "random"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "age": self.age,
            "weight_class": self.weight_class,
            "overall_rating": self.overall_rating,
            "potential": self.potential,
            "ceiling": self.ceiling,
            "fighting_style": self.fighting_style,
            "region": self.region,
            "record": self.record,
            "notable_traits": self.notable_traits,
            "reason": self.reason,
            "scout_source": self.scout_source,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoutReportData':
        return cls(
            fighter_id=data.get("fighter_id", ""),
            fighter_name=data.get("fighter_name", ""),
            age=data.get("age", 20),
            weight_class=data.get("weight_class", ""),
            overall_rating=data.get("overall_rating", 50),
            potential=data.get("potential", "Average"),
            ceiling=data.get("ceiling", 70),
            fighting_style=data.get("fighting_style", "Balanced"),
            region=data.get("region", ""),
            record=data.get("record", "0-0"),
            notable_traits=data.get("notable_traits", []),
            reason=data.get("reason", ""),
            scout_source=data.get("scout_source", "random"),
        )


# =============================================================================
# COACH SCOUTING SPECIALTIES
# =============================================================================

# Maps coach specialty to styles they're good at finding
COACH_SCOUT_PREFERENCES = {
    "Striking": {
        "preferred_styles": ["Orthodox Boxer", "Kickboxer", "Muay Thai", "Karate", "Counter Striker", "Brawler"],
        "preferred_traits": ["Knockout Artist", "Fast Starter", "Counter Striker", "Pressure Fighter"],
        "stat_focus": ["boxing", "kicks", "striking_defense"],
    },
    "Wrestling": {
        "preferred_styles": ["Wrestler", "Ground & Pound", "Sambo"],
        "preferred_traits": ["Wrestler's Base", "Pressure Fighter", "Cardio Machine"],
        "stat_focus": ["takedowns", "takedown_defense", "top_control"],
    },
    "Jiu-Jitsu": {
        "preferred_styles": ["Submission Artist", "BJJ Specialist", "Grappler"],
        "preferred_traits": ["Submission Ace", "Veteran Savvy"],
        "stat_focus": ["submissions", "guard", "bjj"],
    },
    "BJJ": {  # Alias for Jiu-Jitsu
        "preferred_styles": ["Submission Artist", "BJJ Specialist", "Grappler"],
        "preferred_traits": ["Submission Ace", "Veteran Savvy"],
        "stat_focus": ["submissions", "guard", "bjj"],
    },
    "Conditioning": {
        "preferred_styles": [],  # Any style, but looks for cardio potential
        "preferred_traits": ["Cardio Machine", "Durable", "Slow Starter"],
        "stat_focus": ["cardio", "recovery", "heart"],
        "special": "finds_high_cardio",  # Special behavior
    },
    "Cornering": {
        "preferred_styles": [],  # Any style
        "preferred_traits": ["Veteran Savvy", "Big Game Hunter", "Composure"],
        "stat_focus": ["iq", "composure", "heart"],
        "special": "finds_high_iq",  # Finds mentally strong fighters
    },
    "Strength": {
        "preferred_styles": ["Brawler", "Ground & Pound", "Wrestler"],
        "preferred_traits": ["Glass Cannon", "Knockout Artist", "Iron Chin"],
        "stat_focus": ["strength", "power", "chin"],
    },
}


# =============================================================================
# INBOX SYSTEM
# =============================================================================

class InboxSystem:
    """
    Manages all player notifications and integrates with other systems.
    
    Features:
    - Fight offers (migrated from old system)
    - Scout reports (auto-generated based on coaches)
    - Contract/injury/ranking alerts
    - Priority sorting and filtering
    - Read/dismiss tracking
    """
    
    def __init__(self):
        self.notifications: List[Notification] = []
        self._dismissed_ids: Set[str] = set()
        self._scouted_this_week: Set[str] = set()  # Prevent duplicate scouts
    
    # =========================================================================
    # CORE NOTIFICATION METHODS
    # =========================================================================
    
    def add_notification(self, notification: Notification) -> None:
        """Add a new notification to the inbox."""
        # Check for duplicates (same type + fighter + opponent in same week)
        for existing in self.notifications:
            if (existing.notification_type == notification.notification_type and
                existing.fighter_id == notification.fighter_id and
                existing.opponent_id == notification.opponent_id and
                existing.week_created == notification.week_created):
                return  # Duplicate, skip
        
        self.notifications.append(notification)
    
    def get_unread(self) -> List[Notification]:
        """Get all unread notifications, sorted by priority."""
        unread = [n for n in self.notifications 
                  if not n.is_read and not n.is_dismissed]
        return sorted(unread, key=lambda n: (-n.priority.value, -n.week_created))
    
    def get_all(self, include_dismissed: bool = False) -> List[Notification]:
        """Get all notifications, sorted by priority and recency."""
        if include_dismissed:
            notifs = self.notifications
        else:
            notifs = [n for n in self.notifications if not n.is_dismissed]
        return sorted(notifs, key=lambda n: (-n.priority.value, -n.week_created))
    
    def get_by_type(self, notif_type: NotificationType) -> List[Notification]:
        """Get all notifications of a specific type."""
        return [n for n in self.notifications 
                if n.notification_type == notif_type and not n.is_dismissed]
    
    def get_actionable(self) -> List[Notification]:
        """Get notifications that require player action."""
        return [n for n in self.notifications 
                if n.is_actionable and not n.is_dismissed]
    
    def mark_read(self, notification_id: str) -> None:
        """Mark a notification as read."""
        for n in self.notifications:
            if n.notification_id == notification_id:
                n.is_read = True
                break
    
    def mark_all_read(self) -> None:
        """Mark all notifications as read."""
        for n in self.notifications:
            n.is_read = True
    
    def dismiss(self, notification_id: str) -> None:
        """Dismiss a notification (hide but don't delete)."""
        for n in self.notifications:
            if n.notification_id == notification_id:
                n.is_dismissed = True
                self._dismissed_ids.add(notification_id)
                break
    
    def delete(self, notification_id: str) -> None:
        """Permanently delete a notification."""
        self.notifications = [n for n in self.notifications 
                             if n.notification_id != notification_id]
    
    def clear_expired(self, current_week: int) -> int:
        """Remove expired notifications. Returns count removed."""
        before = len(self.notifications)
        self.notifications = [
            n for n in self.notifications
            if n.expires_week is None or n.expires_week > current_week
        ]
        return before - len(self.notifications)
    
    def get_unread_count(self) -> int:
        """Get count of unread notifications."""
        return len(self.get_unread())
    
    def get_count_by_type(self, notif_type: NotificationType) -> int:
        """Get count of notifications of a specific type."""
        return len(self.get_by_type(notif_type))
    
    # =========================================================================
    # FIGHT OFFER METHODS
    # =========================================================================
    
    def add_fight_offer(
        self,
        offer_data: FightOfferData,
        current_week: int,
    ) -> Notification:
        """Create and add a fight offer notification."""
        # Determine priority based on matchup quality
        if offer_data.is_title_fight:
            priority = NotificationPriority.CRITICAL
            title = f"🏆 TITLE FIGHT: vs {offer_data.opponent_name}"
        elif offer_data.matchup_quality == "step_up":
            priority = NotificationPriority.HIGH
            title = f"⬆️ Step Up: vs {offer_data.opponent_name}"
        elif offer_data.matchup_quality == "competitive":
            priority = NotificationPriority.MEDIUM
            title = f"🥊 Fight Offer: vs {offer_data.opponent_name}"
        else:
            priority = NotificationPriority.LOW
            title = f"🥊 Fight Offer: vs {offer_data.opponent_name}"
        
        # Build body
        rank_str = f"#{offer_data.opponent_rank}" if offer_data.opponent_rank else "Unranked"
        body_lines = [
            f"Opponent: {offer_data.opponent_name} ({offer_data.opponent_record})",
            f"Rank: {rank_str} | Rating: {offer_data.opponent_rating} OVR",
            f"Style: {offer_data.opponent_style}",
            f"Purse: ${offer_data.purse:,} + ${offer_data.win_bonus:,} win bonus",
            f"Fight in {offer_data.weeks_until} weeks",
        ]
        if offer_data.is_main_event:
            body_lines.append("📺 Main Event (5 rounds)")
        
        body = "\n".join(body_lines)
        
        notification = Notification(
            notification_id=f"offer_{offer_data.offer_id}",
            notification_type=NotificationType.FIGHT_OFFER,
            priority=priority,
            title=title,
            body=body,
            week_created=current_week,
            fighter_id=offer_data.fighter_id,
            opponent_id=offer_data.opponent_id,
            expires_week=current_week + 2,  # Offers expire in 2 weeks
            is_actionable=True,
            action_data=offer_data.to_dict(),
        )
        
        self.add_notification(notification)
        return notification
    
    def get_fight_offers(self, fighter_id: Optional[str] = None) -> List[Notification]:
        """Get all active fight offers, optionally filtered by fighter."""
        offers = self.get_by_type(NotificationType.FIGHT_OFFER)
        if fighter_id:
            offers = [o for o in offers if o.fighter_id == fighter_id]
        return offers
    
    def get_fight_offer_count(self) -> int:
        """Get count of active fight offers."""
        return len(self.get_fight_offers())
    
    # =========================================================================
    # SCOUT REPORT METHODS
    # =========================================================================
    
    def add_scout_report(
        self,
        scout_data: ScoutReportData,
        current_week: int,
    ) -> Notification:
        """Create and add a scout report notification."""
        # Prevent duplicate scouts in same week
        if scout_data.fighter_id in self._scouted_this_week:
            return None
        self._scouted_this_week.add(scout_data.fighter_id)
        
        # Determine priority based on potential
        if scout_data.potential == "Elite":
            priority = NotificationPriority.HIGH
            potential_icon = "⭐"
        elif scout_data.potential == "High":
            priority = NotificationPriority.MEDIUM
            potential_icon = "🔥"
        else:
            priority = NotificationPriority.LOW
            potential_icon = "📊"
        
        title = f"🔍 Scout Report: {scout_data.fighter_name}"
        
        body_lines = [
            f"{potential_icon} {scout_data.potential} Potential (ceiling: {scout_data.ceiling})",
            f"Age: {scout_data.age} | {scout_data.weight_class}",
            f"Rating: {scout_data.overall_rating} OVR | Record: {scout_data.record}",
            f"Style: {scout_data.fighting_style}",
            f"Region: {scout_data.region}",
        ]
        
        if scout_data.notable_traits:
            body_lines.append(f"Traits: {', '.join(scout_data.notable_traits)}")
        
        body_lines.append(f"")
        body_lines.append(f"📝 {scout_data.reason}")
        
        body = "\n".join(body_lines)
        
        notification = Notification(
            notification_id=f"scout_{scout_data.fighter_id}_{current_week}",
            notification_type=NotificationType.SCOUT_REPORT,
            priority=priority,
            title=title,
            body=body,
            week_created=current_week,
            fighter_id=scout_data.fighter_id,
            expires_week=current_week + 8,  # Scout reports expire in 8 weeks
            is_actionable=True,
            action_data=scout_data.to_dict(),
        )
        
        self.add_notification(notification)
        return notification
    
    def get_scout_reports(self) -> List[Notification]:
        """Get all active scout reports."""
        return self.get_by_type(NotificationType.SCOUT_REPORT)
    
    def reset_weekly_scouts(self) -> None:
        """Reset the weekly scout tracking (call at week start)."""
        self._scouted_this_week.clear()
    
    # =========================================================================
    # ALERT METHODS
    # =========================================================================
    
    def add_title_opportunity(
        self,
        fighter_id: str,
        fighter_name: str,
        division: str,
        current_rank: int,
        current_week: int,
    ) -> Notification:
        """Alert player about title shot opportunity."""
        title = f"🏆 Title Shot Available!"
        body = (
            f"{fighter_name} is ranked #{current_rank} in {division}!\n"
            f"Challenge the champion through Division Ladder."
        )
        
        notification = Notification(
            notification_id=f"title_opp_{fighter_id}_{current_week}",
            notification_type=NotificationType.TITLE_OPPORTUNITY,
            priority=NotificationPriority.CRITICAL,
            title=title,
            body=body,
            week_created=current_week,
            fighter_id=fighter_id,
            expires_week=current_week + 4,
            is_actionable=True,
        )
        
        self.add_notification(notification)
        return notification
    
    def add_ranking_change(
        self,
        fighter_id: str,
        fighter_name: str,
        old_rank: Optional[int],
        new_rank: Optional[int],
        division: str,
        current_week: int,
    ) -> Notification:
        """Alert about ranking change."""
        if new_rank is None or new_rank > 15:
            # Dropped out
            title = f"📊 {fighter_name} dropped from rankings"
            body = f"Lost ranking in {division}"
            priority = NotificationPriority.MEDIUM
        elif old_rank is None or old_rank > 15:
            # Entered rankings
            title = f"📊 {fighter_name} enters rankings!"
            body = f"Now #{new_rank} in {division}"
            priority = NotificationPriority.HIGH
        elif new_rank < old_rank:
            # Moved up
            diff = old_rank - new_rank
            title = f"📊 {fighter_name} rises to #{new_rank}!"
            body = f"Up {diff} spot{'s' if diff > 1 else ''} in {division}"
            priority = NotificationPriority.HIGH if new_rank <= 5 else NotificationPriority.MEDIUM
        else:
            # Moved down
            diff = new_rank - old_rank
            title = f"📊 {fighter_name} drops to #{new_rank}"
            body = f"Down {diff} spot{'s' if diff > 1 else ''} in {division}"
            priority = NotificationPriority.LOW
        
        notification = Notification(
            notification_id=f"rank_{fighter_id}_{current_week}",
            notification_type=NotificationType.RANKING_CHANGE,
            priority=priority,
            title=title,
            body=body,
            week_created=current_week,
            fighter_id=fighter_id,
            expires_week=current_week + 2,
        )
        
        self.add_notification(notification)
        return notification
    
    def add_injury_update(
        self,
        fighter_id: str,
        fighter_name: str,
        injury_type: str,
        weeks_remaining: int,
        is_healed: bool,
        current_week: int,
    ) -> Notification:
        """Alert about injury status."""
        if is_healed:
            title = f"🏥 {fighter_name} cleared to fight!"
            body = f"Recovered from {injury_type}"
            priority = NotificationPriority.HIGH
        else:
            title = f"🏥 {fighter_name} injured"
            body = f"{injury_type} - {weeks_remaining} weeks recovery"
            priority = NotificationPriority.MEDIUM
        
        notification = Notification(
            notification_id=f"injury_{fighter_id}_{current_week}",
            notification_type=NotificationType.INJURY_UPDATE,
            priority=priority,
            title=title,
            body=body,
            week_created=current_week,
            fighter_id=fighter_id,
            expires_week=current_week + 1,
        )
        
        self.add_notification(notification)
        return notification
    
    def add_financial_alert(
        self,
        balance: int,
        weekly_cost: int,
        weeks_until_broke: int,
        current_week: int,
    ) -> Notification:
        """Alert about financial situation."""
        if weeks_until_broke <= 2:
            priority = NotificationPriority.CRITICAL
            title = "💰 CRITICAL: Running out of money!"
            body = f"Balance: ${balance:,}\nWeekly costs: ${weekly_cost:,}\nBroke in {weeks_until_broke} weeks!"
        elif weeks_until_broke <= 4:
            priority = NotificationPriority.HIGH
            title = "💰 Warning: Low funds"
            body = f"Balance: ${balance:,}\nWeekly costs: ${weekly_cost:,}\nBroke in {weeks_until_broke} weeks"
        else:
            priority = NotificationPriority.MEDIUM
            title = "💰 Financial update"
            body = f"Balance: ${balance:,}\nWeekly costs: ${weekly_cost:,}"
        
        notification = Notification(
            notification_id=f"finance_{current_week}",
            notification_type=NotificationType.FINANCIAL_ALERT,
            priority=priority,
            title=title,
            body=body,
            week_created=current_week,
            expires_week=current_week + 1,
        )
        
        self.add_notification(notification)
        return notification
    
    def add_contract_alert(
        self,
        fighter_id: str,
        fighter_name: str,
        weeks_remaining: int,
        current_week: int,
    ) -> Notification:
        """Alert about contract expiring."""
        if weeks_remaining <= 2:
            priority = NotificationPriority.CRITICAL
            title = f"📋 CONTRACT EXPIRING: {fighter_name}"
        elif weeks_remaining <= 4:
            priority = NotificationPriority.HIGH
            title = f"📋 Contract expires soon: {fighter_name}"
        else:
            priority = NotificationPriority.MEDIUM
            title = f"📋 Contract update: {fighter_name}"
        
        body = f"{weeks_remaining} weeks remaining on contract"
        
        notification = Notification(
            notification_id=f"contract_{fighter_id}_{current_week}",
            notification_type=NotificationType.CONTRACT_ALERT,
            priority=priority,
            title=title,
            body=body,
            week_created=current_week,
            fighter_id=fighter_id,
            expires_week=current_week + weeks_remaining,
            is_actionable=True,
        )
        
        self.add_notification(notification)
        return notification
    
    def add_incoming_challenge(
        self,
        fighter_id: str,
        fighter_name: str,
        challenger_id: str,
        challenger_name: str,
        challenger_rank: Optional[int],
        current_week: int,
    ) -> Notification:
        """Alert about incoming challenge from ladder."""
        rank_str = f"#{challenger_rank}" if challenger_rank else "Unranked"
        title = f"⚔️ Challenge from {rank_str} {challenger_name}"
        body = f"{challenger_name} has challenged {fighter_name}!\nRespond in Division Ladder."
        
        notification = Notification(
            notification_id=f"challenge_{fighter_id}_{challenger_id}_{current_week}",
            notification_type=NotificationType.INCOMING_CHALLENGE,
            priority=NotificationPriority.HIGH,
            title=title,
            body=body,
            week_created=current_week,
            fighter_id=fighter_id,
            opponent_id=challenger_id,
            expires_week=current_week + 2,
            is_actionable=True,
            action_data={
                "challenger_id": challenger_id,
                "challenger_name": challenger_name,
                "challenger_rank": challenger_rank,
            },
        )
        
        self.add_notification(notification)
        return notification
    
    def add_training_complete(
        self,
        fighter_id: str,
        fighter_name: str,
        gains_summary: str,
        current_week: int,
    ) -> Notification:
        """Alert that training camp is complete."""
        title = f"💪 Camp Complete: {fighter_name}"
        body = f"Training camp finished!\n{gains_summary}"
        
        notification = Notification(
            notification_id=f"training_{fighter_id}_{current_week}",
            notification_type=NotificationType.TRAINING_COMPLETE,
            priority=NotificationPriority.MEDIUM,
            title=title,
            body=body,
            week_created=current_week,
            fighter_id=fighter_id,
            expires_week=current_week + 1,
        )
        
        self.add_notification(notification)
        return notification
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize inbox to dict."""
        return {
            "notifications": [n.to_dict() for n in self.notifications],
            "dismissed_ids": list(self._dismissed_ids),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InboxSystem':
        """Deserialize inbox from dict."""
        inbox = cls()
        inbox.notifications = [
            Notification.from_dict(n) for n in data.get("notifications", [])
        ]
        inbox._dismissed_ids = set(data.get("dismissed_ids", []))
        return inbox


# =============================================================================
# SCOUT GENERATION HELPER
# =============================================================================

def generate_scout_report_for_coach(
    coach_specialty: str,
    camp_region: str,
    amateur_fighters: List[Any],
    current_week: int,
) -> Optional[ScoutReportData]:
    """
    Generate a scout report based on coach specialty.
    
    Args:
        coach_specialty: Coach's specialty (Striking, Wrestling, etc.)
        camp_region: Camp's region for regional bias
        amateur_fighters: List of amateur fighters to scout from
        current_week: Current game week
    
    Returns:
        ScoutReportData if a prospect is found, None otherwise
    """
    if not amateur_fighters:
        return None
    
    prefs = COACH_SCOUT_PREFERENCES.get(coach_specialty, {})
    preferred_styles = prefs.get("preferred_styles", [])
    preferred_traits = prefs.get("preferred_traits", [])
    stat_focus = prefs.get("stat_focus", [])
    special = prefs.get("special", "")
    
    candidates = []
    
    for fighter in amateur_fighters:
        score = 0
        reasons = []
        
        # Regional bonus
        fighter_region = getattr(fighter, 'region', '')
        if fighter_region == camp_region:
            score += 20
            reasons.append("local talent")
        
        # Style match
        style = getattr(fighter, 'fighting_style', '')
        if style in preferred_styles:
            score += 30
            reasons.append(f"fits {coach_specialty.lower()} focus")
        
        # Trait match
        traits = getattr(fighter, 'traits', []) or []
        for trait in traits:
            trait_str = str(trait)
            if any(pt.lower() in trait_str.lower() for pt in preferred_traits):
                score += 15
                reasons.append(f"has {trait_str}")
        
        # Potential bonus
        potential = getattr(fighter, 'potential_tier', 'Average')
        if potential == "Elite":
            score += 40
            reasons.append("elite ceiling")
        elif potential == "High":
            score += 20
            reasons.append("high ceiling")
        
        # Special abilities
        if special == "finds_high_cardio":
            cardio = getattr(fighter, 'cardio', 50)
            if cardio >= 70:
                score += 25
                reasons.append("excellent cardio")
        elif special == "finds_high_iq":
            iq = getattr(fighter, 'iq', 50)
            composure = getattr(fighter, 'composure', 50)
            if iq >= 70 or composure >= 70:
                score += 25
                reasons.append("high fight IQ")
        
        # Age bonus (younger = more potential)
        age = getattr(fighter, 'age', 25)
        if age <= 21:
            score += 15
        elif age <= 23:
            score += 5
        
        if score > 0:
            candidates.append((fighter, score, reasons))
    
    if not candidates:
        return None
    
    # Sort by score and pick from top candidates
    candidates.sort(key=lambda x: -x[1])
    
    # Weighted random from top 5
    top = candidates[:5]
    weights = [c[1] for c in top]
    selected = random.choices(top, weights=weights)[0]
    
    fighter, score, reasons = selected
    
    # Build scout report
    traits = getattr(fighter, 'traits', []) or []
    trait_names = [str(t) for t in traits]
    
    return ScoutReportData(
        fighter_id=fighter.fighter_id,
        fighter_name=getattr(fighter, 'name', 'Unknown'),
        age=getattr(fighter, 'age', 20),
        weight_class=getattr(fighter, 'weight_class', ''),
        overall_rating=getattr(fighter, 'overall_rating', 50),
        potential=getattr(fighter, 'potential_tier', 'Average'),
        ceiling=getattr(fighter, 'potential_ceiling', 70),
        fighting_style=getattr(fighter, 'fighting_style', 'Balanced'),
        region=getattr(fighter, 'region', ''),
        record=f"{getattr(fighter, 'wins', 0)}-{getattr(fighter, 'losses', 0)}",
        notable_traits=trait_names[:3],
        reason=f"Coach spotted: {', '.join(reasons[:2])}",
        scout_source="coach",
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "NotificationType",
    "NotificationPriority",
    "Notification",
    "FightOfferData",
    "ScoutReportData",
    "InboxSystem",
    "COACH_SCOUT_PREFERENCES",
    "NOTIFICATION_ICONS",
    "PRIORITY_COLORS",
    "generate_scout_report_for_coach",
]
