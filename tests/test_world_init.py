# tests/test_world_init.py
# Tests for World Initialization System

"""
Tests for the world initialization system.

Covers:
- Fighter generation
- Camp generation  
- Name generation
- History simulation
- Rankings calculation
- Game state population
"""

import pytest
from simulation.world_init import (
    FighterGenerator,
    CampGenerator,
    HistorySimulator,
    WorldInitializer,
    GeneratedFighter,
    GeneratedCamp,
    initialize_world,
    WEIGHT_CLASSES,
    COUNTRY_NAMES,
)

from core.game_state import GameState


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def fighter_gen():
    """Fighter generator instance"""
    return FighterGenerator()


@pytest.fixture
def camp_gen():
    """Camp generator instance"""
    return CampGenerator()


@pytest.fixture
def game_state():
    """Fresh game state"""
    gs = GameState()
    gs.new_game(player_camp_name="Test Camp", player_name="Tester")
    return gs


# ============================================================================
# FIGHTER GENERATOR TESTS
# ============================================================================

class TestFighterGenerator:
    """Tests for FighterGenerator class"""
    
    def test_creation(self):
        """Should create generator"""
        gen = FighterGenerator()
        assert gen is not None
        assert gen.starting_year == 2025
    
    def test_generate_country(self, fighter_gen):
        """Should generate valid country"""
        for _ in range(20):
            country = fighter_gen.generate_country()
            assert country in COUNTRY_NAMES
    
    def test_generate_name(self, fighter_gen):
        """Should generate valid name"""
        name = fighter_gen.generate_name("United States")
        assert name
        assert " " in name  # Has first and last name
    
    def test_generate_name_unique(self, fighter_gen):
        """Should generate unique names"""
        names = set()
        for _ in range(50):
            name = fighter_gen.generate_name("Brazil")
            names.add(name)
        
        # Should have at least 45 unique names out of 50
        assert len(names) >= 45
    
    def test_generate_attributes(self, fighter_gen):
        """Should generate valid attributes"""
        attrs = fighter_gen.generate_attributes("average")
        
        assert "strength" in attrs
        assert "speed" in attrs
        assert "boxing" in attrs
        assert "wrestling" in attrs
        assert "heart" in attrs
        
        # All values should be 1-100
        for value in attrs.values():
            assert 1 <= value <= 100
    
    def test_generate_attributes_tiers(self, fighter_gen):
        """Should generate attributes based on tier"""
        elite = fighter_gen.generate_attributes("elite")
        novice = fighter_gen.generate_attributes("novice")
        
        # Elite should average higher than novice
        elite_avg = sum(elite.values()) / len(elite)
        novice_avg = sum(novice.values()) / len(novice)
        
        assert elite_avg > novice_avg
    
    def test_generate_fighter(self, fighter_gen):
        """Should generate complete fighter"""
        fighter = fighter_gen.generate_fighter("Lightweight")
        
        assert fighter.fighter_id
        assert fighter.name
        assert fighter.country
        assert fighter.weight_class == "Lightweight"
        assert 146 <= fighter.weight <= 155
        assert fighter.height > 0
        assert fighter.reach > 0
        assert fighter.attributes
        assert fighter.style
        assert fighter.stance
    
    def test_generate_fighter_age_range(self, fighter_gen):
        """Should respect age range"""
        for _ in range(20):
            fighter = fighter_gen.generate_fighter(
                "Welterweight",
                age_range=(25, 30)
            )
            assert 25 <= fighter.age <= 30
    
    def test_generate_all_weight_classes(self, fighter_gen):
        """Should generate fighters for all weight classes"""
        for weight_class in WEIGHT_CLASSES:
            fighter = fighter_gen.generate_fighter(weight_class)
            assert fighter.weight_class == weight_class


class TestFighterGeneratorAttributes:
    """Detailed tests for attribute generation"""
    
    def test_elite_tier_range(self, fighter_gen):
        """Elite tier should have high stats"""
        attrs = fighter_gen.generate_attributes("elite")
        avg = sum(attrs.values()) / len(attrs)
        assert avg >= 60  # Elite averages at least 60
    
    def test_novice_tier_range(self, fighter_gen):
        """Novice tier should have lower stats"""
        attrs = fighter_gen.generate_attributes("novice")
        avg = sum(attrs.values()) / len(attrs)
        assert avg <= 55  # Novice averages at most 55
    
    def test_all_attributes_present(self, fighter_gen):
        """Should have all expected attributes"""
        attrs = fighter_gen.generate_attributes("average")
        
        expected = [
            "strength", "speed", "cardio", "chin", "recovery",
            "boxing", "kicks", "clinch", "power", "accuracy",
            "wrestling", "bjj", "takedown_defense", "top_control", "submissions",
            "heart", "iq", "composure"
        ]
        
        for attr in expected:
            assert attr in attrs


# ============================================================================
# CAMP GENERATOR TESTS
# ============================================================================

class TestCampGenerator:
    """Tests for CampGenerator class"""
    
    def test_creation(self):
        """Should create generator"""
        gen = CampGenerator()
        assert gen is not None
    
    def test_generate_name(self, camp_gen):
        """Should generate camp name"""
        name = camp_gen.generate_name()
        assert name
        assert len(name) > 5
    
    def test_generate_name_unique(self, camp_gen):
        """Should generate unique names"""
        names = set()
        for _ in range(30):
            name = camp_gen.generate_name()
            names.add(name)
        
        assert len(names) >= 25
    
    def test_generate_camp(self, camp_gen):
        """Should generate complete camp"""
        camp = camp_gen.generate_camp()
        
        assert camp.camp_id
        assert camp.name
        assert camp.location
        assert camp.tier in ["GARAGE", "LOCAL", "REGIONAL", "NATIONAL", "ELITE"]
        assert camp.reputation >= 0
        assert camp.balance >= 0
        assert isinstance(camp.fighter_ids, list)
    
    def test_generate_camp_specific_tier(self, camp_gen):
        """Should generate camp with specific tier"""
        for tier in ["GARAGE", "LOCAL", "REGIONAL", "NATIONAL", "ELITE"]:
            camp = camp_gen.generate_camp(tier=tier)
            assert camp.tier == tier
    
    def test_tier_affects_stats(self, camp_gen):
        """Higher tiers should have better stats"""
        garage = camp_gen.generate_camp(tier="GARAGE")
        elite = camp_gen.generate_camp(tier="ELITE")
        
        assert elite.reputation > garage.reputation
        assert elite.balance > garage.balance


# ============================================================================
# HISTORY SIMULATOR TESTS
# ============================================================================

class TestHistorySimulator:
    """Tests for HistorySimulator class"""
    
    @pytest.fixture
    def fighters_dict(self, fighter_gen):
        """Generate some fighters for testing"""
        fighters = {}
        for _ in range(20):
            fighter = fighter_gen.generate_fighter("Lightweight")
            fighters[fighter.fighter_id] = fighter
        return fighters
    
    def test_creation(self, fighters_dict):
        """Should create simulator"""
        sim = HistorySimulator(fighters_dict)
        assert sim is not None
        assert len(sim.fighters) == 20
    
    def test_simulate_fight(self, fighters_dict):
        """Should simulate a fight"""
        sim = HistorySimulator(fighters_dict)
        
        fighter_ids = list(fighters_dict.keys())
        f1_id, f2_id = fighter_ids[0], fighter_ids[1]
        
        fight = sim.simulate_fight(f1_id, f2_id)
        
        assert fight.winner_id in (f1_id, f2_id)
        assert fight.loser_id in (f1_id, f2_id)
        assert fight.winner_id != fight.loser_id
        assert fight.method in ("KO", "TKO", "SUB", "DEC", "SPLIT")
        assert 1 <= fight.round_ended <= 3
    
    def test_simulate_fight_updates_records(self, fighters_dict):
        """Should update fighter records"""
        sim = HistorySimulator(fighters_dict)
        
        fighter_ids = list(fighters_dict.keys())
        f1, f2 = fighters_dict[fighter_ids[0]], fighters_dict[fighter_ids[1]]
        
        initial_f1_wins = f1.wins
        initial_f2_wins = f2.wins
        
        sim.simulate_fight(f1.fighter_id, f2.fighter_id)
        
        # One should have gained a win
        total_new_wins = (f1.wins - initial_f1_wins) + (f2.wins - initial_f2_wins)
        assert total_new_wins == 1
    
    def test_simulate_title_fight(self, fighters_dict):
        """Should handle title fights"""
        sim = HistorySimulator(fighters_dict)
        
        fighter_ids = list(fighters_dict.keys())
        fight = sim.simulate_fight(fighter_ids[0], fighter_ids[1], is_title_fight=True)
        
        assert fight.was_title_fight is True
        
        # Winner should be champion
        winner = fighters_dict[fight.winner_id]
        assert winner.is_champion is True
    
    def test_simulate_history(self, fighters_dict):
        """Should simulate multiple weeks of history"""
        sim = HistorySimulator(fighters_dict)
        sim.simulate_history(weeks=10)
        
        # Should have simulated fights
        assert len(sim.fight_history) > 0
        
        # Fighters should have records
        total_wins = sum(f.wins for f in fighters_dict.values())
        total_losses = sum(f.losses for f in fighters_dict.values())
        
        # Every fight has one winner and one loser
        # Total wins should equal total losses
        assert total_wins == total_losses
    
    def test_calculate_rankings(self, fighters_dict):
        """Should calculate rankings"""
        sim = HistorySimulator(fighters_dict)
        sim.simulate_history(weeks=20)
        
        rankings = sim.calculate_rankings()
        
        assert "Lightweight" in rankings
        assert len(rankings["Lightweight"]) > 0


# ============================================================================
# WORLD INITIALIZER TESTS
# ============================================================================

class TestWorldInitializer:
    """Tests for WorldInitializer class"""
    
    def test_creation(self, game_state):
        """Should create initializer"""
        init = WorldInitializer(game_state)
        assert init is not None
        assert init.game_state is game_state
    
    def test_generate_fighters(self, game_state):
        """Should generate fighters for all divisions"""
        init = WorldInitializer(game_state)
        init.generate_fighters()
        
        assert len(init.fighters) > 100  # At least 100 fighters
        
        # Should have fighters in all weight classes
        weight_classes_present = set(f.weight_class for f in init.fighters.values())
        assert weight_classes_present == set(WEIGHT_CLASSES)
    
    def test_generate_camps(self, game_state):
        """Should generate AI camps"""
        init = WorldInitializer(game_state)
        init.generate_camps()
        
        assert len(init.camps) >= 20
        
        # Should have various tiers
        tiers = set(c.tier for c in init.camps.values())
        assert len(tiers) >= 3
    
    def test_assign_fighters_to_camps(self, game_state):
        """Should assign all fighters to camps"""
        init = WorldInitializer(game_state)
        init.generate_fighters()
        init.generate_camps()
        init.assign_fighters_to_camps()
        
        # All fighters should have a camp
        for fighter in init.fighters.values():
            assert fighter.camp_id is not None
            assert fighter.camp_id in init.camps
        
        # Most camps should have fighters (allow for edge cases)
        camps_with_fighters = sum(1 for c in init.camps.values() if len(c.fighter_ids) > 0)
        assert camps_with_fighters >= len(init.camps) - 2  # Allow up to 2 empty
    
    def test_simulate_history(self, game_state):
        """Should simulate fight history"""
        init = WorldInitializer(game_state, history_weeks=50)
        init.generate_fighters()
        init.generate_camps()
        init.assign_fighters_to_camps()
        init.simulate_history()
        
        # Should have rankings and title holders
        assert hasattr(init, '_rankings')
        assert hasattr(init, '_title_holders')
        
        # Should have champions
        assert len(init._title_holders) > 0
        
        # Fighters should have records
        total_wins = sum(f.wins for f in init.fighters.values())
        assert total_wins > 0
    
    def test_populate_game_state(self, game_state):
        """Should populate game state with generated content"""
        init = WorldInitializer(game_state, history_weeks=30)
        init.generate_fighters()
        init.generate_camps()
        init.assign_fighters_to_camps()
        init.simulate_history()
        init.populate_game_state()
        
        # Game state should have fighters
        assert len(game_state.fighters) > 100
        
        # Game state should have camps (including player camp)
        assert len(game_state.camps) > 20
    
    def test_full_initialization(self, game_state):
        """Should complete full initialization"""
        init = WorldInitializer(game_state, history_weeks=30)
        init.initialize_world()
        
        # Verify everything is set up
        assert len(init.fighters) > 100
        assert len(init.camps) > 20
        
        # Should have some champions (not necessarily all 9 if short simulation)
        assert len(init._title_holders) >= 5
        
        # Game state should be populated
        assert len(game_state.fighters) > 100


class TestWorldInitializerDivisions:
    """Tests for division-specific initialization"""
    
    def test_all_divisions_have_fighters(self, game_state):
        """Each division should have fighters"""
        init = WorldInitializer(game_state, history_weeks=20)
        init.generate_fighters()
        
        for weight_class in WEIGHT_CLASSES:
            division_fighters = [
                f for f in init.fighters.values()
                if f.weight_class == weight_class
            ]
            assert len(division_fighters) >= 10
    
    def test_most_divisions_have_champion(self, game_state):
        """Most divisions should have a champion after history"""
        init = WorldInitializer(game_state, history_weeks=80)  # More weeks for better coverage
        init.generate_fighters()
        init.generate_camps()
        init.assign_fighters_to_camps()
        init.simulate_history()
        
        # With enough simulation, most divisions should have champions
        champions_count = sum(1 for wc in WEIGHT_CLASSES if wc in init._title_holders)
        assert champions_count >= 7  # At least 7 of 9 divisions


class TestConvenienceFunction:
    """Tests for initialize_world convenience function"""
    
    def test_initialize_world(self, game_state):
        """Should initialize world via convenience function"""
        init = initialize_world(game_state, history_years=1.0)
        
        assert init is not None
        assert len(init.fighters) > 100
        assert len(game_state.fighters) > 100


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestWorldInitIntegration:
    """Integration tests for complete world initialization"""
    
    def test_fighters_have_valid_data(self, game_state):
        """Generated fighters should have valid data"""
        init = WorldInitializer(game_state, history_weeks=30)
        init.initialize_world()
        
        for fighter in init.fighters.values():
            assert fighter.name
            assert fighter.weight_class in WEIGHT_CLASSES
            assert fighter.age >= 18
            assert fighter.camp_id
            assert fighter.wins >= 0
            assert fighter.losses >= 0
    
    def test_camps_have_valid_data(self, game_state):
        """Generated camps should have valid data"""
        init = WorldInitializer(game_state, history_weeks=30)
        init.initialize_world()
        
        for camp in init.camps.values():
            assert camp.name
            assert camp.tier in ["GARAGE", "LOCAL", "REGIONAL", "NATIONAL", "ELITE"]
            assert camp.balance >= 0
            assert camp.reputation >= 0
            # Most camps should have fighters
            # (don't require ALL to have fighters due to edge cases)
    
    def test_rankings_make_sense(self, game_state):
        """Rankings should be based on records"""
        init = WorldInitializer(game_state, history_weeks=60)
        init.initialize_world()
        
        # Check a division's rankings
        for weight_class in WEIGHT_CLASSES:
            ranked_ids = init._rankings.get(weight_class, [])
            
            if len(ranked_ids) >= 2:
                # Higher ranked fighters should generally have better records
                # (This is probabilistic, so we just check it's not random)
                top_fighter = init.fighters[ranked_ids[0]]
                assert top_fighter.wins > 0 or top_fighter.is_champion


class TestNameGeneration:
    """Tests for name generation edge cases"""
    
    def test_all_countries_have_names(self):
        """All countries should have name data"""
        for country in COUNTRY_NAMES:
            assert "first" in COUNTRY_NAMES[country]
            assert "last" in COUNTRY_NAMES[country]
            assert len(COUNTRY_NAMES[country]["first"]) >= 10
            assert len(COUNTRY_NAMES[country]["last"]) >= 10
    
    def test_no_duplicate_names_in_large_batch(self, fighter_gen):
        """Should handle generating many names without duplicates"""
        names = set()
        for _ in range(200):
            name = fighter_gen.generate_name(fighter_gen.generate_country())
            names.add(name)
        
        # Should have at least 180 unique names out of 200
        assert len(names) >= 180
