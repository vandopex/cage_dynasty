# tests/test_config.py
# Tests for Module 3: Configuration Manager
# Lines: 234

"""
Comprehensive tests for core/config.py

Run with: python3 -m pytest tests/test_config.py -v
"""

import pytest
import json
import tempfile
from pathlib import Path
from core.config import (
    GameConfig, config, DEFAULT_CONFIG,
    get_config, set_config
)


class TestDefaultConfig:
    """Tests for default configuration values"""
    
    def test_default_config_has_all_sections(self):
        """Default config should have all required sections"""
        required_sections = [
            "aging", "generation", "training", "camp",
            "economy", "rankings", "fight", "injury",
            "rivalry", "time", "simulation"
        ]
        
        for section in required_sections:
            assert section in DEFAULT_CONFIG, f"Missing section: {section}"
    
    def test_aging_defaults_are_sensible(self):
        """Aging values should make logical sense"""
        aging = DEFAULT_CONFIG["aging"]
        
        assert aging["prime_start"] < aging["prime_end"]
        assert aging["prime_end"] < aging["decline_start"]
        assert aging["decline_start"] < aging["retirement_avg"]
        assert aging["retirement_min"] < aging["retirement_max"]
    
    def test_training_defaults_are_sensible(self):
        """Training values should make logical sense"""
        training = DEFAULT_CONFIG["training"]
        
        assert training["max_gain_per_week"] > 0
        assert training["max_gain_per_camp"] >= training["max_gain_per_week"]
        assert training["weeks_per_camp"] > 0
    
    def test_camp_tiers_are_ordered(self):
        """Camp costs should increase with tier"""
        camp = DEFAULT_CONFIG["camp"]
        tier_costs = camp["tier_costs"]
        
        prev_cost = 0
        for tier in range(1, 6):
            assert tier_costs[tier] > prev_cost
            prev_cost = tier_costs[tier]


class TestGameConfig:
    """Tests for GameConfig class"""
    
    @pytest.fixture
    def cfg(self):
        """Create a fresh config for each test"""
        return GameConfig()
    
    def test_initialization_with_defaults(self, cfg):
        """Config should initialize with default values"""
        assert cfg.get("aging.prime_start") == 26
        assert cfg.get("training.weeks_per_camp") == 8
        assert cfg.get("fight.rounds_standard") == 3
    
    def test_initialization_with_overrides(self):
        """Config should accept initial overrides"""
        overrides = {
            "aging": {"prime_start": 25},
            "training": {"max_gain_per_week": 3}
        }
        
        cfg = GameConfig(overrides)
        
        assert cfg.get("aging.prime_start") == 25  # Overridden
        assert cfg.get("aging.prime_end") == 32    # Default preserved
        assert cfg.get("training.max_gain_per_week") == 3  # Overridden
    
    def test_get_with_valid_path(self, cfg):
        """get() should return values for valid paths"""
        assert cfg.get("aging.prime_start") == 26
        assert cfg.get("economy.purse_minimum") == 5000
        assert cfg.get("fight.rounds_championship") == 5
    
    def test_get_with_invalid_path(self, cfg):
        """get() should return default for invalid paths"""
        assert cfg.get("invalid.path") is None
        assert cfg.get("invalid.path", "default") == "default"
        assert cfg.get("aging.nonexistent", 42) == 42
    
    def test_get_nested_dict(self, cfg):
        """get() should work with nested dictionaries"""
        coach_mult = cfg.get("training.coach_quality_multiplier")
        assert isinstance(coach_mult, dict)
        assert coach_mult[5] == 1.5  # Elite coach
    
    def test_set_existing_value(self, cfg):
        """set() should update existing values"""
        cfg.set("aging.prime_start", 28)
        assert cfg.get("aging.prime_start") == 28
    
    def test_set_creates_path(self, cfg):
        """set() should create path if it doesn't exist"""
        cfg.set("custom.new.path", "value")
        assert cfg.get("custom.new.path") == "value"
    
    def test_section_returns_copy(self, cfg):
        """section() should return a copy, not reference"""
        aging = cfg.section("aging")
        aging["prime_start"] = 999
        
        # Original should be unchanged
        assert cfg.get("aging.prime_start") == 26
    
    def test_section_with_invalid_name(self, cfg):
        """section() should return empty dict for invalid section"""
        result = cfg.section("nonexistent")
        assert result == {}
    
    def test_update_section(self, cfg):
        """update_section() should update multiple values"""
        cfg.update_section("aging", {
            "prime_start": 25,
            "prime_end": 30
        })
        
        assert cfg.get("aging.prime_start") == 25
        assert cfg.get("aging.prime_end") == 30
        # Other values preserved
        assert cfg.get("aging.decline_start") == 33
    
    def test_reset_specific_section(self, cfg):
        """reset() should reset specific section to defaults"""
        cfg.set("aging.prime_start", 999)
        cfg.set("training.max_gain_per_week", 999)
        
        cfg.reset("aging")
        
        assert cfg.get("aging.prime_start") == 26  # Reset
        assert cfg.get("training.max_gain_per_week") == 999  # Unchanged
    
    def test_reset_all(self, cfg):
        """reset() with no args should reset everything"""
        cfg.set("aging.prime_start", 999)
        cfg.set("training.max_gain_per_week", 999)
        
        cfg.reset()
        
        assert cfg.get("aging.prime_start") == 26
        assert cfg.get("training.max_gain_per_week") == 2
    
    def test_to_dict(self, cfg):
        """to_dict() should return full config as dict"""
        result = cfg.to_dict()
        
        assert isinstance(result, dict)
        assert "aging" in result
        assert "training" in result
        assert result["aging"]["prime_start"] == 26
    
    def test_to_dict_returns_copy(self, cfg):
        """to_dict() should return a copy"""
        result = cfg.to_dict()
        result["aging"]["prime_start"] = 999
        
        assert cfg.get("aging.prime_start") == 26
    
    def test_to_json(self, cfg):
        """to_json() should return valid JSON string"""
        result = cfg.to_json()
        
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["aging"]["prime_start"] == 26


class TestConfigPersistence:
    """Tests for save/load functionality"""
    
    def test_save_and_load(self):
        """Config should save and load correctly"""
        cfg = GameConfig()
        cfg.set("aging.prime_start", 28)
        cfg.set("custom.value", "test")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.json"
            cfg.save(filepath)
            
            loaded = GameConfig.load(filepath)
        
        assert loaded.get("aging.prime_start") == 28
        assert loaded.get("custom.value") == "test"
        # Defaults still present
        assert loaded.get("training.max_gain_per_week") == 2
    
    def test_save_creates_directory(self):
        """save() should create parent directories"""
        cfg = GameConfig()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "nested" / "dir" / "config.json"
            cfg.save(filepath)
            
            assert filepath.exists()
    
    def test_load_nonexistent_file(self):
        """load() should raise error for missing file"""
        with pytest.raises(FileNotFoundError):
            GameConfig.load("/nonexistent/path/config.json")


class TestConfigValidation:
    """Tests for configuration validation"""
    
    def test_valid_config_passes(self):
        """Default config should pass validation"""
        cfg = GameConfig()
        errors = cfg.validate()
        assert len(errors) == 0
    
    def test_invalid_aging_detected(self):
        """Validation should catch invalid aging values"""
        cfg = GameConfig()
        cfg.set("aging.prime_start", 35)  # After prime_end
        
        errors = cfg.validate()
        assert any("prime_start" in e for e in errors)
    
    def test_invalid_training_detected(self):
        """Validation should catch invalid training values"""
        cfg = GameConfig()
        cfg.set("training.max_gain_per_week", 0)
        
        errors = cfg.validate()
        assert any("max_gain_per_week" in e for e in errors)
    
    def test_invalid_economy_detected(self):
        """Validation should catch invalid economy values"""
        cfg = GameConfig()
        cfg.set("economy.purse_minimum", -100)
        
        errors = cfg.validate()
        assert any("purse_minimum" in e for e in errors)
    
    def test_invalid_fight_detected(self):
        """Validation should catch invalid fight values"""
        cfg = GameConfig()
        cfg.set("fight.rounds_championship", 2)  # Less than standard
        
        errors = cfg.validate()
        assert any("rounds_championship" in e for e in errors)


class TestGlobalConfig:
    """Tests for global config instance and convenience functions"""
    
    def test_global_config_exists(self):
        """Global config instance should exist"""
        assert config is not None
        assert isinstance(config, GameConfig)
    
    def test_get_config_function(self):
        """get_config() should work with global instance"""
        result = get_config("aging.prime_start")
        assert result == 26
    
    def test_set_config_function(self):
        """set_config() should work with global instance"""
        original = get_config("aging.prime_start")
        
        set_config("aging.prime_start", 99)
        assert get_config("aging.prime_start") == 99
        
        # Restore
        set_config("aging.prime_start", original)
    
    def test_config_repr(self):
        """Config should have readable repr"""
        cfg = GameConfig()
        repr_str = repr(cfg)
        
        assert "GameConfig" in repr_str
        assert "sections" in repr_str


class TestConfigIsolation:
    """Tests to ensure config instances are isolated"""
    
    def test_separate_instances_are_independent(self):
        """Different GameConfig instances should be independent"""
        cfg1 = GameConfig()
        cfg2 = GameConfig()
        
        cfg1.set("aging.prime_start", 100)
        
        assert cfg1.get("aging.prime_start") == 100
        assert cfg2.get("aging.prime_start") == 26  # Unchanged
    
    def test_defaults_not_modified(self):
        """Modifying config should not affect DEFAULT_CONFIG"""
        original = DEFAULT_CONFIG["aging"]["prime_start"]
        
        cfg = GameConfig()
        cfg.set("aging.prime_start", 999)
        
        assert DEFAULT_CONFIG["aging"]["prime_start"] == original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
