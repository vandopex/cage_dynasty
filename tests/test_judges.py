# tests/test_judges.py
# Tests for the judge system

import pytest
import sys
sys.path.insert(0, '/home/claude/cage_dynasty')

from systems.judges import (
    DecisionType,
    Scorecard,
    DecisionResult,
    generate_decision,
    get_decision_type_from_dominance,
    format_decision_for_commentary,
    calculate_dominance_from_fight,
    JUDGE_NAMES,
)


class TestDecisionType:
    """Test decision type enum."""
    
    def test_unanimous_value(self):
        assert DecisionType.UNANIMOUS.value == "Unanimous Decision"
    
    def test_split_value(self):
        assert DecisionType.SPLIT.value == "Split Decision"
    
    def test_majority_value(self):
        assert DecisionType.MAJORITY.value == "Majority Decision"
    
    def test_draw_value(self):
        assert DecisionType.DRAW.value == "Draw"


class TestScorecard:
    """Test scorecard data class."""
    
    def test_winner_fighter1(self):
        sc = Scorecard(
            judge_name="Test Judge",
            fighter1_score=29,
            fighter2_score=28,
        )
        assert sc.winner == 1
    
    def test_winner_fighter2(self):
        sc = Scorecard(
            judge_name="Test Judge",
            fighter1_score=28,
            fighter2_score=29,
        )
        assert sc.winner == 2
    
    def test_winner_draw(self):
        sc = Scorecard(
            judge_name="Test Judge",
            fighter1_score=28,
            fighter2_score=28,
        )
        assert sc.winner is None
    
    def test_display(self):
        sc = Scorecard(
            judge_name="Sal D'Amato",
            fighter1_score=29,
            fighter2_score=28,
        )
        assert sc.display() == "Sal D'Amato: 29-28"


class TestDecisionResult:
    """Test decision result data class."""
    
    def test_is_split(self):
        result = DecisionResult(
            decision_type=DecisionType.SPLIT,
            winner=1,
            scorecards=[],
        )
        assert result.is_split is True
        assert result.is_unanimous is False
    
    def test_is_unanimous(self):
        result = DecisionResult(
            decision_type=DecisionType.UNANIMOUS,
            winner=1,
            scorecards=[],
        )
        assert result.is_unanimous is True
        assert result.is_split is False
    
    def test_get_scores_display(self):
        result = DecisionResult(
            decision_type=DecisionType.SPLIT,
            winner=1,
            scorecards=[
                Scorecard("J1", 29, 28),
                Scorecard("J2", 28, 29),
                Scorecard("J3", 29, 28),
            ],
        )
        assert result.get_scores_display() == "29-28, 28-29, 29-28"


class TestGenerateDecision:
    """Test main decision generation."""
    
    def test_returns_decision_result(self):
        result = generate_decision(winner_dominance=0.6)
        assert isinstance(result, DecisionResult)
    
    def test_has_three_scorecards(self):
        result = generate_decision(winner_dominance=0.6)
        assert len(result.scorecards) == 3
    
    def test_dominant_fight_usually_unanimous(self):
        """Very dominant fights should mostly be unanimous."""
        unanimous_count = 0
        for _ in range(100):
            result = generate_decision(winner_dominance=0.85)
            if result.decision_type == DecisionType.UNANIMOUS:
                unanimous_count += 1
        # Should be at least 50% unanimous for dominant fights
        assert unanimous_count >= 50
    
    def test_close_fight_often_split(self):
        """Close fights should have more split decisions."""
        split_count = 0
        for _ in range(100):
            result = generate_decision(winner_dominance=0.52)
            if result.decision_type == DecisionType.SPLIT:
                split_count += 1
        # Should see significant splits in close fights
        assert split_count >= 20
    
    def test_fighter1_dominant_wins(self):
        """Fighter 1 should win when dominance > 0.5."""
        wins = 0
        for _ in range(100):
            result = generate_decision(winner_dominance=0.7)
            if result.winner == 1:
                wins += 1
        assert wins >= 80  # Fighter 1 should win most
    
    def test_fighter2_dominant_wins(self):
        """Fighter 2 should win when dominance < 0.5."""
        wins = 0
        for _ in range(100):
            result = generate_decision(winner_dominance=0.3)
            if result.winner == 2:
                wins += 1
        assert wins >= 80  # Fighter 2 should win most
    
    def test_title_fight_five_rounds(self):
        """Title fights should generate 5-round scorecards."""
        result = generate_decision(
            winner_dominance=0.6,
            total_rounds=5,
            is_title_fight=True,
        )
        for sc in result.scorecards:
            assert len(sc.round_scores) == 5
    
    def test_regular_fight_three_rounds(self):
        """Regular fights should generate 3-round scorecards."""
        result = generate_decision(
            winner_dominance=0.6,
            total_rounds=3,
            is_title_fight=False,
        )
        for sc in result.scorecards:
            assert len(sc.round_scores) == 3
    
    def test_controversy_possible(self):
        """Controversies should sometimes occur."""
        controversial_count = 0
        for _ in range(200):
            # Generate close fights which are more likely to be controversial
            result = generate_decision(winner_dominance=0.52)
            if result.is_controversial:
                controversial_count += 1
        # Should see some controversies
        assert controversial_count >= 1
    
    def test_judges_are_from_list(self):
        """All judges should be from the judge names list."""
        result = generate_decision(winner_dominance=0.6)
        for sc in result.scorecards:
            assert sc.judge_name in JUDGE_NAMES


class TestGetDecisionTypeFromDominance:
    """Test quick decision type function."""
    
    def test_high_dominance_usually_unanimous(self):
        """High dominance should produce mostly unanimous."""
        unanimous = 0
        for _ in range(100):
            dt = get_decision_type_from_dominance(0.85)
            if dt == DecisionType.UNANIMOUS:
                unanimous += 1
        assert unanimous >= 80
    
    def test_low_dominance_more_splits(self):
        """Low dominance should produce more splits."""
        splits = 0
        for _ in range(100):
            dt = get_decision_type_from_dominance(0.52)
            if dt == DecisionType.SPLIT:
                splits += 1
        assert splits >= 20
    
    def test_returns_valid_type(self):
        """Should always return valid decision type."""
        for _ in range(50):
            dt = get_decision_type_from_dominance(0.6)
            assert isinstance(dt, DecisionType)


class TestFormatDecisionForCommentary:
    """Test commentary formatting."""
    
    def test_split_decision_format(self):
        result = DecisionResult(
            decision_type=DecisionType.SPLIT,
            winner=1,
            scorecards=[
                Scorecard("Judge A", 29, 28, [(10, 9), (10, 9), (9, 10)]),
                Scorecard("Judge B", 28, 29, [(9, 10), (10, 9), (9, 10)]),
                Scorecard("Judge C", 29, 28, [(10, 9), (9, 10), (10, 9)]),
            ],
        )
        text = format_decision_for_commentary(result, "Jones", "Smith")
        assert "SPLIT DECISION" in text
        assert "Jones" in text
    
    def test_unanimous_decision_format(self):
        result = DecisionResult(
            decision_type=DecisionType.UNANIMOUS,
            winner=1,
            scorecards=[
                Scorecard("Judge A", 30, 27, [(10, 9), (10, 9), (10, 9)]),
                Scorecard("Judge B", 30, 27, [(10, 9), (10, 9), (10, 9)]),
                Scorecard("Judge C", 29, 28, [(10, 9), (10, 9), (9, 10)]),
            ],
        )
        text = format_decision_for_commentary(result, "Jones", "Smith")
        assert "UNANIMOUS DECISION" in text
    
    def test_controversy_included(self):
        result = DecisionResult(
            decision_type=DecisionType.SPLIT,
            winner=1,
            scorecards=[
                Scorecard("Judge A", 29, 28),
                Scorecard("Judge B", 28, 29),
                Scorecard("Judge C", 29, 28),
            ],
            is_controversial=True,
            controversy_reason="Wide scoring disparity",
        )
        text = format_decision_for_commentary(result, "Jones", "Smith")
        assert "Wide scoring disparity" in text


class TestCalculateDominance:
    """Test dominance calculation."""
    
    def test_higher_rated_more_dominant(self):
        # Run multiple times due to randomness
        doms = []
        for _ in range(20):
            dom = calculate_dominance_from_fight(
                winner_rating=80,
                loser_rating=60,
            )
            doms.append(dom)
        avg = sum(doms) / len(doms)
        assert avg > 0.55
    
    def test_close_ratings_near_fifty(self):
        # Run multiple times due to randomness
        doms = []
        for _ in range(20):
            dom = calculate_dominance_from_fight(
                winner_rating=70,
                loser_rating=70,
            )
            doms.append(dom)
        avg = sum(doms) / len(doms)
        assert 0.45 <= avg <= 0.65
    
    def test_strike_advantage_increases_dominance(self):
        # Run multiple times due to randomness
        doms = []
        for _ in range(20):
            dom = calculate_dominance_from_fight(
                winner_rating=70,
                loser_rating=70,
                winner_strikes_landed=100,
                loser_strikes_landed=50,
            )
            doms.append(dom)
        avg = sum(doms) / len(doms)
        # With 2:1 strike advantage, should be above baseline 0.5
        assert avg > 0.52
    
    def test_dominance_capped(self):
        """Dominance should be capped at 1.0."""
        dom = calculate_dominance_from_fight(
            winner_rating=99,
            loser_rating=30,
            winner_strikes_landed=200,
            loser_strikes_landed=10,
        )
        assert dom <= 1.0
        assert dom >= 0.5


class TestJudgeNames:
    """Test judge names list."""
    
    def test_has_judges(self):
        assert len(JUDGE_NAMES) >= 10
    
    def test_includes_famous_judges(self):
        assert "Sal D'Amato" in JUDGE_NAMES
        assert "Cecil Peoples" in JUDGE_NAMES  # Known for controversy
