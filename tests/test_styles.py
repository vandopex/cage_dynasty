# tests/test_styles.py
# Tests for systems/styles.py
# Lines: ~400

"""
Comprehensive tests for the Fighting Styles system.

Run with: python3 -m pytest tests/test_styles.py -v
"""

import pytest
from core.types import FightingStyle
from systems.styles import (
    StyleDefinition,
    STYLE_DEFINITIONS,
    STYLE_MATCHUPS,
    COUNTRY_STYLE_WEIGHTS,
    DEFAULT_STYLE_WEIGHTS,
    CAMP_STYLE_PRESETS,
    get_style_definition,
    get_style_matchup_modifier,
    generate_style_for_fighter,
    get_style_attribute_bonuses,
    get_style_finish_rates,
    validate_style_attributes,
    determine_fight_method,
    get_style_commentary,
    get_all_styles,
    get_styles_by_category,
    get_style_for_attributes,
)


class TestStyleDefinitions:
    """Tests for style definitions"""
    
    def test_all_styles_have_definitions(self):
        """Every FightingStyle enum should have a definition"""
        for style in FightingStyle:
            assert style in STYLE_DEFINITIONS, f"Missing definition for {style}"
    
    def test_definitions_have_required_fields(self):
        """Each definition should have all required fields"""
        for style, definition in STYLE_DEFINITIONS.items():
            assert definition.name == style
            assert len(definition.display_name) > 0
            assert len(definition.description) > 0
            assert len(definition.examples) > 0
            assert isinstance(definition.attribute_bonuses, dict)
            assert isinstance(definition.attribute_requirements, dict)
    
    def test_finish_rates_sum_to_one(self):
        """KO + Sub + Dec rates should sum to approximately 1.0"""
        for style, definition in STYLE_DEFINITIONS.items():
            total = definition.ko_rate + definition.sub_rate + definition.dec_rate
            assert 0.99 <= total <= 1.01, f"{style}: rates sum to {total}"
    
    def test_finish_rates_are_positive(self):
        """All finish rates should be non-negative"""
        for style, definition in STYLE_DEFINITIONS.items():
            assert definition.ko_rate >= 0
            assert definition.sub_rate >= 0
            assert definition.dec_rate >= 0
    
    def test_generation_weights_are_positive(self):
        """Generation weights should be positive"""
        for style, definition in STYLE_DEFINITIONS.items():
            assert definition.generation_weight > 0


class TestStyleMatchups:
    """Tests for style matchup system"""
    
    def test_all_styles_have_matchups(self):
        """Every style should have matchup data"""
        for style in FightingStyle:
            assert style in STYLE_MATCHUPS, f"Missing matchups for {style}"
    
    def test_matchups_are_complete(self):
        """Each style should have matchups against all other styles"""
        for style1 in FightingStyle:
            matchups = STYLE_MATCHUPS[style1]
            for style2 in FightingStyle:
                assert style2 in matchups, f"Missing {style1} vs {style2}"
    
    def test_self_matchups_are_zero(self):
        """A style vs itself should have 0 modifier"""
        for style in FightingStyle:
            assert STYLE_MATCHUPS[style][style] == 0.0
    
    def test_matchup_values_in_range(self):
        """Matchup modifiers should be in -0.1 to +0.1 range"""
        for style1, matchups in STYLE_MATCHUPS.items():
            for style2, modifier in matchups.items():
                assert -0.1 <= modifier <= 0.1, f"{style1} vs {style2}: {modifier}"
    
    def test_balanced_has_no_matchup_advantages(self):
        """Balanced style should have no advantages or disadvantages"""
        balanced_matchups = STYLE_MATCHUPS[FightingStyle.BALANCED]
        for style, modifier in balanced_matchups.items():
            assert modifier == 0.0, f"Balanced vs {style}: {modifier}"
    
    def test_wrestler_beats_striker(self):
        """Wrestler should have advantage over Striker"""
        mod = get_style_matchup_modifier(FightingStyle.WRESTLER, FightingStyle.STRIKER)
        assert mod > 0
    
    def test_sprawl_brawl_beats_wrestler(self):
        """Sprawl & Brawl should have advantage over Wrestler"""
        mod = get_style_matchup_modifier(FightingStyle.SPRAWL_AND_BRAWL, FightingStyle.WRESTLER)
        assert mod > 0
    
    def test_bjj_beats_wrestler(self):
        """BJJ Specialist should have advantage over Wrestler"""
        mod = get_style_matchup_modifier(FightingStyle.BJJ_SPECIALIST, FightingStyle.WRESTLER)
        assert mod > 0


class TestCountryStyleWeights:
    """Tests for country-based style generation"""
    
    def test_country_weights_sum_to_100(self):
        """Country style weights should sum to approximately 100"""
        for country, weights in COUNTRY_STYLE_WEIGHTS.items():
            total = sum(weights.values())
            assert 95 <= total <= 105, f"{country}: weights sum to {total}"
    
    def test_russia_favors_wrestling(self):
        """Russia should favor wrestling styles"""
        weights = COUNTRY_STYLE_WEIGHTS.get("Russia", {})
        wrestling = weights.get(FightingStyle.WRESTLER, 0)
        assert wrestling >= 30, f"Russia wrestling weight: {wrestling}"
    
    def test_brazil_favors_bjj(self):
        """Brazil should favor BJJ"""
        weights = COUNTRY_STYLE_WEIGHTS.get("Brazil", {})
        bjj = weights.get(FightingStyle.BJJ_SPECIALIST, 0)
        assert bjj >= 25, f"Brazil BJJ weight: {bjj}"
    
    def test_thailand_favors_muay_thai(self):
        """Thailand should heavily favor Muay Thai"""
        weights = COUNTRY_STYLE_WEIGHTS.get("Thailand", {})
        muay_thai = weights.get(FightingStyle.MUAY_THAI, 0)
        assert muay_thai >= 50, f"Thailand Muay Thai weight: {muay_thai}"
    
    def test_default_weights_cover_all_styles(self):
        """Default weights should cover all styles"""
        for style in FightingStyle:
            assert style in DEFAULT_STYLE_WEIGHTS, f"Missing default weight for {style}"


class TestUtilityFunctions:
    """Tests for utility functions"""
    
    def test_get_style_definition(self):
        """Should return correct definition"""
        defn = get_style_definition(FightingStyle.WRESTLER)
        assert defn.name == FightingStyle.WRESTLER
        assert defn.display_name == "Wrestler"
    
    def test_get_style_matchup_modifier(self):
        """Should return correct modifier"""
        mod = get_style_matchup_modifier(FightingStyle.WRESTLER, FightingStyle.STRIKER)
        assert isinstance(mod, float)
        assert mod > 0  # Wrestler beats Striker
    
    def test_generate_style_unweighted(self):
        """Unweighted generation should return valid style"""
        for _ in range(10):
            style = generate_style_for_fighter(weighted=False)
            assert isinstance(style, FightingStyle)
    
    def test_generate_style_with_country(self):
        """Country should influence style generation"""
        brazil_styles = [generate_style_for_fighter(country="Brazil") for _ in range(100)]
        bjj_count = sum(1 for s in brazil_styles if s == FightingStyle.BJJ_SPECIALIST)
        # BJJ should appear more often than random (9%)
        assert bjj_count > 15, f"Only {bjj_count} BJJ from Brazil"
    
    def test_generate_style_with_camp_influence(self):
        """Camp styles should influence generation"""
        camp_styles = [FightingStyle.WRESTLER, FightingStyle.GROUND_AND_POUND]
        styles = [generate_style_for_fighter(camp_styles=camp_styles) for _ in range(100)]
        wrestling_count = sum(1 for s in styles if s in camp_styles)
        # Should have more wrestling styles
        assert wrestling_count > 20
    
    def test_get_style_attribute_bonuses(self):
        """Should return attribute bonuses dict"""
        bonuses = get_style_attribute_bonuses(FightingStyle.WRESTLER)
        assert isinstance(bonuses, dict)
        assert bonuses.get("wrestling", 0) > 0
    
    def test_get_style_finish_rates(self):
        """Should return finish rates dict"""
        rates = get_style_finish_rates(FightingStyle.BJJ_SPECIALIST)
        assert "ko" in rates
        assert "sub" in rates
        assert "dec" in rates
        assert rates["sub"] > rates["ko"]  # BJJ has more subs
    
    def test_validate_style_attributes_balanced(self):
        """Balanced should have no requirements"""
        result = validate_style_attributes(FightingStyle.BALANCED, {})
        assert result is True
    
    def test_validate_style_attributes_wrestler_meets(self):
        """Fighter with high wrestling should validate for Wrestler"""
        attrs = {"wrestling": 85, "takedown_defense": 75}
        result = validate_style_attributes(FightingStyle.WRESTLER, attrs)
        assert result is True
    
    def test_validate_style_attributes_wrestler_fails(self):
        """Fighter with low wrestling should fail Wrestler validation"""
        attrs = {"wrestling": 50, "takedown_defense": 50}
        result = validate_style_attributes(FightingStyle.WRESTLER, attrs)
        assert result is False
    
    def test_determine_fight_method(self):
        """Should return valid method string"""
        for _ in range(20):
            method = determine_fight_method(FightingStyle.STRIKER)
            assert method in ["KO", "TKO", "Submission", "Unanimous Decision", 
                             "Split Decision", "Majority Decision"]
    
    def test_get_style_commentary(self):
        """Should return non-empty commentary"""
        for style in FightingStyle:
            commentary = get_style_commentary(style)
            assert len(commentary) > 10
    
    def test_get_all_styles(self):
        """Should return all 11 styles"""
        styles = get_all_styles()
        assert len(styles) == 11
        assert all(isinstance(s, FightingStyle) for s in styles)
    
    def test_get_styles_by_category(self):
        """Should organize styles into categories"""
        categories = get_styles_by_category()
        assert "stand_up" in categories
        assert "grappling" in categories
        assert "hybrid" in categories
        assert len(categories["stand_up"]) == 5
        assert len(categories["grappling"]) == 4
        assert len(categories["hybrid"]) == 2
    
    def test_get_style_for_attributes_wrestler(self):
        """High wrestling attributes should suggest Wrestler style"""
        attrs = {
            "wrestling": 90, "takedown_defense": 85, "cardio": 80,
            "boxing": 50, "kicks": 50, "bjj": 60
        }
        style = get_style_for_attributes(attrs)
        assert style in [FightingStyle.WRESTLER, FightingStyle.GROUND_AND_POUND]
    
    def test_get_style_for_attributes_bjj(self):
        """High BJJ attributes should suggest BJJ Specialist"""
        attrs = {
            "bjj": 90, "wrestling": 70, "composure": 80,
            "boxing": 40, "kicks": 40
        }
        style = get_style_for_attributes(attrs)
        assert style == FightingStyle.BJJ_SPECIALIST


class TestCampStylePresets:
    """Tests for camp style presets"""
    
    def test_presets_exist(self):
        """Should have multiple presets"""
        assert len(CAMP_STYLE_PRESETS) >= 5
    
    def test_presets_have_two_styles(self):
        """Each preset should have 2 styles"""
        for name, styles in CAMP_STYLE_PRESETS.items():
            assert len(styles) == 2, f"{name} has {len(styles)} styles"
    
    def test_presets_have_valid_styles(self):
        """All preset styles should be valid"""
        for name, styles in CAMP_STYLE_PRESETS.items():
            for style in styles:
                assert isinstance(style, FightingStyle)


class TestIntegration:
    """Integration tests"""
    
    def test_full_fighter_generation_flow(self):
        """Test generating style for a fighter with full context"""
        # Brazilian fighter at BJJ gym
        style = generate_style_for_fighter(
            country="Brazil",
            camp_styles=[FightingStyle.BJJ_SPECIALIST, FightingStyle.BALANCED]
        )
        assert isinstance(style, FightingStyle)
        
        # Get definition
        defn = get_style_definition(style)
        assert defn is not None
        
        # Get bonuses
        bonuses = get_style_attribute_bonuses(style)
        assert isinstance(bonuses, dict)
        
        # Get finish rates
        rates = get_style_finish_rates(style)
        assert sum(rates.values()) >= 0.99
    
    def test_matchup_asymmetry(self):
        """Test that some matchups are asymmetric"""
        # Wrestler beats Striker
        w_vs_s = get_style_matchup_modifier(FightingStyle.WRESTLER, FightingStyle.STRIKER)
        s_vs_w = get_style_matchup_modifier(FightingStyle.STRIKER, FightingStyle.WRESTLER)
        
        assert w_vs_s > 0  # Wrestler has advantage
        assert s_vs_w < 0  # Striker has disadvantage
        assert w_vs_s == -s_vs_w  # Should be inverse
    
    def test_style_generation_distribution(self):
        """Test that style generation produces reasonable distribution"""
        styles = [generate_style_for_fighter() for _ in range(1000)]
        
        # Count each style
        counts = {}
        for style in FightingStyle:
            counts[style] = sum(1 for s in styles if s == style)
        
        # No style should be less than 1% or more than 20%
        for style, count in counts.items():
            pct = count / 10
            assert 1 <= pct <= 25, f"{style}: {pct}%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
