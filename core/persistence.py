# core/persistence.py
# Module 34: Save/Load System
# Lines: ~650
#
# Handles saving and loading game state to/from disk.
# Manages save slots, autosaves, and data integrity.

"""
Cage Dynasty - Save/Load System

This module handles all persistence operations:
- Save game state to JSON files
- Load game state from JSON files
- Manage multiple save slots
- Autosave functionality
- Save file validation and integrity
- Backup management

USAGE:
    from core.persistence import save_game, load_game, list_saves
    
    # Save current game
    save_game(game_state, slot="slot_1")
    
    # Load a save
    game_state = load_game("slot_1")
    
    # List available saves
    saves = list_saves()

SAVE FILE STRUCTURE:
    saves/
    â”œâ”€â”€ slot_1.json
    â”œâ”€â”€ slot_2.json
    â”œâ”€â”€ slot_3.json
    â”œâ”€â”€ autosave.json
    â”œâ”€â”€ quicksave.json
    â””â”€â”€ backups/
        â”œâ”€â”€ slot_1_backup.json
        â””â”€â”€ autosave_backup.json
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import shutil
import os

from core.events import emit


# ============================================================================
# CONSTANTS
# ============================================================================

# Default save directory (relative to game root)
DEFAULT_SAVE_DIR = "saves"

# Special save slots
AUTOSAVE_SLOT = "autosave"
QUICKSAVE_SLOT = "quicksave"

# Autosave rotation - keep last N autosaves for recovery
AUTOSAVE_ROTATION_COUNT = 5

# Maximum number of regular save slots
MAX_SAVE_SLOTS = 10

# Save file extension
SAVE_EXTENSION = ".json"

# Backup directory name
BACKUP_DIR = "backups"

# Current save format version (for future compatibility)
SAVE_FORMAT_VERSION = 1


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SaveMetadata:
    """
    Metadata about a save file.
    
    Stored separately from game data for quick listing.
    """
    slot_name: str
    game_name: str
    player_name: str
    player_camp: str
    save_date: str  # ISO format
    game_date: str  # In-game date
    week_number: int
    play_time_minutes: int
    format_version: int = SAVE_FORMAT_VERSION
    
    @property
    def play_time_formatted(self) -> str:
        """Format play time as hours:minutes"""
        hours = self.play_time_minutes // 60
        minutes = self.play_time_minutes % 60
        return f"{hours}h {minutes}m"
    
    @property
    def save_date_formatted(self) -> str:
        """Format save date for display"""
        try:
            dt = datetime.fromisoformat(self.save_date)
            return dt.strftime("%B %d, %Y at %I:%M %p")
        except (ValueError, TypeError):
            return self.save_date
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "slot_name": self.slot_name,
            "game_name": self.game_name,
            "player_name": self.player_name,
            "player_camp": self.player_camp,
            "save_date": self.save_date,
            "game_date": self.game_date,
            "week_number": self.week_number,
            "play_time_minutes": self.play_time_minutes,
            "format_version": self.format_version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SaveMetadata":
        """Deserialize from dictionary"""
        return cls(
            slot_name=data["slot_name"],
            game_name=data["game_name"],
            player_name=data["player_name"],
            player_camp=data["player_camp"],
            save_date=data["save_date"],
            game_date=data["game_date"],
            week_number=data["week_number"],
            play_time_minutes=data.get("play_time_minutes", 0),
            format_version=data.get("format_version", 1),
        )


@dataclass
class SaveResult:
    """Result of a save operation"""
    success: bool
    slot_name: str
    file_path: str
    message: str
    backup_created: bool = False
    
    
@dataclass
class LoadResult:
    """Result of a load operation"""
    success: bool
    slot_name: str
    message: str
    game_state: Optional[Any] = None  # GameState if successful
    metadata: Optional[SaveMetadata] = None


# ============================================================================
# SAVE MANAGER CLASS
# ============================================================================

class SaveManager:
    """
    Manages all save/load operations.
    
    Handles:
    - Save file I/O
    - Slot management
    - Autosaves
    - Backups
    - Validation
    """
    
    def __init__(self, save_dir: Optional[str] = None):
        """
        Initialize the save manager.
        
        Args:
            save_dir: Directory for save files (defaults to ./saves)
        """
        self.save_dir = Path(save_dir) if save_dir else Path(DEFAULT_SAVE_DIR)
        self.backup_dir = self.save_dir / BACKUP_DIR
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create save directories if they don't exist"""
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_save_path(self, slot_name: str) -> Path:
        """Get the file path for a save slot"""
        # Sanitize slot name
        safe_name = "".join(c for c in slot_name if c.isalnum() or c in "_-")
        return self.save_dir / f"{safe_name}{SAVE_EXTENSION}"
    
    def _get_backup_path(self, slot_name: str) -> Path:
        """Get the backup file path for a save slot"""
        safe_name = "".join(c for c in slot_name if c.isalnum() or c in "_-")
        return self.backup_dir / f"{safe_name}_backup{SAVE_EXTENSION}"
    
    # -------------------------------------------------------------------------
    # Save Operations
    # -------------------------------------------------------------------------
    
    def save_game(
        self,
        game_state: Any,  # GameState
        slot_name: str,
        create_backup: bool = True,
    ) -> SaveResult:
        """
        Save the game state to a slot.
        
        Args:
            game_state: The GameState object to save
            slot_name: Name of the save slot
            create_backup: Whether to backup existing save first
            
        Returns:
            SaveResult with operation details
        """
        file_path = self._get_save_path(slot_name)
        backup_created = False
        
        try:
            # Create backup of existing save if requested
            if create_backup and file_path.exists():
                self._create_backup(slot_name)
                backup_created = True
            
            # Extract metadata
            metadata = self._extract_metadata(game_state, slot_name)
            
            # Build save data
            save_data = {
                "metadata": metadata.to_dict(),
                "game_state": game_state.to_dict(),
                "format_version": SAVE_FORMAT_VERSION,
                "saved_at": datetime.now().isoformat(),
            }
            
            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            # Emit event
            emit("game_saved", {
                "slot_name": slot_name,
                "file_path": str(file_path),
            })
            
            return SaveResult(
                success=True,
                slot_name=slot_name,
                file_path=str(file_path),
                message=f"Game saved to {slot_name}",
                backup_created=backup_created,
            )
            
        except Exception as e:
            return SaveResult(
                success=False,
                slot_name=slot_name,
                file_path=str(file_path),
                message=f"Failed to save: {str(e)}",
                backup_created=backup_created,
            )
    
    def quicksave(self, game_state: Any) -> SaveResult:
        """Quick save to the quicksave slot"""
        return self.save_game(game_state, QUICKSAVE_SLOT, create_backup=False)
    
    def autosave(self, game_state: Any) -> SaveResult:
        """
        Autosave with rotation - keeps last N autosaves for recovery.
        
        Saves are named autosave_0 (newest) through autosave_4 (oldest).
        """
        # Rotate existing autosaves before saving new one
        self._rotate_autosaves()
        
        # Save to the newest slot (autosave_0)
        return self.save_game(game_state, f"{AUTOSAVE_SLOT}_0", create_backup=False)
    
    def _rotate_autosaves(self) -> None:
        """
        Rotate autosave files to make room for new save.
        
        autosave_4 is deleted
        autosave_3 -> autosave_4
        autosave_2 -> autosave_3
        autosave_1 -> autosave_2
        autosave_0 -> autosave_1
        (new save will become autosave_0)
        """
        # Delete oldest if it exists
        oldest_path = self._get_save_path(f"{AUTOSAVE_SLOT}_{AUTOSAVE_ROTATION_COUNT - 1}")
        if oldest_path.exists():
            try:
                oldest_path.unlink()
            except Exception:
                pass
        
        # Rotate remaining saves (newest to oldest to avoid overwriting)
        for i in range(AUTOSAVE_ROTATION_COUNT - 2, -1, -1):
            current_path = self._get_save_path(f"{AUTOSAVE_SLOT}_{i}")
            next_path = self._get_save_path(f"{AUTOSAVE_SLOT}_{i + 1}")
            
            if current_path.exists():
                try:
                    current_path.rename(next_path)
                except Exception:
                    pass
    
    def list_autosaves(self) -> List[Tuple[str, Optional[SaveMetadata]]]:
        """
        List all available autosaves with their metadata.
        
        Returns:
            List of (slot_name, metadata) tuples, newest first.
            Metadata is None if file exists but metadata can't be read.
        """
        autosaves = []
        
        for i in range(AUTOSAVE_ROTATION_COUNT):
            slot_name = f"{AUTOSAVE_SLOT}_{i}"
            path = self._get_save_path(slot_name)
            
            if path.exists():
                metadata = self.get_save_metadata(slot_name)
                autosaves.append((slot_name, metadata))
        
        return autosaves
    
    def load_autosave_by_index(self, index: int = 0) -> LoadResult:
        """
        Load a specific autosave by index.
        
        Args:
            index: 0 = newest, 4 = oldest
            
        Returns:
            LoadResult
        """
        if index < 0 or index >= AUTOSAVE_ROTATION_COUNT:
            return LoadResult(
                success=False,
                slot_name="",
                message=f"Invalid autosave index: {index}. Must be 0-{AUTOSAVE_ROTATION_COUNT - 1}",
            )
        
        slot_name = f"{AUTOSAVE_SLOT}_{index}"
        return self.load_game(slot_name)
    
    def _extract_metadata(self, game_state: Any, slot_name: str) -> SaveMetadata:
        """Extract metadata from a game state"""
        # Get player camp info
        player_camp = game_state.get_player_camp()
        player_camp_name = player_camp.name if player_camp else "Unknown"
        
        # Get current game date
        try:
            game_date = game_state.calendar.current_date.format("medium")
        except (AttributeError, TypeError):
            game_date = "Unknown"
        
        return SaveMetadata(
            slot_name=slot_name,
            game_name=game_state.game_name or "Unnamed Game",
            player_name=game_state.player_name or "Unknown",
            player_camp=player_camp_name,
            save_date=datetime.now().isoformat(),
            game_date=game_date,
            week_number=game_state.week_number,
            play_time_minutes=game_state.play_time_minutes,
        )
    
    def _create_backup(self, slot_name: str) -> bool:
        """Create a backup of an existing save"""
        source = self._get_save_path(slot_name)
        dest = self._get_backup_path(slot_name)
        
        if source.exists():
            try:
                shutil.copy2(source, dest)
                return True
            except Exception:
                return False
        return False
    
    # -------------------------------------------------------------------------
    # Load Operations
    # -------------------------------------------------------------------------
    
    def load_game(self, slot_name: str) -> LoadResult:
        """
        Load a game from a save slot.
        
        Args:
            slot_name: Name of the save slot to load
            
        Returns:
            LoadResult with game state if successful
        """
        # Import here to avoid circular imports
        from core.game_state import GameState
        
        file_path = self._get_save_path(slot_name)
        
        if not file_path.exists():
            return LoadResult(
                success=False,
                slot_name=slot_name,
                message=f"Save file not found: {slot_name}",
            )
        
        try:
            # Read save file
            with open(file_path, "r", encoding="utf-8") as f:
                save_data = json.load(f)
            
            # Validate format
            validation = self._validate_save_data(save_data)
            if not validation[0]:
                return LoadResult(
                    success=False,
                    slot_name=slot_name,
                    message=f"Invalid save file: {validation[1]}",
                )
            
            # Extract metadata
            metadata = SaveMetadata.from_dict(save_data["metadata"])
            
            # Reconstruct game state
            game_state = GameState.from_dict(save_data["game_state"])
            
            # Emit event
            emit("game_loaded", {
                "slot_name": slot_name,
                "game_name": metadata.game_name,
            })
            
            return LoadResult(
                success=True,
                slot_name=slot_name,
                message=f"Game loaded from {slot_name}",
                game_state=game_state,
                metadata=metadata,
            )
            
        except json.JSONDecodeError as e:
            return LoadResult(
                success=False,
                slot_name=slot_name,
                message=f"Corrupted save file: {str(e)}",
            )
        except Exception as e:
            return LoadResult(
                success=False,
                slot_name=slot_name,
                message=f"Failed to load: {str(e)}",
            )
    
    def quickload(self) -> LoadResult:
        """Load from the quicksave slot"""
        return self.load_game(QUICKSAVE_SLOT)
    
    def load_autosave(self) -> LoadResult:
        """Load the most recent autosave (autosave_0)"""
        return self.load_game(f"{AUTOSAVE_SLOT}_0")
    
    def load_backup(self, slot_name: str) -> LoadResult:
        """Load from a backup file"""
        # Import here to avoid circular imports
        from core.game_state import GameState
        
        backup_path = self._get_backup_path(slot_name)
        
        if not backup_path.exists():
            return LoadResult(
                success=False,
                slot_name=slot_name,
                message=f"Backup not found: {slot_name}",
            )
        
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                save_data = json.load(f)
            
            metadata = SaveMetadata.from_dict(save_data["metadata"])
            game_state = GameState.from_dict(save_data["game_state"])
            
            return LoadResult(
                success=True,
                slot_name=slot_name,
                message=f"Backup loaded for {slot_name}",
                game_state=game_state,
                metadata=metadata,
            )
            
        except Exception as e:
            return LoadResult(
                success=False,
                slot_name=slot_name,
                message=f"Failed to load backup: {str(e)}",
            )
    
    def _validate_save_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate save data structure.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required keys
        required_keys = ["metadata", "game_state", "format_version"]
        for key in required_keys:
            if key not in data:
                return False, f"Missing required key: {key}"
        
        # Check format version compatibility
        version = data.get("format_version", 0)
        if version > SAVE_FORMAT_VERSION:
            return False, f"Save format version {version} is newer than supported ({SAVE_FORMAT_VERSION})"
        
        # Check metadata structure
        metadata = data.get("metadata", {})
        metadata_keys = ["slot_name", "game_name", "save_date", "week_number"]
        for key in metadata_keys:
            if key not in metadata:
                return False, f"Missing metadata key: {key}"
        
        # Check game_state has required data
        game_state = data.get("game_state", {})
        state_keys = ["game_id", "phase", "mode"]
        for key in state_keys:
            if key not in game_state:
                return False, f"Missing game state key: {key}"
        
        return True, "Valid"
    
    # -------------------------------------------------------------------------
    # Slot Management
    # -------------------------------------------------------------------------
    
    def list_saves(self) -> List[SaveMetadata]:
        """
        List all available save files.
        
        Returns:
            List of SaveMetadata for each save, sorted by save date (newest first)
        """
        saves = []
        
        for file_path in self.save_dir.glob(f"*{SAVE_EXTENSION}"):
            if file_path.is_file():
                metadata = self.get_save_metadata(file_path.stem)
                if metadata:
                    saves.append(metadata)
        
        # Sort by save date (newest first)
        saves.sort(key=lambda m: m.save_date, reverse=True)
        
        return saves
    
    def get_save_metadata(self, slot_name: str) -> Optional[SaveMetadata]:
        """
        Get metadata for a specific save slot.
        
        Args:
            slot_name: Name of the save slot
            
        Returns:
            SaveMetadata if save exists, None otherwise
        """
        file_path = self._get_save_path(slot_name)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                save_data = json.load(f)
            
            return SaveMetadata.from_dict(save_data["metadata"])
            
        except Exception:
            return None
    
    def save_exists(self, slot_name: str) -> bool:
        """Check if a save slot exists"""
        return self._get_save_path(slot_name).exists()
    
    def backup_exists(self, slot_name: str) -> bool:
        """Check if a backup exists for a slot"""
        return self._get_backup_path(slot_name).exists()
    
    def delete_save(self, slot_name: str, delete_backup: bool = False) -> bool:
        """
        Delete a save file.
        
        Args:
            slot_name: Name of the save slot
            delete_backup: Also delete the backup if it exists
            
        Returns:
            True if deletion was successful
        """
        file_path = self._get_save_path(slot_name)
        
        try:
            if file_path.exists():
                file_path.unlink()
            
            if delete_backup:
                backup_path = self._get_backup_path(slot_name)
                if backup_path.exists():
                    backup_path.unlink()
            
            emit("save_deleted", {"slot_name": slot_name})
            return True
            
        except Exception:
            return False
    
    def restore_backup(self, slot_name: str) -> bool:
        """
        Restore a save from its backup.
        
        Args:
            slot_name: Name of the save slot
            
        Returns:
            True if restoration was successful
        """
        backup_path = self._get_backup_path(slot_name)
        save_path = self._get_save_path(slot_name)
        
        if not backup_path.exists():
            return False
        
        try:
            shutil.copy2(backup_path, save_path)
            return True
        except Exception:
            return False
    
    def get_available_slots(self) -> List[str]:
        """
        Get list of available (unused) save slot names.
        
        Returns:
            List of slot names that can be used
        """
        used_slots = {s.slot_name for s in self.list_saves()}
        all_slots = [f"slot_{i}" for i in range(1, MAX_SAVE_SLOTS + 1)]
        return [s for s in all_slots if s not in used_slots]
    
    def get_next_available_slot(self) -> Optional[str]:
        """Get the next available save slot name"""
        available = self.get_available_slots()
        return available[0] if available else None
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def get_save_directory(self) -> str:
        """Get the save directory path"""
        return str(self.save_dir)
    
    def get_total_save_size(self) -> int:
        """Get total size of all save files in bytes"""
        total = 0
        for file_path in self.save_dir.glob(f"*{SAVE_EXTENSION}"):
            if file_path.is_file():
                total += file_path.stat().st_size
        return total
    
    def get_total_save_size_formatted(self) -> str:
        """Get formatted total size of save files"""
        size = self.get_total_save_size()
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"


# ============================================================================
# MODULE-LEVEL SINGLETON
# ============================================================================

_save_manager: Optional[SaveManager] = None


def get_save_manager(save_dir: Optional[str] = None) -> SaveManager:
    """
    Get the save manager singleton.
    
    Args:
        save_dir: Optional custom save directory
        
    Returns:
        SaveManager instance
    """
    global _save_manager
    
    if _save_manager is None or save_dir is not None:
        _save_manager = SaveManager(save_dir)
    
    return _save_manager


def reset_save_manager() -> None:
    """Reset the save manager singleton"""
    global _save_manager
    _save_manager = None


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def save_game(
    game_state: Any,
    slot_name: str,
    create_backup: bool = True,
) -> SaveResult:
    """
    Save game to a slot.
    
    Args:
        game_state: GameState to save
        slot_name: Name of save slot
        create_backup: Whether to backup existing save
        
    Returns:
        SaveResult with operation details
    """
    return get_save_manager().save_game(game_state, slot_name, create_backup)


def load_game(slot_name: str) -> LoadResult:
    """
    Load game from a slot.
    
    Args:
        slot_name: Name of save slot
        
    Returns:
        LoadResult with game state if successful
    """
    return get_save_manager().load_game(slot_name)


def quicksave(game_state: Any) -> SaveResult:
    """Quick save the game"""
    return get_save_manager().quicksave(game_state)


def quickload() -> LoadResult:
    """Quick load the game"""
    return get_save_manager().quickload()


def autosave(game_state: Any) -> SaveResult:
    """Autosave the game"""
    return get_save_manager().autosave(game_state)


def load_autosave() -> LoadResult:
    """Load the most recent autosave"""
    return get_save_manager().load_autosave()


def list_autosaves() -> List[Tuple[str, Optional[SaveMetadata]]]:
    """
    List all available autosaves for recovery.
    
    Returns:
        List of (slot_name, metadata) tuples, newest first.
    """
    return get_save_manager().list_autosaves()


def load_autosave_by_index(index: int = 0) -> LoadResult:
    """
    Load a specific autosave by index for recovery.
    
    Args:
        index: 0 = newest (default), up to 4 = oldest
        
    Returns:
        LoadResult with game state if successful
    """
    return get_save_manager().load_autosave_by_index(index)


def list_saves() -> List[SaveMetadata]:
    """List all available saves"""
    return get_save_manager().list_saves()


def get_save_info(slot_name: str) -> Optional[SaveMetadata]:
    """Get info about a specific save"""
    return get_save_manager().get_save_metadata(slot_name)


def delete_save(slot_name: str, delete_backup: bool = False) -> bool:
    """Delete a save file"""
    return get_save_manager().delete_save(slot_name, delete_backup)


def save_exists(slot_name: str) -> bool:
    """Check if a save exists"""
    return get_save_manager().save_exists(slot_name)


def get_available_slots() -> List[str]:
    """Get available save slots"""
    return get_save_manager().get_available_slots()


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    # Constants
    "AUTOSAVE_SLOT",
    "AUTOSAVE_ROTATION_COUNT",
    "QUICKSAVE_SLOT",
    "MAX_SAVE_SLOTS",
    "SAVE_FORMAT_VERSION",
    
    # Data classes
    "SaveMetadata",
    "SaveResult",
    "LoadResult",
    
    # Manager class
    "SaveManager",
    
    # Singleton access
    "get_save_manager",
    "reset_save_manager",
    
    # Convenience functions
    "save_game",
    "load_game",
    "quicksave",
    "quickload",
    "autosave",
    "load_autosave",
    "list_autosaves",
    "load_autosave_by_index",
    "list_saves",
    "get_save_info",
    "delete_save",
    "save_exists",
    "get_available_slots",
]
