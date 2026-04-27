# tests/test_gameplan.py
# Complete test suite for gameplan system
# Lines: ~480

"""
Tests for the gameplan system.
"""

import pytest
from typing import Dict

from systems.gameplan import (
    Stance, Focus, Priority, RoundStrategy,
    Gameplan, GameplanModifiers, MatchupAnalysis, GameplanOption,
    create_gameplan, get_default_gameplan, get_gameplan_modifiers,
    generate_ai_gameplan, recommend_gameplan, adjust_gameplan_for_situation,
    get_matchup_analysis, get_gameplan_options,
    GameplanMenuHelper,
    get_stance_description, get_focus_description, get_priority_description, format_gameplan,
    get_gameplan_warnings,
    STANCE_MODIFIERS, FOCUS_MODIFIERS, PRIORITY_MODIFIERS,
)


@pytest.fixture
def striker_stats() -> Dict[str, int]:
    return {
        "boxing": 85, "kicks": 80, "wrestling": 55, "bjj": 50,
        "cardio": 70, "power": 80, "chin": 65, "speed": 75,
        "aggression": 75, "composure": 60, "submissions": 45,
    }


@pytest.fixture
def wrestler_stats() -> Dict[str, int]:
    return {
        "boxing": 55, "kicks": 50, "wrestling": 85, "bjj": 70,
        "cardio": 80, "power": 65, "chin": 70, "speed": 60,
        "aggression": 50, "composure": 70, "submissions": 65,
    }


class TestGameplanCreation:
    def test_create_basic_gameplan(self):
        plan = create_gameplan("BALANCED", "MIXED", "FINISH")
        assert plan.stance == "BALANCED"
        assert plan.focus == "MIXED"
        assert plan.priority == "FINISH"
    
    def test_create_gameplan_with_tactics(self):
        plan = create_gameplan(
            "AGGRESSIVE", "STRIKING", "KNOCKOUT",
            pressure_cage=True, target_body=True,
        )
        assert plan.pressure_cage is True
        assert plan.target_body is True
    
    def test_default_gameplan(self):
        plan = get_default_gameplan()
        assert plan.stance == "BALANCED"
        assert plan.focus == "MIXED"
        assert plan.priority == "FINISH"
    
    def test_gameplan_serialization(self):
        plan = create_gameplan("DEFENSIVE", "GRAPPLING", "SUBMISSION", counter_fight=True)
        data = plan.to_dict()
        restored = Gameplan.from_dict(data)
        assert restored.stance == plan.stance
        assert restored.counter_fight == plan.counter_fight


class TestGameplanModifiers:
    def test_balanced_minimal_modifiers(self):
        plan = create_gameplan("BALANCED", "MIXED", "FINISH")
        mods = get_gameplan_modifiers(plan)
        assert mods.striking_offense >= 0
        assert mods.grappling_offense >= 0
    
    def test_aggressive_stance_modifiers(self):
        plan = create_gameplan("AGGRESSIVE", "MIXED", "FINISH")
        mods = get_gameplan_modifiers(plan)
        assert mods.striking_offense > 0
        assert mods.aggression_mod > 0
        assert mods.striking_defense < 0
    
    def test_defensive_stance_modifiers(self):
        plan = create_gameplan("DEFENSIVE", "MIXED", "FINISH")
        mods = get_gameplan_modifiers(plan)
        assert mods.striking_defense > 0
        assert mods.grappling_defense > 0
        assert mods.striking_offense < 0
    
    def test_striking_focus_modifiers(self):
        plan = create_gameplan("BALANCED", "STRIKING", "KNOCKOUT")
        mods = get_gameplan_modifiers(plan)
        assert mods.striking_offense > 0
        assert mods.ko_chance_mod > 0
    
    def test_grappling_focus_modifiers(self):
        plan = create_gameplan("BALANCED", "GRAPPLING", "SUBMISSION")
        mods = get_gameplan_modifiers(plan)
        assert mods.grappling_offense > 0
        assert mods.sub_chance_mod > 0
    
    def test_knockout_priority_modifiers(self):
        plan = create_gameplan("BALANCED", "STRIKING", "KNOCKOUT")
        mods = get_gameplan_modifiers(plan)
        assert mods.ko_chance_mod > 0
    
    def test_decision_priority_modifiers(self):
        plan = create_gameplan("BALANCED", "MIXED", "DECISION")
        mods = get_gameplan_modifiers(plan)
        assert mods.ko_chance_mod < 0
        assert mods.damage_taken_mod < 0
        assert mods.striking_defense > 0
    
    def test_tactical_modifiers_wrestle_heavy(self):
        plan = create_gameplan("BALANCED", "GRAPPLING", "FINISH", wrestle_heavy=True)
        mods = get_gameplan_modifiers(plan)
        base_plan = create_gameplan("BALANCED", "GRAPPLING", "FINISH")
        base_mods = get_gameplan_modifiers(base_plan)
        assert mods.grappling_offense > base_mods.grappling_offense
    
    def test_tactical_modifiers_counter_fight(self):
        plan = create_gameplan("BALANCED", "MIXED", "FINISH", counter_fight=True)
        mods = get_gameplan_modifiers(plan)
        assert mods.aggression_mod < 0
        assert mods.striking_defense > 0
    
    def test_round_strategy_applied(self):
        plan = create_gameplan("BALANCED", "MIXED", "FINISH")
        plan.round_strategies = {1: "FEEL_OUT", 5: "ALL_OUT"}
        
        mods_r1 = get_gameplan_modifiers(plan, current_round=1)
        assert mods_r1.cardio_drain_mod < 0
        
        mods_r5 = get_gameplan_modifiers(plan, current_round=5)
        assert mods_r5.ko_chance_mod > 0


class TestAIGameplan:
    def test_striker_gets_striking_focus(self, striker_stats):
        plan = generate_ai_gameplan(striker_stats)
        assert plan.focus == "STRIKING"
    
    def test_wrestler_gets_grappling_focus(self, wrestler_stats):
        plan = generate_ai_gameplan(wrestler_stats)
        assert plan.focus == "GRAPPLING"
    
    def test_high_power_striker_hunts_ko(self, striker_stats):
        plan = generate_ai_gameplan(striker_stats)
        assert plan.priority == "KNOCKOUT"
    
    def test_aggressive_fighter_aggressive_stance(self, striker_stats):
        plan = generate_ai_gameplan(striker_stats)
        assert plan.stance == "AGGRESSIVE"
    
    def test_composed_fighter_not_aggressive(self, wrestler_stats):
        plan = generate_ai_gameplan(wrestler_stats)
        assert plan.stance in ["BALANCED", "MEASURED", "DEFENSIVE"]
    
    def test_wrestler_exploits_weak_tdd(self, wrestler_stats):
        weak_tdd_opponent = {"takedown_defense": 40, "wrestling": 50}
        plan = generate_ai_gameplan(wrestler_stats, weak_tdd_opponent)
        assert plan.focus == "GRAPPLING"
    
    def test_five_round_fight_generates_plan(self, striker_stats):
        plan = generate_ai_gameplan(striker_stats, rounds_in_fight=5)
        assert plan is not None
        assert plan.stance in ["AGGRESSIVE", "BALANCED", "DEFENSIVE", "MEASURED"]
    
    def test_low_cardio_fighter_generates_plan(self):
        low_cardio = {
            "boxing": 70, "kicks": 70, "wrestling": 50, "bjj": 50,
            "cardio": 45, "power": 70, "aggression": 50, "composure": 60,
            "submissions": 50,
        }
        plan = generate_ai_gameplan(low_cardio, rounds_in_fight=5)
        assert plan is not None


class TestRecommendation:
    def test_recommendation_returns_gameplan_and_reasons(self, striker_stats):
        plan, reasons = recommend_gameplan(striker_stats)
        assert isinstance(plan, Gameplan)
        assert isinstance(reasons, str)
        assert len(reasons) > 0
    
    def test_recommendation_has_info(self, striker_stats):
        plan, reasons = recommend_gameplan(striker_stats)
        assert "Based on" in reasons or len(reasons) > 5


class TestAdjustGameplan:
    def test_low_health_goes_survival(self):
        plan = create_gameplan("AGGRESSIVE", "STRIKING", "KNOCKOUT")
        adjusted = adjust_gameplan_for_situation(
            gameplan=plan, current_round=2, total_rounds=3,
            is_winning=False, health_percent=0.2, stamina_percent=0.5,
        )
        assert adjusted.priority == "SURVIVAL"
        assert adjusted.stance == "DEFENSIVE"
    
    def test_low_stamina_conserves(self):
        plan = create_gameplan("AGGRESSIVE", "STRIKING", "KNOCKOUT")
        adjusted = adjust_gameplan_for_situation(
            gameplan=plan, current_round=3, total_rounds=5,
            is_winning=True, health_percent=0.7, stamina_percent=0.2,
        )
        assert adjusted.round_strategies.get(3) == "CONSERVE"
    
    def test_final_round_losing_goes_all_out(self):
        plan = create_gameplan("BALANCED", "MIXED", "FINISH")
        adjusted = adjust_gameplan_for_situation(
            gameplan=plan, current_round=3, total_rounds=3,
            is_winning=False, health_percent=0.6, stamina_percent=0.5,
        )
        assert adjusted.round_strategies.get(3) == "ALL_OUT"
    
    def test_final_round_winning_cruises(self):
        plan = create_gameplan("AGGRESSIVE", "STRIKING", "KNOCKOUT")
        adjusted = adjust_gameplan_for_situation(
            gameplan=plan, current_round=3, total_rounds=3,
            is_winning=True, health_percent=0.7, stamina_percent=0.6,
        )
        assert adjusted.round_strategies.get(3) == "CRUISE"


class TestMatchupAnalysis:
    def test_striker_vs_grappler_analysis(self, striker_stats, wrestler_stats):
        analysis = get_matchup_analysis(striker_stats, wrestler_stats)
        assert analysis.striking_advantage > 0
        assert analysis.grappling_advantage < 0
    
    def test_identifies_edges(self, striker_stats, wrestler_stats):
        analysis = get_matchup_analysis(striker_stats, wrestler_stats)
        assert len(analysis.your_edges) > 0 or len(analysis.their_edges) > 0
    
    def test_suggests_approach(self, striker_stats, wrestler_stats):
        analysis = get_matchup_analysis(striker_stats, wrestler_stats)
        assert len(analysis.suggested_approach) > 0


class TestGameplanOptions:
    def test_get_options_returns_list(self, striker_stats):
        options = get_gameplan_options(striker_stats)
        assert isinstance(options, list)
        assert len(options) > 0
        assert all(isinstance(o, GameplanOption) for o in options)
    
    def test_options_have_required_fields(self, striker_stats):
        options = get_gameplan_options(striker_stats)
        for opt in options:
            assert opt.key is not None
            assert opt.name is not None
            assert opt.gameplan is not None


class TestGameplanMenuHelper:
    def test_get_stance_menu(self):
        helper = GameplanMenuHelper()
        menu = helper.get_stance_menu()
        assert len(menu) == 4
    
    def test_get_focus_menu(self):
        helper = GameplanMenuHelper()
        menu = helper.get_focus_menu()
        assert len(menu) == 4
    
    def test_get_priority_menu(self):
        helper = GameplanMenuHelper()
        menu = helper.get_priority_menu()
        assert len(menu) == 4
    
    def test_get_tactics_menu(self):
        helper = GameplanMenuHelper()
        menu = helper.get_tactics_menu()
        assert len(menu) >= 5
    
    def test_stance_from_choice(self):
        helper = GameplanMenuHelper()
        assert helper.stance_from_choice("1") == "AGGRESSIVE"
        assert helper.stance_from_choice("2") == "BALANCED"
    
    def test_focus_from_choice(self):
        helper = GameplanMenuHelper()
        assert helper.focus_from_choice("1") == "STRIKING"
        assert helper.focus_from_choice("2") == "GRAPPLING"
    
    def test_priority_from_choice(self):
        helper = GameplanMenuHelper()
        assert helper.priority_from_choice("1") == "KNOCKOUT"
        assert helper.priority_from_choice("2") == "SUBMISSION"
        assert helper.priority_from_choice("3") == "DECISION"
        assert helper.priority_from_choice("4") == "FINISH"
    
    def test_tactic_from_choice(self):
        helper = GameplanMenuHelper()
        assert helper.tactic_from_choice("1") == "wrestle_heavy"
        assert helper.tactic_from_choice("invalid") is None
    
    def test_build_gameplan_from_choices(self):
        helper = GameplanMenuHelper()
        plan = helper.build_gameplan_from_choices("1", "1", "1", ["3"])
        assert plan.stance == "AGGRESSIVE"
        assert plan.focus == "STRIKING"
        assert plan.priority == "KNOCKOUT"
        assert plan.pressure_cage is True


class TestDisplayHelpers:
    def test_stance_description(self):
        desc = get_stance_description("AGGRESSIVE")
        assert len(desc) > 0
    
    def test_focus_description(self):
        desc = get_focus_description("STRIKING")
        assert len(desc) > 0
    
    def test_priority_description(self):
        desc = get_priority_description("KNOCKOUT")
        assert len(desc) > 0
    
    def test_format_gameplan(self):
        plan = create_gameplan("AGGRESSIVE", "STRIKING", "KNOCKOUT")
        formatted = format_gameplan(plan)
        assert "AGGRESSIVE" in formatted
        assert "STRIKING" in formatted


class TestGameplanWarnings:
    def test_aggressive_low_cardio_warning(self):
        plan = create_gameplan("AGGRESSIVE", "STRIKING", "KNOCKOUT")
        stats = {"cardio": 45, "power": 70, "chin": 70, "bjj": 60, "wrestling": 60, "composure": 60}
        warnings = get_gameplan_warnings(plan, stats)
        assert any("cardio" in w.lower() for w in warnings)
    
    def test_ko_hunting_low_power_warning(self):
        plan = create_gameplan("BALANCED", "STRIKING", "KNOCKOUT")
        stats = {"cardio": 70, "power": 45, "chin": 70, "bjj": 60, "wrestling": 60, "composure": 60}
        warnings = get_gameplan_warnings(plan, stats)
        assert any("power" in w.lower() for w in warnings)


class TestIntegration:
    def test_full_workflow(self, striker_stats, wrestler_stats):
        analysis = get_matchup_analysis(striker_stats, wrestler_stats)
        assert analysis is not None
        
        options = get_gameplan_options(striker_stats, wrestler_stats)
        assert len(options) > 0
        
        plan, reason = recommend_gameplan(striker_stats, wrestler_stats)
        assert plan is not None
        
        mods = get_gameplan_modifiers(plan)
        assert mods is not None
        
        warnings = get_gameplan_warnings(plan, striker_stats)
        assert isinstance(warnings, list)
    
    def test_cli_helper_workflow(self, striker_stats):
        helper = GameplanMenuHelper()
        
        stances = helper.get_stance_menu()
        focuses = helper.get_focus_menu()
        priorities = helper.get_priority_menu()
        tactics = helper.get_tactics_menu()
        
        assert len(stances) > 0
        assert len(focuses) > 0
        assert len(priorities) > 0
        assert len(tactics) > 0
        
        plan = helper.build_gameplan_from_choices("1", "1", "1", ["1"])
        assert plan is not None
        
        mods = get_gameplan_modifiers(plan)
        assert mods is not None
