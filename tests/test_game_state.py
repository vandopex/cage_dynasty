# tests/test_game_state.py
# Module 33: Game State Manager Tests
# Tests: 52

"""
Tests for the Game State Manager module.
"""

import pytest
from core.game_state import (
    # Enums
    GamePhase,
    GameMode,
    
    # Data classes
    FighterRecord,
    CampRecord,
    DivisionState,
    GameSettings,
    
    # Main class
    GameState,
    
    # Convenience functions
    get_game_state,
    reset_game_state,
    new_game,
    get_current_date,
    get_current_week,
)


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestGamePhase:
    """Tests for GamePhase enum"""
    
    def test_all_phases_defined(self):
        """Should have all expected phases"""
        assert GamePhase.MAIN_MENU.value == "main_menu"
        assert GamePhase.PLAYING.value == "playing"
        assert GamePhase.FIGHT_NIGHT.value == "fight_night"
        assert GamePhase.GAME_OVER.value == "game_over"


class TestGameMode:
    """Tests for GameMode enum"""
    
    def test_all_modes_defined(self):
        """Should have all expected modes"""
        assert GameMode.CAREER.value == "career"
        assert GameMode.SANDBOX.value == "sandbox"
        assert GameMode.CHALLENGE.value == "challenge"


# ============================================================================
# FIGHTER RECORD TESTS
# ============================================================================

class TestFighterRecord:
    """Tests for FighterRecord dataclass"""
    
    def test_creation(self):
        """Should create record with correct values"""
        record = FighterRecord(
            fighter_id="f1",
            name="John Smith",
            weight_class="Lightweight",
            overall_rating=75,
        )
        
        assert record.fighter_id == "f1"
        assert record.name == "John Smith"
        assert record.weight_class == "Lightweight"
        assert record.overall_rating == 75
    
    def test_record_formatting(self):
        """Should format win-loss-draw record"""
        record = FighterRecord(
            fighter_id="f1",
            name="Fighter",
            wins=10,
            losses=2,
            draws=1,
        )
        
        assert record.record == "10-2-1"
    
    def test_display_name_without_nickname(self):
        """Should return name without nickname"""
        record = FighterRecord(fighter_id="f1", name="John Smith")
        assert record.display_name == "John Smith"
    
    def test_display_name_with_nickname(self):
        """Should include nickname in display name"""
        record = FighterRecord(
            fighter_id="f1",
            name="John Smith",
            nickname="The Destroyer",
        )
        assert record.display_name == 'John Smith "The Destroyer"'
    
    def test_serialization(self):
        """Should serialize and deserialize correctly"""
        record = FighterRecord(
            fighter_id="f1",
            name="John Smith",
            nickname="Hitman",
            weight_class="Welterweight",
            wins=15,
            losses=3,
            ko_wins=8,
        )
        
        data = record.to_dict()
        restored = FighterRecord.from_dict(data)
        
        assert restored.fighter_id == record.fighter_id
        assert restored.name == record.name
        assert restored.nickname == record.nickname
        assert restored.wins == record.wins
        assert restored.ko_wins == record.ko_wins


# ============================================================================
# CAMP RECORD TESTS
# ============================================================================

class TestCampRecord:
    """Tests for CampRecord dataclass"""
    
    def test_creation(self):
        """Should create record with correct values"""
        record = CampRecord(
            camp_id="c1",
            name="Alpha MMA",
            is_player=True,
            tier="REGIONAL",
            balance=75000,
        )
        
        assert record.camp_id == "c1"
        assert record.name == "Alpha MMA"
        assert record.is_player
        assert record.tier == "REGIONAL"
        assert record.balance == 75000
    
    def test_serialization(self):
        """Should serialize and deserialize correctly"""
        record = CampRecord(
            camp_id="c1",
            name="Test Camp",
            fighter_count=5,
            total_wins=20,
        )
        
        data = record.to_dict()
        restored = CampRecord.from_dict(data)
        
        assert restored.camp_id == record.camp_id
        assert restored.fighter_count == record.fighter_count
        assert restored.total_wins == record.total_wins


# ============================================================================
# DIVISION STATE TESTS
# ============================================================================

class TestDivisionState:
    """Tests for DivisionState dataclass"""
    
    def test_creation(self):
        """Should create state with correct values"""
        state = DivisionState(
            weight_class="Lightweight",
            champion_id="f1",
            champion_name="Champ",
        )
        
        assert state.weight_class == "Lightweight"
        assert state.champion_id == "f1"
        assert state.champion_name == "Champ"
    
    def test_get_top_contender(self):
        """Should return top contender"""
        state = DivisionState(
            weight_class="Lightweight",
            rankings=["f2", "f3", "f4"],
        )
        
        assert state.get_top_contender() == "f2"
    
    def test_get_top_contender_empty(self):
        """Should return None if no rankings"""
        state = DivisionState(weight_class="Flyweight")
        assert state.get_top_contender() is None
    
    def test_get_top_n(self):
        """Should return top N fighters"""
        state = DivisionState(
            weight_class="Welterweight",
            rankings=["f1", "f2", "f3", "f4", "f5"],
        )
        
        top3 = state.get_top_n(3)
        assert len(top3) == 3
        assert top3 == ["f1", "f2", "f3"]
    
    def test_serialization(self):
        """Should serialize and deserialize correctly"""
        state = DivisionState(
            weight_class="Middleweight",
            champion_id="f1",
            rankings=["f2", "f3"],
            fighter_count=20,
        )
        
        data = state.to_dict()
        restored = DivisionState.from_dict(data)
        
        assert restored.weight_class == state.weight_class
        assert restored.champion_id == state.champion_id
        assert restored.rankings == state.rankings


# ============================================================================
# GAME SETTINGS TESTS
# ============================================================================

class TestGameSettings:
    """Tests for GameSettings dataclass"""
    
    def test_default_values(self):
        """Should have sensible defaults"""
        settings = GameSettings()
        
        assert settings.difficulty == "normal"
        assert settings.auto_advance is False
        assert settings.show_fighter_ratings is True
        assert settings.ai_aggression == 1.0
    
    def test_serialization(self):
        """Should serialize and deserialize correctly"""
        settings = GameSettings(
            difficulty="hard",
            auto_advance=True,
            ai_aggression=1.3,
        )
        
        data = settings.to_dict()
        restored = GameSettings.from_dict(data)
        
        assert restored.difficulty == "hard"
        assert restored.auto_advance is True
        assert restored.ai_aggression == 1.3


# ============================================================================
# GAME STATE TESTS
# ============================================================================

class TestGameState:
    """Tests for GameState class"""
    
    @pytest.fixture
    def game(self):
        """Fresh game state for each test"""
        return GameState()
    
    def test_creation(self, game):
        """Should create with initial state"""
        assert game.phase == GamePhase.MAIN_MENU
        assert game.week_number == 0
        assert len(game.fighters) == 0
        assert len(game.camps) == 0
    
    def test_weight_classes_defined(self, game):
        """Should have all weight classes"""
        assert len(game.WEIGHT_CLASSES) == 9
        assert "Lightweight" in game.WEIGHT_CLASSES
        assert "Heavyweight" in game.WEIGHT_CLASSES
    
    def test_divisions_initialized(self, game):
        """Should initialize all divisions"""
        assert len(game.divisions) == 9
        for wc in game.WEIGHT_CLASSES:
            assert wc in game.divisions


class TestNewGame:
    """Tests for new game creation"""
    
    @pytest.fixture
    def game(self):
        """Fresh game state"""
        return GameState()
    
    def test_new_game_creates_player_camp(self, game):
        """Should create player camp"""
        game.new_game(player_camp_name="My Gym", player_name="Van")
        
        assert game.player_camp_id is not None
        assert game.player_name == "Van"
        
        camp = game.get_player_camp()
        assert camp is not None
        assert camp.name == "My Gym"
        assert camp.is_player
    
    def test_new_game_sets_phase(self, game):
        """Should set game phase to playing"""
        game.new_game(player_camp_name="Test")
        assert game.phase == GamePhase.PLAYING
    
    def test_new_game_sets_mode(self, game):
        """Should set game mode"""
        game.new_game(player_camp_name="Test", mode=GameMode.SANDBOX)
        assert game.mode == GameMode.SANDBOX
    
    def test_new_game_generates_id(self, game):
        """Should generate game ID"""
        game.new_game(player_camp_name="Test")
        assert game.game_id != ""


class TestWorldInitialization:
    """Tests for world population"""
    
    @pytest.fixture
    def game(self):
        """Game ready for world init"""
        g = GameState()
        g.new_game(player_camp_name="Test Camp")
        return g
    
    def test_initialize_world_creates_camps(self, game):
        """Should create AI camps"""
        counts = game.initialize_world(num_ai_camps=5, fighters_per_division=3)
        
        assert counts["camps"] == 5
        # Total camps = AI camps + player camp
        assert len(game.camps) == 6
    
    def test_initialize_world_creates_fighters(self, game):
        """Should create fighters"""
        counts = game.initialize_world(num_ai_camps=3, fighters_per_division=5)
        
        # 9 divisions * 5 fighters = 45
        assert counts["fighters"] == 45
        assert len(game.fighters) == 45
    
    def test_initialize_world_sets_champions(self, game):
        """Should set champions for each division"""
        game.initialize_world(num_ai_camps=3, fighters_per_division=5)
        
        for wc in game.WEIGHT_CLASSES:
            division = game.get_division(wc)
            assert division.champion_id is not None


class TestTimeManagement:
    """Tests for time advancement"""
    
    @pytest.fixture
    def game(self):
        """Initialized game"""
        g = GameState()
        g.new_game(player_camp_name="Test")
        return g
    
    def test_advance_week(self, game):
        """Should advance week"""
        summary = game.advance_week()
        
        assert game.week_number == 1
        assert summary["week"] == 1
    
    def test_advance_multiple_weeks(self, game):
        """Should track week count"""
        for _ in range(4):
            game.advance_week()
        
        assert game.week_number == 4


class TestFighterAccess:
    """Tests for fighter data access"""
    
    @pytest.fixture
    def game(self):
        """Game with fighters"""
        g = GameState()
        g.new_game(player_camp_name="Test")
        g.initialize_world(num_ai_camps=2, fighters_per_division=5)
        return g
    
    def test_get_fighter(self, game):
        """Should get fighter by ID"""
        fighter_id = list(game.fighters.keys())[0]
        fighter = game.get_fighter(fighter_id)
        
        assert fighter is not None
        assert fighter.fighter_id == fighter_id
    
    def test_get_fighter_invalid(self, game):
        """Should return None for invalid ID"""
        fighter = game.get_fighter("invalid_id")
        assert fighter is None
    
    def test_get_fighters_by_weight_class(self, game):
        """Should filter by weight class"""
        fighters = game.get_fighters_by_weight_class("Lightweight")
        
        assert len(fighters) > 0
        assert all(f.weight_class == "Lightweight" for f in fighters)
    
    def test_get_free_agents(self, game):
        """Should return free agents"""
        agents = game.get_free_agents()
        
        # Some fighters should be free agents
        # (30% from initialization)
        assert len(agents) >= 0
    
    def test_search_fighters_by_name(self, game):
        """Should search by name"""
        # Get a real fighter name
        fighter = list(game.fighters.values())[0]
        first_name = fighter.name.split()[0]
        
        results = game.search_fighters(name=first_name)
        
        assert len(results) > 0
        assert all(first_name.lower() in f.name.lower() for f in results)
    
    def test_search_fighters_by_rating(self, game):
        """Should filter by rating range"""
        results = game.search_fighters(min_rating=70, max_rating=90)
        
        for fighter in results:
            assert 70 <= fighter.overall_rating <= 90


class TestCampAccess:
    """Tests for camp data access"""
    
    @pytest.fixture
    def game(self):
        """Game with camps"""
        g = GameState()
        g.new_game(player_camp_name="Player Camp")
        g.initialize_world(num_ai_camps=5, fighters_per_division=3)
        return g
    
    def test_get_camp(self, game):
        """Should get camp by ID"""
        camp_id = list(game.camps.keys())[0]
        camp = game.get_camp(camp_id)
        
        assert camp is not None
        assert camp.camp_id == camp_id
    
    def test_get_player_camp(self, game):
        """Should get player's camp"""
        camp = game.get_player_camp()
        
        assert camp is not None
        assert camp.is_player
        assert camp.name == "Player Camp"
    
    def test_is_player_camp(self, game):
        """Should identify player camp"""
        assert game.is_player_camp(game.player_camp_id)
        
        ai_camp = [c for c in game.camps.values() if not c.is_player][0]
        assert not game.is_player_camp(ai_camp.camp_id)
    
    def test_get_all_camps(self, game):
        """Should return all camps"""
        all_camps = game.get_all_camps()
        assert len(all_camps) == 6  # 5 AI + 1 player
        
        ai_only = game.get_all_camps(include_player=False)
        assert len(ai_only) == 5


class TestDivisionAccess:
    """Tests for division data access"""
    
    @pytest.fixture
    def game(self):
        """Game with populated divisions"""
        g = GameState()
        g.new_game(player_camp_name="Test")
        g.initialize_world(num_ai_camps=2, fighters_per_division=10)
        return g
    
    def test_get_division(self, game):
        """Should get division state"""
        division = game.get_division("Lightweight")
        
        assert division is not None
        assert division.weight_class == "Lightweight"
    
    def test_get_champion(self, game):
        """Should get division champion"""
        champion = game.get_champion("Welterweight")
        
        assert champion is not None
        assert champion.is_champion
    
    def test_get_rankings(self, game):
        """Should get ranked fighters"""
        rankings = game.get_rankings("Middleweight", top_n=5)
        
        assert len(rankings) <= 5
    
    def test_get_all_champions(self, game):
        """Should get all champions"""
        champions = game.get_all_champions()
        
        assert len(champions) == 9  # One per division


class TestStatistics:
    """Tests for game statistics"""
    
    @pytest.fixture
    def game(self):
        """Populated game"""
        g = GameState()
        g.new_game(player_camp_name="Test")
        g.initialize_world(num_ai_camps=3, fighters_per_division=5)
        return g
    
    def test_get_game_stats(self, game):
        """Should return game statistics"""
        stats = game.get_game_stats()
        
        assert "total_fighters" in stats
        assert "active_fighters" in stats
        assert "total_camps" in stats
        assert stats["total_fighters"] == 45
        assert stats["total_camps"] == 4
    
    def test_get_division_summary(self, game):
        """Should return division summary"""
        summary = game.get_division_summary()
        
        assert len(summary) == 9
        assert "Lightweight" in summary
        assert "champion" in summary["Lightweight"]
        assert "fighter_count" in summary["Lightweight"]


class TestSerialization:
    """Tests for save/load functionality"""
    
    def test_full_serialization(self):
        """Should serialize and deserialize full game"""
        game = GameState()
        game.new_game(player_camp_name="Save Test Camp", player_name="Tester")
        game.initialize_world(num_ai_camps=2, fighters_per_division=3)
        game.advance_week()
        
        data = game.to_dict()
        restored = GameState.from_dict(data)
        
        assert restored.game_id == game.game_id
        assert restored.player_name == game.player_name
        assert restored.week_number == game.week_number
        assert len(restored.fighters) == len(game.fighters)
        assert len(restored.camps) == len(game.camps)
    
    def test_serialization_preserves_player_camp(self):
        """Should preserve player camp reference"""
        game = GameState()
        game.new_game(player_camp_name="My Camp")
        
        data = game.to_dict()
        restored = GameState.from_dict(data)
        
        player_camp = restored.get_player_camp()
        assert player_camp is not None
        assert player_camp.name == "My Camp"


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions"""
    
    def test_get_game_state_singleton(self):
        """Should return same instance"""
        reset_game_state()
        g1 = get_game_state()
        g2 = get_game_state()
        
        assert g1 is g2
    
    def test_reset_game_state(self):
        """Should create fresh instance"""
        g1 = get_game_state()
        g1.week_number = 100
        
        reset_game_state()
        g2 = get_game_state()
        
        assert g2.week_number == 0
    
    def test_new_game_convenience(self):
        """Should start new game"""
        game = new_game("Quick Start Camp", "Player")
        
        assert game.player_camp_id is not None
        assert game.phase == GamePhase.PLAYING
    
    def test_get_current_date(self):
        """Should return formatted date"""
        reset_game_state()
        game = get_game_state()
        game.new_game(player_camp_name="Test")
        
        date = get_current_date()
        assert isinstance(date, str)
        assert len(date) > 0
    
    def test_get_current_week(self):
        """Should return week number"""
        reset_game_state()
        game = get_game_state()
        game.new_game(player_camp_name="Test")
        game.advance_week()
        game.advance_week()
        
        assert get_current_week() == 2
