"""
Unit tests for the Title Management System.

Tests cover:
- Vacant title detection
- Contender selection
- Title fight scheduling
- Title change processing
- Champion stripping
"""

import pytest
from dataclasses import dataclass, field
from typing import Optional, List
from systems.titles import (
    TitleSystem,
    TitleChangeType,
    TitleChangeResult,
    VacantTitleFight,
    get_title_system,
)


# Mock classes for testing
@dataclass
class MockDivisionState:
    """Mock division state for testing."""
    weight_class: str
    champion_id: Optional[str] = None
    champion_name: Optional[str] = None
    rankings: List[str] = field(default_factory=list)


@dataclass
class MockFighter:
    """Mock fighter for testing."""
    fighter_id: str
    name: str
    weight_class: str
    overall_rating: int = 75
    wins: int = 10
    losses: int = 2
    is_champion: bool = False
    is_active: bool = True


class TestTitleSystem:
    """Tests for TitleSystem class."""
    
    @pytest.fixture
    def title_system(self):
        """Create a fresh TitleSystem for each test."""
        return TitleSystem()
    
    @pytest.fixture
    def divisions(self):
        """Create mock divisions."""
        return {
            "Lightweight": MockDivisionState(
                weight_class="Lightweight",
                champion_id="champ_lw",
                champion_name="Champ Lightweight"
            ),
            "Welterweight": MockDivisionState(
                weight_class="Welterweight",
                champion_id=None,  # Vacant
                champion_name=None
            ),
            "Middleweight": MockDivisionState(
                weight_class="Middleweight",
                champion_id="champ_mw",
                champion_name="Champ Middleweight"
            ),
        }
    
    @pytest.fixture
    def fighters(self):
        """Create mock fighters."""
        return {
            "champ_lw": MockFighter(
                fighter_id="champ_lw",
                name="Champ Lightweight",
                weight_class="Lightweight",
                overall_rating=90,
                is_champion=True
            ),
            "contender_lw_1": MockFighter(
                fighter_id="contender_lw_1",
                name="Top Contender LW",
                weight_class="Lightweight",
                overall_rating=85
            ),
            "contender_lw_2": MockFighter(
                fighter_id="contender_lw_2",
                name="Second Contender LW",
                weight_class="Lightweight",
                overall_rating=82
            ),
            "contender_ww_1": MockFighter(
                fighter_id="contender_ww_1",
                name="Top Contender WW",
                weight_class="Welterweight",
                overall_rating=88
            ),
            "contender_ww_2": MockFighter(
                fighter_id="contender_ww_2",
                name="Second Contender WW",
                weight_class="Welterweight",
                overall_rating=84
            ),
            "contender_ww_3": MockFighter(
                fighter_id="contender_ww_3",
                name="Third Contender WW",
                weight_class="Welterweight",
                overall_rating=80
            ),
            "champ_mw": MockFighter(
                fighter_id="champ_mw",
                name="Champ Middleweight",
                weight_class="Middleweight",
                overall_rating=92,
                is_champion=True
            ),
            "contender_mw_1": MockFighter(
                fighter_id="contender_mw_1",
                name="Top Contender MW",
                weight_class="Middleweight",
                overall_rating=87
            ),
        }


class TestVacantTitleDetection(TestTitleSystem):
    """Tests for vacant title detection."""
    
    def test_get_vacant_divisions(self, title_system, divisions):
        """Should return list of vacant divisions."""
        vacant = title_system.get_vacant_divisions(divisions)
        
        assert len(vacant) == 1
        assert "Welterweight" in vacant
        assert "Lightweight" not in vacant
        assert "Middleweight" not in vacant
    
    def test_get_vacant_divisions_all_filled(self, title_system, divisions):
        """Should return empty list when all divisions have champions."""
        divisions["Welterweight"].champion_id = "some_champ"
        
        vacant = title_system.get_vacant_divisions(divisions)
        
        assert len(vacant) == 0
    
    def test_get_vacant_divisions_all_vacant(self, title_system, divisions):
        """Should return all divisions when all are vacant."""
        for div in divisions.values():
            div.champion_id = None
        
        vacant = title_system.get_vacant_divisions(divisions)
        
        assert len(vacant) == 3
    
    def test_is_title_vacant_true(self, title_system, divisions):
        """Should return True for vacant division."""
        assert title_system.is_title_vacant(divisions, "Welterweight") is True
    
    def test_is_title_vacant_false(self, title_system, divisions):
        """Should return False for division with champion."""
        assert title_system.is_title_vacant(divisions, "Lightweight") is False
    
    def test_is_title_vacant_unknown_division(self, title_system, divisions):
        """Should return True for unknown division."""
        assert title_system.is_title_vacant(divisions, "Superfight") is True


class TestTitleFightScheduled(TestTitleSystem):
    """Tests for checking if title fight is scheduled."""
    
    def test_title_fight_scheduled_true(self, title_system):
        """Should return True when title fight is scheduled."""
        fights = [
            {"is_title_fight": True, "weight_class": "Welterweight"},
            {"is_title_fight": False, "weight_class": "Lightweight"},
        ]
        
        assert title_system.is_title_fight_scheduled("Welterweight", fights) is True
    
    def test_title_fight_scheduled_false(self, title_system):
        """Should return False when no title fight scheduled."""
        fights = [
            {"is_title_fight": False, "weight_class": "Welterweight"},
            {"is_title_fight": True, "weight_class": "Lightweight"},
        ]
        
        assert title_system.is_title_fight_scheduled("Welterweight", fights) is False
    
    def test_title_fight_scheduled_empty(self, title_system):
        """Should return False for empty fight list."""
        assert title_system.is_title_fight_scheduled("Welterweight", []) is False


class TestGetContenders(TestTitleSystem):
    """Tests for getting title contenders."""
    
    def test_get_top_contenders(self, title_system, fighters):
        """Should return top 2 contenders by rating."""
        contenders = title_system.get_title_contenders("Welterweight", fighters)
        
        assert len(contenders) == 2
        assert contenders[0].fighter_id == "contender_ww_1"  # 88 rating
        assert contenders[1].fighter_id == "contender_ww_2"  # 84 rating
    
    def test_get_contenders_excludes_champion(self, title_system, fighters):
        """Should not include champion in contenders."""
        contenders = title_system.get_title_contenders("Lightweight", fighters)
        
        assert len(contenders) == 2
        assert all(c.fighter_id != "champ_lw" for c in contenders)
    
    def test_get_contenders_excludes_inactive(self, title_system, fighters):
        """Should not include inactive fighters."""
        fighters["contender_ww_1"].is_active = False
        
        contenders = title_system.get_title_contenders("Welterweight", fighters)
        
        assert len(contenders) == 2
        assert contenders[0].fighter_id == "contender_ww_2"  # Now top
    
    def test_get_contenders_with_exclusions(self, title_system, fighters):
        """Should exclude specified fighter IDs."""
        exclude = {"contender_ww_1", "contender_ww_2"}
        
        contenders = title_system.get_title_contenders(
            "Welterweight", fighters, exclude_ids=exclude
        )
        
        assert len(contenders) == 1
        assert contenders[0].fighter_id == "contender_ww_3"
    
    def test_get_contenders_custom_count(self, title_system, fighters):
        """Should return requested number of contenders."""
        contenders = title_system.get_title_contenders(
            "Welterweight", fighters, count=3
        )
        
        assert len(contenders) == 3
    
    def test_get_contenders_not_enough(self, title_system, fighters):
        """Should return available contenders even if less than requested."""
        contenders = title_system.get_title_contenders(
            "Middleweight", fighters, count=5
        )
        
        assert len(contenders) == 1  # Only one non-champion MW


class TestCreateVacantTitleFight(TestTitleSystem):
    """Tests for creating vacant title fights."""
    
    def test_create_vacant_title_fight(self, title_system, fighters):
        """Should create a vacant title fight."""
        fight = title_system.create_vacant_title_fight(
            "Welterweight", fighters, [], event_number=42
        )
        
        assert fight is not None
        assert fight.weight_class == "Welterweight"
        assert fight.fighter1_id == "contender_ww_1"
        assert fight.fighter2_id == "contender_ww_2"
        assert fight.weeks_until == 4
        assert "42" in fight.event_name
        assert "VACANT TITLE" in fight.headline
    
    def test_create_vacant_title_fight_to_dict(self, title_system, fighters):
        """Should convert to proper fight dict."""
        fight = title_system.create_vacant_title_fight(
            "Welterweight", fighters, [], event_number=1
        )
        
        fight_dict = fight.to_fight_dict()
        
        assert fight_dict["is_title_fight"] is True
        assert fight_dict["is_vacant_title"] is True
        assert fight_dict["is_main_event"] is True
        assert fight_dict["rounds"] == 5
    
    def test_create_vacant_title_fight_not_enough_contenders(self, title_system, fighters):
        """Should return None if not enough contenders."""
        # Remove all but one WW fighter
        del fighters["contender_ww_2"]
        del fighters["contender_ww_3"]
        
        fight = title_system.create_vacant_title_fight(
            "Welterweight", fighters, [], event_number=1
        )
        
        assert fight is None
    
    def test_create_vacant_title_fight_respects_scheduled(self, title_system, fighters):
        """Should skip fighters already in scheduled title fights."""
        scheduled = [
            {
                "is_title_fight": True,
                "weight_class": "Welterweight",
                "fighter1_id": "contender_ww_1",
                "fighter2_id": "contender_ww_2",
            }
        ]
        
        fight = title_system.create_vacant_title_fight(
            "Welterweight", fighters, scheduled, event_number=1
        )
        
        # Should return None since only contender_ww_3 is available
        assert fight is None


class TestCheckAndCreateVacantFights(TestTitleSystem):
    """Tests for checking all divisions and creating fights."""
    
    def test_creates_fight_for_vacant(self, title_system, divisions, fighters):
        """Should create fight for vacant division."""
        fights = title_system.check_and_create_vacant_fights(
            divisions, fighters, [], event_number=10
        )
        
        assert len(fights) == 1
        assert fights[0].weight_class == "Welterweight"
    
    def test_skips_already_scheduled(self, title_system, divisions, fighters):
        """Should skip divisions with scheduled title fights."""
        scheduled = [
            {"is_title_fight": True, "weight_class": "Welterweight"}
        ]
        
        fights = title_system.check_and_create_vacant_fights(
            divisions, fighters, scheduled, event_number=10
        )
        
        assert len(fights) == 0
    
    def test_multiple_vacant_divisions(self, title_system, divisions, fighters):
        """Should create fights for all vacant divisions."""
        divisions["Lightweight"].champion_id = None
        
        # Add more LW fighters
        fighters["contender_lw_3"] = MockFighter(
            fighter_id="contender_lw_3",
            name="Third LW",
            weight_class="Lightweight",
            overall_rating=78
        )
        
        fights = title_system.check_and_create_vacant_fights(
            divisions, fighters, [], event_number=10
        )
        
        assert len(fights) == 2
        weight_classes = {f.weight_class for f in fights}
        assert "Lightweight" in weight_classes
        assert "Welterweight" in weight_classes


class TestProcessTitleFightResult(TestTitleSystem):
    """Tests for processing title fight results."""
    
    def test_vacant_title_claimed(self, title_system, divisions, fighters):
        """Should process vacant title being claimed."""
        fight = {
            "is_title_fight": True,
            "is_vacant_title": True,
            "weight_class": "Welterweight",
        }
        
        result = title_system.process_title_fight_result(
            fight,
            winner_id="contender_ww_1",
            loser_id="contender_ww_2",
            winner_name="Top Contender WW",
            loser_name="Second Contender WW",
            divisions=divisions,
            fighters=fighters,
        )
        
        assert result is not None
        assert result.change_type == TitleChangeType.VACANT_CLAIMED
        assert result.new_champion_id == "contender_ww_1"
        assert divisions["Welterweight"].champion_id == "contender_ww_1"
        assert fighters["contender_ww_1"].is_champion is True
    
    def test_champion_loses_title(self, title_system, divisions, fighters):
        """Should process title changing hands."""
        fight = {
            "is_title_fight": True,
            "weight_class": "Lightweight",
        }
        
        result = title_system.process_title_fight_result(
            fight,
            winner_id="contender_lw_1",
            loser_id="champ_lw",
            winner_name="Top Contender LW",
            loser_name="Champ Lightweight",
            divisions=divisions,
            fighters=fighters,
        )
        
        assert result is not None
        assert result.change_type == TitleChangeType.NEW_CHAMPION
        assert result.new_champion_id == "contender_lw_1"
        assert result.former_champion_id == "champ_lw"
        assert divisions["Lightweight"].champion_id == "contender_lw_1"
        assert fighters["contender_lw_1"].is_champion is True
        assert fighters["champ_lw"].is_champion is False
    
    def test_champion_defends(self, title_system, divisions, fighters):
        """Should process successful title defense."""
        fight = {
            "is_title_fight": True,
            "weight_class": "Lightweight",
        }
        
        result = title_system.process_title_fight_result(
            fight,
            winner_id="champ_lw",
            loser_id="contender_lw_1",
            winner_name="Champ Lightweight",
            loser_name="Top Contender LW",
            divisions=divisions,
            fighters=fighters,
        )
        
        assert result is not None
        assert result.change_type == TitleChangeType.SUCCESSFUL_DEFENSE
        assert result.new_champion_id == "champ_lw"
        # Champion should still be champion
        assert divisions["Lightweight"].champion_id == "champ_lw"
        assert fighters["champ_lw"].is_champion is True
    
    def test_not_title_fight(self, title_system, divisions, fighters):
        """Should return None for non-title fight."""
        fight = {
            "is_title_fight": False,
            "weight_class": "Lightweight",
        }
        
        result = title_system.process_title_fight_result(
            fight, "a", "b", "A", "B", divisions, fighters
        )
        
        assert result is None


class TestStripChampion(TestTitleSystem):
    """Tests for stripping champions."""
    
    def test_strip_champion(self, title_system, divisions, fighters):
        """Should strip champion and vacate title."""
        result = title_system.strip_champion(
            "Lightweight", "injury", divisions, fighters
        )
        
        assert result is not None
        assert result.change_type == TitleChangeType.TITLE_STRIPPED
        assert result.former_champion_id == "champ_lw"
        assert divisions["Lightweight"].champion_id is None
        assert fighters["champ_lw"].is_champion is False
    
    def test_strip_champion_retirement(self, title_system, divisions, fighters):
        """Should use VACATED type for retirement."""
        result = title_system.strip_champion(
            "Lightweight", "retirement", divisions, fighters
        )
        
        assert result.change_type == TitleChangeType.TITLE_VACATED
    
    def test_strip_vacant_division(self, title_system, divisions, fighters):
        """Should return None for already vacant division."""
        result = title_system.strip_champion(
            "Welterweight", "injury", divisions, fighters
        )
        
        assert result is None
    
    def test_strip_unknown_division(self, title_system, divisions, fighters):
        """Should return None for unknown division."""
        result = title_system.strip_champion(
            "Superfight", "injury", divisions, fighters
        )
        
        assert result is None


class TestGetChampionInfo(TestTitleSystem):
    """Tests for getting champion information."""
    
    def test_get_champion_info(self, title_system, divisions, fighters):
        """Should return champion info."""
        info = title_system.get_champion_info("Lightweight", divisions, fighters)
        
        assert info is not None
        assert info["fighter_id"] == "champ_lw"
        assert info["name"] == "Champ Lightweight"
        assert info["weight_class"] == "Lightweight"
    
    def test_get_champion_info_vacant(self, title_system, divisions, fighters):
        """Should return None for vacant division."""
        info = title_system.get_champion_info("Welterweight", divisions, fighters)
        
        assert info is None
    
    def test_get_all_champions(self, title_system, divisions, fighters):
        """Should return all champion info."""
        champs = title_system.get_all_champions(divisions, fighters)
        
        assert len(champs) == 3
        assert champs["Lightweight"] is not None
        assert champs["Welterweight"] is None  # Vacant
        assert champs["Middleweight"] is not None


class TestValidateTitleFight(TestTitleSystem):
    """Tests for title fight validation."""
    
    def test_valid_title_fight_with_champion(self, title_system, divisions, fighters):
        """Should validate title fight with champion."""
        fight = {
            "is_title_fight": True,
            "weight_class": "Lightweight",
            "fighter1_id": "champ_lw",
            "fighter2_id": "contender_lw_1",
        }
        
        is_valid, error = title_system.validate_title_fight(fight, divisions, fighters)
        
        assert is_valid is True
        assert error == ""
    
    def test_valid_vacant_title_fight(self, title_system, divisions, fighters):
        """Should validate vacant title fight."""
        fight = {
            "is_title_fight": True,
            "weight_class": "Welterweight",
            "fighter1_id": "contender_ww_1",
            "fighter2_id": "contender_ww_2",
        }
        
        is_valid, error = title_system.validate_title_fight(fight, divisions, fighters)
        
        assert is_valid is True
    
    def test_invalid_no_champion_not_vacant(self, title_system, divisions, fighters):
        """Should reject title fight without champion in non-vacant division."""
        fight = {
            "is_title_fight": True,
            "weight_class": "Lightweight",
            "fighter1_id": "contender_lw_1",
            "fighter2_id": "contender_lw_2",
        }
        
        is_valid, error = title_system.validate_title_fight(fight, divisions, fighters)
        
        assert is_valid is False
        assert "champion" in error.lower()
    
    def test_not_title_fight_always_valid(self, title_system, divisions, fighters):
        """Should always validate non-title fights."""
        fight = {
            "is_title_fight": False,
            "weight_class": "Lightweight",
            "fighter1_id": "contender_lw_1",
            "fighter2_id": "contender_lw_2",
        }
        
        is_valid, error = title_system.validate_title_fight(fight, divisions, fighters)
        
        assert is_valid is True


class TestGlobalInstance:
    """Tests for global instance function."""
    
    def test_get_title_system_returns_instance(self):
        """Should return a TitleSystem instance."""
        system = get_title_system()
        
        assert isinstance(system, TitleSystem)
    
    def test_get_title_system_same_instance(self):
        """Should return the same instance."""
        system1 = get_title_system()
        system2 = get_title_system()
        
        assert system1 is system2


class TestTitleChangeResult:
    """Tests for TitleChangeResult dataclass."""
    
    def test_to_dict(self):
        """Should convert to dictionary."""
        result = TitleChangeResult(
            change_type=TitleChangeType.NEW_CHAMPION,
            weight_class="Lightweight",
            new_champion_id="fighter_1",
            new_champion_name="New Champ",
            former_champion_id="fighter_2",
            former_champion_name="Old Champ",
            headline="Title change!",
            details="Details here",
        )
        
        d = result.to_dict()
        
        assert d["change_type"] == "new_champion"
        assert d["weight_class"] == "Lightweight"
        assert d["new_champion_id"] == "fighter_1"


class TestVacantTitleFight:
    """Tests for VacantTitleFight dataclass."""
    
    def test_to_fight_dict(self):
        """Should convert to fight dictionary."""
        fight = VacantTitleFight(
            weight_class="Welterweight",
            fighter1_id="f1",
            fighter1_name="Fighter 1",
            fighter2_id="f2",
            fighter2_name="Fighter 2",
            weeks_until=4,
            event_name="DFC 100",
        )
        
        d = fight.to_fight_dict()
        
        assert d["is_title_fight"] is True
        assert d["is_vacant_title"] is True
        assert d["rounds"] == 5
        assert d["fighter1_id"] == "f1"
        assert d["event_name"] == "DFC 100"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
