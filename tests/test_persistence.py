# tests/test_persistence.py
# Tests for Module 34: Save/Load System

"""
Tests for the save/load persistence system.

Covers:
- SaveMetadata creation and serialization
- SaveResult and LoadResult data classes
- SaveManager operations
- Save/load round-trip
- Slot management
- Backup functionality
- Error handling
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from core.persistence import (
    # Constants
    AUTOSAVE_SLOT,
    QUICKSAVE_SLOT,
    MAX_SAVE_SLOTS,
    SAVE_FORMAT_VERSION,
    
    # Data classes
    SaveMetadata,
    SaveResult,
    LoadResult,
    
    # Manager class
    SaveManager,
    
    # Singleton
    get_save_manager,
    reset_save_manager,
    
    # Convenience functions
    save_game,
    load_game,
    quicksave,
    quickload,
    autosave,
    load_autosave,
    list_saves,
    get_save_info,
    delete_save,
    save_exists,
    get_available_slots,
)

from core.game_state import GameState, GameMode


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_save_dir():
    """Create a temporary directory for save files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def save_manager(temp_save_dir):
    """SaveManager with temporary directory"""
    return SaveManager(save_dir=temp_save_dir)


@pytest.fixture
def game_state():
    """A game state ready for saving"""
    game = GameState()
    game.new_game(player_camp_name="Test Camp", player_name="Tester")
    return game


@pytest.fixture
def game_state_with_progress(game_state):
    """Game state with some progress"""
    # Advance a few weeks
    for _ in range(5):
        game_state.advance_week()
    game_state.play_time_minutes = 120
    return game_state


# ============================================================================
# SAVE METADATA TESTS
# ============================================================================

class TestSaveMetadata:
    """Tests for SaveMetadata data class"""
    
    def test_creation(self):
        """Should create metadata with all fields"""
        metadata = SaveMetadata(
            slot_name="slot_1",
            game_name="Test Game",
            player_name="Player",
            player_camp="Alpha MMA",
            save_date="2025-01-15T10:30:00",
            game_date="January 15, 2025",
            week_number=10,
            play_time_minutes=90,
        )
        
        assert metadata.slot_name == "slot_1"
        assert metadata.game_name == "Test Game"
        assert metadata.player_name == "Player"
        assert metadata.player_camp == "Alpha MMA"
        assert metadata.week_number == 10
        assert metadata.play_time_minutes == 90
    
    def test_play_time_formatted(self):
        """Should format play time correctly"""
        metadata = SaveMetadata(
            slot_name="test",
            game_name="Test",
            player_name="P",
            player_camp="C",
            save_date="2025-01-01",
            game_date="Jan 1",
            week_number=1,
            play_time_minutes=150,  # 2h 30m
        )
        
        assert metadata.play_time_formatted == "2h 30m"
    
    def test_play_time_zero(self):
        """Should handle zero play time"""
        metadata = SaveMetadata(
            slot_name="test",
            game_name="Test",
            player_name="P",
            player_camp="C",
            save_date="2025-01-01",
            game_date="Jan 1",
            week_number=1,
            play_time_minutes=0,
        )
        
        assert metadata.play_time_formatted == "0h 0m"
    
    def test_serialization(self):
        """Should serialize and deserialize correctly"""
        original = SaveMetadata(
            slot_name="slot_1",
            game_name="My Game",
            player_name="Van",
            player_camp="Dragon Gym",
            save_date="2025-03-20T14:00:00",
            game_date="March 20, 2026",
            week_number=52,
            play_time_minutes=300,
        )
        
        data = original.to_dict()
        restored = SaveMetadata.from_dict(data)
        
        assert restored.slot_name == original.slot_name
        assert restored.game_name == original.game_name
        assert restored.player_name == original.player_name
        assert restored.player_camp == original.player_camp
        assert restored.week_number == original.week_number
        assert restored.play_time_minutes == original.play_time_minutes
    
    def test_format_version_default(self):
        """Should have default format version"""
        metadata = SaveMetadata(
            slot_name="test",
            game_name="Test",
            player_name="P",
            player_camp="C",
            save_date="2025-01-01",
            game_date="Jan 1",
            week_number=1,
            play_time_minutes=0,
        )
        
        assert metadata.format_version == SAVE_FORMAT_VERSION


class TestSaveResult:
    """Tests for SaveResult data class"""
    
    def test_success_result(self):
        """Should create successful result"""
        result = SaveResult(
            success=True,
            slot_name="slot_1",
            file_path="/saves/slot_1.json",
            message="Game saved",
            backup_created=True,
        )
        
        assert result.success is True
        assert result.slot_name == "slot_1"
        assert result.backup_created is True
    
    def test_failure_result(self):
        """Should create failure result"""
        result = SaveResult(
            success=False,
            slot_name="slot_1",
            file_path="/saves/slot_1.json",
            message="Failed to save: disk full",
        )
        
        assert result.success is False
        assert "Failed" in result.message


class TestLoadResult:
    """Tests for LoadResult data class"""
    
    def test_success_result(self):
        """Should create successful result with game state"""
        game = GameState()
        metadata = SaveMetadata(
            slot_name="slot_1",
            game_name="Test",
            player_name="P",
            player_camp="C",
            save_date="2025-01-01",
            game_date="Jan 1",
            week_number=1,
            play_time_minutes=0,
        )
        
        result = LoadResult(
            success=True,
            slot_name="slot_1",
            message="Game loaded",
            game_state=game,
            metadata=metadata,
        )
        
        assert result.success is True
        assert result.game_state is not None
        assert result.metadata is not None
    
    def test_failure_result(self):
        """Should create failure result"""
        result = LoadResult(
            success=False,
            slot_name="slot_1",
            message="Save file not found",
        )
        
        assert result.success is False
        assert result.game_state is None
        assert result.metadata is None


# ============================================================================
# SAVE MANAGER TESTS
# ============================================================================

class TestSaveManager:
    """Tests for SaveManager class"""
    
    def test_creation(self, temp_save_dir):
        """Should create manager with directory"""
        manager = SaveManager(save_dir=temp_save_dir)
        
        assert manager.save_dir == Path(temp_save_dir)
        assert manager.save_dir.exists()
    
    def test_creates_directories(self, temp_save_dir):
        """Should create save and backup directories"""
        # Use a subdirectory that doesn't exist
        new_dir = Path(temp_save_dir) / "new_saves"
        manager = SaveManager(save_dir=str(new_dir))
        
        assert new_dir.exists()
        assert (new_dir / "backups").exists()
    
    def test_save_game_basic(self, save_manager, game_state):
        """Should save game to slot"""
        result = save_manager.save_game(game_state, "slot_1")
        
        assert result.success is True
        assert result.slot_name == "slot_1"
        assert save_manager.save_exists("slot_1")
    
    def test_save_creates_file(self, save_manager, game_state):
        """Should create actual JSON file"""
        save_manager.save_game(game_state, "slot_1")
        
        save_path = save_manager._get_save_path("slot_1")
        assert save_path.exists()
        
        # Verify it's valid JSON
        with open(save_path) as f:
            data = json.load(f)
        assert "metadata" in data
        assert "game_state" in data
    
    def test_save_overwrites_existing(self, save_manager, game_state):
        """Should overwrite existing save"""
        # Save twice
        save_manager.save_game(game_state, "slot_1")
        game_state.week_number = 100  # Modify
        save_manager.save_game(game_state, "slot_1")
        
        # Load and verify updated
        result = save_manager.load_game("slot_1")
        assert result.game_state.week_number == 100
    
    def test_save_creates_backup(self, save_manager, game_state):
        """Should create backup when overwriting"""
        # First save
        save_manager.save_game(game_state, "slot_1")
        original_week = game_state.week_number
        
        # Second save with different data
        game_state.week_number = 999
        save_manager.save_game(game_state, "slot_1", create_backup=True)
        
        # Backup should exist
        assert save_manager.backup_exists("slot_1")
        
        # Load backup and verify it has original data
        backup_result = save_manager.load_backup("slot_1")
        assert backup_result.success
        assert backup_result.game_state.week_number == original_week


class TestSaveManagerLoad:
    """Tests for SaveManager load operations"""
    
    def test_load_game_basic(self, save_manager, game_state):
        """Should load saved game"""
        save_manager.save_game(game_state, "slot_1")
        result = save_manager.load_game("slot_1")
        
        assert result.success is True
        assert result.game_state is not None
        assert result.metadata is not None
    
    def test_load_preserves_data(self, save_manager, game_state):
        """Should preserve all game data"""
        # Set specific values
        game_state.week_number = 42
        game_state.play_time_minutes = 180
        
        save_manager.save_game(game_state, "slot_1")
        result = save_manager.load_game("slot_1")
        
        assert result.game_state.week_number == 42
        assert result.game_state.play_time_minutes == 180
    
    def test_load_nonexistent(self, save_manager):
        """Should fail gracefully for missing save"""
        result = save_manager.load_game("nonexistent")
        
        assert result.success is False
        assert "not found" in result.message.lower()
    
    def test_load_corrupted_file(self, save_manager, temp_save_dir):
        """Should handle corrupted save files"""
        # Create a corrupted save file
        save_path = Path(temp_save_dir) / "corrupted.json"
        with open(save_path, "w") as f:
            f.write("{ not valid json")
        
        result = save_manager.load_game("corrupted")
        
        assert result.success is False
        assert "corrupted" in result.message.lower()


class TestSaveManagerSlots:
    """Tests for SaveManager slot management"""
    
    def test_list_saves_empty(self, save_manager):
        """Should return empty list when no saves"""
        saves = save_manager.list_saves()
        assert saves == []
    
    def test_list_saves_multiple(self, save_manager, game_state):
        """Should list all saves"""
        save_manager.save_game(game_state, "slot_1")
        save_manager.save_game(game_state, "slot_2")
        save_manager.save_game(game_state, "slot_3")
        
        saves = save_manager.list_saves()
        
        assert len(saves) == 3
        slot_names = {s.slot_name for s in saves}
        assert slot_names == {"slot_1", "slot_2", "slot_3"}
    
    def test_list_saves_sorted_by_date(self, save_manager, game_state):
        """Should sort saves newest first"""
        import time
        
        save_manager.save_game(game_state, "old_save")
        time.sleep(0.1)  # Small delay
        save_manager.save_game(game_state, "new_save")
        
        saves = save_manager.list_saves()
        
        assert saves[0].slot_name == "new_save"
        assert saves[1].slot_name == "old_save"
    
    def test_get_save_metadata(self, save_manager, game_state):
        """Should get metadata for specific save"""
        save_manager.save_game(game_state, "slot_1")
        
        metadata = save_manager.get_save_metadata("slot_1")
        
        assert metadata is not None
        assert metadata.slot_name == "slot_1"
        assert metadata.player_camp == "Test Camp"
    
    def test_get_save_metadata_nonexistent(self, save_manager):
        """Should return None for missing save"""
        metadata = save_manager.get_save_metadata("nonexistent")
        assert metadata is None
    
    def test_delete_save(self, save_manager, game_state):
        """Should delete save file"""
        save_manager.save_game(game_state, "slot_1")
        assert save_manager.save_exists("slot_1")
        
        result = save_manager.delete_save("slot_1")
        
        assert result is True
        assert not save_manager.save_exists("slot_1")
    
    def test_delete_save_with_backup(self, save_manager, game_state):
        """Should optionally delete backup too"""
        # Create save and backup
        save_manager.save_game(game_state, "slot_1")
        save_manager.save_game(game_state, "slot_1")  # Creates backup
        
        assert save_manager.backup_exists("slot_1")
        
        save_manager.delete_save("slot_1", delete_backup=True)
        
        assert not save_manager.save_exists("slot_1")
        assert not save_manager.backup_exists("slot_1")
    
    def test_get_available_slots(self, save_manager, game_state):
        """Should return unused slot names"""
        # Use some slots
        save_manager.save_game(game_state, "slot_1")
        save_manager.save_game(game_state, "slot_3")
        
        available = save_manager.get_available_slots()
        
        assert "slot_1" not in available
        assert "slot_2" in available
        assert "slot_3" not in available
    
    def test_get_next_available_slot(self, save_manager, game_state):
        """Should return next available slot"""
        # slot_1 should be first available
        assert save_manager.get_next_available_slot() == "slot_1"
        
        save_manager.save_game(game_state, "slot_1")
        
        # Now slot_2 should be next
        assert save_manager.get_next_available_slot() == "slot_2"


class TestQuickSaveAutosave:
    """Tests for quicksave and autosave functionality"""
    
    def test_quicksave(self, save_manager, game_state):
        """Should quicksave to special slot"""
        result = save_manager.quicksave(game_state)
        
        assert result.success is True
        assert result.slot_name == QUICKSAVE_SLOT
        assert save_manager.save_exists(QUICKSAVE_SLOT)
    
    def test_quickload(self, save_manager, game_state):
        """Should load from quicksave slot"""
        game_state.week_number = 77
        save_manager.quicksave(game_state)
        
        result = save_manager.quickload()
        
        assert result.success is True
        assert result.game_state.week_number == 77
    
    def test_autosave(self, save_manager, game_state):
        """Should autosave to special slot"""
        result = save_manager.autosave(game_state)
        
        assert result.success is True
        assert result.slot_name == "autosave_0"
    
    def test_load_autosave(self, save_manager, game_state):
        """Should load from autosave slot"""
        game_state.week_number = 88
        save_manager.autosave(game_state)
        
        result = save_manager.load_autosave()
        
        assert result.success is True
        assert result.game_state.week_number == 88


class TestBackupRestore:
    """Tests for backup and restore functionality"""
    
    def test_restore_backup(self, save_manager, game_state):
        """Should restore save from backup"""
        # Create original save
        game_state.week_number = 10
        save_manager.save_game(game_state, "slot_1")
        
        # Overwrite with new data (creates backup)
        game_state.week_number = 20
        save_manager.save_game(game_state, "slot_1")
        
        # Restore from backup
        success = save_manager.restore_backup("slot_1")
        assert success is True
        
        # Load and verify original data restored
        result = save_manager.load_game("slot_1")
        assert result.game_state.week_number == 10
    
    def test_restore_nonexistent_backup(self, save_manager):
        """Should fail gracefully when no backup exists"""
        success = save_manager.restore_backup("nonexistent")
        assert success is False


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""
    
    @pytest.fixture(autouse=True)
    def setup_manager(self, temp_save_dir):
        """Reset and configure save manager for each test"""
        reset_save_manager()
        get_save_manager(temp_save_dir)
        yield
        reset_save_manager()
    
    def test_save_game_function(self, game_state):
        """Should save game using convenience function"""
        result = save_game(game_state, "slot_1")
        assert result.success is True
    
    def test_load_game_function(self, game_state):
        """Should load game using convenience function"""
        save_game(game_state, "slot_1")
        result = load_game("slot_1")
        assert result.success is True
    
    def test_quicksave_function(self, game_state):
        """Should quicksave using convenience function"""
        result = quicksave(game_state)
        assert result.success is True
        assert result.slot_name == QUICKSAVE_SLOT
    
    def test_quickload_function(self, game_state):
        """Should quickload using convenience function"""
        quicksave(game_state)
        result = quickload()
        assert result.success is True
    
    def test_autosave_function(self, game_state):
        """Should autosave using convenience function"""
        result = autosave(game_state)
        assert result.success is True
    
    def test_load_autosave_function(self, game_state):
        """Should load autosave using convenience function"""
        autosave(game_state)
        result = load_autosave()
        assert result.success is True
    
    def test_list_saves_function(self, game_state):
        """Should list saves using convenience function"""
        save_game(game_state, "slot_1")
        save_game(game_state, "slot_2")
        
        saves = list_saves()
        assert len(saves) == 2
    
    def test_get_save_info_function(self, game_state):
        """Should get save info using convenience function"""
        save_game(game_state, "slot_1")
        
        info = get_save_info("slot_1")
        assert info is not None
        assert info.slot_name == "slot_1"
    
    def test_delete_save_function(self, game_state):
        """Should delete save using convenience function"""
        save_game(game_state, "slot_1")
        assert save_exists("slot_1")
        
        delete_save("slot_1")
        assert not save_exists("slot_1")
    
    def test_save_exists_function(self, game_state):
        """Should check existence using convenience function"""
        assert not save_exists("slot_1")
        
        save_game(game_state, "slot_1")
        assert save_exists("slot_1")
    
    def test_get_available_slots_function(self, game_state):
        """Should get available slots using convenience function"""
        slots = get_available_slots()
        assert "slot_1" in slots
        
        save_game(game_state, "slot_1")
        
        slots = get_available_slots()
        assert "slot_1" not in slots


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestSaveLoadIntegration:
    """Integration tests for save/load round-trip"""
    
    def test_full_round_trip(self, save_manager, game_state):
        """Should preserve all data through save/load cycle"""
        # Set up game with various data
        game_state.week_number = 52
        game_state.play_time_minutes = 240
        game_state.total_fights_simulated = 100
        game_state.title_changes = 5
        
        # Save
        save_result = save_manager.save_game(game_state, "full_test")
        assert save_result.success
        
        # Load
        load_result = save_manager.load_game("full_test")
        assert load_result.success
        
        loaded = load_result.game_state
        
        # Verify all data preserved
        assert loaded.week_number == 52
        assert loaded.play_time_minutes == 240
        assert loaded.total_fights_simulated == 100
        assert loaded.title_changes == 5
    
    def test_player_camp_preserved(self, save_manager, game_state):
        """Should preserve player camp through save/load"""
        save_manager.save_game(game_state, "slot_1")
        result = save_manager.load_game("slot_1")
        
        player_camp = result.game_state.get_player_camp()
        assert player_camp is not None
        assert player_camp.name == "Test Camp"
        assert player_camp.is_player is True
    
    def test_divisions_preserved(self, save_manager, game_state):
        """Should preserve divisions through save/load"""
        save_manager.save_game(game_state, "slot_1")
        result = save_manager.load_game("slot_1")
        
        # Check divisions exist
        assert len(result.game_state.divisions) == 9
        assert "Lightweight" in result.game_state.divisions


class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_special_characters_in_slot_name(self, save_manager, game_state):
        """Should sanitize slot names with special characters"""
        # These should be sanitized to safe names
        result = save_manager.save_game(game_state, "slot/with/slashes")
        assert result.success
        
        result = save_manager.save_game(game_state, "slot..dots")
        assert result.success
    
    def test_very_long_slot_name(self, save_manager, game_state):
        """Should handle very long slot names"""
        long_name = "a" * 200
        result = save_manager.save_game(game_state, long_name)
        assert result.success
    
    def test_empty_slot_name(self, save_manager, game_state):
        """Should handle empty slot name"""
        result = save_manager.save_game(game_state, "")
        # Should either succeed with sanitized name or fail gracefully
        assert isinstance(result.success, bool)
    
    def test_unicode_in_game_data(self, save_manager, game_state):
        """Should handle unicode characters in game data"""
        game_state.player_name = "日本語プレイヤー"  # Japanese
        game_state.game_name = "Jökulhlaup's Gym"  # Icelandic
        
        save_manager.save_game(game_state, "unicode_test")
        result = save_manager.load_game("unicode_test")
        
        assert result.success
        assert result.game_state.player_name == "日本語プレイヤー"


class TestSaveManagerUtilities:
    """Tests for utility methods"""
    
    def test_get_save_directory(self, save_manager, temp_save_dir):
        """Should return save directory path"""
        assert save_manager.get_save_directory() == temp_save_dir
    
    def test_get_total_save_size(self, save_manager, game_state):
        """Should calculate total save size"""
        # Initially zero
        assert save_manager.get_total_save_size() == 0
        
        # Save some files
        save_manager.save_game(game_state, "slot_1")
        save_manager.save_game(game_state, "slot_2")
        
        # Should be greater than zero
        assert save_manager.get_total_save_size() > 0
    
    def test_get_total_save_size_formatted(self, save_manager, game_state):
        """Should format save size nicely"""
        save_manager.save_game(game_state, "slot_1")
        
        formatted = save_manager.get_total_save_size_formatted()
        
        # Should contain a unit
        assert any(unit in formatted for unit in ["B", "KB", "MB"])
