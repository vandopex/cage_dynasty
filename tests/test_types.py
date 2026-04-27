# tests/test_types.py
# Tests for Module 1: Core Data Types
# Lines: 250

"""
Comprehensive tests for core/types.py

Run with: python3 -m pytest tests/test_types.py -v
"""

import pytest
from datetime import date
from core.types import (
    # Enums
    WeightClass, FightOutcome, FighterStatus, CampTier, CampCulture,
    RivalryIntensity, InjuryType, EventType, ContractStatus,
    
    # Data classes
    WeightClassSpec, FightRecord, FightResultData, AttributeSet,
    
    # Constants
    WEIGHT_CLASS_SPECS, WEIGHT_CLASS_ORDER, ALL_ATTRIBUTES,
    PHYSICAL_ATTRIBUTES, STRIKING_ATTRIBUTES, GRAPPLING_ATTRIBUTES,
    MENTAL_ATTRIBUTES, ATTR_MIN, ATTR_MAX, ATTR_AVERAGE,
    AGE_PRIME_START, AGE_PRIME_END, AGE_DECLINE_START,
    
    # Functions
    clamp, clamp_attribute, calculate_age, format_money, format_record,
    get_weight_class_for_weight, weight_classes_adjacent,
    validate_fighter_name, validate_weight, validate_attribute_dict,
)


class TestWeightClasses:
    """Tests for weight class definitions and utilities"""
    
    def test_all_weight_classes_have_specs(self):
        """Every weight class enum should have a corresponding spec"""
        for wc in WeightClass:
            assert wc in WEIGHT_CLASS_SPECS, f"Missing spec for {wc}"
    
    def test_weight_class_order_complete(self):
        """Weight class order should include all classes"""
        assert len(WEIGHT_CLASS_ORDER) == len(WeightClass)
        for wc in WeightClass:
            assert wc in WEIGHT_CLASS_ORDER
    
    def test_weight_class_order_ascending(self):
        """Weight classes should be ordered from lightest to heaviest"""
        prev_max = 0
        for wc in WEIGHT_CLASS_ORDER:
            spec = WEIGHT_CLASS_SPECS[wc]
            assert spec.min_weight > prev_max, f"{wc} not in ascending order"
            prev_max = spec.max_weight
    
    def test_weight_class_ranges_valid(self):
        """Each weight class should have min < max"""
        for wc, spec in WEIGHT_CLASS_SPECS.items():
            assert spec.min_weight < spec.max_weight, f"Invalid range for {wc}"
            # Natural weight should exceed fight weight (except heavyweight has no upper limit)
            if wc != WeightClass.HEAVYWEIGHT:
                assert spec.natural_weight_avg > spec.max_weight, \
                    f"Natural weight should exceed fight weight for {wc}"
    
    def test_get_weight_class_for_weight(self):
        """Should return correct weight class for given weight"""
        assert get_weight_class_for_weight(125) == WeightClass.FLYWEIGHT
        assert get_weight_class_for_weight(155) == WeightClass.LIGHTWEIGHT
        assert get_weight_class_for_weight(185) == WeightClass.MIDDLEWEIGHT
        assert get_weight_class_for_weight(265) == WeightClass.HEAVYWEIGHT
    
    def test_get_weight_class_overweight(self):
        """Overweight fighters should be placed in heavyweight"""
        assert get_weight_class_for_weight(280) == WeightClass.HEAVYWEIGHT
        assert get_weight_class_for_weight(300) == WeightClass.HEAVYWEIGHT
    
    def test_weight_classes_adjacent(self):
        """Should correctly identify adjacent weight classes"""
        assert weight_classes_adjacent(
            WeightClass.LIGHTWEIGHT, WeightClass.WELTERWEIGHT
        )
        assert weight_classes_adjacent(
            WeightClass.FEATHERWEIGHT, WeightClass.LIGHTWEIGHT
        )
        assert not weight_classes_adjacent(
            WeightClass.FLYWEIGHT, WeightClass.WELTERWEIGHT
        )


class TestFightRecord:
    """Tests for FightRecord data class"""
    
    def test_default_record(self):
        """New record should be all zeros"""
        record = FightRecord()
        assert record.wins == 0
        assert record.losses == 0
        assert record.draws == 0
        assert record.total_fights == 0
    
    def test_record_with_values(self):
        """Record should store provided values"""
        record = FightRecord(wins=10, losses=2, draws=1)
        assert record.wins == 10
        assert record.losses == 2
        assert record.draws == 1
        assert record.total_fights == 13
    
    def test_win_percentage(self):
        """Win percentage should calculate correctly"""
        record = FightRecord(wins=8, losses=2)
        assert record.win_percentage == 80.0
        
        empty = FightRecord()
        assert empty.win_percentage == 0.0
    
    def test_record_immutability(self):
        """FightRecord should be immutable"""
        record = FightRecord(wins=5, losses=2)
        with pytest.raises(Exception):  # frozen dataclass raises error
            record.wins = 6
    
    def test_with_win(self):
        """with_win should return new record with incremented wins"""
        original = FightRecord(wins=5, losses=2)
        updated = original.with_win()
        
        assert original.wins == 5  # Original unchanged
        assert updated.wins == 6
        assert updated.losses == 2
    
    def test_with_loss(self):
        """with_loss should return new record with incremented losses"""
        original = FightRecord(wins=5, losses=2)
        updated = original.with_loss()
        
        assert original.losses == 2
        assert updated.losses == 3
        assert updated.wins == 5
    
    def test_record_string_format(self):
        """String representation should be standard format"""
        assert str(FightRecord(wins=10, losses=2)) == "10-2"
        assert str(FightRecord(wins=10, losses=2, draws=1)) == "10-2-1"


class TestAttributeSet:
    """Tests for AttributeSet data class"""
    
    def test_default_attributes(self):
        """Default attributes should all be average (50)"""
        attrs = AttributeSet()
        for attr_name in ALL_ATTRIBUTES:
            assert attrs.get(attr_name) == ATTR_AVERAGE
    
    def test_custom_attributes(self):
        """Should accept custom attribute values"""
        attrs = AttributeSet(strength=80, speed=70, boxing=90)
        assert attrs.strength == 80
        assert attrs.speed == 70
        assert attrs.boxing == 90
        assert attrs.cardio == ATTR_AVERAGE  # Unchanged
    
    def test_overall_calculation(self):
        """Overall should be average of all attributes"""
        # All at 50 = overall 50
        attrs = AttributeSet()
        assert attrs.overall == 50
        
        # All at 100 = overall 100
        all_max = {attr: 100 for attr in ALL_ATTRIBUTES}
        attrs_max = AttributeSet(**all_max)
        assert attrs_max.overall == 100
    
    def test_striking_overall(self):
        """Striking overall should average striking attributes"""
        attrs = AttributeSet(boxing=100, kicks=100, clinch=100, power=100, accuracy=100)
        assert attrs.striking_overall == 100
    
    def test_grappling_overall(self):
        """Grappling overall should average grappling attributes"""
        attrs = AttributeSet(wrestling=80, bjj=80, td_defense=80, 
                            top_control=80, submissions=80)
        assert attrs.grappling_overall == 80
    
    def test_with_change(self):
        """with_change should return new AttributeSet with modified value"""
        original = AttributeSet(boxing=50)
        updated = original.with_change("boxing", 75)
        
        assert original.boxing == 50  # Original unchanged
        assert updated.boxing == 75
    
    def test_with_change_clamps_values(self):
        """with_change should clamp values to valid range"""
        attrs = AttributeSet()
        
        too_high = attrs.with_change("boxing", 150)
        assert too_high.boxing == ATTR_MAX
        
        too_low = attrs.with_change("boxing", -10)
        assert too_low.boxing == ATTR_MIN
    
    def test_attribute_immutability(self):
        """AttributeSet should be immutable"""
        attrs = AttributeSet(boxing=80)
        with pytest.raises(Exception):
            attrs.boxing = 90


class TestUtilityFunctions:
    """Tests for utility functions"""
    
    def test_clamp(self):
        """clamp should constrain values to range"""
        assert clamp(50, 0, 100) == 50
        assert clamp(-10, 0, 100) == 0
        assert clamp(150, 0, 100) == 100
    
    def test_clamp_attribute(self):
        """clamp_attribute should use attribute range (1-100)"""
        assert clamp_attribute(50) == 50
        assert clamp_attribute(0) == ATTR_MIN
        assert clamp_attribute(150) == ATTR_MAX
    
    def test_calculate_age(self):
        """calculate_age should return correct age"""
        birth = date(1990, 6, 15)
        reference = date(2024, 1, 1)
        assert calculate_age(birth, reference) == 33
        
        # Birthday not yet occurred in reference year
        reference_before = date(2024, 6, 1)
        assert calculate_age(birth, reference_before) == 33
        
        # After birthday
        reference_after = date(2024, 7, 1)
        assert calculate_age(birth, reference_after) == 34
    
    def test_format_money(self):
        """format_money should format currency correctly"""
        assert format_money(1_500_000) == "$1.5M"
        assert format_money(1_000_000) == "$1.0M"
        assert format_money(750_000) == "$750K"  # Under 1M shows as K
        assert format_money(75_000) == "$75K"
        assert format_money(5_000) == "$5K"
        assert format_money(500) == "$500"


class TestValidationFunctions:
    """Tests for validation functions"""
    
    def test_validate_fighter_name_valid(self):
        """Valid names should pass validation"""
        assert validate_fighter_name("John Smith") == "John Smith"
        assert validate_fighter_name("  John Smith  ") == "John Smith"  # Trimmed
        assert validate_fighter_name("Jean-Claude") == "Jean-Claude"
        assert validate_fighter_name("O'Brien") == "O'Brien"
    
    def test_validate_fighter_name_empty(self):
        """Empty names should raise ValueError"""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_fighter_name("")
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_fighter_name("   ")
    
    def test_validate_fighter_name_too_long(self):
        """Names over 50 chars should raise ValueError"""
        long_name = "A" * 51
        with pytest.raises(ValueError, match="cannot exceed 50"):
            validate_fighter_name(long_name)
    
    def test_validate_fighter_name_invalid_chars(self):
        """Names with invalid characters should raise ValueError"""
        with pytest.raises(ValueError, match="invalid characters"):
            validate_fighter_name("John123")
        with pytest.raises(ValueError, match="invalid characters"):
            validate_fighter_name("John@Smith")
    
    def test_validate_weight_valid(self):
        """Valid weights should pass validation"""
        assert validate_weight(155) == 155
        assert validate_weight(265) == 265
    
    def test_validate_weight_out_of_range(self):
        """Weights outside realistic range should raise ValueError"""
        with pytest.raises(ValueError, match="must be between"):
            validate_weight(50)
        with pytest.raises(ValueError, match="must be between"):
            validate_weight(350)
    
    def test_validate_weight_with_class(self):
        """Weight exceeding class limit should raise ValueError"""
        with pytest.raises(ValueError, match="exceeds"):
            validate_weight(160, WeightClass.LIGHTWEIGHT)  # Limit is 155
    
    def test_validate_attribute_dict(self):
        """Should clamp all values and fill missing attributes"""
        input_dict = {"strength": 150, "speed": -10, "boxing": 80}
        result = validate_attribute_dict(input_dict)
        
        assert result["strength"] == ATTR_MAX  # Clamped from 150
        assert result["speed"] == ATTR_MIN    # Clamped from -10
        assert result["boxing"] == 80         # Unchanged
        assert result["cardio"] == ATTR_AVERAGE  # Missing, filled with default


class TestEnums:
    """Tests for enum completeness and values"""
    
    def test_fight_outcome_values(self):
        """FightOutcome should have all standard MMA outcomes"""
        outcomes = [o.value for o in FightOutcome]
        assert "KO" in outcomes
        assert "TKO" in outcomes
        assert "Submission" in outcomes
        assert "Unanimous Decision" in outcomes
    
    def test_fighter_status_values(self):
        """FighterStatus should cover all possible states"""
        statuses = list(FighterStatus)
        assert len(statuses) >= 5  # At minimum: active, injured, suspended, retired, free agent
    
    def test_camp_tier_ordering(self):
        """CampTier values should be ordered 1-5"""
        assert CampTier.GARAGE.value == 1
        assert CampTier.ELITE.value == 5
    
    def test_event_types_complete(self):
        """EventType should cover major game events"""
        event_names = [e.name for e in EventType]
        assert "FIGHT_COMPLETED" in event_names
        assert "FIGHTER_SIGNED" in event_names
        assert "TITLE_WON" in event_names
        assert "WEEK_ADVANCED" in event_names


class TestAttributeCategories:
    """Tests for attribute category definitions"""
    
    def test_no_duplicate_attributes(self):
        """Each attribute should appear in only one category"""
        all_attrs = set(ALL_ATTRIBUTES)
        physical = set(PHYSICAL_ATTRIBUTES)
        striking = set(STRIKING_ATTRIBUTES)
        grappling = set(GRAPPLING_ATTRIBUTES)
        mental = set(MENTAL_ATTRIBUTES)
        
        # Check no overlaps
        assert len(physical & striking) == 0
        assert len(physical & grappling) == 0
        assert len(physical & mental) == 0
        assert len(striking & grappling) == 0
        assert len(striking & mental) == 0
        assert len(grappling & mental) == 0
    
    def test_all_attributes_categorized(self):
        """ALL_ATTRIBUTES should be union of all categories"""
        combined = set(
            PHYSICAL_ATTRIBUTES + STRIKING_ATTRIBUTES + 
            GRAPPLING_ATTRIBUTES + MENTAL_ATTRIBUTES
        )
        assert combined == set(ALL_ATTRIBUTES)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
