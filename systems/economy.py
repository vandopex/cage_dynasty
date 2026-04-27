# systems/economy.py
# Enhanced Economy System - Phase 1 Update
# Lines: ~2,200
#
# Comprehensive financial system for Cage Dynasty including:
# - Fighter purses and bonuses (with main event bonus)
# - FICTIONAL sponsorship brands by tier
# - Multi-fight sponsorship contracts
# - Camp sponsorships (facility sponsors)
# - Fighter overhead costs by facility tier
# - Camp finances and operating costs
# - Loan system with interest
# - Camp upgrade requirements
# - Full transaction history

"""
Cage Dynasty - Economy System

Handles all financial aspects of the simulation:
- Fighter purses and bonuses
- Fictional sponsorship deals and tiers
- Camp operating costs and revenue
- Fighter overhead (varies by facility tier)
- Camp sponsorships (steady income)
- Loan system with interest payments
- Camp tier upgrades with requirements
- Transaction history for all money movements

Usage:
    from systems.economy import (
        EconomyManager,
        create_economy_manager,
        TransactionType,
        Loan,
        UpgradeRequirement,
    )
    
    # Create manager
    manager = create_economy_manager()
    
    # Process weekly finances
    summary = manager.process_weekly_finances(camp_id, camp_data)
    
    # Pay fight purse
    earnings = manager.pay_fight_purse(camp_id, fighter_id, fight_result)
    
    # Check upgrade eligibility
    eligible, unmet = manager.check_upgrade_eligibility(camp_id, target_tier, camp_data)
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum, auto
from datetime import datetime
import uuid


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class TransactionType(Enum):
    """Types of financial transactions"""
    # Income
    FIGHT_PURSE = "fight_purse"
    WIN_BONUS = "win_bonus"
    MAIN_EVENT_BONUS = "main_event_bonus"
    PERFORMANCE_BONUS = "performance_bonus"
    SPONSORSHIP_PAYMENT = "sponsorship_payment"
    SPONSORSHIP_BONUS = "sponsorship_bonus"
    CAMP_SPONSORSHIP = "camp_sponsorship"
    LOAN_RECEIVED = "loan_received"
    
    # Expenses
    WEEKLY_OPERATING = "weekly_operating"
    COACH_SALARY = "coach_salary"
    FIGHTER_OVERHEAD = "fighter_overhead"
    LOAN_PAYMENT = "loan_payment"
    LOAN_INTEREST = "loan_interest"
    UPGRADE_COST = "upgrade_cost"
    SIGNING_BONUS = "signing_bonus"
    FACILITY_COST = "facility_cost"


class LoanStatus(Enum):
    """Status of a loan"""
    ACTIVE = "active"
    PAID_OFF = "paid_off"
    DEFAULTED = "defaulted"


class SponsorTier(Enum):
    """Sponsorship tiers based on fighter status"""
    ELITE = "elite"
    RANKED = "ranked"
    PROSPECT = "prospect"
    LOCAL = "local"


# Base purse by rank tier
# Bumped debut/unranked to make early game viable
BASE_PURSE_BY_TIER: Dict[str, int] = {
    "champion": 500000,
    "top_5": 150000,
    "top_10": 75000,
    "top_15": 40000,
    "ranked": 30000,     # Was 25,000
    "unranked": 18000,   # Was 12,000 - this is the key fix
    "debut": 12000,      # Was 8,000
}

# Win bonus multiplier (100% of base purse)
WIN_BONUS_MULTIPLIER: float = 1.0

# Performance bonus amounts
PERFORMANCE_BONUSES: Dict[str, int] = {
    "fight_of_the_night": 50000,
    "performance_of_the_night": 50000,
    "knockout_of_the_night": 50000,
    "submission_of_the_night": 50000,
}

# Title fight and main event multipliers
TITLE_FIGHT_MULTIPLIER: float = 2.0
MAIN_EVENT_MULTIPLIER: float = 1.5  # Applied to base purse for main events

# Main event bonuses (flat bonuses, not multipliers)
MAIN_EVENT_BONUS: int = 15000       # Non-title main event bonus
MAIN_EVENT_TITLE_BONUS: int = 25000  # Title fight main event bonus
CO_MAIN_EVENT_BONUS: int = 7500      # Co-main event bonus

# Camp tier costs (monthly)
# Balanced for early-game survival - garage should be almost free
CAMP_MONTHLY_COSTS: Dict[str, int] = {
    "GARAGE": 500,       # Was 5,000 - it's a garage, just utilities
    "LOCAL": 3000,       # Was 15,000 - small strip mall dojo
    "REGIONAL": 10000,   # Was 40,000 - warehouse gym
    "NATIONAL": 30000,   # Was 100,000 - proper facility
    "ELITE": 75000,      # Was 250,000 - world-class but not insane
}

# Fighter overhead costs per week (varies by facility tier)
# Garage fighters bring their own water and tape
FIGHTER_OVERHEAD_BY_TIER: Dict[str, int] = {
    "GARAGE": 0,        # Was 50 - they self-fund at this level
    "LOCAL": 25,        # Was 100 - basic gym access
    "REGIONAL": 75,     # Was 200 - some stipends
    "NATIONAL": 200,    # Was 400 - proper support
    "ELITE": 400,       # Was 750 - first-class
}

# Camp tier values for comparison
CAMP_TIER_VALUES: Dict[str, int] = {
    "GARAGE": 1,
    "LOCAL": 2,
    "REGIONAL": 3,
    "NATIONAL": 4,
    "ELITE": 5,
}

# Starting funds by tier
STARTING_FUNDS: Dict[str, int] = {
    "GARAGE": 50000,
    "LOCAL": 100000,
    "REGIONAL": 250000,
    "NATIONAL": 500000,
    "ELITE": 1000000,
}

# Loan configuration by tier
LOAN_CONFIG: Dict[str, Dict[str, Any]] = {
    "GARAGE": {
        "max_loan": 25000,
        "interest_rate": 0.06,  # 6% per month
        "min_payment_pct": 0.05,  # 5% of balance minimum
    },
    "LOCAL": {
        "max_loan": 75000,
        "interest_rate": 0.05,
        "min_payment_pct": 0.05,
    },
    "REGIONAL": {
        "max_loan": 200000,
        "interest_rate": 0.04,
        "min_payment_pct": 0.05,
    },
    "NATIONAL": {
        "max_loan": 500000,
        "interest_rate": 0.03,
        "min_payment_pct": 0.05,
    },
    "ELITE": {
        "max_loan": 1000000,
        "interest_rate": 0.02,
        "min_payment_pct": 0.05,
    },
}

# Emergency loan (higher interest, offered when struggling)
EMERGENCY_LOAN_INTEREST: float = 0.08  # 8% per month

# Upgrade requirements: cost + ONE of (reputation, championships, roster)
UPGRADE_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "LOCAL": {  # From GARAGE to LOCAL
        "cost": 50000,
        "reputation": 40,
        "championships": 1,
        "min_roster": 5,
    },
    "REGIONAL": {  # From LOCAL to REGIONAL
        "cost": 150000,
        "reputation": 55,
        "championships": 2,
        "min_roster": 10,
    },
    "NATIONAL": {  # From REGIONAL to NATIONAL
        "cost": 400000,
        "reputation": 70,
        "championships": 3,
        "min_roster": 15,
    },
    "ELITE": {  # From NATIONAL to ELITE
        "cost": 1000000,
        "reputation": 85,
        "championships": 5,
        "min_roster": 25,
    },
}

# Default coach for new camps
DEFAULT_COACH_SALARY: int = 2000  # Weekly
DEFAULT_COACH_QUALITY: int = 3  # 3-star

# Bankruptcy thresholds
BANKRUPTCY_WEEKS_THRESHOLD: int = 4  # Consecutive weeks in debt
BANKRUPTCY_DEBT_THRESHOLD: int = -50000  # Maximum allowed debt


# ============================================================================
# FICTIONAL SPONSORSHIP BRANDS
# ============================================================================

# Sponsorship contract length by tier (in fights)
SPONSOR_CONTRACT_LENGTH: Dict[str, Tuple[int, int]] = {
    "elite": (6, 8),      # 6-8 fights for elite sponsors
    "ranked": (4, 6),     # 4-6 fights for ranked sponsors
    "prospect": (3, 4),   # 3-4 fights for prospect sponsors
    "local": (2, 3),      # 2-3 fights for local sponsors
}

# Fighter sponsorship companies by tier (FICTIONAL BRANDS)
SPONSORSHIP_COMPANIES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "elite": {
        # Premium apparel and beverage sponsors for champions and top 5
        "APEX Fightwear": {
            "base_payment": (18000, 35000),
            "bonuses": {"win": 6000, "title_win": 30000, "finish": 3000},
            "type": "apparel",
            "prestige": 100,
        },
        "Titan Athletics": {
            "base_payment": (15000, 30000),
            "bonuses": {"win": 5000, "title_win": 25000, "finish": 2500},
            "type": "apparel",
            "prestige": 95,
        },
        "SURGE Energy": {
            "base_payment": (20000, 40000),
            "bonuses": {"win": 7500, "title_win": 35000, "finish": 4000},
            "type": "beverage",
            "prestige": 98,
        },
        "Vanguard Combat": {
            "base_payment": (16000, 32000),
            "bonuses": {"win": 5500, "title_win": 28000, "finish": 2800},
            "type": "apparel",
            "prestige": 92,
        },
        "Dominion Sports": {
            "base_payment": (14000, 28000),
            "bonuses": {"win": 4500, "title_win": 22000, "finish": 2200},
            "type": "apparel",
            "prestige": 88,
        },
    },
    "ranked": {
        # Mid-tier sponsors for ranked fighters (top 15)
        "Iron Will Apparel": {
            "base_payment": (5000, 12000),
            "bonuses": {"win": 2500, "title_win": 15000, "finish": 1200},
            "type": "apparel",
            "prestige": 70,
        },
        "Warpath Gear": {
            "base_payment": (4500, 10000),
            "bonuses": {"win": 2200, "title_win": 12000, "finish": 1100},
            "type": "apparel",
            "prestige": 65,
        },
        "Combat Fuel": {
            "base_payment": (6000, 14000),
            "bonuses": {"win": 3000, "title_win": 18000, "finish": 1500},
            "type": "beverage",
            "prestige": 75,
        },
        "Grind Mode Athletics": {
            "base_payment": (4000, 9000),
            "bonuses": {"win": 2000, "title_win": 10000, "finish": 1000},
            "type": "apparel",
            "prestige": 60,
        },
        "Predator Sports": {
            "base_payment": (5500, 11000),
            "bonuses": {"win": 2800, "title_win": 14000, "finish": 1400},
            "type": "apparel",
            "prestige": 68,
        },
    },
    "prospect": {
        # Entry-level sponsors for unranked fighters with potential
        "Underground Combat": {
            "base_payment": (800, 2000),
            "bonuses": {"win": 750, "title_win": 5000, "finish": 350},
            "type": "apparel",
            "prestige": 40,
        },
        "Hustle Fight Co.": {
            "base_payment": (600, 1800),
            "bonuses": {"win": 600, "title_win": 4000, "finish": 300},
            "type": "apparel",
            "prestige": 35,
        },
        "Raw Power Apparel": {
            "base_payment": (500, 1500),
            "bonuses": {"win": 500, "title_win": 3500, "finish": 250},
            "type": "apparel",
            "prestige": 30,
        },
        "Next Level Gear": {
            "base_payment": (700, 1600),
            "bonuses": {"win": 550, "title_win": 3800, "finish": 280},
            "type": "apparel",
            "prestige": 32,
        },
        "Pump Supplements": {
            "base_payment": (900, 2200),
            "bonuses": {"win": 800, "title_win": 5500, "finish": 400},
            "type": "nutrition",
            "prestige": 42,
        },
    },
    "local": {
        # Small sponsors for debuting/regional fighters
        "Garage Gym Gear": {
            "base_payment": (150, 400),
            "bonuses": {"win": 100, "title_win": 1000, "finish": 50},
            "type": "apparel",
            "prestige": 15,
        },
        "Fight Ready Basics": {
            "base_payment": (200, 500),
            "bonuses": {"win": 150, "title_win": 1200, "finish": 75},
            "type": "apparel",
            "prestige": 18,
        },
        "Corner Deli": {
            "base_payment": (100, 300),
            "bonuses": {"win": 75, "title_win": 800, "finish": 40},
            "type": "local",
            "prestige": 10,
        },
        "Hometown Auto": {
            "base_payment": (120, 350),
            "bonuses": {"win": 80, "title_win": 900, "finish": 45},
            "type": "local",
            "prestige": 12,
        },
        "Joe's Supplements": {
            "base_payment": (180, 450),
            "bonuses": {"win": 120, "title_win": 1100, "finish": 60},
            "type": "nutrition",
            "prestige": 16,
        },
    },
}

# Camp sponsorship companies by facility tier
CAMP_SPONSORS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "GARAGE": {},  # No camp sponsors for garage gyms
    "LOCAL": {
        "Hometown Supplements": {
            "weekly_payment": (500, 800),
            "training_bonus": 0.0,
            "prestige": 15,
        },
        "City Fitness Equipment": {
            "weekly_payment": (600, 1000),
            "training_bonus": 0.01,  # +1% training
            "prestige": 18,
        },
        "Local Credit Union": {
            "weekly_payment": (400, 700),
            "training_bonus": 0.0,
            "prestige": 12,
        },
    },
    "REGIONAL": {
        "Grind Mode Athletics Center": {
            "weekly_payment": (1500, 2500),
            "training_bonus": 0.02,  # +2% training
            "prestige": 40,
        },
        "Combat Fuel Performance Lab": {
            "weekly_payment": (2000, 3000),
            "training_bonus": 0.03,  # +3% training
            "prestige": 50,
        },
        "Iron Will Training Facility": {
            "weekly_payment": (1800, 2800),
            "training_bonus": 0.02,
            "prestige": 45,
        },
    },
    "NATIONAL": {
        "Powered by Iron Will Apparel": {
            "weekly_payment": (5000, 8000),
            "training_bonus": 0.03,
            "prestige": 70,
        },
        "SURGE Energy Training Facility": {
            "weekly_payment": (7000, 10000),
            "training_bonus": 0.04,  # +4% training
            "prestige": 80,
        },
        "Warpath Performance Center": {
            "weekly_payment": (6000, 9000),
            "training_bonus": 0.03,
            "prestige": 75,
        },
    },
    "ELITE": {
        "APEX Fightwear Elite Training Center": {
            "weekly_payment": (15000, 25000),
            "training_bonus": 0.05,  # +5% training
            "prestige": 95,
        },
        "Titan Athletics World Headquarters": {
            "weekly_payment": (18000, 28000),
            "training_bonus": 0.05,
            "prestige": 98,
        },
        "Vanguard Combat Institute": {
            "weekly_payment": (12000, 20000),
            "training_bonus": 0.04,
            "prestige": 90,
        },
    },
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Transaction:
    """
    A single financial transaction.
    
    Tracks all money movements for history and reporting.
    """
    transaction_id: str
    transaction_type: TransactionType
    amount: int  # Positive for income, negative for expenses
    description: str
    camp_id: str
    fighter_id: Optional[str] = None
    date: str = ""
    week: int = 0
    balance_after: int = 0
    
    @property
    def is_income(self) -> bool:
        return self.amount > 0
    
    @property
    def is_expense(self) -> bool:
        return self.amount < 0
    
    @property
    def formatted_amount(self) -> str:
        if self.amount >= 0:
            return f"+${self.amount:,}"
        return f"-${abs(self.amount):,}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "transaction_type": self.transaction_type.value,
            "amount": self.amount,
            "description": self.description,
            "camp_id": self.camp_id,
            "fighter_id": self.fighter_id,
            "date": self.date,
            "week": self.week,
            "balance_after": self.balance_after,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        return cls(
            transaction_id=data.get("transaction_id", str(uuid.uuid4())[:8]),
            transaction_type=TransactionType(data.get("transaction_type", "fight_purse")),
            amount=data.get("amount", 0),
            description=data.get("description", ""),
            camp_id=data.get("camp_id", ""),
            fighter_id=data.get("fighter_id"),
            date=data.get("date", ""),
            week=data.get("week", 0),
            balance_after=data.get("balance_after", 0),
        )


@dataclass
class Loan:
    """
    A loan taken by a camp.
    
    Tracks principal, interest, payments, and status.
    """
    loan_id: str
    camp_id: str
    principal: int  # Original amount borrowed
    current_balance: int  # Remaining balance with interest
    interest_rate: float  # Monthly rate (e.g., 0.06 = 6%)
    min_payment_pct: float  # Minimum payment as % of balance
    status: LoanStatus = LoanStatus.ACTIVE
    date_taken: str = ""
    week_taken: int = 0
    total_paid: int = 0
    total_interest_paid: int = 0
    payments_made: int = 0
    weeks_since_payment: int = 0
    is_emergency: bool = False  # Emergency loans have higher interest
    
    @property
    def min_weekly_payment(self) -> int:
        """Minimum payment required per week (interest only + min principal)"""
        # Weekly interest (monthly rate / 4)
        weekly_interest = int(self.current_balance * (self.interest_rate / 4))
        # Minimum principal payment
        min_principal = int(self.current_balance * (self.min_payment_pct / 4))
        return max(weekly_interest + min_principal, 100)  # At least $100
    
    @property
    def is_paid_off(self) -> bool:
        return self.current_balance <= 0 or self.status == LoanStatus.PAID_OFF
    
    @property
    def weekly_interest(self) -> int:
        """Interest accrued per week"""
        return int(self.current_balance * (self.interest_rate / 4))
    
    def apply_weekly_interest(self) -> int:
        """Apply weekly interest to balance. Returns interest amount."""
        if self.status != LoanStatus.ACTIVE:
            return 0
        interest = self.weekly_interest
        self.current_balance += interest
        return interest
    
    def make_payment(self, amount: int) -> Tuple[int, int]:
        """
        Make a payment on the loan.
        
        Returns: (principal_paid, interest_paid)
        """
        if self.status != LoanStatus.ACTIVE or amount <= 0:
            return (0, 0)
        
        # Calculate how much goes to interest vs principal
        weekly_interest = self.weekly_interest
        
        if amount <= weekly_interest:
            # Payment only covers interest (or less)
            interest_paid = amount
            principal_paid = 0
        else:
            # Payment covers interest and some principal
            interest_paid = weekly_interest
            principal_paid = min(amount - interest_paid, self.current_balance - interest_paid)
        
        # Apply payment
        self.current_balance -= (principal_paid + interest_paid)
        self.total_paid += principal_paid + interest_paid
        self.total_interest_paid += interest_paid
        self.payments_made += 1
        self.weeks_since_payment = 0
        
        # Check if paid off
        if self.current_balance <= 0:
            self.current_balance = 0
            self.status = LoanStatus.PAID_OFF
        
        return (principal_paid, interest_paid)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "loan_id": self.loan_id,
            "camp_id": self.camp_id,
            "principal": self.principal,
            "current_balance": self.current_balance,
            "interest_rate": self.interest_rate,
            "min_payment_pct": self.min_payment_pct,
            "status": self.status.value,
            "date_taken": self.date_taken,
            "week_taken": self.week_taken,
            "total_paid": self.total_paid,
            "total_interest_paid": self.total_interest_paid,
            "payments_made": self.payments_made,
            "weeks_since_payment": self.weeks_since_payment,
            "is_emergency": self.is_emergency,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Loan":
        return cls(
            loan_id=data.get("loan_id", str(uuid.uuid4())[:8]),
            camp_id=data.get("camp_id", ""),
            principal=data.get("principal", 0),
            current_balance=data.get("current_balance", 0),
            interest_rate=data.get("interest_rate", 0.05),
            min_payment_pct=data.get("min_payment_pct", 0.05),
            status=LoanStatus(data.get("status", "active")),
            date_taken=data.get("date_taken", ""),
            week_taken=data.get("week_taken", 0),
            total_paid=data.get("total_paid", 0),
            total_interest_paid=data.get("total_interest_paid", 0),
            payments_made=data.get("payments_made", 0),
            weeks_since_payment=data.get("weeks_since_payment", 0),
            is_emergency=data.get("is_emergency", False),
        )


@dataclass
class Sponsorship:
    """
    Represents a sponsorship deal for a fighter.
    
    Now uses FIGHTS remaining instead of months.
    """
    company_name: str
    payment_per_fight: int  # Payment per fight
    fights_total: int       # Total fights in contract
    fights_remaining: int   # Fights left on contract
    performance_bonuses: Dict[str, int] = field(default_factory=dict)
    tier: SponsorTier = SponsorTier.LOCAL
    fighter_id: str = ""
    sponsorship_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sponsor_type: str = "apparel"  # apparel, beverage, nutrition, local
    prestige: int = 50
    
    @property
    def is_active(self) -> bool:
        return self.fights_remaining > 0
    
    def get_win_bonus(self) -> int:
        return self.performance_bonuses.get("win", 0)
    
    def get_title_win_bonus(self) -> int:
        return self.performance_bonuses.get("title_win", 0)
    
    def get_finish_bonus(self) -> int:
        return self.performance_bonuses.get("finish", 0)
    
    def process_fight(self) -> int:
        """Process a fight, return payment and decrement remaining."""
        if not self.is_active:
            return 0
        self.fights_remaining -= 1
        return self.payment_per_fight
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_name": self.company_name,
            "payment_per_fight": self.payment_per_fight,
            "fights_total": self.fights_total,
            "fights_remaining": self.fights_remaining,
            "performance_bonuses": self.performance_bonuses,
            "tier": self.tier.value,
            "fighter_id": self.fighter_id,
            "sponsorship_id": self.sponsorship_id,
            "sponsor_type": self.sponsor_type,
            "prestige": self.prestige,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Sponsorship":
        return cls(
            company_name=data.get("company_name", "Unknown"),
            payment_per_fight=data.get("payment_per_fight", 0),
            fights_total=data.get("fights_total", 3),
            fights_remaining=data.get("fights_remaining", 3),
            performance_bonuses=data.get("performance_bonuses", {}),
            tier=SponsorTier(data.get("tier", "local")),
            fighter_id=data.get("fighter_id", ""),
            sponsorship_id=data.get("sponsorship_id", str(uuid.uuid4())[:8]),
            sponsor_type=data.get("sponsor_type", "apparel"),
            prestige=data.get("prestige", 50),
        )


@dataclass
class CampSponsorship:
    """
    Represents a facility/camp sponsorship deal.
    
    Provides steady weekly income to the camp.
    """
    company_name: str
    weekly_payment: int
    training_bonus: float  # Multiplier bonus (0.02 = +2%)
    prestige: int
    camp_id: str
    sponsorship_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    is_active: bool = True
    weeks_active: int = 0
    
    def process_week(self) -> int:
        """Process a week and return payment."""
        if not self.is_active:
            return 0
        self.weeks_active += 1
        return self.weekly_payment
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_name": self.company_name,
            "weekly_payment": self.weekly_payment,
            "training_bonus": self.training_bonus,
            "prestige": self.prestige,
            "camp_id": self.camp_id,
            "sponsorship_id": self.sponsorship_id,
            "is_active": self.is_active,
            "weeks_active": self.weeks_active,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampSponsorship":
        return cls(
            company_name=data.get("company_name", "Unknown"),
            weekly_payment=data.get("weekly_payment", 0),
            training_bonus=data.get("training_bonus", 0.0),
            prestige=data.get("prestige", 0),
            camp_id=data.get("camp_id", ""),
            sponsorship_id=data.get("sponsorship_id", str(uuid.uuid4())[:8]),
            is_active=data.get("is_active", True),
            weeks_active=data.get("weeks_active", 0),
        )


@dataclass
class UpgradeRequirement:
    """Requirements for upgrading camp tier."""
    target_tier: str
    cost: int
    reputation_needed: int
    championships_needed: int
    min_roster: int
    
    def check_eligibility(
        self,
        balance: int,
        reputation: int,
        championships: int,
        roster_size: int,
    ) -> Tuple[bool, List[str]]:
        """Check if camp meets upgrade requirements."""
        unmet = []
        
        if balance < self.cost:
            unmet.append(f"Need ${self.cost:,} (have ${balance:,})")
        
        # Need to meet ONE of: reputation, championships, or roster
        paths_met = 0
        path_details = []
        
        if reputation >= self.reputation_needed:
            paths_met += 1
        else:
            path_details.append(f"Reputation {reputation}/{self.reputation_needed}")
        
        if championships >= self.championships_needed:
            paths_met += 1
        else:
            path_details.append(f"Championships {championships}/{self.championships_needed}")
        
        if roster_size >= self.min_roster:
            paths_met += 1
        else:
            path_details.append(f"Roster {roster_size}/{self.min_roster}")
        
        if paths_met == 0:
            unmet.append(f"Need ONE of: {' OR '.join(path_details)}")
        
        return (len(unmet) == 0, unmet)


@dataclass
class CampFinanceState:
    """
    Complete financial state for a camp.
    
    Tracks balance, loans, transactions, and history.
    """
    camp_id: str
    balance: int = 0
    total_earnings: int = 0
    total_expenses: int = 0
    
    # Loans
    active_loans: List[Loan] = field(default_factory=list)
    loan_history: List[Loan] = field(default_factory=list)
    
    # Sponsorship
    camp_sponsorship: Optional[CampSponsorship] = None
    
    # Transaction history (last 100)
    transactions: List[Transaction] = field(default_factory=list)
    
    # Weekly tracking
    weekly_income: int = 0
    weekly_expenses: int = 0
    
    # Bankruptcy tracking
    weeks_in_debt: int = 0
    
    @property
    def total_debt(self) -> int:
        return sum(loan.current_balance for loan in self.active_loans)
    
    @property
    def net_worth(self) -> int:
        return self.balance - self.total_debt
    
    @property
    def is_in_debt(self) -> bool:
        return self.balance < 0
    
    @property
    def has_active_loan(self) -> bool:
        return len(self.active_loans) > 0
    
    @property
    def min_loan_payment_due(self) -> int:
        """Minimum payment due this week across all loans."""
        return sum(loan.min_weekly_payment for loan in self.active_loans)
    
    def add_transaction(self, transaction: Transaction) -> None:
        """Add transaction, keeping only last 100."""
        self.transactions.append(transaction)
        if len(self.transactions) > 100:
            self.transactions = self.transactions[-100:]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "camp_id": self.camp_id,
            "balance": self.balance,
            "total_earnings": self.total_earnings,
            "total_expenses": self.total_expenses,
            "active_loans": [loan.to_dict() for loan in self.active_loans],
            "loan_history": [loan.to_dict() for loan in self.loan_history],
            "camp_sponsorship": self.camp_sponsorship.to_dict() if self.camp_sponsorship else None,
            "transactions": [t.to_dict() for t in self.transactions[-50:]],
            "weekly_income": self.weekly_income,
            "weekly_expenses": self.weekly_expenses,
            "weeks_in_debt": self.weeks_in_debt,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampFinanceState":
        state = cls(
            camp_id=data.get("camp_id", ""),
            balance=data.get("balance", 0),
            total_earnings=data.get("total_earnings", 0),
            total_expenses=data.get("total_expenses", 0),
            weekly_income=data.get("weekly_income", 0),
            weekly_expenses=data.get("weekly_expenses", 0),
            weeks_in_debt=data.get("weeks_in_debt", 0),
        )
        
        # Deserialize loans
        state.active_loans = [
            Loan.from_dict(loan_data) 
            for loan_data in data.get("active_loans", [])
        ]
        state.loan_history = [
            Loan.from_dict(loan_data) 
            for loan_data in data.get("loan_history", [])
        ]
        
        # Deserialize camp sponsorship
        if data.get("camp_sponsorship"):
            state.camp_sponsorship = CampSponsorship.from_dict(data["camp_sponsorship"])
        
        # Deserialize transactions
        state.transactions = [
            Transaction.from_dict(t_data) 
            for t_data in data.get("transactions", [])
        ]
        
        return state


@dataclass
class FightEarnings:
    """Breakdown of earnings from a single fight."""
    fighter_id: str
    fighter_name: str
    camp_id: str
    
    # Purse components
    show_money: int = 0
    win_bonus: int = 0
    main_event_bonus: int = 0  # NEW: Separate main event bonus
    performance_bonuses: Dict[str, int] = field(default_factory=dict)
    sponsorship_payment: int = 0
    sponsorship_bonuses: int = 0
    
    # Camp cut (bumped to 20% for viable early game)
    camp_cut_pct: float = 0.20
    camp_cut_amount: int = 0
    
    # Calculated totals
    fighter_take_home: int = 0
    camp_revenue: int = 0
    total_earned: int = 0
    
    @property
    def total_performance_bonuses(self) -> int:
        return sum(self.performance_bonuses.values())
    
    def calculate_totals(self) -> None:
        """Calculate final amounts after all values are set."""
        self.total_earned = (
            self.show_money + 
            self.win_bonus + 
            self.main_event_bonus +
            self.total_performance_bonuses + 
            self.sponsorship_payment +
            self.sponsorship_bonuses
        )
        self.camp_cut_amount = int(self.total_earned * self.camp_cut_pct)
        self.fighter_take_home = self.total_earned - self.camp_cut_amount
        self.camp_revenue = self.camp_cut_amount
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "camp_id": self.camp_id,
            "show_money": self.show_money,
            "win_bonus": self.win_bonus,
            "main_event_bonus": self.main_event_bonus,
            "performance_bonuses": self.performance_bonuses,
            "sponsorship_payment": self.sponsorship_payment,
            "sponsorship_bonuses": self.sponsorship_bonuses,
            "camp_cut_pct": self.camp_cut_pct,
            "camp_cut_amount": self.camp_cut_amount,
            "fighter_take_home": self.fighter_take_home,
            "camp_revenue": self.camp_revenue,
            "total_earned": self.total_earned,
        }


@dataclass
class WeeklyFinanceSummary:
    """Summary of weekly financial processing."""
    camp_id: str
    week: int
    date: str
    
    # Starting state
    opening_balance: int = 0
    
    # Income
    fight_purses: int = 0
    win_bonuses: int = 0
    main_event_bonuses: int = 0
    performance_bonuses: int = 0
    sponsorship_income: int = 0
    camp_sponsorship_income: int = 0
    other_income: int = 0
    total_income: int = 0
    
    # Expenses
    facility_costs: int = 0
    coach_salaries: int = 0
    fighter_overhead: int = 0
    loan_payments: int = 0
    loan_interest: int = 0
    other_expenses: int = 0
    total_expenses: int = 0
    
    # Net
    net_change: int = 0
    closing_balance: int = 0
    
    # Loan status
    total_debt: int = 0
    min_payment_due: int = 0
    
    # Warnings
    warnings: List[str] = field(default_factory=list)
    is_in_debt: bool = False
    bankruptcy_warning: bool = False
    weeks_in_debt: int = 0
    
    def calculate_totals(self) -> None:
        """Calculate totals from components."""
        self.total_income = (
            self.fight_purses +
            self.win_bonuses +
            self.main_event_bonuses +
            self.performance_bonuses +
            self.sponsorship_income +
            self.camp_sponsorship_income +
            self.other_income
        )
        self.total_expenses = (
            self.facility_costs +
            self.coach_salaries +
            self.fighter_overhead +
            self.loan_payments +
            self.loan_interest +
            self.other_expenses
        )
        self.net_change = self.total_income - self.total_expenses
        self.closing_balance = self.opening_balance + self.net_change
        self.is_in_debt = self.closing_balance < 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "camp_id": self.camp_id,
            "week": self.week,
            "date": self.date,
            "opening_balance": self.opening_balance,
            "fight_purses": self.fight_purses,
            "win_bonuses": self.win_bonuses,
            "main_event_bonuses": self.main_event_bonuses,
            "performance_bonuses": self.performance_bonuses,
            "sponsorship_income": self.sponsorship_income,
            "camp_sponsorship_income": self.camp_sponsorship_income,
            "other_income": self.other_income,
            "total_income": self.total_income,
            "facility_costs": self.facility_costs,
            "coach_salaries": self.coach_salaries,
            "fighter_overhead": self.fighter_overhead,
            "loan_payments": self.loan_payments,
            "loan_interest": self.loan_interest,
            "other_expenses": self.other_expenses,
            "total_expenses": self.total_expenses,
            "net_change": self.net_change,
            "closing_balance": self.closing_balance,
            "total_debt": self.total_debt,
            "min_payment_due": self.min_payment_due,
            "warnings": self.warnings,
            "is_in_debt": self.is_in_debt,
            "bankruptcy_warning": self.bankruptcy_warning,
            "weeks_in_debt": self.weeks_in_debt,
        }


class FinancialPressureStage(Enum):
    """Stages of financial pressure."""
    HEALTHY = "healthy"              # Positive balance
    WARNING = "warning"              # 1-2 weeks in debt
    EMERGENCY_LOAN = "emergency"     # 3-4 weeks, offer emergency loan
    COST_CUTTING = "cost_cutting"    # 5-6 weeks, forced cuts
    DOWNGRADE = "downgrade"          # 7-8 weeks, facility downgrade
    BANKRUPTCY = "bankruptcy"        # 10+ weeks, game over


@dataclass
class FinancialPressureResult:
    """Result of financial pressure check."""
    stage: FinancialPressureStage
    weeks_in_debt: int
    balance: int
    
    # Messages for the player
    headline: str = ""
    description: str = ""
    
    # Emergency loan offer (if applicable)
    emergency_loan_available: bool = False
    emergency_loan_amount: int = 0
    emergency_loan_interest: float = 0.08
    
    # Required cuts (if applicable)
    must_release_fighter: bool = False
    must_fire_coach: bool = False
    releasable_fighters: List[str] = field(default_factory=list)  # Fighter IDs
    fireable_coaches: List[str] = field(default_factory=list)     # Coach IDs
    
    # Downgrade info
    must_downgrade: bool = False
    current_tier: str = ""
    downgrade_tier: str = ""
    
    # Bankruptcy
    is_bankrupt: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "weeks_in_debt": self.weeks_in_debt,
            "balance": self.balance,
            "headline": self.headline,
            "description": self.description,
            "emergency_loan_available": self.emergency_loan_available,
            "emergency_loan_amount": self.emergency_loan_amount,
            "must_release_fighter": self.must_release_fighter,
            "must_fire_coach": self.must_fire_coach,
            "must_downgrade": self.must_downgrade,
            "is_bankrupt": self.is_bankrupt,
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_purse_tier(
    rank: Optional[int], 
    is_champion: bool, 
    total_fights: int
) -> str:
    """Determine purse tier based on fighter status."""
    if is_champion:
        return "champion"
    if total_fights == 0:
        return "debut"
    if rank is None:
        return "unranked"
    if rank <= 5:
        return "top_5"
    if rank <= 10:
        return "top_10"
    if rank <= 15:
        return "top_15"
    return "ranked"


def calculate_base_purse(
    rank: Optional[int] = None,
    is_champion: bool = False,
    total_fights: int = 1,
    is_title_fight: bool = False,
    is_main_event: bool = False,
) -> int:
    """Calculate base purse for a fighter."""
    tier = get_purse_tier(rank, is_champion, total_fights)
    base = BASE_PURSE_BY_TIER[tier]
    
    # Title fight gets 2x multiplier on base
    if is_title_fight:
        base = int(base * TITLE_FIGHT_MULTIPLIER)
    # Main event (non-title) gets 1.5x multiplier
    elif is_main_event:
        base = int(base * MAIN_EVENT_MULTIPLIER)
    
    return base


def calculate_main_event_bonus(
    is_main_event: bool = False,
    is_co_main: bool = False,
    is_title_fight: bool = False,
) -> int:
    """Calculate flat main event bonus."""
    if is_main_event:
        if is_title_fight:
            return MAIN_EVENT_TITLE_BONUS  # $25,000
        return MAIN_EVENT_BONUS  # $15,000
    elif is_co_main:
        return CO_MAIN_EVENT_BONUS  # $7,500
    return 0


def determine_sponsor_tier(
    rank: Optional[int],
    is_champion: bool = False,
    marketability: int = 50
) -> SponsorTier:
    """Determine what tier of sponsorships a fighter can attract."""
    if is_champion or (rank is not None and rank <= 3):
        return SponsorTier.ELITE
    if rank is not None and rank <= 15:
        return SponsorTier.RANKED
    if marketability >= 60 or (rank is not None and rank <= 25):
        return SponsorTier.PROSPECT
    return SponsorTier.LOCAL


def generate_sponsorship_offer(
    rank: Optional[int] = None,
    is_champion: bool = False,
    marketability: int = 50,
    wins: int = 0,
    fighter_id: str = "",
    offer_chance: float = 0.3
) -> Optional[Sponsorship]:
    """Generate a sponsorship offer based on fighter's status."""
    # Must have some credibility
    if wins < 3 and rank is None:
        return None
    
    # Adjust offer chance based on status
    adjusted_chance = offer_chance
    if is_champion:
        adjusted_chance = 0.9
    elif rank is not None and rank <= 5:
        adjusted_chance = 0.7
    elif rank is not None and rank <= 15:
        adjusted_chance = 0.5
    elif wins >= 5:
        adjusted_chance = 0.4
    
    if random.random() > adjusted_chance:
        return None
    
    # Determine tier
    tier = determine_sponsor_tier(rank, is_champion, marketability)
    
    # Get available companies for tier
    tier_companies = SPONSORSHIP_COMPANIES.get(tier.value, SPONSORSHIP_COMPANIES["local"])
    
    # Pick a random company
    company_name = random.choice(list(tier_companies.keys()))
    company_data = tier_companies[company_name]
    
    # Generate payment
    min_pay, max_pay = company_data["base_payment"]
    payment = random.randint(min_pay, max_pay)
    
    # Adjust payment based on champion status
    if is_champion:
        payment = int(payment * 1.5)
    
    # Get contract length
    min_fights, max_fights = SPONSOR_CONTRACT_LENGTH.get(tier.value, (2, 3))
    fights = random.randint(min_fights, max_fights)
    
    return Sponsorship(
        company_name=company_name,
        payment_per_fight=payment,
        fights_total=fights,
        fights_remaining=fights,
        performance_bonuses=company_data["bonuses"].copy(),
        tier=tier,
        fighter_id=fighter_id,
        sponsor_type=company_data.get("type", "apparel"),
        prestige=company_data.get("prestige", 50),
    )


def generate_camp_sponsorship_offer(
    camp_tier: str,
    camp_id: str,
) -> Optional[CampSponsorship]:
    """Generate a camp sponsorship offer based on facility tier."""
    tier = camp_tier.upper()
    
    # Get available sponsors for tier
    tier_sponsors = CAMP_SPONSORS.get(tier, {})
    
    if not tier_sponsors:
        return None
    
    # Pick a random sponsor
    company_name = random.choice(list(tier_sponsors.keys()))
    sponsor_data = tier_sponsors[company_name]
    
    # Generate payment
    min_pay, max_pay = sponsor_data["weekly_payment"]
    payment = random.randint(min_pay, max_pay)
    
    return CampSponsorship(
        company_name=company_name,
        weekly_payment=payment,
        training_bonus=sponsor_data["training_bonus"],
        prestige=sponsor_data["prestige"],
        camp_id=camp_id,
    )


def get_upgrade_requirement(target_tier: str) -> Optional[UpgradeRequirement]:
    """Get requirements for upgrading to target tier."""
    target = target_tier.upper()
    if target not in UPGRADE_REQUIREMENTS:
        return None
    
    req = UPGRADE_REQUIREMENTS[target]
    return UpgradeRequirement(
        target_tier=target,
        cost=req["cost"],
        reputation_needed=req["reputation"],
        championships_needed=req["championships"],
        min_roster=req["min_roster"],
    )


def get_next_tier(current_tier: str) -> Optional[str]:
    """Get the next tier after current."""
    tiers = list(CAMP_TIER_VALUES.keys())
    current = current_tier.upper()
    
    if current not in tiers:
        return None
    
    idx = tiers.index(current)
    if idx >= len(tiers) - 1:
        return None  # Already at max tier
    
    return tiers[idx + 1]


def format_money(amount: int, include_sign: bool = True) -> str:
    """Format money amount with optional sign."""
    if include_sign and amount > 0:
        return f"+${amount:,}"
    elif amount < 0:
        return f"-${abs(amount):,}"
    return f"${amount:,}"


def get_fighter_overhead_cost(tier: str) -> int:
    """Get per-fighter weekly overhead cost for a facility tier."""
    return FIGHTER_OVERHEAD_BY_TIER.get(tier.upper(), 100)


# ============================================================================
# ECONOMY MANAGER
# ============================================================================

class EconomyManager:
    """
    Central manager for all economic operations.
    
    Handles:
    - Camp balance tracking
    - Fight purse payments
    - Weekly expense processing
    - Loan management
    - Sponsorship tracking
    - Upgrade requirements
    """
    
    def __init__(self):
        # Camp finances by camp_id
        self._camp_finances: Dict[str, CampFinanceState] = {}
        
        # Fighter sponsorships by fighter_id
        self._fighter_sponsorships: Dict[str, Sponsorship] = {}  # One sponsor per fighter
        
        # Global stats
        self._total_purses_paid: int = 0
        self._total_loans_issued: int = 0
        self._total_upgrades: int = 0
        
        # Current date tracking
        self._current_week: int = 0
        self._current_date: str = ""
    
    # -------------------------------------------------------------------------
    # Camp Finance Access
    # -------------------------------------------------------------------------
    
    def get_camp_finances(self, camp_id: str) -> CampFinanceState:
        """Get or create finance state for a camp."""
        if camp_id not in self._camp_finances:
            self._camp_finances[camp_id] = CampFinanceState(camp_id=camp_id)
        return self._camp_finances[camp_id]
    
    def set_camp_balance(self, camp_id: str, balance: int) -> None:
        """Set a camp's balance (for initialization)."""
        state = self.get_camp_finances(camp_id)
        state.balance = balance
    
    def get_balance(self, camp_id: str) -> int:
        """Get camp's current balance."""
        return self.get_camp_finances(camp_id).balance
    
    def get_net_worth(self, camp_id: str) -> int:
        """Get camp's net worth (balance - debt)."""
        return self.get_camp_finances(camp_id).net_worth
    
    def get_camp_sponsor(self, camp_id: str) -> Optional[CampSponsorship]:
        """Get camp's facility sponsor."""
        return self.get_camp_finances(camp_id).camp_sponsorship
    
    def set_camp_sponsor(self, camp_id: str, sponsor: CampSponsorship) -> None:
        """Set camp's facility sponsor."""
        state = self.get_camp_finances(camp_id)
        state.camp_sponsorship = sponsor
    
    def get_camp_training_bonus(self, camp_id: str) -> float:
        """Get training bonus from camp sponsor (if any)."""
        sponsor = self.get_camp_sponsor(camp_id)
        if sponsor and sponsor.is_active:
            return sponsor.training_bonus
        return 0.0
    
    # -------------------------------------------------------------------------
    # Fighter Sponsorship Management
    # -------------------------------------------------------------------------
    
    def get_fighter_sponsor(self, fighter_id: str) -> Optional[Sponsorship]:
        """Get a fighter's current sponsor."""
        return self._fighter_sponsorships.get(fighter_id)
    
    def set_fighter_sponsor(self, fighter_id: str, sponsor: Sponsorship) -> None:
        """Set a fighter's sponsor (exclusive - replaces existing)."""
        sponsor.fighter_id = fighter_id
        self._fighter_sponsorships[fighter_id] = sponsor
    
    def remove_fighter_sponsor(self, fighter_id: str) -> Optional[Sponsorship]:
        """Remove and return a fighter's sponsor."""
        return self._fighter_sponsorships.pop(fighter_id, None)
    
    def process_fighter_sponsorship_for_fight(
        self, 
        fighter_id: str,
        won: bool,
        is_title_fight: bool,
        is_finish: bool,
    ) -> Tuple[int, int]:
        """
        Process sponsorship for a fight.
        
        Returns: (base_payment, bonus_payment)
        """
        sponsor = self.get_fighter_sponsor(fighter_id)
        if not sponsor or not sponsor.is_active:
            return (0, 0)
        
        # Get base payment for fight
        base_payment = sponsor.process_fight()
        
        # Calculate bonuses
        bonus = 0
        if won:
            bonus += sponsor.get_win_bonus()
            if is_title_fight:
                bonus += sponsor.get_title_win_bonus()
            if is_finish:
                bonus += sponsor.get_finish_bonus()
        
        # Check if contract expired
        if not sponsor.is_active:
            # Contract ended - could generate news
            pass
        
        return (base_payment, bonus)
    
    # -------------------------------------------------------------------------
    # Transaction Recording
    # -------------------------------------------------------------------------
    
    def _record_transaction(
        self,
        camp_id: str,
        trans_type: TransactionType,
        amount: int,
        description: str,
        fighter_id: Optional[str] = None,
    ) -> Transaction:
        """Record a transaction and update balance."""
        state = self.get_camp_finances(camp_id)
        
        # Update balance
        state.balance += amount
        if amount > 0:
            state.total_earnings += amount
        else:
            state.total_expenses += abs(amount)
        
        # Create transaction record
        transaction = Transaction(
            transaction_id=str(uuid.uuid4())[:8],
            transaction_type=trans_type,
            amount=amount,
            description=description,
            camp_id=camp_id,
            fighter_id=fighter_id,
            date=self._current_date,
            week=self._current_week,
            balance_after=state.balance,
        )
        
        state.add_transaction(transaction)
        return transaction
    
    def add_income(
        self,
        camp_id: str,
        amount: int,
        trans_type: TransactionType,
        description: str,
        fighter_id: Optional[str] = None,
    ) -> Transaction:
        """Add income to a camp."""
        return self._record_transaction(
            camp_id=camp_id,
            trans_type=trans_type,
            amount=abs(amount),  # Ensure positive
            description=description,
            fighter_id=fighter_id,
        )
    
    def deduct_expense(
        self,
        camp_id: str,
        amount: int,
        trans_type: TransactionType,
        description: str,
        fighter_id: Optional[str] = None,
    ) -> Transaction:
        """Deduct expense from a camp (can go negative for debt)."""
        return self._record_transaction(
            camp_id=camp_id,
            trans_type=trans_type,
            amount=-abs(amount),  # Ensure negative
            description=description,
            fighter_id=fighter_id,
        )
    
    # -------------------------------------------------------------------------
    # Fight Purse Processing
    # -------------------------------------------------------------------------
    
    def calculate_fight_purse(
        self,
        rank: Optional[int] = None,
        is_champion: bool = False,
        total_fights: int = 1,
        is_title_fight: bool = False,
        is_main_event: bool = False,
    ) -> Dict[str, int]:
        """
        Calculate purse breakdown for a fight.
        
        Returns dict with 'show_money' and 'win_bonus'.
        """
        base = calculate_base_purse(
            rank=rank,
            is_champion=is_champion,
            total_fights=total_fights,
            is_title_fight=is_title_fight,
            is_main_event=is_main_event,
        )
        
        return {
            "show_money": base,
            "win_bonus": int(base * WIN_BONUS_MULTIPLIER),
        }
    
    def pay_fight_purse(
        self,
        camp_id: str,
        fighter_id: str,
        fighter_name: str,
        won: bool,
        rank: Optional[int] = None,
        is_champion: bool = False,
        total_fights: int = 1,
        is_title_fight: bool = False,
        is_main_event: bool = False,
        is_co_main: bool = False,
        is_finish: bool = False,
        method: str = "",
        performance_bonuses: Optional[List[str]] = None,
        camp_cut_pct: float = 0.20,
    ) -> FightEarnings:
        """
        Process complete fight purse payment.
        
        Args:
            camp_id: Camp receiving payment
            fighter_id: Fighter who fought
            fighter_name: Fighter's name
            won: Whether fighter won
            rank: Fighter's rank
            is_champion: Whether fighter is champion
            total_fights: Fighter's total career fights
            is_title_fight: Whether this was a title fight
            is_main_event: Whether this was main event
            is_co_main: Whether this was co-main event
            is_finish: Whether fight ended in finish (KO/SUB)
            method: Win method (KO, TKO, SUB, DEC, etc.)
            performance_bonuses: List of bonus types earned
            camp_cut_pct: Camp's cut percentage
            
        Returns:
            FightEarnings with full breakdown
        """
        purse = self.calculate_fight_purse(
            rank=rank,
            is_champion=is_champion,
            total_fights=total_fights,
            is_title_fight=is_title_fight,
            is_main_event=is_main_event,
        )
        
        earnings = FightEarnings(
            fighter_id=fighter_id,
            fighter_name=fighter_name,
            camp_id=camp_id,
            show_money=purse["show_money"],
            camp_cut_pct=camp_cut_pct,
        )
        
        # Win bonus
        if won:
            earnings.win_bonus = purse["win_bonus"]
        
        # Main event bonus (flat amount, always paid if main/co-main)
        main_event_bonus = calculate_main_event_bonus(
            is_main_event=is_main_event,
            is_co_main=is_co_main,
            is_title_fight=is_title_fight,
        )
        earnings.main_event_bonus = main_event_bonus
        
        # Performance bonuses
        if performance_bonuses:
            for bonus_type in performance_bonuses:
                if bonus_type in PERFORMANCE_BONUSES:
                    earnings.performance_bonuses[bonus_type] = PERFORMANCE_BONUSES[bonus_type]
        
        # Auto-award KO/SUB of the night for finishes (simplified)
        if won and is_finish:
            if method in ["KO", "TKO"] and "knockout_of_the_night" not in earnings.performance_bonuses:
                # 20% chance for KOTN
                if random.random() < 0.20:
                    earnings.performance_bonuses["knockout_of_the_night"] = PERFORMANCE_BONUSES["knockout_of_the_night"]
            elif method in ["SUB", "Submission"] and "submission_of_the_night" not in earnings.performance_bonuses:
                # 25% chance for SOTN
                if random.random() < 0.25:
                    earnings.performance_bonuses["submission_of_the_night"] = PERFORMANCE_BONUSES["submission_of_the_night"]
        
        # Sponsorship payment and bonuses
        sponsor_payment, sponsor_bonus = self.process_fighter_sponsorship_for_fight(
            fighter_id=fighter_id,
            won=won,
            is_title_fight=is_title_fight,
            is_finish=is_finish,
        )
        earnings.sponsorship_payment = sponsor_payment
        earnings.sponsorship_bonuses = sponsor_bonus
        
        # Calculate totals
        earnings.calculate_totals()
        
        # Record transactions
        # Show money (always paid)
        self.add_income(
            camp_id=camp_id,
            amount=earnings.show_money,
            trans_type=TransactionType.FIGHT_PURSE,
            description=f"Show money: {fighter_name}",
            fighter_id=fighter_id,
        )
        
        # Win bonus
        if earnings.win_bonus > 0:
            self.add_income(
                camp_id=camp_id,
                amount=earnings.win_bonus,
                trans_type=TransactionType.WIN_BONUS,
                description=f"Win bonus: {fighter_name}",
                fighter_id=fighter_id,
            )
        
        # Main event bonus
        if earnings.main_event_bonus > 0:
            self.add_income(
                camp_id=camp_id,
                amount=earnings.main_event_bonus,
                trans_type=TransactionType.MAIN_EVENT_BONUS,
                description=f"Main event bonus: {fighter_name}",
                fighter_id=fighter_id,
            )
        
        # Performance bonuses
        for bonus_name, bonus_amount in earnings.performance_bonuses.items():
            self.add_income(
                camp_id=camp_id,
                amount=bonus_amount,
                trans_type=TransactionType.PERFORMANCE_BONUS,
                description=f"{bonus_name.replace('_', ' ').title()}: {fighter_name}",
                fighter_id=fighter_id,
            )
        
        # Sponsorship payment
        if earnings.sponsorship_payment > 0:
            self.add_income(
                camp_id=camp_id,
                amount=earnings.sponsorship_payment,
                trans_type=TransactionType.SPONSORSHIP_PAYMENT,
                description=f"Sponsorship payment: {fighter_name}",
                fighter_id=fighter_id,
            )
        
        # Sponsorship bonuses
        if earnings.sponsorship_bonuses > 0:
            self.add_income(
                camp_id=camp_id,
                amount=earnings.sponsorship_bonuses,
                trans_type=TransactionType.SPONSORSHIP_BONUS,
                description=f"Sponsorship bonuses: {fighter_name}",
                fighter_id=fighter_id,
            )
        
        # Track global stats
        self._total_purses_paid += earnings.total_earned
        
        return earnings
    
    # -------------------------------------------------------------------------
    # Weekly Processing
    # -------------------------------------------------------------------------
    
    def process_weekly_finances(
        self,
        camp_id: str,
        tier: str,
        roster_size: int,
        coach_count: int = 1,
        coach_salaries: int = 0,
        week: int = 0,
        date: str = "",
        is_player_camp: bool = False,
    ) -> WeeklyFinanceSummary:
        """
        Process all weekly financial operations for a camp.
        
        Args:
            camp_id: Camp to process
            tier: Camp tier (GARAGE, LOCAL, etc.)
            roster_size: Number of fighters
            coach_count: Number of coaches
            coach_salaries: Total weekly coach salaries
            week: Current week number
            date: Current date string
            is_player_camp: If True and tier is GARAGE, facility is free
            
        Returns:
            WeeklyFinanceSummary with full breakdown
        """
        self._current_week = week
        self._current_date = date
        
        state = self.get_camp_finances(camp_id)
        
        summary = WeeklyFinanceSummary(
            camp_id=camp_id,
            week=week,
            date=date,
            opening_balance=state.balance,
        )
        
        # Reset weekly trackers
        state.weekly_income = 0
        state.weekly_expenses = 0
        
        # --- INCOME ---
        
        # Camp sponsorship income (if any)
        if state.camp_sponsorship and state.camp_sponsorship.is_active:
            camp_sponsor_payment = state.camp_sponsorship.process_week()
            if camp_sponsor_payment > 0:
                self.add_income(
                    camp_id=camp_id,
                    amount=camp_sponsor_payment,
                    trans_type=TransactionType.CAMP_SPONSORSHIP,
                    description=f"Camp sponsor: {state.camp_sponsorship.company_name}",
                )
                summary.camp_sponsorship_income = camp_sponsor_payment
        
        # --- EXPENSES ---
        
        # Facility costs (weekly = monthly / 4)
        # Player's garage is free - it's YOUR garage!
        if is_player_camp and tier.upper() == "GARAGE":
            facility_weekly = 0
        else:
            facility_monthly = CAMP_MONTHLY_COSTS.get(tier.upper(), 5000)
            facility_weekly = facility_monthly // 4
        
        if facility_weekly > 0:
            self.deduct_expense(
                camp_id=camp_id,
                amount=facility_weekly,
                trans_type=TransactionType.FACILITY_COST,
                description=f"Weekly facility costs ({tier})",
            )
        summary.facility_costs = facility_weekly
        
        # Coach salaries
        if coach_salaries <= 0 and coach_count > 0:
            # Default coach salary
            coach_salaries = coach_count * DEFAULT_COACH_SALARY
        
        if coach_salaries > 0:
            self.deduct_expense(
                camp_id=camp_id,
                amount=coach_salaries,
                trans_type=TransactionType.COACH_SALARY,
                description=f"Coach salaries ({coach_count} coach{'es' if coach_count > 1 else ''})",
            )
            summary.coach_salaries = coach_salaries
        
        # Fighter overhead (varies by tier)
        overhead_per_fighter = get_fighter_overhead_cost(tier)
        fighter_overhead = roster_size * overhead_per_fighter
        if fighter_overhead > 0:
            self.deduct_expense(
                camp_id=camp_id,
                amount=fighter_overhead,
                trans_type=TransactionType.FIGHTER_OVERHEAD,
                description=f"Fighter overhead ({roster_size} Ãƒâ€” ${overhead_per_fighter})",
            )
            summary.fighter_overhead = fighter_overhead
        
        # --- LOAN PROCESSING ---
        
        for loan in state.active_loans:
            if loan.status != LoanStatus.ACTIVE:
                continue
            
            # Apply weekly interest
            interest = loan.apply_weekly_interest()
            if interest > 0:
                summary.loan_interest += interest
            
            # Auto-pay minimum if we can afford it
            if state.balance >= loan.min_weekly_payment:
                payment = loan.min_weekly_payment
                principal, interest_paid = loan.make_payment(payment)
                
                self.deduct_expense(
                    camp_id=camp_id,
                    amount=payment,
                    trans_type=TransactionType.LOAN_PAYMENT,
                    description=f"Loan payment (${principal:,} principal, ${interest_paid:,} interest)",
                )
                summary.loan_payments += payment
                
                if loan.is_paid_off:
                    summary.warnings.append(f"Ã¢Å“â€œ Loan paid off!")
                    state.loan_history.append(loan)
            else:
                # Can't make payment
                loan.weeks_since_payment += 1
                summary.warnings.append(
                    f"Ã¢Å¡Â  Couldn't make loan payment (need ${loan.min_weekly_payment:,})"
                )
        
        # Remove paid off loans from active
        state.active_loans = [
            loan for loan in state.active_loans 
            if loan.status == LoanStatus.ACTIVE
        ]
        
        # --- CALCULATE TOTALS ---
        
        summary.total_debt = state.total_debt
        summary.min_payment_due = sum(
            loan.min_weekly_payment for loan in state.active_loans
        )
        
        summary.calculate_totals()
        
        # --- BANKRUPTCY TRACKING ---
        
        if summary.closing_balance < 0:
            state.weeks_in_debt += 1
            summary.weeks_in_debt = state.weeks_in_debt
            
            if state.weeks_in_debt >= 3:
                summary.warnings.append(f"Ã¢Å¡Â  In debt for {state.weeks_in_debt} weeks!")
            
            if state.weeks_in_debt >= BANKRUPTCY_WEEKS_THRESHOLD:
                summary.bankruptcy_warning = True
                summary.warnings.append("Ã°Å¸â€™â‚¬ BANKRUPTCY WARNING: Consider taking a loan or cutting costs!")
        else:
            state.weeks_in_debt = 0
        
        return summary
    
    # -------------------------------------------------------------------------
    # Loan Management
    # -------------------------------------------------------------------------
    
    def get_available_loan(self, camp_id: str, tier: str) -> Dict[str, Any]:
        """Get available loan options for a camp."""
        config = LOAN_CONFIG.get(tier.upper(), LOAN_CONFIG["GARAGE"])
        state = self.get_camp_finances(camp_id)
        
        # Check if already has active loan
        has_active_loan = len(state.active_loans) > 0
        
        return {
            "max_loan": config["max_loan"],
            "interest_rate": config["interest_rate"],
            "min_payment_pct": config["min_payment_pct"],
            "can_take_loan": not has_active_loan,
            "has_active_loan": has_active_loan,
            "current_debt": state.total_debt,
        }
    
    def take_loan(
        self, 
        camp_id: str, 
        amount: int, 
        tier: str,
        is_emergency: bool = False,
    ) -> Optional[Loan]:
        """
        Take out a loan for a camp.
        
        Args:
            camp_id: Camp taking the loan
            amount: Loan amount
            tier: Camp tier
            is_emergency: Whether this is an emergency loan (higher interest)
            
        Returns:
            Loan object if successful, None if denied
        """
        state = self.get_camp_finances(camp_id)
        config = LOAN_CONFIG.get(tier.upper(), LOAN_CONFIG["GARAGE"])
        
        # Check if can take loan
        if len(state.active_loans) > 0 and not is_emergency:
            return None  # Already has a loan
        
        # Cap amount
        max_loan = config["max_loan"]
        if is_emergency:
            max_loan = int(max_loan * 0.5)  # Emergency loans are smaller
        amount = min(amount, max_loan)
        
        # Determine interest rate
        interest_rate = EMERGENCY_LOAN_INTEREST if is_emergency else config["interest_rate"]
        
        # Create loan
        loan = Loan(
            loan_id=str(uuid.uuid4())[:8],
            camp_id=camp_id,
            principal=amount,
            current_balance=amount,
            interest_rate=interest_rate,
            min_payment_pct=config["min_payment_pct"],
            date_taken=self._current_date,
            week_taken=self._current_week,
            is_emergency=is_emergency,
        )
        
        state.active_loans.append(loan)
        
        # Add funds
        self.add_income(
            camp_id=camp_id,
            amount=amount,
            trans_type=TransactionType.LOAN_RECEIVED,
            description=f"{'Emergency ' if is_emergency else ''}Loan received",
        )
        
        # Reset debt counter if balance is now positive
        if state.balance >= 0:
            state.weeks_in_debt = 0
        
        self._total_loans_issued += 1
        
        return loan
    
    def pay_off_loan(self, camp_id: str, loan_id: str, amount: int) -> Tuple[bool, str]:
        """
        Make a payment on a specific loan.
        
        Returns: (success, message)
        """
        state = self.get_camp_finances(camp_id)
        
        # Find the loan
        loan = None
        for l in state.active_loans:
            if l.loan_id == loan_id:
                loan = l
                break
        
        if not loan:
            return (False, "Loan not found")
        
        if state.balance < amount:
            return (False, f"Insufficient funds (have ${state.balance:,})")
        
        principal, interest = loan.make_payment(amount)
        
        self.deduct_expense(
            camp_id=camp_id,
            amount=amount,
            trans_type=TransactionType.LOAN_PAYMENT,
            description=f"Extra loan payment (${principal:,} principal, ${interest:,} interest)",
        )
        
        if loan.is_paid_off:
            state.loan_history.append(loan)
            state.active_loans = [l for l in state.active_loans if l.loan_id != loan_id]
            return (True, "Loan paid off!")
        
        return (True, f"Payment made. Remaining: ${loan.current_balance:,}")
    
    # -------------------------------------------------------------------------
    # Financial Pressure System
    # -------------------------------------------------------------------------
    
    def check_financial_pressure(
        self,
        camp_id: str,
        tier: str,
        fighter_ids: List[str] = None,
        coach_ids: List[str] = None,
    ) -> FinancialPressureResult:
        """
        Check financial pressure status and determine required actions.
        
        Stages:
        - HEALTHY: Balance >= 0
        - WARNING (1-2 weeks): Alert player
        - EMERGENCY_LOAN (3-4 weeks): Offer emergency loan
        - COST_CUTTING (5-6 weeks): Must release fighter or fire coach
        - DOWNGRADE (7-8 weeks): Facility downgrade
        - BANKRUPTCY (10+ weeks): Game over
        """
        state = self.get_camp_finances(camp_id)
        weeks = state.weeks_in_debt
        balance = state.balance
        
        fighter_ids = fighter_ids or []
        coach_ids = coach_ids or []
        
        # HEALTHY
        if balance >= 0:
            return FinancialPressureResult(
                stage=FinancialPressureStage.HEALTHY,
                weeks_in_debt=0,
                balance=balance,
            )
        
        # WARNING (1-2 weeks)
        if weeks <= 2:
            return FinancialPressureResult(
                stage=FinancialPressureStage.WARNING,
                weeks_in_debt=weeks,
                balance=balance,
                headline="Ã¢Å¡Â Ã¯Â¸Â FINANCIAL WARNING",
                description=f"Your camp has been in debt for {weeks} week(s). Win some fights or take a loan to recover.",
            )
        
        # EMERGENCY_LOAN (3-4 weeks)
        if weeks <= 4:
            # Calculate emergency loan amount
            config = LOAN_CONFIG.get(tier.upper(), LOAN_CONFIG["GARAGE"])
            max_emergency = config["max_loan"] // 2  # 50% of normal max
            loan_amount = min(max_emergency, abs(balance) + 10000)  # Cover debt + buffer
            
            return FinancialPressureResult(
                stage=FinancialPressureStage.EMERGENCY_LOAN,
                weeks_in_debt=weeks,
                balance=balance,
                headline="Ã°Å¸â€™Â° EMERGENCY LOAN AVAILABLE",
                description=f"Your camp has been struggling for {weeks} weeks. An emergency loan is available at 8% interest.",
                emergency_loan_available=True,
                emergency_loan_amount=loan_amount,
                emergency_loan_interest=EMERGENCY_LOAN_INTEREST,
            )
        
        # COST_CUTTING (5-6 weeks)
        if weeks <= 6:
            can_release = len(fighter_ids) > 1  # Must keep at least one fighter
            can_fire = len(coach_ids) > 1  # Must keep at least one coach
            
            return FinancialPressureResult(
                stage=FinancialPressureStage.COST_CUTTING,
                weeks_in_debt=weeks,
                balance=balance,
                headline="Ã°Å¸ËœÂ° COST CUTTING REQUIRED",
                description=f"Your camp is in crisis! You must release a fighter or fire a coach to reduce costs.",
                must_release_fighter=can_release,
                must_fire_coach=can_fire,
                releasable_fighters=fighter_ids[:-1] if can_release else [],  # Keep last fighter
                fireable_coaches=coach_ids[:-1] if can_fire else [],  # Keep last coach
                emergency_loan_available=True,  # Still offer emergency loan as option
                emergency_loan_amount=LOAN_CONFIG.get(tier.upper(), LOAN_CONFIG["GARAGE"])["max_loan"] // 2,
                emergency_loan_interest=EMERGENCY_LOAN_INTEREST,
            )
        
        # DOWNGRADE (7-9 weeks)
        if weeks <= 9:
            tier_order = ["GARAGE", "LOCAL", "REGIONAL", "NATIONAL", "ELITE"]
            current_idx = tier_order.index(tier.upper()) if tier.upper() in tier_order else 0
            downgrade_tier = tier_order[max(0, current_idx - 1)]
            
            if current_idx == 0:
                # Already at garage, go to bankruptcy
                return FinancialPressureResult(
                    stage=FinancialPressureStage.BANKRUPTCY,
                    weeks_in_debt=weeks,
                    balance=balance,
                    headline="Ã°Å¸â€™â‚¬ DYNASTY COLLAPSE",
                    description="Your camp has gone bankrupt at the lowest tier. Your journey ends here.",
                    is_bankrupt=True,
                )
            
            return FinancialPressureResult(
                stage=FinancialPressureStage.DOWNGRADE,
                weeks_in_debt=weeks,
                balance=balance,
                headline="Ã°Å¸â€œâ€° FACILITY DOWNGRADE",
                description=f"Your camp is being downgraded from {tier.upper()} to {downgrade_tier} to reduce costs.",
                must_downgrade=True,
                current_tier=tier.upper(),
                downgrade_tier=downgrade_tier,
            )
        
        # BANKRUPTCY (10+ weeks)
        return FinancialPressureResult(
            stage=FinancialPressureStage.BANKRUPTCY,
            weeks_in_debt=weeks,
            balance=balance,
            headline="Ã°Å¸â€™â‚¬ DYNASTY COLLAPSE",
            description="Your camp has been in debt for too long. Creditors have seized your assets. Your journey ends here.",
            is_bankrupt=True,
        )
    
    def take_emergency_loan(
        self,
        camp_id: str,
        amount: int,
        tier: str,
        week: int = None,  # Kept for backward compatibility but not used
    ) -> Tuple[bool, str, Optional[Loan]]:
        """Take an emergency loan with higher interest rate."""
        loan = self.take_loan(
            camp_id=camp_id,
            amount=amount,
            tier=tier,
            is_emergency=True,
        )
        if loan:
            return True, f"Emergency loan of ${amount:,} approved", loan
        return False, "Emergency loan denied", None
    
    def process_forced_downgrade(
        self,
        camp_id: str,
        from_tier: str,
        to_tier: str,
    ) -> bool:
        """Process a forced facility downgrade."""
        state = self.get_camp_finances(camp_id)
        
        # Record transaction
        self.add_income(
            camp_id=camp_id,
            amount=0,
            trans_type=TransactionType.OTHER,
            description=f"Facility downgraded from {from_tier} to {to_tier}",
        )
        
        # The actual tier change happens in the Camp object
        # This just records it in finances
        return True
    
    def calculate_cost_savings(
        self,
        tier: str,
        action: str,
        coach_salary: int = 0,
    ) -> int:
        """Calculate weekly savings from a cost-cutting action."""
        overhead_per_fighter = FIGHTER_OVERHEAD_BY_TIER.get(tier.upper(), 100)
        
        if action == "release_fighter":
            return overhead_per_fighter
        elif action == "fire_coach":
            return coach_salary // 4  # Weekly portion of salary
        elif action == "downgrade":
            current_cost = CAMP_MONTHLY_COSTS.get(tier.upper(), 5000) // 4
            tier_order = ["GARAGE", "LOCAL", "REGIONAL", "NATIONAL", "ELITE"]
            current_idx = tier_order.index(tier.upper()) if tier.upper() in tier_order else 0
            if current_idx > 0:
                new_tier = tier_order[current_idx - 1]
                new_cost = CAMP_MONTHLY_COSTS.get(new_tier, 5000) // 4
                return current_cost - new_cost
        
        return 0
    
    # -------------------------------------------------------------------------
    # Upgrade System
    # -------------------------------------------------------------------------
    
    def check_upgrade_eligibility(
        self,
        camp_id: str,
        target_tier: str,
        reputation: int,
        championships: int,
        roster_size: int,
    ) -> Tuple[bool, List[str]]:
        """
        Check if camp can upgrade to target tier.
        
        Returns: (eligible, list of unmet requirements)
        """
        requirement = get_upgrade_requirement(target_tier)
        if not requirement:
            return (False, ["Invalid target tier"])
        
        balance = self.get_balance(camp_id)
        
        return requirement.check_eligibility(
            balance=balance,
            reputation=reputation,
            championships=championships,
            roster_size=roster_size,
        )
    
    def process_upgrade(
        self,
        camp_id: str,
        target_tier: str,
    ) -> Tuple[bool, str]:
        """
        Process camp upgrade payment.
        
        Returns: (success, message)
        """
        requirement = get_upgrade_requirement(target_tier)
        if not requirement:
            return (False, "Invalid target tier")
        
        state = self.get_camp_finances(camp_id)
        
        if state.balance < requirement.cost:
            return (False, f"Insufficient funds (need ${requirement.cost:,})")
        
        # Deduct cost
        self.deduct_expense(
            camp_id=camp_id,
            amount=requirement.cost,
            trans_type=TransactionType.UPGRADE_COST,
            description=f"Facility upgrade to {target_tier}",
        )
        
        self._total_upgrades += 1
        
        return (True, f"Upgraded to {target_tier}!")
    
    # -------------------------------------------------------------------------
    # Additional Helper Methods (for CLI compatibility)
    # -------------------------------------------------------------------------
    
    def get_financial_summary(self, camp_id: str) -> Dict[str, Any]:
        """Get a summary of camp's financial state."""
        state = self.get_camp_finances(camp_id)
        return {
            "balance": state.balance,
            "total_debt": state.total_debt,
            "net_worth": state.net_worth,
            "total_earnings": state.total_earnings,
            "total_expenses": state.total_expenses,
            "has_active_loan": len(state.active_loans) > 0,
            "weekly_income": state.weekly_income,
            "weekly_expenses": state.weekly_expenses,
            "weeks_in_debt": state.weeks_in_debt,
            "camp_sponsor": state.camp_sponsorship.company_name if state.camp_sponsorship else None,
        }
    
    def get_loan_options(self, camp_id: str, tier: str) -> Dict[str, Any]:
        """Get available loan options for a camp."""
        state = self.get_camp_finances(camp_id)
        config = LOAN_CONFIG.get(tier.upper(), LOAN_CONFIG["GARAGE"])
        
        has_loan = len(state.active_loans) > 0
        current_debt = state.total_debt
        max_loan = config["max_loan"]
        available = max_loan - current_debt if not has_loan else 0
        
        return {
            "max_loan": max_loan,
            "available": available,
            "interest_rate": config["interest_rate"],
            "interest_rate_display": f"{config['interest_rate'] * 100:.1f}%/month",
            "min_payment_pct": config["min_payment_pct"],
            "can_take_loan": not has_loan and available > 0,
            "has_active_loan": has_loan,
            "current_debt": current_debt,
            "reason": "Already have an active loan" if has_loan else "",
        }
    
    def make_extra_loan_payment(
        self, 
        camp_id: str, 
        amount: int
    ) -> Tuple[bool, str]:
        """Make an extra payment on active loan."""
        state = self.get_camp_finances(camp_id)
        
        if not state.active_loans:
            return (False, "No active loans")
        
        if state.balance < amount:
            return (False, f"Insufficient funds (have ${state.balance:,})")
        
        loan = state.active_loans[0]  # Pay first loan
        return self.pay_off_loan(camp_id, loan.loan_id, amount)
    
    def get_recent_transactions(
        self, 
        camp_id: str, 
        count: int = 20
    ) -> List[Transaction]:
        """Get recent transactions for a camp."""
        state = self.get_camp_finances(camp_id)
        return state.transactions[-count:]
    
    def get_upgrade_info(self, current_tier: str) -> Optional[Dict[str, Any]]:
        """Get info about upgrading to next tier."""
        next_tier = get_next_tier(current_tier)
        if not next_tier:
            return None
        
        req = get_upgrade_requirement(next_tier)
        if not req:
            return None
        
        return {
            "current_tier": current_tier.upper(),
            "next_tier": next_tier,
            "cost": req.cost,
            "reputation_needed": req.reputation_needed,
            "championships_needed": req.championships_needed,
            "min_roster": req.min_roster,
        }
    
    def process_bonus(
        self,
        fighter_id: str,
        amount: int,
        bonus_type: str,
        camp_id: Optional[str] = None,
    ) -> bool:
        """Process a bonus payment for a fighter."""
        # Find camp from fighter sponsorship or use provided camp_id
        if camp_id is None:
            sponsor = self.get_fighter_sponsor(fighter_id)
            if sponsor:
                # We need to find the camp - this is a limitation
                # For now, we'll need to pass camp_id explicitly
                return False
            return False
        
        self.add_income(
            camp_id=camp_id,
            amount=amount,
            trans_type=TransactionType.PERFORMANCE_BONUS,
            description=f"{bonus_type} bonus",
            fighter_id=fighter_id,
        )
        return True
    
    def offer_camp_sponsorship(
        self,
        camp_id: str,
        tier: str,
    ) -> Optional[CampSponsorship]:
        """Generate and potentially assign a camp sponsorship offer."""
        offer = generate_camp_sponsorship_offer(tier, camp_id)
        return offer
    
    def accept_camp_sponsorship(
        self,
        camp_id: str,
        sponsor: CampSponsorship,
    ) -> bool:
        """Accept a camp sponsorship deal."""
        state = self.get_camp_finances(camp_id)
        sponsor.camp_id = camp_id
        sponsor.is_active = True
        state.camp_sponsorship = sponsor
        return True
    
    def get_sponsorship_offers_for_fighter(
        self,
        fighter_id: str,
        rank: Optional[int] = None,
        is_champion: bool = False,
        marketability: int = 50,
        wins: int = 0,
    ) -> List[Sponsorship]:
        """Get potential sponsorship offers for a fighter."""
        offers = []
        
        # Generate 1-3 offers based on status
        num_offers = 1
        if is_champion:
            num_offers = 3
        elif rank is not None and rank <= 5:
            num_offers = 3
        elif rank is not None and rank <= 15:
            num_offers = 2
        
        for _ in range(num_offers):
            offer = generate_sponsorship_offer(
                rank=rank,
                is_champion=is_champion,
                marketability=marketability,
                wins=wins,
                fighter_id=fighter_id,
                offer_chance=0.9,  # High chance since we're explicitly requesting
            )
            if offer and offer.company_name not in [o.company_name for o in offers]:
                offers.append(offer)
        
        return offers
    
    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize manager state."""
        return {
            "camp_finances": {
                camp_id: state.to_dict() 
                for camp_id, state in self._camp_finances.items()
            },
            "fighter_sponsorships": {
                fighter_id: sponsor.to_dict()
                for fighter_id, sponsor in self._fighter_sponsorships.items()
            },
            "total_purses_paid": self._total_purses_paid,
            "total_loans_issued": self._total_loans_issued,
            "total_upgrades": self._total_upgrades,
            "current_week": self._current_week,
            "current_date": self._current_date,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EconomyManager":
        """Deserialize manager state."""
        manager = cls()
        
        # Restore camp finances
        for camp_id, state_data in data.get("camp_finances", {}).items():
            manager._camp_finances[camp_id] = CampFinanceState.from_dict(state_data)
        
        # Restore fighter sponsorships
        for fighter_id, sponsor_data in data.get("fighter_sponsorships", {}).items():
            manager._fighter_sponsorships[fighter_id] = Sponsorship.from_dict(sponsor_data)
        
        # Restore stats
        manager._total_purses_paid = data.get("total_purses_paid", 0)
        manager._total_loans_issued = data.get("total_loans_issued", 0)
        manager._total_upgrades = data.get("total_upgrades", 0)
        manager._current_week = data.get("current_week", 0)
        manager._current_date = data.get("current_date", "")
        
        return manager


# ============================================================================
# GLOBAL MANAGER
# ============================================================================

_economy_manager: Optional[EconomyManager] = None


def get_economy_manager() -> EconomyManager:
    """Get the global economy manager instance."""
    global _economy_manager
    if _economy_manager is None:
        _economy_manager = EconomyManager()
    return _economy_manager


def create_economy_manager() -> EconomyManager:
    """Create a new economy manager instance."""
    return EconomyManager()


def reset_economy_manager() -> None:
    """Reset the global economy manager."""
    global _economy_manager
    _economy_manager = EconomyManager()


def initialize_camp_finances(
    camp_id: str,
    tier: str = "GARAGE",
    is_player: bool = False,
    manager: Optional[EconomyManager] = None,
) -> CampFinanceState:
    """
    Initialize finances for a new camp.
    
    Args:
        camp_id: Camp ID
        tier: Starting tier
        is_player: Whether this is the player's camp
        manager: Economy manager (uses global if None)
        
    Returns:
        Initialized CampFinanceState
    """
    if manager is None:
        manager = get_economy_manager()
    
    starting_funds = STARTING_FUNDS.get(tier.upper(), 50000)
    if not is_player:
        starting_funds = int(starting_funds * 1.5)  # AI camps get more
    
    manager.set_camp_balance(camp_id, starting_funds)
    return manager.get_camp_finances(camp_id)


# ============================================================================
# CONVENIENCE EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "TransactionType",
    "LoanStatus", 
    "SponsorTier",
    
    # Data classes
    "Transaction",
    "Loan",
    "Sponsorship",
    "CampSponsorship",
    "UpgradeRequirement",
    "CampFinanceState",
    "FightEarnings",
    "WeeklyFinanceSummary",
    
    # Manager
    "EconomyManager",
    
    # Factory functions
    "get_economy_manager",
    "create_economy_manager",
    "reset_economy_manager",
    "initialize_camp_finances",
    
    # Helper functions
    "format_money",
    "calculate_base_purse",
    "calculate_main_event_bonus",
    "get_purse_tier",
    "get_upgrade_requirement",
    "get_next_tier",
    "get_fighter_overhead_cost",
    "generate_sponsorship_offer",
    "generate_camp_sponsorship_offer",
    "determine_sponsor_tier",
    
    # Constants
    "BASE_PURSE_BY_TIER",
    "CAMP_MONTHLY_COSTS",
    "FIGHTER_OVERHEAD_BY_TIER",
    "LOAN_CONFIG",
    "UPGRADE_REQUIREMENTS",
    "PERFORMANCE_BONUSES",
    "SPONSORSHIP_COMPANIES",
    "CAMP_SPONSORS",
    "MAIN_EVENT_BONUS",
    "MAIN_EVENT_TITLE_BONUS",
    "CO_MAIN_EVENT_BONUS",
]
