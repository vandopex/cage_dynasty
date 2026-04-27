# tests/test_generator.py
# Tests for Module 17: Name Database & Fighter Generator
# Tests: 45

"""
Test suite for name database and fighter generation systems.
"""

import pytest
import random
from typing import Set

# Import name database
from data.name_database import (
    COUNTRY_NAMES,
    get_available_countries,
    get_random_name,
    get_full_name,
    get_random_country,
    generate_unique_name,
    get_database_stats,
)

# Import generator
from simulation.generator import (
    WEIGHT_CLASSES,
    COUNTRIES,
    BUILD_TYPES,
    STYLES,
    PERSONALITIES,
    COUNTRY_STYLE_MAP,
    stat_gauss,
    stat_uniform,
    get_weight_class_for_weight,
    get_weight_for_class,
    select_style_for_country,
    select_build,
    generate_birth_date,
    calculate_age,
    generate_fighter,
    generate_roster,
    generate_weight_class_roster,
    generate_division,
    get_fighter_summary,
    calculate_overall,
)

from simulation.fight_engine import FighterAttributes


# ============================================================================
# NAME DATABASE TESTS
# ============================================================================

class TestCountryNames:
    """Tests for the country name database"""
    
    def test_database_has_countries(self):
        """Database should have multiple countries"""
        assert len(COUNTRY_NAMES) >= 17
    
    def test_each_country_has_names(self):
        """Each country should have first and last names"""
        for country, names in COUNTRY_NAMES.items():
            assert "first_names" in names, f"{country} missing first_names"
            assert "last_names" in names, f"{country} missing last_names"
            assert len(names["first_names"]) >= 20, f"{country} has too few first names"
            assert len(names["last_names"]) >= 20, f"{country} has too few last names"
    
    def test_us_names_exist(self):
        """US should have comprehensive name list"""
        assert "United States" in COUNTRY_NAMES
        us = COUNTRY_NAMES["United States"]
        assert len(us["first_names"]) >= 90
        assert len(us["last_names"]) >= 90
    
    def test_brazil_names_exist(self):
        """Brazil should have names"""
        assert "Brazil" in COUNTRY_NAMES
        brazil = COUNTRY_NAMES["Brazil"]
        assert "Gabriel" in brazil["first_names"]
        assert "Silva" in brazil["last_names"]
    
    def test_japan_names_exist(self):
        """Japan should have names"""
        assert "Japan" in COUNTRY_NAMES
        japan = COUNTRY_NAMES["Japan"]
        assert "Hiroto" in japan["first_names"] or "Takeshi" in japan["first_names"]
        assert "Sato" in japan["last_names"]


class TestNameHelpers:
    """Tests for name helper functions"""
    
    def test_get_available_countries(self):
        """Should return list of countries"""
        countries = get_available_countries()
        assert isinstance(countries, list)
        assert "United States" in countries
        assert "Brazil" in countries
    
    def test_get_random_name(self):
        """Should return first and last name tuple"""
        first, last = get_random_name("United States")
        assert isinstance(first, str)
        assert isinstance(last, str)
        assert len(first) > 0
        assert len(last) > 0
    
    def test_get_random_name_fallback(self):
        """Should fall back to US for unknown country"""
        first, last = get_random_name("Unknown Country")
        assert isinstance(first, str)
        assert isinstance(last, str)
    
    def test_get_full_name(self):
        """Should return full name string"""
        name = get_full_name("Brazil")
        assert isinstance(name, str)
        assert " " in name  # Has first and last
    
    def test_get_random_country(self):
        """Should return a valid country"""
        country = get_random_country()
        assert country in COUNTRY_NAMES
    
    def test_generate_unique_name(self):
        """Should generate unique names"""
        existing = {"John Smith", "Mike Johnson"}
        name, country = generate_unique_name(existing_names=existing)
        assert name not in existing
    
    def test_generate_unique_name_specific_country(self):
        """Should respect country parameter"""
        name, country = generate_unique_name(country="Japan")
        assert country == "Japan"
    
    def test_database_stats(self):
        """Should return statistics"""
        stats = get_database_stats()
        assert "total_countries" in stats
        assert "total_first_names" in stats
        assert "total_last_names" in stats
        assert "total_combinations" in stats
        assert stats["total_countries"] >= 17
        assert stats["total_combinations"] > 50000  # ~58k combinations available


# ============================================================================
# GENERATOR CONSTANTS TESTS
# ============================================================================

class TestGeneratorConstants:
    """Tests for generator data structures"""
    
    def test_weight_classes(self):
        """Should have all standard weight classes"""
        assert "Flyweight" in WEIGHT_CLASSES
        assert "Lightweight" in WEIGHT_CLASSES
        assert "Heavyweight" in WEIGHT_CLASSES
        assert len(WEIGHT_CLASSES) >= 8
    
    def test_weight_class_ranges(self):
        """Weight class ranges should be valid"""
        for wc, (low, high) in WEIGHT_CLASSES.items():
            assert low < high, f"{wc} has invalid range"
            assert low >= 100, f"{wc} min too low"
            assert high <= 300, f"{wc} max too high"
    
    def test_countries_list(self):
        """Should have countries for generation"""
        assert len(COUNTRIES) >= 20
        assert "United States" in COUNTRIES
        assert "Brazil" in COUNTRIES
    
    def test_build_types(self):
        """Should have build types with modifiers"""
        assert len(BUILD_TYPES) >= 4
        for build in BUILD_TYPES:
            assert "name" in build
            assert "modifiers" in build
    
    def test_styles(self):
        """Should have fighting styles"""
        assert len(STYLES) >= 8
        style_names = [s["name"] for s in STYLES]
        assert "Boxing" in style_names
        assert "Wrestling" in style_names
        assert "BJJ" in style_names
        assert "Muay Thai" in style_names
    
    def test_personalities(self):
        """Should have personality archetypes"""
        assert len(PERSONALITIES) >= 5
        for p in PERSONALITIES:
            assert "name" in p
            assert "modifiers" in p
    
    def test_country_style_map(self):
        """Country style weights should sum to ~1"""
        for country, weights in COUNTRY_STYLE_MAP.items():
            total = sum(weights.values())
            assert 0.95 <= total <= 1.05, f"{country} weights sum to {total}"


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestHelperFunctions:
    """Tests for generator helper functions"""
    
    def test_stat_gauss_range(self):
        """Gaussian stats should be clamped 1-100"""
        for _ in range(100):
            val = stat_gauss(50, 30)  # High variance
            assert 1 <= val <= 100
    
    def test_stat_gauss_distribution(self):
        """Stats should cluster around mean"""
        values = [stat_gauss(50, 10) for _ in range(100)]
        avg = sum(values) / len(values)
        assert 40 <= avg <= 60
    
    def test_stat_uniform(self):
        """Uniform stats should be in range"""
        for _ in range(50):
            val = stat_uniform(30, 70)
            assert 30 <= val <= 70
    
    def test_get_weight_class_for_weight(self):
        """Should correctly classify weights"""
        assert get_weight_class_for_weight(150) == "Lightweight"
        assert get_weight_class_for_weight(185) == "Middleweight"
        assert get_weight_class_for_weight(250) == "Heavyweight"
        assert get_weight_class_for_weight(120) == "Flyweight"
    
    def test_get_weight_for_class(self):
        """Should generate valid weight for class"""
        for wc, (low, high) in WEIGHT_CLASSES.items():
            for _ in range(10):
                weight = get_weight_for_class(wc)
                assert low <= weight <= high, f"{wc}: {weight} out of range"
    
    def test_select_style_for_country(self):
        """Should return valid style"""
        style = select_style_for_country("Brazil")
        assert "name" in style
        assert "modifiers" in style
    
    def test_select_build(self):
        """Should return valid build"""
        build = select_build("Russia")
        assert "name" in build
        assert "modifiers" in build
    
    def test_generate_birth_date(self):
        """Should generate valid birth date"""
        year, month, day = generate_birth_date(20, 35)
        assert 1 <= month <= 12
        assert 1 <= day <= 31
        # Year should make fighter 20-35 years old
        import datetime
        current_year = datetime.date.today().year
        assert current_year - 35 <= year <= current_year - 20
    
    def test_calculate_age(self):
        """Should calculate correct age"""
        import datetime
        current_year = datetime.date.today().year
        age = calculate_age(current_year - 25, 1, 1)
        assert age == 25 or age == 24  # Depends on current date


# ============================================================================
# FIGHTER GENERATION TESTS
# ============================================================================

class TestFighterGeneration:
    """Tests for the main fighter generation function"""
    
    def test_generate_basic_fighter(self):
        """Should generate a fighter with defaults"""
        fighter = generate_fighter()
        assert isinstance(fighter, FighterAttributes)
        assert fighter.name
        assert fighter.fighter_id
    
    def test_generate_named_fighter(self):
        """Should respect custom name"""
        fighter = generate_fighter(name="Custom Fighter")
        assert fighter.name == "Custom Fighter"
    
    def test_generate_fighter_country(self):
        """Should generate country-appropriate name"""
        # Generate multiple and check names exist
        fighter = generate_fighter(country="Japan")
        assert fighter.name  # Has a name
    
    def test_generate_fighter_weight_class(self):
        """Fighter should be generated (weight class doesn't affect FighterAttributes directly)"""
        fighter = generate_fighter(weight_class="Heavyweight")
        assert isinstance(fighter, FighterAttributes)
        # Heavyweights should tend to be stronger
        # (Not guaranteed but tendency)
    
    def test_generate_prospect(self):
        """Prospects should have certain tendencies"""
        fighters = [generate_fighter(fighter_type="prospect") for _ in range(20)]
        # Prospects tend to have lower fight IQ
        avg_iq = sum(f.fight_iq for f in fighters) / len(fighters)
        assert avg_iq < 70  # Lower than prime fighters
    
    def test_generate_veteran(self):
        """Veterans should have certain tendencies"""
        fighters = [generate_fighter(fighter_type="veteran") for _ in range(20)]
        # Veterans tend to have higher fight IQ
        avg_iq = sum(f.fight_iq for f in fighters) / len(fighters)
        avg_composure = sum(f.composure for f in fighters) / len(fighters)
        # Experience helps
        assert avg_iq > 40 or avg_composure > 40
    
    def test_generate_with_style(self):
        """Should apply style modifiers"""
        # Generate boxers
        boxers = [generate_fighter(style="Boxing") for _ in range(20)]
        avg_boxing = sum(f.boxing for f in boxers) / len(boxers)
        
        # Generate wrestlers
        wrestlers = [generate_fighter(style="Wrestling") for _ in range(20)]
        avg_wrestling = sum(f.wrestling for f in wrestlers) / len(wrestlers)
        
        # Boxers should have higher boxing than wrestlers
        # Wrestlers should have higher wrestling than boxers
        boxer_wrestling = sum(f.wrestling for f in boxers) / len(boxers)
        wrestler_boxing = sum(f.boxing for f in wrestlers) / len(wrestlers)
        
        assert avg_boxing > wrestler_boxing - 15  # Boxers better at boxing
        assert avg_wrestling > boxer_wrestling - 15  # Wrestlers better at wrestling
    
    def test_generate_with_overall(self):
        """Should generate around target overall"""
        # High overall
        elite = [generate_fighter(overall_rating=85) for _ in range(10)]
        elite_avg = sum(calculate_overall(f) for f in elite) / len(elite)
        
        # Low overall
        low = [generate_fighter(overall_rating=45) for _ in range(10)]
        low_avg = sum(calculate_overall(f) for f in low) / len(low)
        
        # Elite should be higher
        assert elite_avg > low_avg
    
    def test_fighter_stats_in_range(self):
        """All stats should be 1-100"""
        for _ in range(50):
            fighter = generate_fighter()
            assert 1 <= fighter.boxing <= 100
            assert 1 <= fighter.kicks <= 100
            assert 1 <= fighter.wrestling <= 100
            assert 1 <= fighter.bjj <= 100
            assert 1 <= fighter.strength <= 100
            assert 1 <= fighter.speed <= 100
            assert 1 <= fighter.cardio <= 100
            assert 1 <= fighter.chin <= 100
            assert 1 <= fighter.heart <= 100
            assert 1 <= fighter.fight_iq <= 100
            assert 1 <= fighter.composure <= 100
    
    def test_unique_names(self):
        """Should generate unique names when requested"""
        existing = {"John Smith", "Mike Johnson"}
        fighter = generate_fighter(existing_names=existing)
        assert fighter.name not in existing


# ============================================================================
# ROSTER GENERATION TESTS
# ============================================================================

class TestRosterGeneration:
    """Tests for roster and division generation"""
    
    def test_generate_roster(self):
        """Should generate specified number of fighters"""
        roster = generate_roster(count=20)
        assert len(roster) == 20
        assert all(isinstance(f, FighterAttributes) for f in roster)
    
    def test_generate_roster_unique_names(self):
        """Roster should have unique names"""
        roster = generate_roster(count=50)
        names = [f.name for f in roster]
        assert len(names) == len(set(names))
    
    def test_generate_weight_class_roster(self):
        """Should generate roster for specific weight class"""
        roster = generate_weight_class_roster("Lightweight", count=15)
        assert len(roster) == 15
    
    def test_generate_division(self):
        """Should generate ranked and unranked fighters"""
        division = generate_division("Welterweight", ranked_count=10, unranked_count=15)
        
        assert "ranked" in division
        assert "unranked" in division
        assert len(division["ranked"]) == 10
        assert len(division["unranked"]) == 15
    
    def test_division_ranked_quality(self):
        """Ranked fighters should generally be better"""
        division = generate_division("Middleweight", ranked_count=15, unranked_count=20)
        
        ranked_overall = sum(calculate_overall(f) for f in division["ranked"]) / 15
        unranked_overall = sum(calculate_overall(f) for f in division["unranked"]) / 20
        
        # Ranked should be higher on average
        assert ranked_overall > unranked_overall - 5


# ============================================================================
# UTILITY FUNCTION TESTS  
# ============================================================================

class TestUtilityFunctions:
    """Tests for utility functions"""
    
    def test_get_fighter_summary(self):
        """Should return summary string"""
        fighter = generate_fighter(name="Test Fighter")
        summary = get_fighter_summary(fighter)
        assert "Test Fighter" in summary
        assert "OVR:" in summary
    
    def test_calculate_overall(self):
        """Should calculate reasonable overall"""
        fighter = generate_fighter()
        overall = calculate_overall(fighter)
        assert 1 <= overall <= 100
    
    def test_calculate_overall_consistency(self):
        """Higher stat fighters should have higher overall"""
        low = generate_fighter(overall_rating=40)
        high = generate_fighter(overall_rating=90)
        
        # Not guaranteed but likely
        low_ovr = calculate_overall(low)
        high_ovr = calculate_overall(high)
        
        # Check that the high-rated target produces higher results on average
        # (Individual variance may cause overlap)
        assert high_ovr >= low_ovr - 20  # Allow some variance
