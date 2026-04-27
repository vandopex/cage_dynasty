# systems/negotiation.py
# Module: Contract Negotiation System
# Lines: ~850
#
# Handles fighter contract demands, negotiation, and AI camp bidding.

"""
Cage Dynasty - Contract Negotiation System

This module handles the business side of signing fighters:
- Fighter demand calculation based on rating, age, potential, market
- Contract offer creation and evaluation
- AI camp interest and bidding wars
- Acceptance probability calculation
- Loyalty factors (nationality, region, facilities)

USAGE:
    from systems.negotiation import (
        NegotiationSystem,
        ContractOffer,
        FighterDemands,
        BiddingWar,
        calculate_fighter_demands,
        evaluate_offer,
    )
    
    # Get what a fighter wants
    demands = calculate_fighter_demands(fighter_data, market_heat)
    
    # Create an offer
    offer = ContractOffer(signing_bonus=20000, ...)
    
    # Check acceptance probability
    probability = evaluate_offer(offer, demands, camp_data, fighter_data)
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random
import uuid


# ============================================================================
# CONSTANTS
# ============================================================================

# Base contract values by overall rating tier
BASE_DEMANDS = {
    # (min_rating, max_rating): (signing_bonus, base_purse, win_bonus)
    (0, 54): (5_000, 8_000, 4_000),
    (55, 64): (10_000, 12_000, 6_000),
    (65, 69): (20_000, 15_000, 8_000),
    (70, 74): (35_000, 20_000, 10_000),
    (75, 79): (60_000, 30_000, 15_000),
    (80, 84): (100_000, 50_000, 25_000),
    (85, 89): (200_000, 80_000, 40_000),
    (90, 99): (500_000, 150_000, 75_000),
}

# Camp tier budgets (approximate total they'll spend on a signing)
CAMP_BUDGETS = {
    "GARAGE": 30_000,
    "LOCAL": 75_000,
    "REGIONAL": 150_000,
    "NATIONAL": 400_000,
    "ELITE": 1_000_000,
}

# Camp tier attractiveness bonus (fighters prefer better facilities)
CAMP_TIER_BONUS = {
    "GARAGE": -20,
    "LOCAL": -10,
    "REGIONAL": 0,
    "NATIONAL": 10,
    "ELITE": 20,
}

# Nationality/region bonuses
SAME_NATIONALITY_BONUS = 15  # Same country
SAME_REGION_BONUS = 8  # Same continent/region

# Region mappings for fighters
NATIONALITY_REGIONS = {
    # Americas
    "United States": "Americas", "USA": "Americas", "Brazil": "Americas",
    "Mexico": "Americas", "Canada": "Americas", "Argentina": "Americas",
    "Colombia": "Americas", "Peru": "Americas", "Chile": "Americas",
    "Venezuela": "Americas", "Ecuador": "Americas",
    # Europe
    "Russia": "Europe", "United Kingdom": "Europe", "UK": "Europe",
    "Ireland": "Europe", "Poland": "Europe", "France": "Europe",
    "Germany": "Europe", "Netherlands": "Europe", "Sweden": "Europe",
    "Italy": "Europe", "Spain": "Europe", "Ukraine": "Europe",
    "Georgia": "Europe", "Croatia": "Europe", "Serbia": "Europe",
    # Asia
    "China": "Asia", "Japan": "Asia", "South Korea": "Asia",
    "Philippines": "Asia", "Indonesia": "Asia", "Thailand": "Asia",
    "Kazakhstan": "Asia", "Uzbekistan": "Asia", "Kyrgyzstan": "Asia",
    "India": "Asia", "Mongolia": "Asia",
    # Pacific
    "Australia": "Pacific", "New Zealand": "Pacific",
    # Africa/Middle East
    "Nigeria": "Africa", "South Africa": "Africa", "Cameroon": "Africa",
    "Egypt": "Africa", "Morocco": "Africa", "Israel": "Middle East",
}

# Fighter personality types affecting negotiation
class NegotiationStyle(Enum):
    LOYAL = "loyal"           # Values relationships, takes less money
    MERCENARY = "mercenary"   # All about the money
    AMBITIOUS = "ambitious"   # Wants best facilities/coaching
    HOMEBODY = "homebody"     # Strong regional preference
    BALANCED = "balanced"     # Normal negotiator


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FighterDemands:
    """What a fighter wants in a contract."""
    fighter_id: str
    fighter_name: str
    
    # Financial demands (ranges)
    signing_bonus_min: int
    signing_bonus_max: int
    base_purse_min: int
    base_purse_max: int
    win_bonus_min: int
    win_bonus_max: int
    
    # Contract length preferences
    min_fights: int = 3
    max_fights: int = 6
    preferred_fights: int = 4
    
    # What they ideally want (middle of range)
    ideal_signing_bonus: int = 0
    ideal_base_purse: int = 0
    ideal_win_bonus: int = 0
    
    # Market factors
    market_heat: float = 1.0  # Multiplier from AI interest
    negotiation_style: NegotiationStyle = NegotiationStyle.BALANCED
    
    # Loyalty factors
    nationality: str = ""
    preferred_region: str = ""
    
    def __post_init__(self):
        """Calculate ideals as midpoint of ranges."""
        if self.ideal_signing_bonus == 0:
            self.ideal_signing_bonus = (self.signing_bonus_min + self.signing_bonus_max) // 2
        if self.ideal_base_purse == 0:
            self.ideal_base_purse = (self.base_purse_min + self.base_purse_max) // 2
        if self.ideal_win_bonus == 0:
            self.ideal_win_bonus = (self.win_bonus_min + self.win_bonus_max) // 2
    
    @property
    def total_value_min(self) -> int:
        """Minimum total contract value (all fights, all wins)."""
        return self.signing_bonus_min + (self.base_purse_min + self.win_bonus_min) * self.min_fights
    
    @property
    def total_value_max(self) -> int:
        """Maximum total contract value (all fights, all wins)."""
        return self.signing_bonus_max + (self.base_purse_max + self.win_bonus_max) * self.max_fights
    
    @property
    def total_value_ideal(self) -> int:
        """Ideal total contract value."""
        return self.ideal_signing_bonus + (self.ideal_base_purse + self.ideal_win_bonus) * self.preferred_fights


@dataclass
class ContractOffer:
    """A contract offer from a camp to a fighter."""
    offer_id: str = ""
    camp_id: str = ""
    camp_name: str = ""
    camp_tier: str = "LOCAL"
    
    # Financial terms
    signing_bonus: int = 0
    base_purse: int = 0
    win_bonus: int = 0
    
    # Contract length
    num_fights: int = 4
    
    # Calculated
    total_value: int = 0
    
    # Camp info for evaluation
    camp_nationality: str = ""
    camp_region: str = ""
    has_matching_coach: bool = False
    development_reputation: int = 50  # 0-100
    
    def __post_init__(self):
        if not self.offer_id:
            self.offer_id = str(uuid.uuid4())[:8]
        self.calculate_total()
    
    def calculate_total(self) -> int:
        """Calculate total contract value assuming all wins."""
        self.total_value = self.signing_bonus + (self.base_purse + self.win_bonus) * self.num_fights
        return self.total_value


@dataclass
class OfferEvaluation:
    """Result of evaluating an offer against demands."""
    acceptance_probability: int  # 0-100
    
    # Breakdown factors
    financial_score: int = 0      # How offer compares to demands
    facilities_score: int = 0     # Camp tier bonus
    loyalty_score: int = 0        # Nationality/region bonus
    coaching_score: int = 0       # Matching coach style
    reputation_score: int = 0     # Camp's development reputation
    
    # Comparison to other offers
    is_best_offer: bool = True
    competing_offers: int = 0
    
    # Feedback
    positive_factors: List[str] = field(default_factory=list)
    negative_factors: List[str] = field(default_factory=list)
    
    @property
    def summary(self) -> str:
        """Get acceptance summary."""
        if self.acceptance_probability >= 80:
            return "Very Likely"
        elif self.acceptance_probability >= 60:
            return "Likely"
        elif self.acceptance_probability >= 40:
            return "Possible"
        elif self.acceptance_probability >= 20:
            return "Unlikely"
        else:
            return "Very Unlikely"


@dataclass
class AIBidder:
    """An AI camp interested in a fighter."""
    camp_id: str
    camp_name: str
    camp_tier: str
    budget: int
    interest_level: str  # "Strong", "Moderate", "Mild"
    likely_offer: int  # Estimated total offer
    nationality: str = ""
    region: str = ""


@dataclass
class BiddingWar:
    """A bidding war for a fighter."""
    fighter_id: str
    fighter_name: str
    demands: FighterDemands
    
    # AI bidders
    ai_bidders: List[AIBidder] = field(default_factory=list)
    
    # Market heat (increases demands)
    heat_multiplier: float = 1.0
    
    # Status
    is_resolved: bool = False
    winner_camp_id: Optional[str] = None
    winning_offer: Optional[ContractOffer] = None
    
    @property
    def num_bidders(self) -> int:
        return len(self.ai_bidders) + 1  # +1 for player
    
    @property
    def has_competition(self) -> bool:
        return len(self.ai_bidders) > 0


@dataclass 
class NegotiationResult:
    """Result of a negotiation attempt."""
    success: bool
    fighter_id: str
    fighter_name: str
    
    # If successful
    final_offer: Optional[ContractOffer] = None
    
    # If failed
    winner_camp_name: Optional[str] = None
    winner_offer_total: int = 0
    player_offer_total: int = 0
    
    # Reasons
    decision_factors: List[str] = field(default_factory=list)


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def get_negotiation_style(fighter_data: Any) -> NegotiationStyle:
    """Determine a fighter's negotiation style based on traits/personality."""
    traits = getattr(fighter_data, 'traits', []) or []
    
    # Check for specific traits that indicate style
    if "Gym Rat" in traits or "Loyal" in traits:
        return NegotiationStyle.LOYAL
    
    # Check personality if available
    personality = getattr(fighter_data, 'personality', None)
    if personality:
        mentality = getattr(personality, 'mentality', None)
        if mentality:
            mentality_val = mentality.value if hasattr(mentality, 'value') else str(mentality)
            if mentality_val == "businessman":
                return NegotiationStyle.MERCENARY
            elif mentality_val == "glory_seeker":
                return NegotiationStyle.AMBITIOUS
    
    # Random assignment weighted toward balanced
    roll = random.random()
    if roll < 0.15:
        return NegotiationStyle.LOYAL
    elif roll < 0.30:
        return NegotiationStyle.MERCENARY
    elif roll < 0.45:
        return NegotiationStyle.AMBITIOUS
    elif roll < 0.55:
        return NegotiationStyle.HOMEBODY
    else:
        return NegotiationStyle.BALANCED


def calculate_fighter_demands(
    fighter_data: Any,
    market_heat: float = 1.0,
    num_interested_camps: int = 0,
) -> FighterDemands:
    """
    Calculate what a fighter demands in contract negotiations.
    
    Args:
        fighter_data: Fighter's data object
        market_heat: Multiplier from market conditions (1.0 = normal)
        num_interested_camps: Number of AI camps interested (increases demands)
    
    Returns:
        FighterDemands with ranges for all terms
    """
    fighter_id = getattr(fighter_data, 'fighter_id', 'unknown')
    name = getattr(fighter_data, 'name', 'Unknown')
    overall = getattr(fighter_data, 'overall_rating', 60)
    age = getattr(fighter_data, 'age', 25)
    wins = getattr(fighter_data, 'wins', 0)
    losses = getattr(fighter_data, 'losses', 0)
    is_champion = getattr(fighter_data, 'is_champion', False)
    nationality = getattr(fighter_data, 'nationality', getattr(fighter_data, 'country', 'Unknown'))
    
    # Get win/lose streaks if available
    win_streak = getattr(fighter_data, 'win_streak', 0)
    lose_streak = getattr(fighter_data, 'lose_streak', 0)
    
    # Get potential if available
    potential_ceiling = getattr(fighter_data, 'potential_ceiling', overall + 5)
    
    # Find base demands for this rating tier
    base_signing = 10_000
    base_purse = 12_000
    base_win = 6_000
    
    for (min_r, max_r), (sign, purse, win) in BASE_DEMANDS.items():
        if min_r <= overall <= max_r:
            base_signing = sign
            base_purse = purse
            base_win = win
            break
    
    # === MODIFIERS ===
    
    # Age modifier (younger = more value, demands more)
    if age <= 23:
        age_mod = 1.15  # Young prospects command premium
    elif age <= 26:
        age_mod = 1.1
    elif age <= 29:
        age_mod = 1.0
    elif age <= 32:
        age_mod = 0.9
    else:
        age_mod = 0.75  # Older fighters take less
    
    # Win streak modifier
    streak_mod = 1.0
    if win_streak >= 5:
        streak_mod = 1.3
    elif win_streak >= 3:
        streak_mod = 1.15
    elif lose_streak >= 3:
        streak_mod = 0.8
    elif lose_streak >= 2:
        streak_mod = 0.9
    
    # Champion modifier
    champ_mod = 1.5 if is_champion else 1.0
    
    # Potential modifier (high ceiling = higher demands)
    potential_mod = 1.0
    if potential_ceiling >= 90:
        potential_mod = 1.25
    elif potential_ceiling >= 85:
        potential_mod = 1.15
    elif potential_ceiling >= 80:
        potential_mod = 1.1
    
    # Competition modifier (more interested camps = higher demands)
    competition_mod = 1.0 + (num_interested_camps * 0.1)  # +10% per interested camp
    competition_mod = min(1.5, competition_mod)  # Cap at 50% increase
    
    # Apply all modifiers
    total_mod = age_mod * streak_mod * champ_mod * potential_mod * competition_mod * market_heat
    
    # Calculate final demands with ranges (±20% from base * mods)
    signing_base = int(base_signing * total_mod)
    purse_base = int(base_purse * total_mod)
    win_base = int(base_win * total_mod)
    
    # Ranges
    signing_min = int(signing_base * 0.8)
    signing_max = int(signing_base * 1.2)
    purse_min = int(purse_base * 0.85)
    purse_max = int(purse_base * 1.15)
    win_min = int(win_base * 0.85)
    win_max = int(win_base * 1.15)
    
    # Contract length preferences based on age/situation
    if age <= 24:
        min_fights, max_fights, pref = 3, 5, 4  # Shorter to re-negotiate as they grow
    elif age >= 32:
        min_fights, max_fights, pref = 2, 4, 3  # Shorter near retirement
    elif is_champion:
        min_fights, max_fights, pref = 3, 6, 4
    else:
        min_fights, max_fights, pref = 3, 6, 4
    
    # Get negotiation style
    neg_style = get_negotiation_style(fighter_data)
    
    # Get region
    region = NATIONALITY_REGIONS.get(nationality, "Unknown")
    
    return FighterDemands(
        fighter_id=fighter_id,
        fighter_name=name,
        signing_bonus_min=signing_min,
        signing_bonus_max=signing_max,
        base_purse_min=purse_min,
        base_purse_max=purse_max,
        win_bonus_min=win_min,
        win_bonus_max=win_max,
        min_fights=min_fights,
        max_fights=max_fights,
        preferred_fights=pref,
        market_heat=market_heat * competition_mod,
        negotiation_style=neg_style,
        nationality=nationality,
        preferred_region=region,
    )


def generate_ai_interest(
    fighter_data: Any,
    all_camps: List[Any],
    player_camp_id: str,
) -> List[AIBidder]:
    """
    Generate AI camp interest in a fighter.
    
    Args:
        fighter_data: Fighter being signed
        all_camps: List of all camps in game
        player_camp_id: Player's camp ID (excluded)
    
    Returns:
        List of AIBidder objects for interested camps
    """
    overall = getattr(fighter_data, 'overall_rating', 60)
    weight_class = getattr(fighter_data, 'weight_class', 'Lightweight')
    nationality = getattr(fighter_data, 'nationality', getattr(fighter_data, 'country', 'Unknown'))
    fighter_region = NATIONALITY_REGIONS.get(nationality, "Unknown")
    
    interested = []
    
    for camp in all_camps:
        camp_id = getattr(camp, 'camp_id', '')
        if camp_id == player_camp_id:
            continue
        
        # Skip player camps
        if getattr(camp, 'is_player', False):
            continue
        
        camp_tier = getattr(camp, 'tier', 'LOCAL')
        camp_name = getattr(camp, 'name', 'Unknown Camp')
        budget = CAMP_BUDGETS.get(camp_tier, 50_000)
        
        # Base interest chance based on fighter quality vs camp tier
        tier_quality_match = {
            "GARAGE": (45, 65),
            "LOCAL": (50, 72),
            "REGIONAL": (60, 80),
            "NATIONAL": (70, 88),
            "ELITE": (78, 99),
        }
        
        min_qual, max_qual = tier_quality_match.get(camp_tier, (50, 75))
        
        # Interest if fighter fits camp's range
        if min_qual <= overall <= max_qual:
            interest_chance = 0.3  # 30% base
        elif overall < min_qual:
            interest_chance = 0.1  # Below their standards
        else:
            interest_chance = 0.15  # Above their budget probably
        
        # Nationality bonus
        camp_nationality = getattr(camp, 'nationality', 'Unknown')
        camp_region = NATIONALITY_REGIONS.get(camp_nationality, "Unknown")
        if camp_nationality == nationality:
            interest_chance += 0.2
        elif camp_region == fighter_region:
            interest_chance += 0.1
        
        # Random roll
        if random.random() < interest_chance:
            # Determine interest level
            if random.random() < 0.3:
                level = "Strong"
                offer_mult = 1.1
            elif random.random() < 0.6:
                level = "Moderate"
                offer_mult = 1.0
            else:
                level = "Mild"
                offer_mult = 0.9
            
            # Estimate what they'd offer
            base_offer = min(budget * 0.8, overall * 1500 * offer_mult)
            
            interested.append(AIBidder(
                camp_id=camp_id,
                camp_name=camp_name,
                camp_tier=camp_tier,
                budget=budget,
                interest_level=level,
                likely_offer=int(base_offer),
                nationality=camp_nationality,
                region=camp_region,
            ))
    
    # Sort by likely offer (highest first)
    interested.sort(key=lambda b: b.likely_offer, reverse=True)
    
    # Limit to top 3 interested
    return interested[:3]


def evaluate_offer(
    offer: ContractOffer,
    demands: FighterDemands,
    fighter_data: Any,
    competing_offers: List[ContractOffer] = None,
) -> OfferEvaluation:
    """
    Evaluate a contract offer and calculate acceptance probability.
    
    Args:
        offer: The offer being evaluated
        demands: Fighter's demands
        fighter_data: Fighter data for loyalty checks
        competing_offers: Other offers the fighter has
    
    Returns:
        OfferEvaluation with probability and breakdown
    """
    competing_offers = competing_offers or []
    
    positives = []
    negatives = []
    
    # === FINANCIAL SCORE (0-50 points) ===
    # Compare offer to demands
    
    # Signing bonus
    if offer.signing_bonus >= demands.ideal_signing_bonus:
        sign_score = 15
        if offer.signing_bonus >= demands.signing_bonus_max:
            positives.append("Excellent signing bonus")
    elif offer.signing_bonus >= demands.signing_bonus_min:
        sign_score = 10
    else:
        shortfall = (demands.signing_bonus_min - offer.signing_bonus) / demands.signing_bonus_min
        sign_score = max(0, 10 - int(shortfall * 20))
        negatives.append("Signing bonus below expectations")
    
    # Base purse
    if offer.base_purse >= demands.ideal_base_purse:
        purse_score = 15
        if offer.base_purse >= demands.base_purse_max:
            positives.append("Strong per-fight purse")
    elif offer.base_purse >= demands.base_purse_min:
        purse_score = 10
    else:
        shortfall = (demands.base_purse_min - offer.base_purse) / demands.base_purse_min
        purse_score = max(0, 10 - int(shortfall * 20))
        negatives.append("Base purse too low")
    
    # Win bonus
    if offer.win_bonus >= demands.ideal_win_bonus:
        win_score = 10
    elif offer.win_bonus >= demands.win_bonus_min:
        win_score = 7
    else:
        win_score = 3
        negatives.append("Win bonus underwhelming")
    
    # Contract length
    length_score = 10
    if offer.num_fights < demands.min_fights:
        length_score = 5
        negatives.append("Contract too short")
    elif offer.num_fights > demands.max_fights:
        length_score = 5
        negatives.append("Contract too long")
    elif offer.num_fights == demands.preferred_fights:
        positives.append("Ideal contract length")
    
    financial_score = sign_score + purse_score + win_score + length_score
    
    # === FACILITIES SCORE (0-20 points) ===
    tier_bonus = CAMP_TIER_BONUS.get(offer.camp_tier, 0)
    facilities_score = 10 + tier_bonus  # Base 10 ± tier adjustment
    facilities_score = max(0, min(20, facilities_score))
    
    if tier_bonus >= 10:
        positives.append(f"Elite training facilities ({offer.camp_tier})")
    elif tier_bonus <= -10:
        negatives.append(f"Limited facilities ({offer.camp_tier})")
    
    # Ambitious fighters care more about facilities
    if demands.negotiation_style == NegotiationStyle.AMBITIOUS:
        facilities_score = int(facilities_score * 1.5)
    
    # === LOYALTY SCORE (0-20 points) ===
    loyalty_score = 0
    fighter_nationality = demands.nationality
    fighter_region = demands.preferred_region
    
    if offer.camp_nationality and offer.camp_nationality == fighter_nationality:
        loyalty_score += SAME_NATIONALITY_BONUS
        positives.append(f"Same nationality ({fighter_nationality})")
    elif offer.camp_region and offer.camp_region == fighter_region:
        loyalty_score += SAME_REGION_BONUS
        positives.append(f"Same region ({fighter_region})")
    
    # Homebody fighters care more about location
    if demands.negotiation_style == NegotiationStyle.HOMEBODY:
        loyalty_score = int(loyalty_score * 1.5)
    
    # === COACHING SCORE (0-10 points) ===
    coaching_score = 5  # Base
    if offer.has_matching_coach:
        coaching_score = 10
        positives.append("Has coach matching fighter's style")
    
    # === REPUTATION SCORE (0-10 points) ===
    reputation_score = offer.development_reputation // 10
    if offer.development_reputation >= 80:
        positives.append("Excellent development reputation")
    elif offer.development_reputation <= 30:
        negatives.append("Poor development track record")
    
    # === NEGOTIATION STYLE ADJUSTMENTS ===
    style = demands.negotiation_style
    
    if style == NegotiationStyle.LOYAL:
        # Loyal fighters are easier to sign, less money focused
        financial_score = int(financial_score * 0.8)
        loyalty_score = int(loyalty_score * 1.3)
    elif style == NegotiationStyle.MERCENARY:
        # Mercenaries only care about money
        financial_score = int(financial_score * 1.3)
        loyalty_score = int(loyalty_score * 0.5)
        facilities_score = int(facilities_score * 0.7)
    elif style == NegotiationStyle.AMBITIOUS:
        # Ambitious want best facilities
        facilities_score = int(facilities_score * 1.3)
    
    # === COMPETITION CHECK ===
    is_best = True
    if competing_offers:
        best_competing = max(o.total_value for o in competing_offers)
        if offer.total_value < best_competing:
            is_best = False
            diff = best_competing - offer.total_value
            if diff > 20000:
                negatives.append(f"Other camp offering ${diff:,} more")
    
    # === CALCULATE FINAL PROBABILITY ===
    # Base from scores
    total_score = financial_score + facilities_score + loyalty_score + coaching_score + reputation_score
    
    # Normalize to percentage (max possible ~110)
    base_probability = min(95, int(total_score * 0.9))
    
    # Penalty if not best offer
    if not is_best:
        base_probability = int(base_probability * 0.6)
    
    # Market heat penalty (hot market = pickier)
    if demands.market_heat > 1.2:
        base_probability = int(base_probability * 0.9)
    
    # Floor and ceiling
    final_probability = max(5, min(95, base_probability))
    
    return OfferEvaluation(
        acceptance_probability=final_probability,
        financial_score=financial_score,
        facilities_score=facilities_score,
        loyalty_score=loyalty_score,
        coaching_score=coaching_score,
        reputation_score=reputation_score,
        is_best_offer=is_best,
        competing_offers=len(competing_offers),
        positive_factors=positives,
        negative_factors=negatives,
    )


def generate_ai_offer(bidder: AIBidder, demands: FighterDemands) -> ContractOffer:
    """Generate a concrete offer from an AI bidder."""
    # AI offers based on interest level
    if bidder.interest_level == "Strong":
        sign_mult = random.uniform(1.0, 1.15)
        purse_mult = random.uniform(1.0, 1.1)
    elif bidder.interest_level == "Moderate":
        sign_mult = random.uniform(0.9, 1.05)
        purse_mult = random.uniform(0.9, 1.0)
    else:  # Mild
        sign_mult = random.uniform(0.8, 0.95)
        purse_mult = random.uniform(0.85, 0.95)
    
    # Calculate offer within budget
    signing = int(demands.ideal_signing_bonus * sign_mult)
    purse = int(demands.ideal_base_purse * purse_mult)
    win = int(demands.ideal_win_bonus * purse_mult)
    fights = demands.preferred_fights
    
    # Check against budget
    total = signing + (purse + win) * fights
    if total > bidder.budget:
        # Scale down to fit budget
        scale = bidder.budget / total * 0.95
        signing = int(signing * scale)
        purse = int(purse * scale)
        win = int(win * scale)
    
    return ContractOffer(
        camp_id=bidder.camp_id,
        camp_name=bidder.camp_name,
        camp_tier=bidder.camp_tier,
        signing_bonus=signing,
        base_purse=purse,
        win_bonus=win,
        num_fights=fights,
        camp_nationality=bidder.nationality,
        camp_region=bidder.region,
    )


def resolve_bidding_war(
    player_offer: ContractOffer,
    bidding_war: BiddingWar,
    fighter_data: Any,
) -> NegotiationResult:
    """
    Resolve a bidding war and determine if player wins.
    
    Args:
        player_offer: Player's offer
        bidding_war: The bidding war context
        fighter_data: Fighter being signed
    
    Returns:
        NegotiationResult with outcome
    """
    demands = bidding_war.demands
    
    # Generate AI offers
    ai_offers = [generate_ai_offer(b, demands) for b in bidding_war.ai_bidders]
    
    # Evaluate all offers
    player_eval = evaluate_offer(player_offer, demands, fighter_data, ai_offers)
    
    ai_evals = []
    for ai_offer in ai_offers:
        other_offers = [player_offer] + [o for o in ai_offers if o.offer_id != ai_offer.offer_id]
        ai_eval = evaluate_offer(ai_offer, demands, fighter_data, other_offers)
        ai_evals.append((ai_offer, ai_eval))
    
    # Determine winner based on weighted random using probabilities
    all_candidates = [(player_offer, player_eval)] + ai_evals
    
    # Normalize probabilities
    total_prob = sum(e[1].acceptance_probability for e in all_candidates)
    
    # Random selection weighted by probability
    roll = random.uniform(0, total_prob)
    cumulative = 0
    winner = all_candidates[0]
    
    for offer, eval_result in all_candidates:
        cumulative += eval_result.acceptance_probability
        if roll <= cumulative:
            winner = (offer, eval_result)
            break
    
    winning_offer, winning_eval = winner
    
    # Check if player won
    if winning_offer.camp_id == player_offer.camp_id:
        return NegotiationResult(
            success=True,
            fighter_id=demands.fighter_id,
            fighter_name=demands.fighter_name,
            final_offer=player_offer,
            decision_factors=winning_eval.positive_factors,
        )
    else:
        # Find why player lost
        factors = []
        if player_offer.total_value < winning_offer.total_value:
            factors.append("Higher total compensation")
        if CAMP_TIER_BONUS.get(winning_offer.camp_tier, 0) > CAMP_TIER_BONUS.get(player_offer.camp_tier, 0):
            factors.append("Better training facilities")
        if winning_offer.camp_nationality == demands.nationality:
            factors.append("Same nationality")
        if not factors:
            factors.append("Better overall package")
        
        return NegotiationResult(
            success=False,
            fighter_id=demands.fighter_id,
            fighter_name=demands.fighter_name,
            winner_camp_name=winning_offer.camp_name,
            winner_offer_total=winning_offer.total_value,
            player_offer_total=player_offer.total_value,
            decision_factors=factors,
        )


def attempt_signing_no_competition(
    player_offer: ContractOffer,
    demands: FighterDemands,
    fighter_data: Any,
) -> NegotiationResult:
    """
    Attempt to sign a fighter with no AI competition.
    
    Args:
        player_offer: Player's offer
        demands: Fighter's demands
        fighter_data: Fighter being signed
    
    Returns:
        NegotiationResult with outcome
    """
    eval_result = evaluate_offer(player_offer, demands, fighter_data, [])
    
    # Roll against probability
    roll = random.randint(1, 100)
    success = roll <= eval_result.acceptance_probability
    
    if success:
        return NegotiationResult(
            success=True,
            fighter_id=demands.fighter_id,
            fighter_name=demands.fighter_name,
            final_offer=player_offer,
            decision_factors=eval_result.positive_factors,
        )
    else:
        return NegotiationResult(
            success=False,
            fighter_id=demands.fighter_id,
            fighter_name=demands.fighter_name,
            decision_factors=eval_result.negative_factors or ["Offer didn't meet expectations"],
        )


# ============================================================================
# NEGOTIATION SYSTEM CLASS
# ============================================================================

class NegotiationSystem:
    """
    Main negotiation system for managing contract negotiations.
    """
    
    def __init__(self):
        self.active_negotiations: Dict[str, BiddingWar] = {}
        self.completed_negotiations: List[NegotiationResult] = []
    
    def start_negotiation(
        self,
        fighter_data: Any,
        all_camps: List[Any],
        player_camp_id: str,
    ) -> BiddingWar:
        """
        Start a negotiation for a fighter.
        
        Args:
            fighter_data: Fighter to negotiate with
            all_camps: All camps for AI interest
            player_camp_id: Player's camp ID
        
        Returns:
            BiddingWar with demands and AI bidders
        """
        fighter_id = getattr(fighter_data, 'fighter_id', 'unknown')
        name = getattr(fighter_data, 'name', 'Unknown')
        
        # Generate AI interest
        ai_bidders = generate_ai_interest(fighter_data, all_camps, player_camp_id)
        
        # Calculate demands (with competition modifier)
        demands = calculate_fighter_demands(
            fighter_data,
            market_heat=1.0,
            num_interested_camps=len(ai_bidders),
        )
        
        # Calculate heat multiplier
        heat = 1.0 + (len(ai_bidders) * 0.1)
        
        bidding_war = BiddingWar(
            fighter_id=fighter_id,
            fighter_name=name,
            demands=demands,
            ai_bidders=ai_bidders,
            heat_multiplier=heat,
        )
        
        self.active_negotiations[fighter_id] = bidding_war
        return bidding_war
    
    def submit_offer(
        self,
        fighter_id: str,
        offer: ContractOffer,
        fighter_data: Any,
    ) -> NegotiationResult:
        """
        Submit an offer and resolve the negotiation.
        
        Args:
            fighter_id: Fighter being signed
            offer: Player's offer
            fighter_data: Fighter data
        
        Returns:
            NegotiationResult with outcome
        """
        bidding_war = self.active_negotiations.get(fighter_id)
        
        if not bidding_war:
            # No active negotiation, create demands on the fly
            demands = calculate_fighter_demands(fighter_data)
            result = attempt_signing_no_competition(offer, demands, fighter_data)
        elif not bidding_war.has_competition:
            # No AI competition
            result = attempt_signing_no_competition(offer, bidding_war.demands, fighter_data)
        else:
            # Bidding war
            result = resolve_bidding_war(offer, bidding_war, fighter_data)
        
        # Clean up
        if fighter_id in self.active_negotiations:
            del self.active_negotiations[fighter_id]
        
        self.completed_negotiations.append(result)
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Export system state."""
        return {
            "completed_count": len(self.completed_negotiations),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NegotiationSystem':
        """Create from saved data."""
        return cls()


# ============================================================================
# CONTRACT LIFECYCLE TRACKING
# ============================================================================

@dataclass
class ActiveContract:
    """
    Tracks an active fighter contract.
    
    This is the runtime tracking for contracts created through negotiation.
    """
    contract_id: str
    fighter_id: str
    fighter_name: str
    camp_id: str
    camp_name: str
    
    # Terms
    signing_bonus: int
    base_purse: int
    win_bonus: int
    total_fights: int
    
    # Progress
    fights_completed: int = 0
    fights_won: int = 0
    total_earnings: int = 0
    
    # Dates
    signed_week: int = 0
    
    # Status
    is_active: bool = True
    is_champion_clause: bool = False  # Auto-extends if wins title
    
    @property
    def fights_remaining(self) -> int:
        return max(0, self.total_fights - self.fights_completed)
    
    @property
    def is_expiring(self) -> bool:
        """True if 1 or fewer fights remaining."""
        return self.fights_remaining <= 1
    
    @property
    def is_expired(self) -> bool:
        return self.fights_remaining == 0
    
    @property
    def contract_value(self) -> int:
        """Total contract value (assuming all wins)."""
        return self.signing_bonus + (self.base_purse + self.win_bonus) * self.total_fights
    
    @property 
    def win_rate(self) -> float:
        """Win rate during this contract."""
        if self.fights_completed == 0:
            return 0.0
        return self.fights_won / self.fights_completed
    
    @property
    def status_str(self) -> str:
        """Status string for display."""
        if self.is_expired:
            return "EXPIRED"
        elif self.is_expiring:
            return "FINAL FIGHT"
        elif self.fights_remaining <= 2:
            return "EXPIRING SOON"
        else:
            return "ACTIVE"
    
    def record_fight(self, won: bool, purse_earned: int) -> None:
        """Record a completed fight."""
        self.fights_completed += 1
        if won:
            self.fights_won += 1
        self.total_earnings += purse_earned
    
    def extend(self, additional_fights: int) -> None:
        """Extend contract by additional fights."""
        self.total_fights += additional_fights
    
    def to_dict(self) -> Dict[str, Any]:
        """Export for saving."""
        return {
            "contract_id": self.contract_id,
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "camp_id": self.camp_id,
            "camp_name": self.camp_name,
            "signing_bonus": self.signing_bonus,
            "base_purse": self.base_purse,
            "win_bonus": self.win_bonus,
            "total_fights": self.total_fights,
            "fights_completed": self.fights_completed,
            "fights_won": self.fights_won,
            "total_earnings": self.total_earnings,
            "signed_week": self.signed_week,
            "is_active": self.is_active,
            "is_champion_clause": self.is_champion_clause,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActiveContract':
        """Create from saved data."""
        return cls(
            contract_id=data.get("contract_id", str(uuid.uuid4())[:8]),
            fighter_id=data["fighter_id"],
            fighter_name=data.get("fighter_name", "Unknown"),
            camp_id=data["camp_id"],
            camp_name=data.get("camp_name", "Unknown"),
            signing_bonus=data.get("signing_bonus", 0),
            base_purse=data.get("base_purse", 10000),
            win_bonus=data.get("win_bonus", 5000),
            total_fights=data.get("total_fights", 4),
            fights_completed=data.get("fights_completed", 0),
            fights_won=data.get("fights_won", 0),
            total_earnings=data.get("total_earnings", 0),
            signed_week=data.get("signed_week", 0),
            is_active=data.get("is_active", True),
            is_champion_clause=data.get("is_champion_clause", False),
        )


@dataclass
class ContractAlert:
    """Alert for contract-related events."""
    alert_type: str  # "expiring", "expired", "re-sign_available"
    fighter_id: str
    fighter_name: str
    contract_id: str
    message: str
    fights_remaining: int = 0
    week: int = 0


class ContractManager:
    """
    Manages all active contracts and lifecycle events.
    """
    
    def __init__(self):
        self.contracts: Dict[str, ActiveContract] = {}  # contract_id -> contract
        self.fighter_contracts: Dict[str, str] = {}  # fighter_id -> contract_id
        self.pending_alerts: List[ContractAlert] = []
        self.expired_contracts: List[ActiveContract] = []
    
    def create_contract(
        self,
        fighter_id: str,
        fighter_name: str,
        camp_id: str,
        camp_name: str,
        offer: ContractOffer,
        current_week: int,
    ) -> ActiveContract:
        """
        Create a new contract from an accepted offer.
        
        Args:
            fighter_id: Fighter's ID
            fighter_name: Fighter's name
            camp_id: Camp's ID
            camp_name: Camp's name
            offer: The accepted contract offer
            current_week: Current game week
        
        Returns:
            ActiveContract object
        """
        contract_id = str(uuid.uuid4())[:8]
        
        contract = ActiveContract(
            contract_id=contract_id,
            fighter_id=fighter_id,
            fighter_name=fighter_name,
            camp_id=camp_id,
            camp_name=camp_name,
            signing_bonus=offer.signing_bonus,
            base_purse=offer.base_purse,
            win_bonus=offer.win_bonus,
            total_fights=offer.num_fights,
            signed_week=current_week,
        )
        
        self.contracts[contract_id] = contract
        self.fighter_contracts[fighter_id] = contract_id
        
        return contract
    
    def get_fighter_contract(self, fighter_id: str) -> Optional[ActiveContract]:
        """Get a fighter's current contract."""
        contract_id = self.fighter_contracts.get(fighter_id)
        if contract_id:
            return self.contracts.get(contract_id)
        return None
    
    def record_fight(
        self,
        fighter_id: str,
        won: bool,
        purse_earned: int,
    ) -> Optional[ActiveContract]:
        """
        Record a fight for a fighter's contract.
        
        Args:
            fighter_id: Fighter who fought
            won: Whether they won
            purse_earned: Total purse earned
        
        Returns:
            Updated contract, or None if no contract
        """
        contract = self.get_fighter_contract(fighter_id)
        if not contract:
            return None
        
        contract.record_fight(won, purse_earned)
        
        # Check for expiration
        if contract.is_expired:
            self._handle_expiration(contract)
        elif contract.is_expiring:
            self._create_expiring_alert(contract)
        
        return contract
    
    def _handle_expiration(self, contract: ActiveContract) -> None:
        """Handle a contract that has expired."""
        contract.is_active = False
        self.expired_contracts.append(contract)
        
        # Remove from active tracking
        if contract.fighter_id in self.fighter_contracts:
            del self.fighter_contracts[contract.fighter_id]
        
        # Create alert
        self.pending_alerts.append(ContractAlert(
            alert_type="expired",
            fighter_id=contract.fighter_id,
            fighter_name=contract.fighter_name,
            contract_id=contract.contract_id,
            message=f"{contract.fighter_name}'s contract has expired!",
            fights_remaining=0,
        ))
    
    def _create_expiring_alert(self, contract: ActiveContract) -> None:
        """Create alert for expiring contract."""
        # Don't duplicate alerts
        for alert in self.pending_alerts:
            if alert.contract_id == contract.contract_id and alert.alert_type == "expiring":
                return
        
        self.pending_alerts.append(ContractAlert(
            alert_type="expiring",
            fighter_id=contract.fighter_id,
            fighter_name=contract.fighter_name,
            contract_id=contract.contract_id,
            message=f"{contract.fighter_name} has {contract.fights_remaining} fight(s) left on contract",
            fights_remaining=contract.fights_remaining,
        ))
    
    def release_fighter(self, fighter_id: str) -> Optional[ActiveContract]:
        """
        Release a fighter from their contract early.
        
        Args:
            fighter_id: Fighter to release
        
        Returns:
            The terminated contract, or None
        """
        contract = self.get_fighter_contract(fighter_id)
        if not contract:
            return None
        
        contract.is_active = False
        self.expired_contracts.append(contract)
        
        if fighter_id in self.fighter_contracts:
            del self.fighter_contracts[fighter_id]
        
        return contract
    
    def get_expiring_contracts(self, camp_id: str) -> List[ActiveContract]:
        """Get all expiring contracts for a camp."""
        expiring = []
        for contract in self.contracts.values():
            if contract.camp_id == camp_id and contract.is_active:
                if contract.is_expiring or contract.fights_remaining <= 2:
                    expiring.append(contract)
        return expiring
    
    def get_camp_contracts(self, camp_id: str) -> List[ActiveContract]:
        """Get all active contracts for a camp."""
        return [c for c in self.contracts.values() 
                if c.camp_id == camp_id and c.is_active]
    
    def get_alerts(self, clear: bool = True) -> List[ContractAlert]:
        """Get pending alerts, optionally clearing them."""
        alerts = self.pending_alerts.copy()
        if clear:
            self.pending_alerts = []
        return alerts
    
    def check_all_contracts(self, camp_id: str) -> List[ContractAlert]:
        """Check all contracts for a camp and generate alerts."""
        alerts = []
        for contract in self.get_camp_contracts(camp_id):
            if contract.is_expiring:
                alerts.append(ContractAlert(
                    alert_type="expiring",
                    fighter_id=contract.fighter_id,
                    fighter_name=contract.fighter_name,
                    contract_id=contract.contract_id,
                    message=f"{contract.fighter_name}: {contract.fights_remaining} fight(s) remaining",
                    fights_remaining=contract.fights_remaining,
                ))
        return alerts
    
    def to_dict(self) -> Dict[str, Any]:
        """Export for saving."""
        return {
            "contracts": {cid: c.to_dict() for cid, c in self.contracts.items()},
            "fighter_contracts": self.fighter_contracts.copy(),
            "expired_contracts": [c.to_dict() for c in self.expired_contracts],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContractManager':
        """Create from saved data."""
        manager = cls()
        
        for cid, cdata in data.get("contracts", {}).items():
            contract = ActiveContract.from_dict(cdata)
            manager.contracts[cid] = contract
        
        manager.fighter_contracts = data.get("fighter_contracts", {}).copy()
        
        for cdata in data.get("expired_contracts", []):
            manager.expired_contracts.append(ActiveContract.from_dict(cdata))
        
        return manager


# ============================================================================
# RE-SIGNING CALCULATIONS
# ============================================================================

def calculate_resigning_demands(
    fighter_data: Any,
    current_contract: ActiveContract,
    market_heat: float = 1.0,
) -> FighterDemands:
    """
    Calculate demands for a contract renewal.
    
    Re-signing demands are based on:
    - Current contract terms
    - Fighter's performance during contract
    - Rating changes
    - Market conditions
    
    Args:
        fighter_data: Current fighter data
        current_contract: The expiring contract
        market_heat: Market multiplier
    
    Returns:
        FighterDemands for re-signing
    """
    # Start with base demands
    base_demands = calculate_fighter_demands(fighter_data, market_heat, 0)
    
    # Adjustment based on performance
    win_rate = current_contract.win_rate
    
    # Winners want more, losers accept less
    if win_rate >= 0.75:
        performance_mult = 1.25  # Dominated, wants raise
    elif win_rate >= 0.5:
        performance_mult = 1.1  # Winning record
    elif win_rate >= 0.25:
        performance_mult = 0.9  # Losing record
    else:
        performance_mult = 0.75  # Poor performance
    
    # Compare to old contract
    old_per_fight = current_contract.base_purse + current_contract.win_bonus
    new_per_fight = base_demands.ideal_base_purse + base_demands.ideal_win_bonus
    
    # Fighters expect at least what they were making
    if new_per_fight < old_per_fight:
        # Bump up to at least match old contract
        ratio = old_per_fight / new_per_fight if new_per_fight > 0 else 1.2
        base_demands.signing_bonus_min = int(base_demands.signing_bonus_min * ratio)
        base_demands.signing_bonus_max = int(base_demands.signing_bonus_max * ratio)
        base_demands.base_purse_min = int(base_demands.base_purse_min * ratio)
        base_demands.base_purse_max = int(base_demands.base_purse_max * ratio)
        base_demands.win_bonus_min = int(base_demands.win_bonus_min * ratio)
        base_demands.win_bonus_max = int(base_demands.win_bonus_max * ratio)
    
    # Apply performance multiplier
    base_demands.signing_bonus_min = int(base_demands.signing_bonus_min * performance_mult)
    base_demands.signing_bonus_max = int(base_demands.signing_bonus_max * performance_mult)
    base_demands.ideal_signing_bonus = int(base_demands.ideal_signing_bonus * performance_mult)
    base_demands.base_purse_min = int(base_demands.base_purse_min * performance_mult)
    base_demands.base_purse_max = int(base_demands.base_purse_max * performance_mult)
    base_demands.ideal_base_purse = int(base_demands.ideal_base_purse * performance_mult)
    base_demands.win_bonus_min = int(base_demands.win_bonus_min * performance_mult)
    base_demands.win_bonus_max = int(base_demands.win_bonus_max * performance_mult)
    base_demands.ideal_win_bonus = int(base_demands.ideal_win_bonus * performance_mult)
    
    return base_demands


# ============================================================================
# ENHANCED MULTI-ROUND NEGOTIATION SYSTEM
# ============================================================================

class NegotiationConcern(Enum):
    """What the fighter is most concerned about in negotiations."""
    MONEY = "money"
    FACILITIES = "facilities"
    LOCATION = "location"
    COACHING = "coaching"
    CONTRACT_LENGTH = "length"
    DEVELOPMENT = "development"


@dataclass
class CounterOffer:
    """Fighter's counter-request during negotiation."""
    fighter_id: str
    fighter_name: str
    round_number: int
    
    # What they want changed (None = current amount acceptable)
    signing_bonus_request: Optional[int] = None
    base_purse_request: Optional[int] = None
    win_bonus_request: Optional[int] = None
    fights_request: Optional[int] = None
    
    # Explanation
    reason: str = ""
    key_concern: NegotiationConcern = NegotiationConcern.MONEY
    
    # Would accepting this counter change acceptance?
    acceptance_if_met: int = 0  # 0-100
    
    @property
    def has_requests(self) -> bool:
        return any([
            self.signing_bonus_request is not None,
            self.base_purse_request is not None,
            self.win_bonus_request is not None,
            self.fights_request is not None,
        ])
    
    @property
    def total_increase_requested(self) -> int:
        """Estimate total value increase being requested."""
        increase = 0
        # These would need current offer context to calculate properly
        return increase


@dataclass
class AIOfferUpdate:
    """Track an AI camp's offer update in response to competition."""
    camp_id: str
    camp_name: str
    previous_offer: Optional[ContractOffer]
    new_offer: Optional[ContractOffer]
    action: str  # "raised", "held", "dropped_out"
    reason: str = ""
    
    @property
    def increase_amount(self) -> int:
        if self.previous_offer and self.new_offer:
            return self.new_offer.total_value - self.previous_offer.total_value
        return 0


@dataclass
class NegotiationRound:
    """State for a single round of negotiation."""
    round_number: int
    player_offer: Optional[ContractOffer] = None
    ai_offers: Dict[str, ContractOffer] = field(default_factory=dict)  # camp_id -> offer
    counter_offer: Optional[CounterOffer] = None
    ai_updates: List[AIOfferUpdate] = field(default_factory=list)
    player_acceptance: int = 0  # Probability at end of round


@dataclass
class ActiveNegotiation:
    """Tracks full state across multi-round negotiation."""
    negotiation_id: str
    fighter_id: str
    fighter_name: str
    demands: FighterDemands
    
    # Competing camps
    ai_bidders: List[AIBidder] = field(default_factory=list)
    active_ai_camps: List[str] = field(default_factory=list)  # camp_ids still bidding
    
    # Round tracking
    max_rounds: int = 3
    current_round: int = 1
    rounds: List[NegotiationRound] = field(default_factory=list)
    
    # Timing
    deadline_week: int = 0  # Fighter decides by this week
    started_week: int = 0
    
    # Resolution
    is_resolved: bool = False
    winner_camp_id: Optional[str] = None
    winning_offer: Optional[ContractOffer] = None
    resolution_reason: str = ""
    
    def __post_init__(self):
        if not self.negotiation_id:
            self.negotiation_id = str(uuid.uuid4())[:8]
        self.active_ai_camps = [b.camp_id for b in self.ai_bidders]
    
    @property
    def is_final_round(self) -> bool:
        return self.current_round >= self.max_rounds
    
    @property
    def has_competition(self) -> bool:
        return len(self.active_ai_camps) > 0
    
    @property
    def num_active_bidders(self) -> int:
        return len(self.active_ai_camps) + 1  # +1 for player
    
    def get_current_round(self) -> Optional[NegotiationRound]:
        for r in self.rounds:
            if r.round_number == self.current_round:
                return r
        return None
    
    def get_best_ai_offer(self) -> Optional[ContractOffer]:
        """Get the highest AI offer from active camps."""
        current = self.get_current_round()
        if not current or not current.ai_offers:
            return None
        
        active_offers = [
            offer for camp_id, offer in current.ai_offers.items()
            if camp_id in self.active_ai_camps
        ]
        if not active_offers:
            return None
        return max(active_offers, key=lambda o: o.total_value)
    
    def get_ai_offer(self, camp_id: str) -> Optional[ContractOffer]:
        """Get specific camp's current offer."""
        current = self.get_current_round()
        if current:
            return current.ai_offers.get(camp_id)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "negotiation_id": self.negotiation_id,
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "demands": {
                "fighter_id": self.demands.fighter_id,
                "fighter_name": self.demands.fighter_name,
                "signing_bonus_min": self.demands.signing_bonus_min,
                "signing_bonus_max": self.demands.signing_bonus_max,
                "base_purse_min": self.demands.base_purse_min,
                "base_purse_max": self.demands.base_purse_max,
                "win_bonus_min": self.demands.win_bonus_min,
                "win_bonus_max": self.demands.win_bonus_max,
                "min_fights": self.demands.min_fights,
                "max_fights": self.demands.max_fights,
                "preferred_fights": self.demands.preferred_fights,
                "ideal_signing_bonus": self.demands.ideal_signing_bonus,
                "ideal_base_purse": self.demands.ideal_base_purse,
                "ideal_win_bonus": self.demands.ideal_win_bonus,
                "market_heat": self.demands.market_heat,
                "negotiation_style": self.demands.negotiation_style.value,
                "nationality": self.demands.nationality,
                "preferred_region": self.demands.preferred_region,
            },
            "ai_bidders": [
                {
                    "camp_id": b.camp_id,
                    "camp_name": b.camp_name,
                    "camp_tier": b.camp_tier,
                    "budget": b.budget,
                    "interest_level": b.interest_level,
                    "likely_offer": b.likely_offer,
                    "nationality": b.nationality,
                    "region": b.region,
                }
                for b in self.ai_bidders
            ],
            "active_ai_camps": self.active_ai_camps,
            "max_rounds": self.max_rounds,
            "current_round": self.current_round,
            "deadline_week": self.deadline_week,
            "started_week": self.started_week,
            "is_resolved": self.is_resolved,
            "winner_camp_id": self.winner_camp_id,
            "resolution_reason": self.resolution_reason,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActiveNegotiation':
        demands_data = data.get("demands", {})
        demands = FighterDemands(
            fighter_id=demands_data.get("fighter_id", ""),
            fighter_name=demands_data.get("fighter_name", ""),
            signing_bonus_min=demands_data.get("signing_bonus_min", 10000),
            signing_bonus_max=demands_data.get("signing_bonus_max", 20000),
            base_purse_min=demands_data.get("base_purse_min", 10000),
            base_purse_max=demands_data.get("base_purse_max", 15000),
            win_bonus_min=demands_data.get("win_bonus_min", 5000),
            win_bonus_max=demands_data.get("win_bonus_max", 8000),
            min_fights=demands_data.get("min_fights", 3),
            max_fights=demands_data.get("max_fights", 6),
            preferred_fights=demands_data.get("preferred_fights", 4),
            ideal_signing_bonus=demands_data.get("ideal_signing_bonus", 15000),
            ideal_base_purse=demands_data.get("ideal_base_purse", 12000),
            ideal_win_bonus=demands_data.get("ideal_win_bonus", 6000),
            market_heat=demands_data.get("market_heat", 1.0),
            negotiation_style=NegotiationStyle(demands_data.get("negotiation_style", "balanced")),
            nationality=demands_data.get("nationality", ""),
            preferred_region=demands_data.get("preferred_region", ""),
        )
        
        bidders = []
        for b in data.get("ai_bidders", []):
            bidders.append(AIBidder(
                camp_id=b["camp_id"],
                camp_name=b["camp_name"],
                camp_tier=b["camp_tier"],
                budget=b["budget"],
                interest_level=b["interest_level"],
                likely_offer=b["likely_offer"],
                nationality=b.get("nationality", ""),
                region=b.get("region", ""),
            ))
        
        neg = cls(
            negotiation_id=data.get("negotiation_id", ""),
            fighter_id=data.get("fighter_id", ""),
            fighter_name=data.get("fighter_name", ""),
            demands=demands,
            ai_bidders=bidders,
            max_rounds=data.get("max_rounds", 3),
            current_round=data.get("current_round", 1),
            deadline_week=data.get("deadline_week", 0),
            started_week=data.get("started_week", 0),
            is_resolved=data.get("is_resolved", False),
            winner_camp_id=data.get("winner_camp_id"),
            resolution_reason=data.get("resolution_reason", ""),
        )
        neg.active_ai_camps = data.get("active_ai_camps", [])
        return neg


# ============================================================================
# COUNTER-OFFER GENERATION
# ============================================================================

# Fighter response templates based on negotiation style
COUNTER_TEMPLATES = {
    NegotiationStyle.LOYAL: [
        "I appreciate the offer. I'm not looking for the most money, but {concern}.",
        "Money isn't everything to me, but {concern}.",
        "I'd love to join your camp. Could you work on {concern}?",
    ],
    NegotiationStyle.MERCENARY: [
        "Let's talk numbers. {concern}.",
        "I've got other camps offering more. {concern}.",
        "This is business. {concern}.",
    ],
    NegotiationStyle.AMBITIOUS: [
        "I want to be a champion. Can you guarantee {concern}?",
        "I need the best training to reach my potential. {concern}.",
        "Facilities and development matter more than money. {concern}.",
    ],
    NegotiationStyle.HOMEBODY: [
        "I'd prefer to stay close to home. {concern}.",
        "Location is important to me. {concern}.",
        "Being near my family matters. {concern}.",
    ],
    NegotiationStyle.BALANCED: [
        "That's a fair offer, but {concern}.",
        "I'm interested, but let's discuss {concern}.",
        "We're close. Can you improve {concern}?",
    ],
}

CONCERN_PHRASES = {
    NegotiationConcern.MONEY: "the signing bonus could be better",
    NegotiationConcern.FACILITIES: "I need better training facilities",
    NegotiationConcern.LOCATION: "the location isn't ideal for me",
    NegotiationConcern.COACHING: "I'd want specialized coaching",
    NegotiationConcern.CONTRACT_LENGTH: "the contract length doesn't work for me",
    NegotiationConcern.DEVELOPMENT: "I need to know you'll develop me properly",
}


def generate_counter_offer(
    player_offer: ContractOffer,
    demands: FighterDemands,
    evaluation: OfferEvaluation,
    round_number: int,
    ai_best_offer: Optional[ContractOffer] = None,
) -> Optional[CounterOffer]:
    """
    Generate a fighter's counter-offer based on the current offer and their demands.
    
    Args:
        player_offer: The player's current offer
        demands: Fighter's demands
        evaluation: Evaluation of player's offer
        round_number: Current negotiation round
        ai_best_offer: Best competing AI offer (if any)
    
    Returns:
        CounterOffer with specific requests, or None if offer is acceptable
    """
    # If acceptance is very high, might accept without counter
    if evaluation.acceptance_probability >= 80 and random.random() < 0.6:
        return None
    
    # If acceptance is reasonable and final round, more likely to accept
    if evaluation.acceptance_probability >= 60 and round_number >= 3 and random.random() < 0.5:
        return None
    
    # Determine primary concern based on evaluation scores
    concerns: List[Tuple[NegotiationConcern, int]] = []
    
    # Financial concerns
    if evaluation.financial_score < 35:
        concerns.append((NegotiationConcern.MONEY, 40 - evaluation.financial_score))
    
    # Facilities concerns (for non-mercenary types)
    if evaluation.facilities_score < 12 and demands.negotiation_style != NegotiationStyle.MERCENARY:
        concerns.append((NegotiationConcern.FACILITIES, 15 - evaluation.facilities_score))
    
    # Location concerns (for homebody types)
    if evaluation.loyalty_score < 10 and demands.negotiation_style == NegotiationStyle.HOMEBODY:
        concerns.append((NegotiationConcern.LOCATION, 15 - evaluation.loyalty_score))
    
    # Coaching concerns
    if evaluation.coaching_score < 7:
        concerns.append((NegotiationConcern.COACHING, 10 - evaluation.coaching_score))
    
    # Development concerns (for ambitious types)
    if evaluation.reputation_score < 6 and demands.negotiation_style == NegotiationStyle.AMBITIOUS:
        concerns.append((NegotiationConcern.DEVELOPMENT, 10 - evaluation.reputation_score))
    
    # Default to money if no other concerns
    if not concerns:
        concerns.append((NegotiationConcern.MONEY, 10))
    
    # Pick primary concern
    concerns.sort(key=lambda x: -x[1])
    primary_concern = concerns[0][0]
    
    # Generate specific requests based on concern
    counter = CounterOffer(
        fighter_id=demands.fighter_id,
        fighter_name=demands.fighter_name,
        round_number=round_number,
        key_concern=primary_concern,
    )
    
    # Calculate request amounts based on concern type
    if primary_concern == NegotiationConcern.MONEY:
        # Want more money - request increase
        if player_offer.signing_bonus < demands.ideal_signing_bonus:
            # Request at least ideal, up to max
            target = min(demands.signing_bonus_max, int(demands.ideal_signing_bonus * 1.1))
            if player_offer.signing_bonus < target:
                counter.signing_bonus_request = target
        
        if player_offer.win_bonus < demands.ideal_win_bonus:
            target = min(demands.win_bonus_max, int(demands.ideal_win_bonus * 1.05))
            if player_offer.win_bonus < target:
                counter.win_bonus_request = target
        
        # If AI is offering more, ask to match
        if ai_best_offer and ai_best_offer.total_value > player_offer.total_value:
            diff = ai_best_offer.total_value - player_offer.total_value
            if diff > 10000:
                # Ask for significant increase to match
                counter.signing_bonus_request = min(
                    demands.signing_bonus_max,
                    player_offer.signing_bonus + int(diff * 0.4)
                )
    
    elif primary_concern == NegotiationConcern.CONTRACT_LENGTH:
        if player_offer.num_fights < demands.min_fights:
            counter.fights_request = demands.preferred_fights
        elif player_offer.num_fights > demands.max_fights:
            counter.fights_request = demands.preferred_fights
    
    # Generate reason text
    style = demands.negotiation_style
    templates = COUNTER_TEMPLATES.get(style, COUNTER_TEMPLATES[NegotiationStyle.BALANCED])
    template = random.choice(templates)
    concern_phrase = CONCERN_PHRASES.get(primary_concern, "there are some concerns")
    counter.reason = template.format(concern=concern_phrase)
    
    # Calculate acceptance if counter is met
    bonus = 15 + (5 * round_number)  # More bonus for later rounds
    counter.acceptance_if_met = min(95, evaluation.acceptance_probability + bonus)
    
    # Only return if there are actual requests
    if counter.has_requests or primary_concern in [NegotiationConcern.FACILITIES, NegotiationConcern.DEVELOPMENT]:
        return counter
    
    return None


# ============================================================================
# AI REACTION SYSTEM
# ============================================================================

def ai_react_to_competition(
    bidder: AIBidder,
    current_offer: ContractOffer,
    player_offer: ContractOffer,
    other_ai_offers: List[ContractOffer],
    demands: FighterDemands,
    round_number: int,
) -> AIOfferUpdate:
    """
    AI camp decides whether to raise, hold, or drop out.
    
    Args:
        bidder: The AI bidder
        current_offer: Their current offer
        player_offer: Player's latest offer
        other_ai_offers: Other AI camps' offers
        demands: Fighter's demands
        round_number: Current round
    
    Returns:
        AIOfferUpdate with new offer or dropout
    """
    # Find best competing offer
    all_competing = [player_offer] + other_ai_offers
    best_competing = max(all_competing, key=lambda o: o.total_value)
    
    # Are we currently winning?
    we_are_winning = current_offer.total_value >= best_competing.total_value
    gap = best_competing.total_value - current_offer.total_value if not we_are_winning else 0
    
    # Decision factors based on interest level
    if bidder.interest_level == "Strong":
        raise_chance = 0.8 if gap > 0 else 0.3  # Likely to raise if behind
        dropout_chance = 0.05
        max_raise = 0.25  # Up to 25% increase
    elif bidder.interest_level == "Moderate":
        raise_chance = 0.5 if gap > 0 else 0.1
        dropout_chance = 0.15 if gap > 20000 else 0.05
        max_raise = 0.15
    else:  # Mild
        raise_chance = 0.2 if gap > 0 else 0.0
        dropout_chance = 0.35 if gap > 15000 else 0.15
        max_raise = 0.10
    
    # Increase dropout chance in later rounds
    dropout_chance += (round_number - 1) * 0.1
    
    # Budget constraint
    budget_remaining = bidder.budget - current_offer.total_value
    if budget_remaining < 5000:
        dropout_chance += 0.3
        raise_chance *= 0.3
    
    # Roll for action
    roll = random.random()
    
    if roll < dropout_chance:
        # Drop out
        return AIOfferUpdate(
            camp_id=bidder.camp_id,
            camp_name=bidder.camp_name,
            previous_offer=current_offer,
            new_offer=None,
            action="dropped_out",
            reason="Decided the price was too high",
        )
    
    if we_are_winning:
        # We're winning - might hold or raise slightly
        if random.random() < 0.7:
            return AIOfferUpdate(
                camp_id=bidder.camp_id,
                camp_name=bidder.camp_name,
                previous_offer=current_offer,
                new_offer=current_offer,
                action="held",
                reason="Confident in current offer",
            )
    
    if random.random() < raise_chance and gap > 0:
        # Raise offer
        # Calculate raise amount
        raise_target = min(
            current_offer.total_value * (1 + max_raise),
            bidder.budget * 0.95,
            best_competing.total_value * 1.05,  # Try to beat by 5%
        )
        
        raise_amount = raise_target - current_offer.total_value
        if raise_amount < 3000:
            raise_amount = 3000  # Minimum raise
        
        # Distribute raise across terms
        new_signing = current_offer.signing_bonus + int(raise_amount * 0.5)
        new_purse = current_offer.base_purse + int(raise_amount * 0.03)  # Small per-fight increase
        new_win = current_offer.win_bonus + int(raise_amount * 0.02)
        
        new_offer = ContractOffer(
            camp_id=bidder.camp_id,
            camp_name=bidder.camp_name,
            camp_tier=bidder.camp_tier,
            signing_bonus=new_signing,
            base_purse=new_purse,
            win_bonus=new_win,
            num_fights=current_offer.num_fights,
            camp_nationality=bidder.nationality,
            camp_region=bidder.region,
        )
        
        return AIOfferUpdate(
            camp_id=bidder.camp_id,
            camp_name=bidder.camp_name,
            previous_offer=current_offer,
            new_offer=new_offer,
            action="raised",
            reason=f"Increased offer by ${int(raise_amount):,}",
        )
    
    # Default: hold current offer
    return AIOfferUpdate(
        camp_id=bidder.camp_id,
        camp_name=bidder.camp_name,
        previous_offer=current_offer,
        new_offer=current_offer,
        action="held",
        reason="Holding current offer",
    )


# ============================================================================
# INFORMATION VISIBILITY (Scouting-based)
# ============================================================================

def get_visible_offer_info(
    ai_offer: ContractOffer,
    bidder: AIBidder,
    scouting_level: int = 50,  # 0-100
) -> Dict[str, Any]:
    """
    Return information about AI offer based on player's scouting ability.
    
    Low scouting: Only see interest level
    Medium scouting: See estimated total
    High scouting: See specific terms
    
    Args:
        ai_offer: The AI camp's offer
        bidder: The AI bidder info
        scouting_level: Player's scouting/intel ability (0-100)
    
    Returns:
        Dict with visible information
    """
    info = {
        "camp_name": bidder.camp_name,
        "camp_tier": bidder.camp_tier,
        "interest_level": bidder.interest_level,
        "is_active": True,
    }
    
    if scouting_level < 30:
        # Low: Only basic interest
        info["offer_description"] = f"{bidder.interest_level} interest"
        info["estimated_total"] = None
        info["signing_visible"] = False
        info["terms_visible"] = False
    
    elif scouting_level < 60:
        # Medium: Estimated total with variance
        variance = random.uniform(0.85, 1.15)
        estimated = int(ai_offer.total_value * variance)
        # Round to nearest 5K
        estimated = (estimated // 5000) * 5000
        info["offer_description"] = f"~${estimated:,} total (estimated)"
        info["estimated_total"] = estimated
        info["signing_visible"] = False
        info["terms_visible"] = False
    
    elif scouting_level < 80:
        # Good: Accurate total, approximate signing
        info["offer_description"] = f"${ai_offer.total_value:,} total"
        info["estimated_total"] = ai_offer.total_value
        # Show approximate signing (rounded to 5K)
        approx_signing = (ai_offer.signing_bonus // 5000) * 5000
        info["signing_estimate"] = f"~${approx_signing:,}"
        info["signing_visible"] = True
        info["terms_visible"] = False
    
    else:
        # High: Full visibility
        info["offer_description"] = f"${ai_offer.total_value:,} total"
        info["estimated_total"] = ai_offer.total_value
        info["signing_bonus"] = ai_offer.signing_bonus
        info["base_purse"] = ai_offer.base_purse
        info["win_bonus"] = ai_offer.win_bonus
        info["num_fights"] = ai_offer.num_fights
        info["signing_visible"] = True
        info["terms_visible"] = True
    
    return info


# ============================================================================
# MULTI-ROUND NEGOTIATION MANAGER
# ============================================================================

class MultiRoundNegotiationManager:
    """
    Manages multi-round competitive negotiations.
    
    Handles the back-and-forth of offers, counter-offers,
    AI reactions, and final resolution.
    """
    
    def __init__(self):
        self.active_negotiations: Dict[str, ActiveNegotiation] = {}
        self.completed_negotiations: List[NegotiationResult] = []
    
    def start_negotiation(
        self,
        fighter_data: Any,
        all_camps: List[Any],
        player_camp_id: str,
        current_week: int = 0,
        max_rounds: int = 3,
    ) -> ActiveNegotiation:
        """
        Start a new multi-round negotiation.
        
        Args:
            fighter_data: Fighter to negotiate with
            all_camps: All camps for AI interest generation
            player_camp_id: Player's camp ID
            current_week: Current game week
            max_rounds: Maximum negotiation rounds
        
        Returns:
            ActiveNegotiation instance
        """
        fighter_id = getattr(fighter_data, 'fighter_id', str(uuid.uuid4())[:8])
        name = getattr(fighter_data, 'name', 'Unknown Fighter')
        
        # Generate AI interest
        ai_bidders = generate_ai_interest(fighter_data, all_camps, player_camp_id)
        
        # Calculate demands with competition modifier
        demands = calculate_fighter_demands(
            fighter_data,
            market_heat=1.0 + (len(ai_bidders) * 0.1),
            num_interested_camps=len(ai_bidders),
        )
        
        # Create negotiation
        negotiation = ActiveNegotiation(
            negotiation_id=str(uuid.uuid4())[:8],
            fighter_id=fighter_id,
            fighter_name=name,
            demands=demands,
            ai_bidders=ai_bidders,
            max_rounds=max_rounds,
            current_round=1,
            started_week=current_week,
            deadline_week=current_week + max_rounds + 1,  # Deadline after all rounds
        )
        
        # Generate initial AI offers
        first_round = NegotiationRound(round_number=1)
        for bidder in ai_bidders:
            offer = generate_ai_offer(bidder, demands)
            first_round.ai_offers[bidder.camp_id] = offer
        
        negotiation.rounds.append(first_round)
        
        # Store
        self.active_negotiations[negotiation.negotiation_id] = negotiation
        
        return negotiation
    
    def submit_player_offer(
        self,
        negotiation_id: str,
        player_offer: ContractOffer,
        fighter_data: Any,
    ) -> Tuple[OfferEvaluation, Optional[CounterOffer], List[AIOfferUpdate]]:
        """
        Submit player's offer for current round.
        
        Args:
            negotiation_id: The negotiation ID
            player_offer: Player's offer
            fighter_data: Fighter data for evaluation
        
        Returns:
            Tuple of (evaluation, counter_offer, ai_updates)
        """
        negotiation = self.active_negotiations.get(negotiation_id)
        if not negotiation or negotiation.is_resolved:
            return None, None, []
        
        current_round = negotiation.get_current_round()
        if not current_round:
            return None, None, []
        
        # Store player offer
        current_round.player_offer = player_offer
        
        # Get active AI offers for comparison
        ai_offers = [
            current_round.ai_offers[camp_id]
            for camp_id in negotiation.active_ai_camps
            if camp_id in current_round.ai_offers
        ]
        
        # Evaluate player offer
        evaluation = evaluate_offer(player_offer, negotiation.demands, fighter_data, ai_offers)
        current_round.player_acceptance = evaluation.acceptance_probability
        
        # Generate counter-offer
        best_ai = negotiation.get_best_ai_offer()
        counter = generate_counter_offer(
            player_offer,
            negotiation.demands,
            evaluation,
            negotiation.current_round,
            best_ai,
        )
        current_round.counter_offer = counter
        
        # AI camps react to player offer
        ai_updates = []
        for camp_id in list(negotiation.active_ai_camps):
            bidder = next((b for b in negotiation.ai_bidders if b.camp_id == camp_id), None)
            if not bidder:
                continue
            
            current_ai_offer = current_round.ai_offers.get(camp_id)
            if not current_ai_offer:
                continue
            
            other_ai = [o for cid, o in current_round.ai_offers.items() 
                       if cid != camp_id and cid in negotiation.active_ai_camps]
            
            update = ai_react_to_competition(
                bidder=bidder,
                current_offer=current_ai_offer,
                player_offer=player_offer,
                other_ai_offers=other_ai,
                demands=negotiation.demands,
                round_number=negotiation.current_round,
            )
            ai_updates.append(update)
            
            # Handle dropout
            if update.action == "dropped_out":
                negotiation.active_ai_camps.remove(camp_id)
            elif update.new_offer:
                current_round.ai_offers[camp_id] = update.new_offer
        
        current_round.ai_updates = ai_updates
        
        return evaluation, counter, ai_updates
    
    def advance_round(self, negotiation_id: str) -> bool:
        """
        Advance to the next negotiation round.
        
        Returns:
            True if advanced, False if at max rounds
        """
        negotiation = self.active_negotiations.get(negotiation_id)
        if not negotiation or negotiation.is_resolved:
            return False
        
        if negotiation.is_final_round:
            return False
        
        negotiation.current_round += 1
        
        # Create new round with carried-over AI offers
        new_round = NegotiationRound(round_number=negotiation.current_round)
        
        # Copy AI offers from previous round
        prev_round = negotiation.rounds[-1] if negotiation.rounds else None
        if prev_round:
            for camp_id in negotiation.active_ai_camps:
                if camp_id in prev_round.ai_offers:
                    new_round.ai_offers[camp_id] = prev_round.ai_offers[camp_id]
        
        negotiation.rounds.append(new_round)
        
        return True
    
    def resolve_negotiation(
        self,
        negotiation_id: str,
        player_offer: ContractOffer,
        fighter_data: Any,
        player_camp_id: str,
    ) -> NegotiationResult:
        """
        Resolve the negotiation and determine winner.
        
        Args:
            negotiation_id: The negotiation ID
            player_offer: Player's final offer
            fighter_data: Fighter data
            player_camp_id: Player's camp ID
        
        Returns:
            NegotiationResult with outcome
        """
        negotiation = self.active_negotiations.get(negotiation_id)
        if not negotiation:
            return NegotiationResult(
                success=False,
                fighter_id="",
                fighter_name="Unknown",
                decision_factors=["Negotiation not found"],
            )
        
        demands = negotiation.demands
        
        # Gather all active offers
        current_round = negotiation.get_current_round()
        
        # Build candidate list
        candidates: List[Tuple[ContractOffer, OfferEvaluation]] = []
        
        # Player offer
        ai_offers = [
            current_round.ai_offers[camp_id]
            for camp_id in negotiation.active_ai_camps
            if camp_id in current_round.ai_offers
        ]
        player_eval = evaluate_offer(player_offer, demands, fighter_data, ai_offers)
        player_offer.camp_id = player_camp_id  # Ensure camp_id is set
        candidates.append((player_offer, player_eval))
        
        # AI offers
        for camp_id in negotiation.active_ai_camps:
            ai_offer = current_round.ai_offers.get(camp_id)
            if not ai_offer:
                continue
            
            other_offers = [player_offer] + [
                o for cid, o in current_round.ai_offers.items()
                if cid != camp_id and cid in negotiation.active_ai_camps
            ]
            ai_eval = evaluate_offer(ai_offer, demands, fighter_data, other_offers)
            candidates.append((ai_offer, ai_eval))
        
        # Weighted random selection based on acceptance probability
        total_prob = sum(e.acceptance_probability for _, e in candidates)
        if total_prob == 0:
            total_prob = len(candidates)  # Fallback to equal odds
        
        roll = random.uniform(0, total_prob)
        cumulative = 0
        winner_offer, winner_eval = candidates[0]
        
        for offer, eval_result in candidates:
            cumulative += eval_result.acceptance_probability
            if roll <= cumulative:
                winner_offer = offer
                winner_eval = eval_result
                break
        
        # Mark resolved
        negotiation.is_resolved = True
        negotiation.winner_camp_id = winner_offer.camp_id
        negotiation.winning_offer = winner_offer
        
        # Determine if player won
        player_won = winner_offer.camp_id == player_camp_id
        
        if player_won:
            result = NegotiationResult(
                success=True,
                fighter_id=demands.fighter_id,
                fighter_name=demands.fighter_name,
                final_offer=player_offer,
                decision_factors=winner_eval.positive_factors,
            )
            negotiation.resolution_reason = "Player's offer accepted"
        else:
            # Find why player lost
            factors = []
            if player_offer.total_value < winner_offer.total_value:
                diff = winner_offer.total_value - player_offer.total_value
                factors.append(f"Offered ${diff:,} more in total compensation")
            
            player_tier_bonus = CAMP_TIER_BONUS.get(player_offer.camp_tier, 0)
            winner_tier_bonus = CAMP_TIER_BONUS.get(winner_offer.camp_tier, 0)
            if winner_tier_bonus > player_tier_bonus:
                factors.append("Better training facilities")
            
            if winner_offer.camp_nationality == demands.nationality and player_offer.camp_nationality != demands.nationality:
                factors.append("Same nationality as fighter")
            
            if not factors:
                factors.append("Better overall package and fit")
            
            result = NegotiationResult(
                success=False,
                fighter_id=demands.fighter_id,
                fighter_name=demands.fighter_name,
                winner_camp_name=winner_offer.camp_name,
                winner_offer_total=winner_offer.total_value,
                player_offer_total=player_offer.total_value,
                decision_factors=factors,
            )
            negotiation.resolution_reason = f"Signed with {winner_offer.camp_name}"
        
        # Store result
        self.completed_negotiations.append(result)
        
        # Remove from active
        if negotiation_id in self.active_negotiations:
            del self.active_negotiations[negotiation_id]
        
        return result
    
    def get_negotiation(self, negotiation_id: str) -> Optional[ActiveNegotiation]:
        """Get an active negotiation by ID."""
        return self.active_negotiations.get(negotiation_id)
    
    def get_fighter_negotiation(self, fighter_id: str) -> Optional[ActiveNegotiation]:
        """Get active negotiation for a specific fighter."""
        for neg in self.active_negotiations.values():
            if neg.fighter_id == fighter_id:
                return neg
        return None
    
    def cancel_negotiation(self, negotiation_id: str) -> bool:
        """Cancel/abandon a negotiation."""
        if negotiation_id in self.active_negotiations:
            del self.active_negotiations[negotiation_id]
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_negotiations": {
                nid: n.to_dict() for nid, n in self.active_negotiations.items()
            },
            "completed_count": len(self.completed_negotiations),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MultiRoundNegotiationManager':
        manager = cls()
        for nid, ndata in data.get("active_negotiations", {}).items():
            manager.active_negotiations[nid] = ActiveNegotiation.from_dict(ndata)
        return manager


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_money(amount: int) -> str:
    """Format money amount for display."""
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif amount >= 1000:
        return f"${amount:,}"
    else:
        return f"${amount}"


def get_market_description(num_bidders: int) -> Tuple[str, str]:
    """Get market heat description based on number of bidders."""
    if num_bidders == 0:
        return "Cold", "No other camps interested"
    elif num_bidders == 1:
        return "Lukewarm", "One other camp interested"
    elif num_bidders == 2:
        return "Warm", "Multiple camps competing"
    elif num_bidders >= 3:
        return "Hot", "Bidding war in progress!"
    return "Normal", ""


def get_acceptance_description(probability: int) -> Tuple[str, str]:
    """Get acceptance probability description and color hint."""
    if probability >= 80:
        return "Very Likely", "green"
    elif probability >= 60:
        return "Likely", "cyan"
    elif probability >= 40:
        return "Possible", "yellow"
    elif probability >= 20:
        return "Unlikely", "orange"
    else:
        return "Very Unlikely", "red"


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Data classes
    "FighterDemands",
    "ContractOffer", 
    "OfferEvaluation",
    "AIBidder",
    "BiddingWar",
    "NegotiationResult",
    "NegotiationStyle",
    "ActiveContract",
    "ContractAlert",
    # New multi-round classes
    "CounterOffer",
    "AIOfferUpdate",
    "NegotiationRound",
    "ActiveNegotiation",
    "NegotiationConcern",
    
    # Core functions
    "calculate_fighter_demands",
    "generate_ai_interest",
    "evaluate_offer",
    "generate_ai_offer",
    "resolve_bidding_war",
    "attempt_signing_no_competition",
    "calculate_resigning_demands",
    # New multi-round functions
    "generate_counter_offer",
    "ai_react_to_competition",
    "get_visible_offer_info",
    "format_money",
    "get_market_description",
    "get_acceptance_description",
    
    # System classes
    "NegotiationSystem",
    "ContractManager",
    "MultiRoundNegotiationManager",
    
    # Constants
    "BASE_DEMANDS",
    "CAMP_BUDGETS",
    "CAMP_TIER_BONUS",
    "NATIONALITY_REGIONS",
]
