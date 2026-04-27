# tests/test_balance.py
# Tests for the balance system

import pytest
import sys
sys.path.insert(0, '/home/claude/cage_dynasty')

from systems.balance import (
    MENTALITY_COMBAT_MODIFIERS,
    MENTALITY_FINISH_MODIFIERS,
    FINISHING_INSTINCT_MODIFIERS,
    CHAMPION_ADVANTAGE,
    get_mentality_modifier,
    get_mentality_finish_modifier,
    get_finishing_instinct_modifier,
    get_champion_advantage,
    FightContext,
    FighterCombatProfile,
    BalanceResult,
    calculate_fight_probability,
    simulate_fight_outcome,
)
from simulation.ai_behavior import FighterMentality, FinishingInstinct


class TestMentalityModifiers:
    """Test mentality combat modifiers."""
    
    def test_warrior_has_positive_bonus(self):
        """Warrior should have combat advantage."""
        mod = get_mentality_modifier(FighterMentality.WARRIOR)
        assert mod > 0
        assert mod == 0.02  # +2%
    
    def test_killer_has_positive_bonus(self):
        """Killer should have combat advantage."""
        mod = get_mentality_modifier(FighterMentality.KILLER)
        assert mod > 0
        assert mod == 0.015  # +1.5%
    
    def test_businessman_has_penalty(self):
        """Businessman should have combat penalty."""
        mod = get_mentality_modifier(FighterMentality.BUSINESSMAN)
        assert mod < 0
        assert mod == -0.025  # -2.5%
    
    def test_journeyman_is_neutral(self):
        """Journeyman should be neutral."""
        mod = get_mentality_modifier(FighterMentality.JOURNEYMAN)
        assert mod == 0.0
    
    def test_technician_is_neutral(self):
        """Technician should be neutral."""
        mod = get_mentality_modifier(FighterMentality.TECHNICIAN)
        assert mod == 0.0
    
    def test_all_mentalities_have_modifier(self):
        """All mentalities should have a defined modifier."""
        for mentality in FighterMentality:
            mod = get_mentality_modifier(mentality)
            assert isinstance(mod, float)


class TestFinishModifiers:
    """Test finish rate modifiers."""
    
    def test_killer_has_high_finish_rate(self):
        """Killer mentality should have high finish rate."""
        mod = get_mentality_finish_modifier(FighterMentality.KILLER)
        assert mod > 0
        assert mod == 0.08  # +8%
    
    def test_businessman_has_low_finish_rate(self):
        """Businessman should have low finish rate."""
        mod = get_mentality_finish_modifier(FighterMentality.BUSINESSMAN)
        assert mod < 0
    
    def test_killer_instinct_highest_finish(self):
        """Killer instinct should have highest finish bonus."""
        mod = get_finishing_instinct_modifier(FinishingInstinct.KILLER_INSTINCT)
        assert mod == 0.10  # +10%
    
    def test_point_fighter_lowest_finish(self):
        """Point fighter should have lowest finish rate."""
        mod = get_finishing_instinct_modifier(FinishingInstinct.POINT_FIGHTER)
        assert mod < 0


class TestChampionAdvantage:
    """Test champion's advantage system."""
    
    def test_champion_gets_bonus_in_title_fight(self):
        """Defending champion should get bonus."""
        bonus = get_champion_advantage(is_title_fight=True, fighter_is_champion=True)
        assert bonus == CHAMPION_ADVANTAGE
        assert bonus == 0.025  # +2.5%
    
    def test_challenger_gets_no_bonus(self):
        """Challenger should not get champion bonus."""
        bonus = get_champion_advantage(is_title_fight=True, fighter_is_champion=False)
        assert bonus == 0.0
    
    def test_no_bonus_in_regular_fight(self):
        """No champion bonus in regular fights."""
        bonus = get_champion_advantage(is_title_fight=False, fighter_is_champion=True)
        assert bonus == 0.0


class TestFightProbabilityCalculation:
    """Test the main probability calculation."""
    
    @pytest.fixture
    def equal_fighters(self):
        """Create two equal fighters."""
        f1 = FighterCombatProfile(
            fighter_id="f1",
            overall_rating=70,
            mentality=FighterMentality.JOURNEYMAN,
            finishing=FinishingInstinct.MEASURED,
            traits=[],
        )
        f2 = FighterCombatProfile(
            fighter_id="f2",
            overall_rating=70,
            mentality=FighterMentality.JOURNEYMAN,
            finishing=FinishingInstinct.MEASURED,
            traits=[],
        )
        return f1, f2
    
    @pytest.fixture
    def context(self):
        """Create fight context."""
        return FightContext(
            is_title_fight=False,
            is_main_event=False,
            total_rounds=3,
        )
    
    def test_equal_fighters_near_fifty_percent(self, equal_fighters, context):
        """Equal fighters should have ~50% win chance."""
        f1, f2 = equal_fighters
        result = calculate_fight_probability(f1, f2, context)
        assert 0.45 <= result.final_win_probability <= 0.55
    
    def test_higher_rated_fighter_favored(self, context):
        """Higher rated fighter should be favored."""
        f1 = FighterCombatProfile(
            fighter_id="f1", overall_rating=80,
            mentality=FighterMentality.JOURNEYMAN,
            finishing=FinishingInstinct.MEASURED, traits=[],
        )
        f2 = FighterCombatProfile(
            fighter_id="f2", overall_rating=60,
            mentality=FighterMentality.JOURNEYMAN,
            finishing=FinishingInstinct.MEASURED, traits=[],
        )
        result = calculate_fight_probability(f1, f2, context)
        assert result.final_win_probability > 0.55
    
    def test_warrior_vs_businessman(self, context):
        """Warrior should have advantage over businessman."""
        warrior = FighterCombatProfile(
            fighter_id="f1", overall_rating=70,
            mentality=FighterMentality.WARRIOR,
            finishing=FinishingInstinct.MEASURED, traits=[],
        )
        businessman = FighterCombatProfile(
            fighter_id="f2", overall_rating=70,
            mentality=FighterMentality.BUSINESSMAN,
            finishing=FinishingInstinct.MEASURED, traits=[],
        )
        result = calculate_fight_probability(warrior, businessman, context)
        # Warrior +2%, Businessman -2.5% = 4.5% swing
        assert result.final_win_probability > 0.52
    
    def test_champion_advantage_applied(self):
        """Champion should get advantage in title fight."""
        champion = FighterCombatProfile(
            fighter_id="champ", overall_rating=70,
            mentality=FighterMentality.JOURNEYMAN,
            finishing=FinishingInstinct.MEASURED, traits=[],
        )
        challenger = FighterCombatProfile(
            fighter_id="challenger", overall_rating=70,
            mentality=FighterMentality.JOURNEYMAN,
            finishing=FinishingInstinct.MEASURED, traits=[],
        )
        context = FightContext(
            is_title_fight=True,
            champion_id="champ",
            total_rounds=5,
        )
        result = calculate_fight_probability(champion, challenger, context)
        assert result.champion_mod == 0.025
        assert result.final_win_probability > 0.51
    
    def test_probability_clamped(self):
        """Probability should be clamped to reasonable range."""
        super_fighter = FighterCombatProfile(
            fighter_id="f1", overall_rating=99,
            mentality=FighterMentality.WARRIOR,
            finishing=FinishingInstinct.KILLER_INSTINCT,
            traits=["Iron Chin", "Knockout Artist"],
        )
        weak_fighter = FighterCombatProfile(
            fighter_id="f2", overall_rating=30,
            mentality=FighterMentality.BUSINESSMAN,
            finishing=FinishingInstinct.POINT_FIGHTER,
            traits=["Choke Artist"],
        )
        context = FightContext()
        result = calculate_fight_probability(super_fighter, weak_fighter, context)
        assert result.final_win_probability <= 0.92
        assert result.final_win_probability >= 0.08


class TestSimulateFightOutcome:
    """Test fight outcome simulation."""
    
    def test_returns_winner_method_round(self):
        """Should return winner ID, method, and round."""
        f1 = FighterCombatProfile(
            fighter_id="f1", overall_rating=70,
            mentality=FighterMentality.JOURNEYMAN,
            finishing=FinishingInstinct.MEASURED, traits=[],
        )
        f2 = FighterCombatProfile(
            fighter_id="f2", overall_rating=70,
            mentality=FighterMentality.JOURNEYMAN,
            finishing=FinishingInstinct.MEASURED, traits=[],
        )
        context = FightContext(total_rounds=3)
        
        winner_id, method, round_num = simulate_fight_outcome(f1, f2, context)
        
        assert winner_id in ["f1", "f2"]
        assert method in ["KO", "TKO", "SUB", "DEC"]
        assert 1 <= round_num <= 3
    
    def test_title_fight_has_five_rounds(self):
        """Title fight decisions should be in round 5."""
        f1 = FighterCombatProfile(
            fighter_id="f1", overall_rating=70,
            mentality=FighterMentality.TECHNICIAN,
            finishing=FinishingInstinct.POINT_FIGHTER, traits=["Decision Machine"],
        )
        f2 = FighterCombatProfile(
            fighter_id="f2", overall_rating=70,
            mentality=FighterMentality.TECHNICIAN,
            finishing=FinishingInstinct.POINT_FIGHTER, traits=["Decision Machine"],
        )
        context = FightContext(is_title_fight=True, total_rounds=5)
        
        # Run many times to get decisions
        decisions = []
        for _ in range(100):
            _, method, round_num = simulate_fight_outcome(f1, f2, context)
            if method == "DEC":
                decisions.append(round_num)
        
        # All decisions should be in round 5
        assert all(r == 5 for r in decisions)
    
    def test_killer_finishes_more(self):
        """Killer mentality should have higher finish rate."""
        killer = FighterCombatProfile(
            fighter_id="killer", overall_rating=70,
            mentality=FighterMentality.KILLER,
            finishing=FinishingInstinct.KILLER_INSTINCT,
            traits=["Knockout Artist"],
        )
        point_fighter = FighterCombatProfile(
            fighter_id="pf", overall_rating=50,  # Lower rated so killer wins
            mentality=FighterMentality.TECHNICIAN,
            finishing=FinishingInstinct.POINT_FIGHTER, traits=[],
        )
        context = FightContext(total_rounds=3)
        
        finishes = 0
        for _ in range(100):
            winner_id, method, _ = simulate_fight_outcome(killer, point_fighter, context)
            if winner_id == "killer" and method != "DEC":
                finishes += 1
        
        # Should have high finish rate when winning
        assert finishes > 30  # At least 30% finishes


class TestBalanceValues:
    """Test that balance values are reasonable."""
    
    def test_mentality_modifiers_balanced(self):
        """Sum of mentality modifiers should be near zero."""
        total = sum(MENTALITY_COMBAT_MODIFIERS.values())
        # With 6 mentalities, average should be near 0
        assert -0.05 <= total <= 0.05
    
    def test_champion_advantage_reasonable(self):
        """Champion advantage should be significant but not overwhelming."""
        assert 0.02 <= CHAMPION_ADVANTAGE <= 0.10
    
    def test_no_overpowered_modifier(self):
        """No single modifier should be too extreme."""
        for mod in MENTALITY_COMBAT_MODIFIERS.values():
            assert -0.05 <= mod <= 0.05
        
        for mod in MENTALITY_FINISH_MODIFIERS.values():
            assert -0.15 <= mod <= 0.15
