# core/config.py
# Module 3: Configuration Manager
# Lines: 341
#
# Centralized game configuration and balance settings.
# Change values here to tune the entire simulation.

"""
Cage Dynasty - Configuration Manager

This module provides centralized configuration for all game systems.
Instead of hardcoding values throughout the codebase, all tunable
parameters live here, making balance adjustments easy.

FEATURES:
- Default configurations for all game systems
- Runtime configuration updates
- Configuration validation
- Save/load configuration to JSON
- Environment-based overrides (for testing)

USAGE:
    from core.config import config
    
    # Read a value
    prime_start = config.get("aging.prime_start")
    
    # Update a value
    config.set("training.max_gain_per_week", 3)
    
    # Get entire section
    aging_config = config.section("aging")

IMPORT RULES:
- This module imports ONLY from Python standard library
- All other game modules may import from this module
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from pathlib import Path
import json
import copy

# ============================================================================
# DEFAULT CONFIGURATION VALUES
# ============================================================================

DEFAULT_CONFIG: Dict[str, Any] = {
    # ========================================================================
    # AGING & PHYSICAL DECLINE
    # ========================================================================
    "aging": {
        "prime_start": 26,          # Age when fighter enters prime
        "prime_end": 32,            # Age when prime ends
        "decline_start": 33,        # Age when decline begins
        "retirement_avg": 38,       # Average retirement age
        "retirement_min": 34,       # Earliest typical retirement
        "retirement_max": 45,       # Latest typical retirement
        "decline_rate_base": 1.5,   # Base stat points lost per year after prime
        "decline_rate_physical": 2.0,  # Physical stats decline faster
        "decline_rate_mental": 0.5,    # Mental stats decline slower
        "chin_decline_multiplier": 1.5,  # Chin degrades faster than other stats
        "injury_decline_bonus": 0.5,     # Extra decline per major injury
    },
    
    # ========================================================================
    # FIGHTER GENERATION
    # ========================================================================
    "generation": {
        "debut_age_min": 18,        # Minimum debut age
        "debut_age_max": 28,        # Maximum debut age
        "debut_age_avg": 23,        # Average debut age
        "base_stat_min": 35,        # Minimum starting stat
        "base_stat_max": 75,        # Maximum starting stat (prospects)
        "elite_prospect_chance": 0.05,  # 5% chance of elite prospect
        "elite_stat_bonus": 15,     # Bonus stats for elite prospects
        "style_weights": {          # Probability weights for fighting styles
            "Boxing": 15,
            "Wrestling": 20,
            "BJJ": 15,
            "Muay_Thai": 12,
            "Kickboxing": 10,
            "Judo": 8,
            "Sambo": 5,
            "Karate": 5,
            "MMA_Hybrid": 10,
        },
    },
    
    # ========================================================================
    # TRAINING & DEVELOPMENT
    # ========================================================================
    "training": {
        "weeks_per_camp": 8,        # Standard training camp length
        "max_gain_per_week": 2,     # Maximum stat gain per week
        "max_gain_per_camp": 5,     # Maximum total gain per camp
        "fatigue_threshold": 80,    # Fatigue level that hurts gains
        "overtraining_penalty": 0.5,  # Multiplier when overtrained
        "rest_recovery_rate": 10,   # Fatigue points recovered per rest week
        "age_learning_penalty": {   # Reduced gains as fighter ages
            30: 0.9,   # 90% effectiveness at 30
            33: 0.75,  # 75% at 33
            36: 0.5,   # 50% at 36
            40: 0.25,  # 25% at 40
        },
        "coach_quality_multiplier": {  # Training effectiveness by coach quality
            1: 0.6,    # Poor coach
            2: 0.8,    # Below average
            3: 1.0,    # Average
            4: 1.2,    # Good
            5: 1.5,    # Elite
        },
    },
    
    # ========================================================================
    # CAMP MANAGEMENT
    # ========================================================================
    "camp": {
        "starting_funds": 50000,    # Player starting money
        "tier_costs": {             # Monthly operating costs by tier
            1: 5000,    # Garage
            2: 15000,   # Local
            3: 40000,   # Regional
            4: 100000,  # National
            5: 250000,  # Elite
        },
        "upgrade_costs": {          # Cost to upgrade to each tier
            2: 100000,   # Garage -> Local
            3: 500000,   # Local -> Regional
            4: 2000000,  # Regional -> National
            5: 10000000, # National -> Elite
        },
        "max_fighters_by_tier": {   # Roster limits
            1: 5,
            2: 10,
            3: 20,
            4: 35,
            5: 50,
        },
        "bankruptcy_threshold": -50000,  # Debt that triggers bankruptcy
    },
    
    # ========================================================================
    # FINANCES & ECONOMY
    # ========================================================================
    "economy": {
        "purse_minimum": 5000,      # Minimum fight purse
        "purse_base_by_rank": {     # Base purse by ranking
            0: 500000,   # Champion
            1: 150000,   # #1 contender
            5: 75000,    # Top 5
            10: 40000,   # Top 10
            15: 20000,   # Ranked
            "unranked": 10000,
        },
        "title_fight_multiplier": 2.0,   # Purse multiplier for title fights
        "main_event_multiplier": 1.5,    # Purse multiplier for main events
        "win_bonus_percentage": 0.5,     # Win bonus as percentage of purse
        "ppv_points_threshold": 10,      # Rank needed for PPV points
        "sponsorship_base": 1000,        # Base monthly sponsorship
        "sponsorship_per_popularity": 100,  # Extra per popularity point
        "gate_revenue_share": 0.10,      # Fighter share of gate revenue
    },
    
    # ========================================================================
    # RANKINGS & MATCHMAKING
    # ========================================================================
    "rankings": {
        "ranks_per_division": 15,   # Number of ranked fighters
        "inactivity_weeks": 52,     # Weeks before inactivity penalty
        "inactivity_drop_rate": 1,  # Ranks dropped per month inactive
        "win_points": {             # Points for wins by opponent rank
            "champion": 100,
            "top5": 50,
            "top10": 30,
            "top15": 20,
            "unranked": 5,
        },
        "loss_points": {            # Points lost for losses
            "champion": -20,
            "top5": -30,
            "top10": -25,
            "top15": -20,
            "unranked": -40,
        },
        "finish_bonus": 10,         # Bonus points for finishes
    },
    
    # ========================================================================
    # FIGHT SIMULATION
    # ========================================================================
    "fight": {
        "rounds_standard": 3,       # Regular fight rounds
        "rounds_championship": 5,   # Title fight rounds
        "round_length_seconds": 300,  # 5 minutes
        "knockdown_recovery_chance": 0.7,  # Chance to survive knockdown
        "submission_escape_base": 0.4,     # Base escape chance
        "doctor_stoppage_threshold": 30,   # Damage threshold for stoppage
        "judge_bias_range": 0.05,   # Random variance in scoring
        "hometown_advantage": 0.03, # Slight edge for "home" fighter
    },
    
    # ========================================================================
    # INJURIES
    # ========================================================================
    "injury": {
        "fight_injury_chance": 0.15,  # Chance of injury from fight
        "training_injury_chance": 0.02,  # Chance per training week
        "ko_injury_multiplier": 2.0,  # Higher injury chance after KO
        "recovery_weeks": {           # Recovery time by severity
            "minor": (1, 2),
            "moderate": (4, 8),
            "severe": (12, 26),
            "career": (26, 52),
        },
        "reinjury_chance_bonus": 0.1,  # Extra injury chance if recently hurt
    },
    
    # ========================================================================
    # RIVALRIES & NARRATIVES
    # ========================================================================
    "rivalry": {
        "min_fights_to_form": 1,    # Fights needed to start rivalry
        "intensity_decay_weeks": 26,  # Weeks for rivalry to cool down
        "trash_talk_intensity_boost": 5,  # Points from trash talk
        "controversial_finish_boost": 15,  # Points from controversial ending
        "close_fight_boost": 10,    # Points from close decision
        "rematch_boost": 20,        # Extra intensity in rematches
        "intensity_thresholds": {   # Points needed for each level
            "mild": 10,
            "moderate": 30,
            "heated": 60,
            "bitter": 100,
            "legendary": 150,
        },
    },
    
    # ========================================================================
    # TIME & SCHEDULING
    # ========================================================================
    "time": {
        "weeks_per_year": 52,
        "events_per_month": 2,      # Average events per month
        "min_weeks_between_fights": 4,   # Minimum rest between fights
        "preferred_weeks_between": 12,   # Ideal rest period
        "max_weeks_without_fight": 52,   # Before considered inactive
    },
    
    # ========================================================================
    # SIMULATION SETTINGS
    # ========================================================================
    "simulation": {
        "random_seed": None,        # Set for reproducible results
        "log_level": "INFO",        # Logging verbosity
        "auto_save_weeks": 4,       # Auto-save interval
        "max_history_events": 10000,  # Event history limit
    },
}


# ============================================================================
# CONFIGURATION CLASS
# ============================================================================

class GameConfig:
    """
    Centralized configuration manager for Cage Dynasty.
    
    Provides a hierarchical configuration system with:
    - Dot-notation access (config.get("aging.prime_start"))
    - Section access (config.section("training"))
    - Runtime updates with validation
    - JSON serialization for save/load
    """
    
    def __init__(self, initial_config: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration with defaults, optionally overriding.
        
        Args:
            initial_config: Optional dict to override defaults
        """
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        
        if initial_config:
            self._deep_update(self._config, initial_config)
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            path: Dot-separated path (e.g., "aging.prime_start")
            default: Value to return if path not found
        
        Returns:
            Configuration value or default
        
        Example:
            config.get("training.max_gain_per_week")  # Returns 2
            config.get("invalid.path", 0)  # Returns 0
        """
        keys = path.split(".")
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, path: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            path: Dot-separated path
            value: New value to set
        
        Example:
            config.set("training.max_gain_per_week", 3)
        """
        keys = path.split(".")
        target = self._config
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        # Set the value
        target[keys[-1]] = value
    
    def section(self, name: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            name: Section name (top-level key)
        
        Returns:
            Copy of the section dictionary
        
        Example:
            aging = config.section("aging")
            print(aging["prime_start"])  # 26
        """
        return copy.deepcopy(self._config.get(name, {}))
    
    def update_section(self, name: str, values: Dict[str, Any]) -> None:
        """
        Update multiple values in a section.
        
        Args:
            name: Section name
            values: Dictionary of values to update
        """
        if name not in self._config:
            self._config[name] = {}
        
        self._deep_update(self._config[name], values)
    
    def reset(self, section: Optional[str] = None) -> None:
        """
        Reset configuration to defaults.
        
        Args:
            section: Specific section to reset, or None for all
        """
        if section:
            if section in DEFAULT_CONFIG:
                self._config[section] = copy.deepcopy(DEFAULT_CONFIG[section])
        else:
            self._config = copy.deepcopy(DEFAULT_CONFIG)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export entire configuration as dictionary"""
        return copy.deepcopy(self._config)
    
    def to_json(self, indent: int = 2) -> str:
        """Export configuration as JSON string"""
        return json.dumps(self._config, indent=indent)
    
    def save(self, filepath: Union[str, Path]) -> None:
        """
        Save configuration to a JSON file.
        
        Args:
            filepath: Path to save file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    @classmethod
    def load(cls, filepath: Union[str, Path]) -> 'GameConfig':
        """
        Load configuration from a JSON file.
        
        Args:
            filepath: Path to config file
        
        Returns:
            New GameConfig instance with loaded values
        """
        filepath = Path(filepath)
        
        with open(filepath, 'r') as f:
            loaded = json.load(f)
        
        return cls(loaded)
    
    def _deep_update(self, base: Dict, updates: Dict) -> None:
        """Recursively update nested dictionaries"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def validate(self) -> List[str]:
        """
        Validate configuration values.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # =====================================================================
        # AGING VALIDATIONS
        # =====================================================================
        aging = self.section("aging")
        
        # Age sequence validation
        if aging.get("prime_start", 0) >= aging.get("prime_end", 0):
            errors.append("aging.prime_start must be < aging.prime_end")
        if aging.get("decline_start", 0) <= aging.get("prime_end", 0):
            errors.append("aging.decline_start must be > aging.prime_end")
        if aging.get("retirement_min", 0) <= aging.get("decline_start", 0):
            errors.append("aging.retirement_min must be > aging.decline_start")
        if aging.get("retirement_avg", 0) < aging.get("retirement_min", 0):
            errors.append("aging.retirement_avg must be >= aging.retirement_min")
        if aging.get("retirement_max", 0) < aging.get("retirement_avg", 0):
            errors.append("aging.retirement_max must be >= aging.retirement_avg")
        if aging.get("retirement_max", 100) > 55:
            errors.append("aging.retirement_max should be <= 55 (sanity check)")
        
        # Decline rate validation
        if aging.get("decline_rate_base", 0) <= 0:
            errors.append("aging.decline_rate_base must be positive")
        if aging.get("decline_rate_base", 0) > 10:
            errors.append("aging.decline_rate_base > 10 is likely a mistake")
        
        # =====================================================================
        # GENERATION VALIDATIONS
        # =====================================================================
        gen = self.section("generation")
        
        if gen.get("debut_age_min", 0) < 16:
            errors.append("generation.debut_age_min must be >= 16")
        if gen.get("debut_age_max", 0) <= gen.get("debut_age_min", 0):
            errors.append("generation.debut_age_max must be > debut_age_min")
        if gen.get("base_stat_min", 0) < 1:
            errors.append("generation.base_stat_min must be >= 1")
        if gen.get("base_stat_max", 0) > 99:
            errors.append("generation.base_stat_max must be <= 99")
        if gen.get("base_stat_min", 0) >= gen.get("base_stat_max", 100):
            errors.append("generation.base_stat_min must be < base_stat_max")
        if not (0 <= gen.get("elite_prospect_chance", 0) <= 1):
            errors.append("generation.elite_prospect_chance must be between 0 and 1")
        
        # =====================================================================
        # TRAINING VALIDATIONS
        # =====================================================================
        training = self.section("training")
        
        if training.get("max_gain_per_week", 0) <= 0:
            errors.append("training.max_gain_per_week must be positive")
        if training.get("max_gain_per_week", 0) > 10:
            errors.append("training.max_gain_per_week > 10 is likely a mistake")
        if training.get("max_gain_per_camp", 0) < training.get("max_gain_per_week", 0):
            errors.append("training.max_gain_per_camp must be >= max_gain_per_week")
        if training.get("weeks_per_camp", 0) <= 0:
            errors.append("training.weeks_per_camp must be positive")
        if not (0 < training.get("fatigue_threshold", 0) <= 100):
            errors.append("training.fatigue_threshold must be between 1 and 100")
        if not (0 < training.get("overtraining_penalty", 0) <= 1):
            errors.append("training.overtraining_penalty must be between 0 and 1")
        if training.get("rest_recovery_rate", 0) <= 0:
            errors.append("training.rest_recovery_rate must be positive")
        
        # =====================================================================
        # CAMP VALIDATIONS
        # =====================================================================
        camp = self.section("camp")
        
        if camp.get("starting_funds", 0) <= 0:
            errors.append("camp.starting_funds must be positive")
        if camp.get("bankruptcy_threshold", 0) >= 0:
            errors.append("camp.bankruptcy_threshold must be negative")
        
        # Tier costs should increase
        tier_costs = camp.get("tier_costs", {})
        if tier_costs:
            prev_cost = 0
            for tier in sorted(tier_costs.keys()):
                if tier_costs[tier] <= prev_cost:
                    errors.append(f"camp.tier_costs[{tier}] must be > tier {tier-1}")
                prev_cost = tier_costs[tier]
        
        # =====================================================================
        # ECONOMY VALIDATIONS
        # =====================================================================
        economy = self.section("economy")
        
        if economy.get("purse_minimum", 0) <= 0:
            errors.append("economy.purse_minimum must be positive")
        if economy.get("title_fight_multiplier", 0) < 1:
            errors.append("economy.title_fight_multiplier must be >= 1")
        if not (0 <= economy.get("win_bonus_percentage", 0) <= 2):
            errors.append("economy.win_bonus_percentage must be between 0 and 2")
        
        # =====================================================================
        # RANKINGS VALIDATIONS
        # =====================================================================
        rankings = self.section("rankings")
        
        if rankings.get("ranks_per_division", 0) <= 0:
            errors.append("rankings.ranks_per_division must be positive")
        if rankings.get("ranks_per_division", 0) > 25:
            errors.append("rankings.ranks_per_division > 25 is unusual")
        if rankings.get("inactivity_weeks", 0) <= 0:
            errors.append("rankings.inactivity_weeks must be positive")
        if rankings.get("finish_bonus", 0) < 0:
            errors.append("rankings.finish_bonus must be >= 0")
        
        # =====================================================================
        # FIGHT VALIDATIONS
        # =====================================================================
        fight = self.section("fight")
        
        if fight.get("rounds_standard", 0) <= 0:
            errors.append("fight.rounds_standard must be positive")
        if fight.get("rounds_standard", 0) > 5:
            errors.append("fight.rounds_standard > 5 is unusual for MMA")
        if fight.get("rounds_championship", 0) < fight.get("rounds_standard", 0):
            errors.append("fight.rounds_championship must be >= rounds_standard")
        if fight.get("round_length_seconds", 0) <= 0:
            errors.append("fight.round_length_seconds must be positive")
        if not (0 <= fight.get("knockdown_recovery_chance", 0) <= 1):
            errors.append("fight.knockdown_recovery_chance must be between 0 and 1")
        if not (0 <= fight.get("submission_escape_base", 0) <= 1):
            errors.append("fight.submission_escape_base must be between 0 and 1")
        if fight.get("doctor_stoppage_threshold", 0) <= 0:
            errors.append("fight.doctor_stoppage_threshold must be positive")
        
        # =====================================================================
        # INJURY VALIDATIONS
        # =====================================================================
        injury = self.section("injury")
        
        if not (0 <= injury.get("fight_injury_chance", 0) <= 1):
            errors.append("injury.fight_injury_chance must be between 0 and 1")
        if not (0 <= injury.get("training_injury_chance", 0) <= 1):
            errors.append("injury.training_injury_chance must be between 0 and 1")
        if injury.get("ko_injury_multiplier", 0) < 1:
            errors.append("injury.ko_injury_multiplier must be >= 1")
        
        # =====================================================================
        # TIME VALIDATIONS
        # =====================================================================
        time_cfg = self.section("time")
        
        if time_cfg.get("weeks_per_year", 0) != 52:
            errors.append("time.weeks_per_year should be 52")
        if time_cfg.get("min_weeks_between_fights", 0) <= 0:
            errors.append("time.min_weeks_between_fights must be positive")
        if time_cfg.get("min_weeks_between_fights", 0) > time_cfg.get("preferred_weeks_between", 0):
            errors.append("time.min_weeks_between_fights must be <= preferred_weeks_between")
        
        # =====================================================================
        # SIMULATION VALIDATIONS
        # =====================================================================
        sim = self.section("simulation")
        
        if sim.get("auto_save_weeks", 0) <= 0:
            errors.append("simulation.auto_save_weeks must be positive")
        if sim.get("max_history_events", 0) <= 0:
            errors.append("simulation.max_history_events must be positive")
        
        return errors
    
    def validate_or_raise(self) -> None:
        """
        Validate configuration and raise exception if invalid.
        
        Raises:
            ValueError: If configuration has errors
        """
        errors = self.validate()
        if errors:
            error_list = "\n  - ".join(errors)
            raise ValueError(f"Configuration validation failed:\n  - {error_list}")
    
    def is_valid(self) -> bool:
        """Check if configuration is valid without returning errors."""
        return len(self.validate()) == 0
    
    def __repr__(self) -> str:
        sections = list(self._config.keys())
        return f"GameConfig(sections={sections})"


# ============================================================================
# GLOBAL CONFIG INSTANCE
# ============================================================================

# Singleton instance for the entire game
config = GameConfig()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_config(path: str, default: Any = None) -> Any:
    """Get a configuration value from the global config"""
    return config.get(path, default)


def set_config(path: str, value: Any) -> None:
    """Set a configuration value in the global config"""
    config.set(path, value)


def validate_config(raise_on_error: bool = False) -> List[str]:
    """
    Validate the global configuration.
    
    Call this on game startup to catch config errors early.
    
    Args:
        raise_on_error: If True, raise ValueError on invalid config
        
    Returns:
        List of error messages (empty if valid)
        
    Raises:
        ValueError: If raise_on_error=True and config is invalid
        
    Example:
        # On game startup
        errors = validate_config()
        if errors:
            print("Config errors:", errors)
            
        # Or strict mode
        validate_config(raise_on_error=True)  # Raises if invalid
    """
    if raise_on_error:
        config.validate_or_raise()
        return []
    return config.validate()


def config_is_valid() -> bool:
    """Quick check if global config is valid."""
    return config.is_valid()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Constants
    "DEFAULT_CONFIG",
    
    # Classes
    "GameConfig",
    
    # Global instance
    "config",
    
    # Convenience functions
    "get_config",
    "set_config",
    "validate_config",
    "config_is_valid",
]
