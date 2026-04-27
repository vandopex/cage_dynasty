# tests/test_matchmaking.py
# Tests for Module 12: Matchmaking Engine
# Lines: ~640

"""
Tests for the Matchmaking Engine module.

Covers:
- Matchup scoring components
- Fighter eligibility
- Best opponent finding
- Title fight logic
- Card generation
- Serialization
"""

import pytest
from datetime import date

from systems.matchmaking import (
    # Enums
    MatchupType,
    MatchupReason,
    # Classes
    MatchupScore,
    FighterMatchInfo,
    MatchmakingEngine,
    # Scoring functions
    calculate_ranking_score,
    calculate_skill_score,
    calculate_streak_score,
    calculate_rivalry_score,
    calculate_freshness_score,
    calculate_title_score,
    calculate_entertainment_score,
    # Convenience functions
    find_best_opponent,
    is_good_matchup,
    get_matchup_quality,
    matchmaking_engine,
    DEFAULT_WEIGHTS,
)
from core.types import WeightClass, FighterStatus
from core.calendar import GameDate, calendar


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def engine():
    """Fresh matchmaking engine for each test"""
    return MatchmakingEngine()


@pytest.fixture
def champion():
    """Champion fighter info"""
    return FighterMatchInfo(
        fighter_id="champ_001",
        name="Champion Fighter",
        weight_class=WeightClass.LIGHTWEIGHT,
        rank=0,
        overall_rating=85,
        win_streak=3,
        lose_streak=0,
        wins=15,
        losses=2,
        is_champion=True,
        status=FighterStatus.ACTIVE,
        recent_opponents=["fighter_003"],
        rivalry_ids=["fighter_002"],
        style_tags=["striker", "finisher"]
    )


@pytest.fixture
def contender():
    """#1 Contender fighter info"""
    return FighterMatchInfo(
        fighter_id="fighter_001",
        name="Top Contender",
        weight_class=WeightClass.LIGHTWEIGHT,
        rank=1,
        overall_rating=82,
        win_streak=5,
        lose_streak=0,
        wins=12,
        losses=1,
        is_champion=False,
        status=FighterStatus.ACTIVE,
        recent_opponents=[],
        rivalry_ids=[],
        style_tags=["grappler"]
    )


@pytest.fixture
def ranked_fighter():
    """Mid-ranked fighter info"""
    return FighterMatchInfo(
        fighter_id="fighter_005",
        name="Ranked Fighter",
        weight_class=WeightClass.LIGHTWEIGHT,
        rank=5,
        overall_rating=75,
        win_streak=2,
        lose_streak=0,
        wins=8,
        losses=3,
        is_champion=False,
        status=FighterStatus.ACTIVE,
        recent_opponents=[],
        rivalry_ids=[],
        style_tags=["action"]
    )


@pytest.fixture
def unranked_fighter():
    """Unranked fighter info"""
    return FighterMatchInfo(
        fighter_id="fighter_020",
        name="Unranked Fighter",
        weight_class=WeightClass.LIGHTWEIGHT,
        rank=None,
        overall_rating=65,
        win_streak=0,
        lose_streak=2,
        wins=3,
        losses=4,
        is_champion=False,
        status=FighterStatus.ACTIVE,
        recent_opponents=[],
        rivalry_ids=[],
        style_tags=[]
    )


@pytest.fixture
def rival():
    """Fighter with rivalry to champion"""
    return FighterMatchInfo(
        fighter_id="fighter_002",
        name="Rival Fighter",
        weight_class=WeightClass.LIGHTWEIGHT,
        rank=2,
        overall_rating=80,
        win_streak=4,
        lose_streak=0,
        wins=10,
        losses=2,
        is_champion=False,
        status=FighterStatus.ACTIVE,
        recent_opponents=[],
        rivalry_ids=["champ_001"],
        style_tags=["striker"]
    )


@pytest.fixture(autouse=True)
def reset_calendar():
    """Reset calendar to known date"""
    calendar.set_date(GameDate(2024, 6, 1))
    yield


# ============================================================================
# MATCHUP TYPE TESTS
# ============================================================================

class TestMatchupType:
    """Tests for MatchupType enum"""
    
    def test_all_types_defined(self):
        """Should have all matchup types"""
        assert MatchupType.TITLE_FIGHT.value == "Title Fight"
        assert MatchupType.TITLE_ELIMINATOR.value == "Title Eliminator"
        assert MatchupType.PRELIM.value == "Preliminary"


# ============================================================================
# RANKING SCORE TESTS
# ============================================================================

class TestRankingScore:
    """Tests for ranking proximity scoring"""
    
    def test_same_rank_max_score(self, contender):
        """Same rank should get max score"""
        fighter2 = FighterMatchInfo(
            fighter_id="f2", name="F2", weight_class=WeightClass.LIGHTWEIGHT,
            rank=1, overall_rating=80, win_streak=0, lose_streak=0,
            wins=5, losses=2, is_champion=False, status=FighterStatus.ACTIVE,
            recent_opponents=[], rivalry_ids=[]
        )
        score = calculate_ranking_score(contender, fighter2)
        assert score == 30.0  # Max score
    
    def test_adjacent_ranks_high_score(self, contender, rival):
        """Adjacent ranks should score high"""
        score = calculate_ranking_score(contender, rival)
        assert score >= 27.0  # 90% of max
    
    def test_distant_ranks_low_score(self, contender, unranked_fighter):
        """Distant ranks should score low"""
        score = calculate_ranking_score(contender, unranked_fighter)
        assert score < 10.0
    
    def test_champion_treated_as_rank_zero(self, champion, contender):
        """Champion should be treated as rank 0"""
        score = calculate_ranking_score(champion, contender)
        assert score >= 27.0  # #0 vs #1


# ============================================================================
# SKILL SCORE TESTS
# ============================================================================

class TestSkillScore:
    """Tests for skill balance scoring"""
    
    def test_similar_ratings_high_score(self, champion, contender):
        """Similar overall ratings should score high"""
        score = calculate_skill_score(champion, contender)
        assert score >= 16.0  # 80% of 20
    
    def test_mismatched_ratings_low_score(self, champion, unranked_fighter):
        """Big rating gap should score low"""
        score = calculate_skill_score(champion, unranked_fighter)
        assert score <= 8.0  # 40% of 20


# ============================================================================
# STREAK SCORE TESTS
# ============================================================================

class TestStreakScore:
    """Tests for win/lose streak scoring"""
    
    def test_both_on_win_streaks_high_score(self, contender, rival):
        """Both on win streaks should be exciting"""
        score = calculate_streak_score(contender, rival)
        assert score >= 10.0
    
    def test_winner_vs_loser_low_score(self, contender, unranked_fighter):
        """Win streak vs lose streak is less interesting"""
        score = calculate_streak_score(contender, unranked_fighter)
        assert score < 8.0


# ============================================================================
# RIVALRY SCORE TESTS
# ============================================================================

class TestRivalryScore:
    """Tests for rivalry scoring"""
    
    def test_rivals_max_score(self, champion, rival):
        """Rivals should get max score"""
        score = calculate_rivalry_score(champion, rival)
        assert score == 25.0  # Max rivalry bonus
    
    def test_non_rivals_zero(self, champion, contender):
        """Non-rivals should get 0"""
        score = calculate_rivalry_score(champion, contender)
        assert score == 0.0


# ============================================================================
# FRESHNESS SCORE TESTS
# ============================================================================

class TestFreshnessScore:
    """Tests for recent matchup penalty"""
    
    def test_recent_opponent_penalty(self, champion):
        """Recent opponents should get penalty"""
        recent = FighterMatchInfo(
            fighter_id="fighter_003",  # In champion's recent opponents
            name="Recent Opponent",
            weight_class=WeightClass.LIGHTWEIGHT,
            rank=3, overall_rating=78, win_streak=1, lose_streak=0,
            wins=9, losses=2, is_champion=False, status=FighterStatus.ACTIVE,
            recent_opponents=["champ_001"], rivalry_ids=[]
        )
        score = calculate_freshness_score(champion, recent)
        assert score == 0.0  # Full penalty for recent rematch
    
    def test_fresh_matchup_full_score(self, champion, contender):
        """Fresh matchup should get full score"""
        score = calculate_freshness_score(champion, contender)
        assert score == 10.0  # Max freshness (default max_score)


# ============================================================================
# TITLE SCORE TESTS
# ============================================================================

class TestTitleScore:
    """Tests for title fight scoring"""
    
    def test_title_fight_max_score(self, champion, contender):
        """Title fight should get max score"""
        score = calculate_title_score(champion, contender)
        assert score == 20.0
    
    def test_title_shot_for_ranked_below_5(self, champion, ranked_fighter):
        """Any fight involving champion gets max title score"""
        score = calculate_title_score(champion, ranked_fighter)
        # Champion is involved, so it's still a title fight
        assert score == 20.0
    
    def test_non_title_fight_contenders(self, contender, ranked_fighter):
        """Non-champion fights score based on rankings"""
        score = calculate_title_score(contender, ranked_fighter)
        # Contender (#1) vs ranked (#5) - one is contender
        assert score > 0.0  # Gets partial score for contender involvement


# ============================================================================
# ENTERTAINMENT SCORE TESTS
# ============================================================================

class TestEntertainmentScore:
    """Tests for entertainment value scoring"""
    
    def test_striker_vs_grappler_max_score(self, champion):
        """Striker vs grappler is maximum entertainment"""
        grappler = FighterMatchInfo(
            fighter_id="grappler", name="Grappler", weight_class=WeightClass.LIGHTWEIGHT,
            rank=5, overall_rating=75, win_streak=0, lose_streak=0,
            wins=8, losses=3, is_champion=False, status=FighterStatus.ACTIVE,
            recent_opponents=[], rivalry_ids=[], style_tags=["grappler"]
        )
        score = calculate_entertainment_score(champion, grappler)
        assert score == 10.0
    
    def test_both_finishers_high_score(self, champion):
        """Two finishers should score high (80% of max)"""
        other_finisher = FighterMatchInfo(
            fighter_id="finisher", name="Finisher", weight_class=WeightClass.LIGHTWEIGHT,
            rank=3, overall_rating=78, win_streak=2, lose_streak=0,
            wins=9, losses=2, is_champion=False, status=FighterStatus.ACTIVE,
            recent_opponents=[], rivalry_ids=[], style_tags=["finisher"]
        )
        score = calculate_entertainment_score(champion, other_finisher)
        assert score == 8.0  # 80% of max for same style finishers
    
    def test_unknown_styles_average(self, champion):
        """Unknown styles get average score"""
        unknown = FighterMatchInfo(
            fighter_id="unknown", name="Unknown", weight_class=WeightClass.LIGHTWEIGHT,
            rank=10, overall_rating=70, win_streak=0, lose_streak=0,
            wins=5, losses=5, is_champion=False, status=FighterStatus.ACTIVE,
            recent_opponents=[], rivalry_ids=[], style_tags=[]
        )
        score = calculate_entertainment_score(champion, unknown)
        assert score == 5.0


# ============================================================================
# FIGHTER MATCH INFO TESTS
# ============================================================================

class TestFighterMatchInfo:
    """Tests for FighterMatchInfo data class"""
    
    def test_creation(self, champion):
        """Should create with all fields"""
        assert champion.fighter_id == "champ_001"
        assert champion.is_champion is True
        assert champion.rank == 0
    
    def test_is_ranked_property(self, ranked_fighter, unranked_fighter):
        """is_ranked property should work"""
        assert ranked_fighter.is_ranked is True
        assert unranked_fighter.is_ranked is False
    
    def test_is_contender_property(self, contender, ranked_fighter):
        """is_contender property (top 5) should work"""
        assert contender.is_contender is True  # Rank 1
        assert ranked_fighter.is_contender is True  # Rank 5
    
    def test_is_available_property(self, champion):
        """is_available based on status"""
        assert champion.is_available is True


# ============================================================================
# MATCHMAKING ENGINE TESTS
# ============================================================================

class TestMatchmakingEngine:
    """Tests for MatchmakingEngine class"""
    
    def test_creation(self, engine):
        """Should create engine"""
        assert engine is not None
        assert len(engine._fighters) == 0
    
    def test_add_fighter(self, engine, champion):
        """Should add fighter"""
        engine.add_fighter(champion)
        assert "champ_001" in engine._fighters
    
    def test_remove_fighter(self, engine, champion):
        """Should remove fighter"""
        engine.add_fighter(champion)
        engine.remove_fighter("champ_001")
        assert "champ_001" not in engine._fighters
    
    def test_get_fighter(self, engine, champion):
        """Should retrieve fighter"""
        engine.add_fighter(champion)
        retrieved = engine.get_fighter("champ_001")
        assert retrieved.name == champion.name


class TestScoreMatchup:
    """Tests for matchup scoring"""
    
    def test_score_returns_matchup_score(self, engine, champion, contender):
        """Should return MatchupScore"""
        engine.add_fighter(champion)
        engine.add_fighter(contender)
        
        score = engine.score_matchup(champion, contender)
        
        assert isinstance(score, MatchupScore)
        assert score.fighter1_id == "champ_001"
        assert score.fighter2_id == "fighter_001"
    
    def test_score_includes_all_components(self, engine, champion, contender):
        """Should have all score components"""
        engine.add_fighter(champion)
        engine.add_fighter(contender)
        
        score = engine.score_matchup(champion, contender)
        
        assert score.ranking_score >= 0
        assert score.skill_score >= 0
        assert score.streak_score >= 0
        assert score.freshness_score >= 0
        assert score.title_score >= 0
        assert score.total_score > 0
    
    def test_title_fight_detected(self, engine, champion, contender):
        """Should detect title fights"""
        engine.add_fighter(champion)
        engine.add_fighter(contender)
        
        score = engine.score_matchup(champion, contender)
        
        assert score.is_title_fight
        assert score.matchup_type == MatchupType.TITLE_FIGHT
    
    def test_rivalry_matchup_high_score(self, engine, champion, rival):
        """Rivalry matchup should score high"""
        engine.add_fighter(champion)
        engine.add_fighter(rival)
        
        score = engine.score_matchup(champion, rival)
        
        assert score.rivalry_score == 25.0
        assert MatchupReason.RIVALRY in score.reasons


class TestFindOpponents:
    """Tests for opponent finding"""
    
    def test_find_opponents_returns_sorted(
        self, engine, champion, contender, ranked_fighter, unranked_fighter
    ):
        """Should return opponents sorted by score"""
        engine.add_fighter(champion)
        engine.add_fighter(contender)
        engine.add_fighter(ranked_fighter)
        engine.add_fighter(unranked_fighter)
        
        matches = engine.find_opponents("champ_001", limit=3)
        
        assert len(matches) == 3
        # Should be sorted descending
        assert matches[0].total_score >= matches[1].total_score
        assert matches[1].total_score >= matches[2].total_score
    
    def test_find_opponents_respects_limit(
        self, engine, champion, contender, ranked_fighter
    ):
        """Should respect limit parameter"""
        engine.add_fighter(champion)
        engine.add_fighter(contender)
        engine.add_fighter(ranked_fighter)
        
        matches = engine.find_opponents("champ_001", limit=1)
        
        assert len(matches) == 1


class TestFindTitleChallenger:
    """Tests for title challenger finding"""
    
    def test_finds_number_one_contender(
        self, engine, champion, contender, rival
    ):
        """Should prioritize #1 contender"""
        engine.add_fighter(champion)
        engine.add_fighter(contender)  # Rank 1
        engine.add_fighter(rival)  # Rank 2
        
        match = engine.find_title_challenger("champ_001")
        
        assert match is not None
        assert match.fighter2_id == "fighter_001"  # The #1 contender
    
    def test_returns_none_for_non_champion(self, engine, contender):
        """Should return None if fighter isn't champion"""
        engine.add_fighter(contender)
        
        match = engine.find_title_challenger("fighter_001")
        
        assert match is None


class TestGenerateCard:
    """Tests for card generation"""
    
    def test_generate_card_creates_fights(self, engine):
        """Should generate requested number of fights"""
        # Add 10 fighters
        for i in range(10):
            fighter = FighterMatchInfo(
                fighter_id=f"fighter_{i:03d}",
                name=f"Fighter {i}",
                weight_class=WeightClass.WELTERWEIGHT,
                rank=i if i < 8 else None,
                overall_rating=80 - i,
                win_streak=0,
                lose_streak=0,
                wins=5,
                losses=2,
                is_champion=(i == 0),
                status=FighterStatus.ACTIVE,
                recent_opponents=[],
                rivalry_ids=[]
            )
            engine.add_fighter(fighter)
        
        card = engine.generate_card(WeightClass.WELTERWEIGHT, num_fights=4)
        
        assert len(card) == 4
    
    def test_generate_card_no_fighter_reuse(self, engine):
        """No fighter should appear twice on card"""
        # Add 8 fighters
        for i in range(8):
            fighter = FighterMatchInfo(
                fighter_id=f"fighter_{i:03d}",
                name=f"Fighter {i}",
                weight_class=WeightClass.MIDDLEWEIGHT,
                rank=i + 1,
                overall_rating=75,
                win_streak=0,
                lose_streak=0,
                wins=5,
                losses=2,
                is_champion=False,
                status=FighterStatus.ACTIVE,
                recent_opponents=[],
                rivalry_ids=[]
            )
            engine.add_fighter(fighter)
        
        card = engine.generate_card(WeightClass.MIDDLEWEIGHT, num_fights=4)
        
        used_fighters = set()
        for matchup in card:
            assert matchup.fighter1_id not in used_fighters
            assert matchup.fighter2_id not in used_fighters
            used_fighters.add(matchup.fighter1_id)
            used_fighters.add(matchup.fighter2_id)
    
    def test_generate_card_prioritizes_title(self, engine, champion, contender):
        """Title fight should be first on card"""
        engine.add_fighter(champion)
        engine.add_fighter(contender)
        
        # Add more fighters
        for i in range(4):
            fighter = FighterMatchInfo(
                fighter_id=f"extra_{i}",
                name=f"Extra {i}",
                weight_class=WeightClass.LIGHTWEIGHT,
                rank=i + 5,
                overall_rating=70,
                win_streak=0,
                lose_streak=0,
                wins=4,
                losses=3,
                is_champion=False,
                status=FighterStatus.ACTIVE,
                recent_opponents=[],
                rivalry_ids=[]
            )
            engine.add_fighter(fighter)
        
        card = engine.generate_card(WeightClass.LIGHTWEIGHT, num_fights=3)
        
        assert card[0].matchup_type == MatchupType.TITLE_FIGHT


class TestDivisionState:
    """Tests for division state reporting"""
    
    def test_get_division_state(self, engine, champion, contender, ranked_fighter):
        """Should return comprehensive division info"""
        engine.add_fighter(champion)
        engine.add_fighter(contender)
        engine.add_fighter(ranked_fighter)
        
        state = engine.get_division_state(WeightClass.LIGHTWEIGHT)
        
        assert state["weight_class"] == "Lightweight"
        assert state["total_fighters"] == 3
        assert state["champion"] == "champ_001"
        assert state["ranked_count"] == 2


class TestSerialization:
    """Tests for engine serialization"""
    
    def test_to_dict_from_dict(self, engine, champion):
        """Should serialize and deserialize state"""
        engine.add_fighter(champion)
        engine.set_booked("champ_001")
        engine.record_matchup("fighter_001", "fighter_002")
        
        data = engine.to_dict()
        restored = MatchmakingEngine.from_dict(data)
        
        assert "champ_001" in restored._booked_fighters
        assert len(restored._recent_matchups) == 1


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""
    
    def test_get_matchup_quality_ratings(self):
        """Should return quality string"""
        # Test with mock - just checking the function exists and returns string
        quality = get_matchup_quality("nonexistent1", "nonexistent2")
        assert quality == "Unknown"
    
    def test_is_good_matchup_threshold(self, engine, champion, contender):
        """Should check against threshold"""
        engine.add_fighter(champion)
        engine.add_fighter(contender)
        
        # Manually add to global engine for convenience function test
        matchmaking_engine.add_fighter(champion)
        matchmaking_engine.add_fighter(contender)
        
        result = is_good_matchup("champ_001", "fighter_001", threshold=50.0)
        assert result is True
        
        # Cleanup
        matchmaking_engine.remove_fighter("champ_001")
        matchmaking_engine.remove_fighter("fighter_001")


class TestMatchupScore:
    """Tests for MatchupScore dataclass"""
    
    def test_to_dict(self, engine, champion, contender):
        """Should serialize to dict"""
        engine.add_fighter(champion)
        engine.add_fighter(contender)
        
        score = engine.score_matchup(champion, contender)
        data = score.to_dict()
        
        assert data["fighter1_id"] == "champ_001"
        assert data["fighter2_id"] == "fighter_001"
        assert "total_score" in data
        assert data["is_title_fight"] is True
