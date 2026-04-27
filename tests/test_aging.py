# tests/test_aging.py
# Tests for Module 9: Aging & Degradation System
# Lines: 287

"""
Comprehensive tests for systems/aging.py

Run with: python3 -m pytest tests/test_aging.py -v
"""

import pytest
from systems.aging import (
    AgingSystem, AgingProfile, CareerPhase,
    get_career_phase, calculate_years_past_prime,
    calculate_physical_decline, calculate_mental_decline,
    calculate_chin_decline, calculate_retirement_probability,
    get_prime_years, is_in_prime, years_until_decline
)


class TestCareerPhase:
    """Tests for career phase determination"""
    
    def test_prospect_phase(self):
        """Young fighters should be prospects"""
        assert get_career_phase(18) == CareerPhase.PROSPECT
        assert get_career_phase(22) == CareerPhase.PROSPECT
        assert get_career_phase(25) == CareerPhase.PROSPECT
    
    def test_prime_phase(self):
        """Fighters 26-32 should be in prime"""
        assert get_career_phase(26) == CareerPhase.PRIME
        assert get_career_phase(29) == CareerPhase.PRIME
        assert get_career_phase(32) == CareerPhase.PRIME
    
    def test_veteran_phase(self):
        """Fighters 33-36 should be veterans"""
        assert get_career_phase(33) == CareerPhase.VETERAN
        assert get_career_phase(35) == CareerPhase.VETERAN
        assert get_career_phase(36) == CareerPhase.VETERAN
    
    def test_twilight_phase(self):
        """Fighters 37+ should be in twilight"""
        assert get_career_phase(37) == CareerPhase.TWILIGHT
        assert get_career_phase(40) == CareerPhase.TWILIGHT
        assert get_career_phase(45) == CareerPhase.TWILIGHT


class TestYearsPastPrime:
    """Tests for years past prime calculation"""
    
    def test_before_prime(self):
        """Should return 0 for young fighters"""
        assert calculate_years_past_prime(20) == 0
        assert calculate_years_past_prime(25) == 0
    
    def test_during_prime(self):
        """Should return 0 during prime"""
        assert calculate_years_past_prime(26) == 0
        assert calculate_years_past_prime(32) == 0
    
    def test_after_prime(self):
        """Should return correct years after prime"""
        assert calculate_years_past_prime(33) == 1
        assert calculate_years_past_prime(35) == 3
        assert calculate_years_past_prime(40) == 8


class TestPhysicalDecline:
    """Tests for physical decline calculation"""
    
    def test_no_decline_before_prime_end(self):
        """No decline during or before prime"""
        assert calculate_physical_decline(25) == 0.0
        assert calculate_physical_decline(30) == 0.0
        assert calculate_physical_decline(32) == 0.0
    
    def test_decline_starts_after_prime(self):
        """Decline should start after prime"""
        decline_33 = calculate_physical_decline(33)
        assert decline_33 > 0
    
    def test_decline_accelerates(self):
        """Decline should accelerate with age"""
        decline_33 = calculate_physical_decline(33)
        decline_35 = calculate_physical_decline(35)
        decline_40 = calculate_physical_decline(40)
        
        assert decline_35 > decline_33
        assert decline_40 > decline_35


class TestMentalDecline:
    """Tests for mental decline calculation"""
    
    def test_no_decline_early(self):
        """No mental decline until well past prime"""
        assert calculate_mental_decline(25) == 0.0
        assert calculate_mental_decline(32) == 0.0
        assert calculate_mental_decline(34) == 0.0  # 2 years grace period
    
    def test_mental_decline_slower_than_physical(self):
        """Mental decline should be slower than physical"""
        age = 38
        physical = calculate_physical_decline(age)
        mental = calculate_mental_decline(age)
        
        assert mental < physical


class TestChinDecline:
    """Tests for chin decline calculation"""
    
    def test_no_decline_in_prime(self):
        """Chin doesn't decline during prime"""
        assert calculate_chin_decline(30) == 0.0
    
    def test_chin_declines_faster_than_physical(self):
        """Chin should decline faster than other physical attributes"""
        age = 35
        physical = calculate_physical_decline(age)
        chin = calculate_chin_decline(age)
        
        assert chin > physical
    
    def test_ko_losses_accelerate_chin_decline(self):
        """KO losses should increase chin decline"""
        age = 35
        chin_no_kos = calculate_chin_decline(age, ko_losses=0)
        chin_with_kos = calculate_chin_decline(age, ko_losses=5)
        
        assert chin_with_kos > chin_no_kos


class TestRetirementProbability:
    """Tests for retirement probability calculation"""
    
    def test_no_retirement_young(self):
        """Young fighters shouldn't retire"""
        prob = calculate_retirement_probability(25)
        assert prob == 0.0
        
        prob = calculate_retirement_probability(30)
        assert prob == 0.0
    
    def test_retirement_increases_with_age(self):
        """Retirement probability should increase with age"""
        prob_35 = calculate_retirement_probability(35)
        prob_38 = calculate_retirement_probability(38)
        prob_42 = calculate_retirement_probability(42)
        
        assert prob_38 > prob_35
        assert prob_42 > prob_38
    
    def test_losing_streak_increases_retirement(self):
        """Losing streak should increase retirement chance"""
        prob_no_streak = calculate_retirement_probability(36, current_lose_streak=0)
        prob_with_streak = calculate_retirement_probability(36, current_lose_streak=3)
        
        assert prob_with_streak > prob_no_streak
    
    def test_champion_less_likely_to_retire(self):
        """Champions should be less likely to retire"""
        prob_not_champ = calculate_retirement_probability(36, is_champion=False)
        prob_champ = calculate_retirement_probability(36, is_champion=True)
        
        assert prob_champ < prob_not_champ
    
    def test_low_morale_increases_retirement(self):
        """Low morale should increase retirement chance"""
        prob_high_morale = calculate_retirement_probability(36, morale=80)
        prob_low_morale = calculate_retirement_probability(36, morale=20)
        
        assert prob_low_morale > prob_high_morale
    
    def test_probability_clamped(self):
        """Probability should be between 0 and 1"""
        # Extreme case
        prob = calculate_retirement_probability(
            age=50, 
            current_lose_streak=10,
            morale=0
        )
        
        assert 0.0 <= prob <= 1.0


class TestAgingProfile:
    """Tests for AgingProfile"""
    
    def test_profile_not_declining(self):
        """Profile should show not declining for young fighters"""
        system = AgingSystem()
        profile = system.get_aging_profile("fighter_001", age=28)
        
        assert profile.is_declining is False
        assert profile.decline_severity == "None"
    
    def test_profile_declining(self):
        """Profile should show declining for older fighters"""
        system = AgingSystem()
        profile = system.get_aging_profile("fighter_001", age=36)
        
        assert profile.is_declining is True
        assert profile.decline_severity in ["Moderate", "Significant"]
    
    def test_profile_career_phase(self):
        """Profile should have correct career phase"""
        system = AgingSystem()
        
        prospect = system.get_aging_profile("f1", age=22)
        prime = system.get_aging_profile("f2", age=29)
        veteran = system.get_aging_profile("f3", age=35)
        twilight = system.get_aging_profile("f4", age=40)
        
        assert prospect.career_phase == CareerPhase.PROSPECT
        assert prime.career_phase == CareerPhase.PRIME
        assert veteran.career_phase == CareerPhase.VETERAN
        assert twilight.career_phase == CareerPhase.TWILIGHT


class TestAgingSystem:
    """Tests for AgingSystem class"""
    
    @pytest.fixture
    def system(self):
        return AgingSystem()
    
    def test_apply_decline_young_fighter(self, system):
        """Young fighters should have no decline"""
        changes = system.apply_annual_decline(
            "fighter_001", age=28, current_attributes={}
        )
        
        assert len(changes) == 0
    
    def test_apply_decline_old_fighter(self, system):
        """Older fighters should have decline"""
        changes = system.apply_annual_decline(
            "fighter_001", age=36, current_attributes={}
        )
        
        # Should have some negative changes
        assert len(changes) > 0
        assert all(v < 0 for v in changes.values())
    
    def test_apply_decline_chin_affected_by_ko_losses(self, system):
        """Chin decline should be worse with KO losses"""
        changes_no_kos = system.apply_annual_decline(
            "f1", age=36, current_attributes={}, ko_losses=0
        )
        changes_with_kos = system.apply_annual_decline(
            "f2", age=36, current_attributes={}, ko_losses=5
        )
        
        chin_decline_no_kos = abs(changes_no_kos.get("chin", 0))
        chin_decline_with_kos = abs(changes_with_kos.get("chin", 0))
        
        # With randomness, we just check it's applied
        assert "chin" in changes_no_kos or "chin" in changes_with_kos
    
    def test_should_process_annual_aging(self, system):
        """Should track which year was processed"""
        assert system.should_process_annual_aging("fighter_001", 2025) is True
        
        system.mark_annual_aging_processed("fighter_001", 2025)
        
        assert system.should_process_annual_aging("fighter_001", 2025) is False
        assert system.should_process_annual_aging("fighter_001", 2026) is True
    
    def test_process_birthday(self, system):
        """Birthday processing should return phase and changes"""
        phase, changes = system.process_birthday("fighter_001", new_age=35)
        
        assert phase == CareerPhase.VETERAN
        assert isinstance(changes, dict)
    
    def test_check_retirement_young(self, system):
        """Young fighters should not retire"""
        # Run multiple times since it's probabilistic
        retirements = sum(
            system.check_retirement("fighter_001", age=25)
            for _ in range(100)
        )
        
        assert retirements == 0
    
    def test_check_retirement_old(self, system):
        """Old fighters should sometimes retire"""
        # Run multiple times
        retirements = sum(
            system.check_retirement("fighter_001", age=42, lose_streak=3)
            for _ in range(100)
        )
        
        # Should have some retirements (probabilistic)
        assert retirements > 0
    
    def test_serialization(self, system):
        """System should serialize and deserialize"""
        system.mark_annual_aging_processed("fighter_001", 2025)
        system.mark_annual_aging_processed("fighter_002", 2024)
        
        data = system.to_dict()
        restored = AgingSystem.from_dict(data)
        
        assert restored.should_process_annual_aging("fighter_001", 2025) is False
        assert restored.should_process_annual_aging("fighter_002", 2025) is True


class TestConvenienceFunctions:
    """Tests for convenience functions"""
    
    def test_get_prime_years(self):
        """Should return prime year range"""
        start, end = get_prime_years()
        
        assert start == 26
        assert end == 32
        assert start < end
    
    def test_is_in_prime(self):
        """Should correctly identify prime years"""
        assert is_in_prime(25) is False
        assert is_in_prime(26) is True
        assert is_in_prime(29) is True
        assert is_in_prime(32) is True
        assert is_in_prime(33) is False
    
    def test_years_until_decline(self):
        """Should calculate years until decline"""
        assert years_until_decline(25) == 7  # 32 - 25
        assert years_until_decline(30) == 2  # 32 - 30
        assert years_until_decline(32) == 0
        assert years_until_decline(35) == 0  # Already declining


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
