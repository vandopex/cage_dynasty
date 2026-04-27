# tests/test_contract.py
# Tests for Module 8: Contract System
# Lines: 298

"""
Comprehensive tests for entities/contract.py

Run with: python3 -m pytest tests/test_contract.py -v
"""

import pytest
from core.types import ContractStatus, WeightClass
from core.calendar import GameDate
from entities.contract import (
    ContractTerms, ContractType,
    CampContract, PromotionalContract,
    create_camp_contract, create_promotional_contract,
    ContractManager
)


class TestContractTerms:
    """Tests for ContractTerms dataclass"""
    
    def test_default_terms(self):
        """Terms should have sensible defaults"""
        terms = ContractTerms()
        
        assert terms.base_purse == 10000
        assert terms.win_bonus == 5000
        assert terms.finish_bonus == 2500
        assert terms.camp_cut_percentage == 15.0
    
    def test_custom_terms(self):
        """Terms should accept custom values"""
        terms = ContractTerms(
            base_purse=50000,
            win_bonus=25000,
            ppv_points=True,
            ppv_percentage=1.5
        )
        
        assert terms.base_purse == 50000
        assert terms.ppv_points is True
        assert terms.ppv_percentage == 1.5


class TestCampContract:
    """Tests for CampContract"""
    
    @pytest.fixture
    def contract(self):
        return create_camp_contract(
            fighter_id="fighter_001",
            camp_id="camp_001",
            duration_fights=4,
            camp_cut_percentage=15.0,
            base_purse=20000,
            win_bonus=10000
        )
    
    def test_creation(self, contract):
        """Contract should be created with correct values"""
        assert contract.fighter_id == "fighter_001"
        assert contract.camp_id == "camp_001"
        assert contract.total_fights == 4
        assert contract.fights_remaining == 4
        assert contract.is_active is True
    
    def test_contract_type(self, contract):
        """Should be a camp contract"""
        assert contract.contract_type == ContractType.CAMP
    
    def test_camp_cut_percentage(self, contract):
        """Should have correct camp cut"""
        assert contract.camp_cut_percentage == 15.0
    
    def test_calculate_camp_cut(self, contract):
        """Should calculate camp's cut correctly"""
        cut = contract.calculate_camp_cut(20000)
        assert cut == 3000  # 15% of 20000
    
    def test_record_fight_win(self, contract):
        """Recording a win should pay bonus"""
        payout = contract.record_fight(won=True, was_finish=False)
        
        assert payout == 30000  # 20000 base + 10000 win bonus
        assert contract.fights_completed == 1
        assert contract.fights_remaining == 3
    
    def test_record_fight_finish(self, contract):
        """Finish should pay additional bonus"""
        payout = contract.record_fight(won=True, was_finish=True)
        
        assert payout == 32500  # 20000 + 10000 + 2500
    
    def test_record_fight_loss(self, contract):
        """Loss should only pay base purse"""
        payout = contract.record_fight(won=False)
        
        assert payout == 20000  # Base only
    
    def test_contract_expires(self, contract):
        """Contract should expire when fights completed"""
        for _ in range(4):
            contract.record_fight()
        
        assert contract.is_active is False
        assert contract.is_expired is True
        assert contract.fights_remaining == 0
    
    def test_camp_earnings_tracked(self, contract):
        """Camp earnings should be tracked"""
        contract.record_fight(won=True)  # 30000 payout
        
        expected_cut = int(30000 * 0.15)
        assert contract.camp_earnings == expected_cut
    
    def test_terminate(self, contract):
        """Contract can be terminated early"""
        contract.terminate("Mutual agreement")
        
        assert contract.status == ContractStatus.TERMINATED
        assert contract.is_active is False
    
    def test_extend(self, contract):
        """Contract can be extended"""
        contract.extend(2)
        
        assert contract.total_fights == 6
        assert contract.fights_remaining == 6
    
    def test_serialization(self, contract):
        """Contract should serialize and deserialize"""
        contract.record_fight(won=True)
        
        data = contract.to_dict()
        restored = CampContract.from_dict(data)
        
        assert restored.fighter_id == contract.fighter_id
        assert restored.camp_id == contract.camp_id
        assert restored.fights_completed == contract.fights_completed
        assert restored.total_earnings == contract.total_earnings


class TestPromotionalContract:
    """Tests for PromotionalContract"""
    
    @pytest.fixture
    def contract(self):
        return create_promotional_contract(
            fighter_id="fighter_001",
            promotion_id="dfc_001",
            fights=4,
            base_purse=50000,
            win_bonus=25000,
            weight_class=WeightClass.LIGHTWEIGHT
        )
    
    def test_creation(self, contract):
        """Contract should be created correctly"""
        assert contract.fighter_id == "fighter_001"
        assert contract.promotion_id == "dfc_001"
        assert contract.total_fights == 4
        assert contract.weight_class == WeightClass.LIGHTWEIGHT
        assert contract.is_exclusive is True
    
    def test_contract_type(self, contract):
        """Should be a promotional contract"""
        assert contract.contract_type == ContractType.PROMOTIONAL
    
    def test_base_purse(self, contract):
        """Should have correct base purse"""
        assert contract.base_purse == 50000
    
    def test_win_bonus(self, contract):
        """Should have correct win bonus"""
        assert contract.win_bonus == 25000
    
    def test_record_fight(self, contract):
        """Should record fights correctly"""
        payout = contract.record_fight(won=True, was_finish=True)
        
        assert payout == 80000  # 50000 + 25000 + 5000
        assert contract.fights_completed == 1
    
    def test_record_title_fight(self, contract):
        """Should track title fights"""
        contract.record_fight(won=True, was_title_fight=True)
        
        assert contract.title_fights == 1
    
    def test_record_main_event(self, contract):
        """Should track main events"""
        contract.record_fight(won=True, was_main_event=True)
        
        assert contract.main_events == 1
    
    def test_calculate_title_fight_purse(self, contract):
        """Title fights should pay more"""
        normal_purse = contract.calculate_fight_purse()
        title_purse = contract.calculate_fight_purse(is_title_fight=True)
        
        assert title_purse > normal_purse
        assert title_purse == 100000  # 2x multiplier
    
    def test_calculate_main_event_purse(self, contract):
        """Main events should pay more"""
        normal_purse = contract.calculate_fight_purse()
        main_event_purse = contract.calculate_fight_purse(is_main_event=True)
        
        assert main_event_purse > normal_purse
        assert main_event_purse == 75000  # 1.5x multiplier
    
    def test_ppv_points(self):
        """PPV points should be configurable"""
        contract = create_promotional_contract(
            fighter_id="star_001",
            promotion_id="dfc_001",
            fights=4,
            base_purse=500000,
            ppv_points=True
        )
        
        assert contract.has_ppv_points is True
    
    def test_weight_class_setter(self, contract):
        """Weight class can be changed"""
        contract.weight_class = WeightClass.WELTERWEIGHT
        
        assert contract.weight_class == WeightClass.WELTERWEIGHT
    
    def test_contract_expires(self, contract):
        """Contract should expire when fights completed"""
        for _ in range(4):
            contract.record_fight()
        
        assert contract.is_expired is True
    
    def test_serialization(self, contract):
        """Contract should serialize and deserialize"""
        contract.record_fight(won=True, was_title_fight=True, was_main_event=True)
        
        data = contract.to_dict()
        restored = PromotionalContract.from_dict(data)
        
        assert restored.fighter_id == contract.fighter_id
        assert restored.promotion_id == contract.promotion_id
        assert restored.weight_class == contract.weight_class
        assert restored.title_fights == contract.title_fights
        assert restored.main_events == contract.main_events


class TestContractManager:
    """Tests for ContractManager"""
    
    @pytest.fixture
    def manager(self):
        return ContractManager()
    
    @pytest.fixture
    def camp_contract(self):
        return create_camp_contract(
            fighter_id="fighter_001",
            camp_id="camp_001",
            duration_fights=4
        )
    
    @pytest.fixture
    def promo_contract(self):
        return create_promotional_contract(
            fighter_id="fighter_001",
            promotion_id="dfc_001",
            fights=4
        )
    
    def test_add_camp_contract(self, manager, camp_contract):
        """Should add camp contracts"""
        manager.add_camp_contract(camp_contract)
        
        retrieved = manager.get_camp_contract(camp_contract.id)
        assert retrieved is not None
        assert retrieved.id == camp_contract.id
    
    def test_add_promo_contract(self, manager, promo_contract):
        """Should add promotional contracts"""
        manager.add_promo_contract(promo_contract)
        
        retrieved = manager.get_promo_contract(promo_contract.id)
        assert retrieved is not None
    
    def test_get_fighter_camp_contract(self, manager, camp_contract):
        """Should find fighter's camp contract"""
        manager.add_camp_contract(camp_contract)
        
        contract = manager.get_fighter_camp_contract("fighter_001")
        assert contract is not None
        assert contract.camp_id == "camp_001"
    
    def test_get_fighter_promo_contract(self, manager, promo_contract):
        """Should find fighter's promo contract"""
        manager.add_promo_contract(promo_contract)
        
        contract = manager.get_fighter_promo_contract("fighter_001")
        assert contract is not None
        assert contract.promotion_id == "dfc_001"
    
    def test_get_camp_contracts(self, manager):
        """Should get all contracts for a camp"""
        contract1 = create_camp_contract("fighter_001", "camp_001", 4)
        contract2 = create_camp_contract("fighter_002", "camp_001", 4)
        contract3 = create_camp_contract("fighter_003", "camp_002", 4)
        
        manager.add_camp_contract(contract1)
        manager.add_camp_contract(contract2)
        manager.add_camp_contract(contract3)
        
        camp_001_contracts = manager.get_camp_contracts("camp_001")
        assert len(camp_001_contracts) == 2
    
    def test_get_active_camp_contracts(self, manager):
        """Should only return active contracts"""
        contract1 = create_camp_contract("fighter_001", "camp_001", 4)
        contract2 = create_camp_contract("fighter_002", "camp_001", 4)
        contract2.terminate()
        
        manager.add_camp_contract(contract1)
        manager.add_camp_contract(contract2)
        
        active = manager.get_active_camp_contracts("camp_001")
        assert len(active) == 1
    
    def test_remove_contract(self, manager, camp_contract):
        """Should remove contracts"""
        manager.add_camp_contract(camp_contract)
        
        result = manager.remove_contract(camp_contract.id)
        
        assert result is True
        assert manager.get_camp_contract(camp_contract.id) is None
    
    def test_serialization(self, manager, camp_contract, promo_contract):
        """Manager should serialize and deserialize"""
        manager.add_camp_contract(camp_contract)
        manager.add_promo_contract(promo_contract)
        
        data = manager.to_dict()
        restored = ContractManager.from_dict(data)
        
        assert restored.get_camp_contract(camp_contract.id) is not None
        assert restored.get_promo_contract(promo_contract.id) is not None


class TestFactoryFunctions:
    """Tests for factory functions"""
    
    def test_create_camp_contract(self):
        """Factory should create valid camp contract"""
        contract = create_camp_contract(
            fighter_id="fighter_001",
            camp_id="camp_001",
            duration_fights=6,
            camp_cut_percentage=20.0
        )
        
        assert contract.fighter_id == "fighter_001"
        assert contract.camp_id == "camp_001"
        assert contract.total_fights == 6
        assert contract.camp_cut_percentage == 20.0
    
    def test_create_promotional_contract(self):
        """Factory should create valid promo contract"""
        contract = create_promotional_contract(
            fighter_id="fighter_001",
            promotion_id="dfc_001",
            fights=4,
            base_purse=100000,
            weight_class=WeightClass.HEAVYWEIGHT,
            ppv_points=True
        )
        
        assert contract.fighter_id == "fighter_001"
        assert contract.promotion_id == "dfc_001"
        assert contract.base_purse == 100000
        assert contract.weight_class == WeightClass.HEAVYWEIGHT
        assert contract.has_ppv_points is True


class TestContractExpiration:
    """Tests for contract expiration behavior"""
    
    def test_expired_contract_not_returned_for_fighter(self):
        """Expired contracts shouldn't be returned as active"""
        manager = ContractManager()
        contract = create_camp_contract("fighter_001", "camp_001", 1)
        manager.add_camp_contract(contract)
        
        # Complete the contract
        contract.record_fight()
        
        assert contract.is_expired is True
        assert manager.get_fighter_camp_contract("fighter_001") is None
    
    def test_extend_expired_contract(self):
        """Extending should reactivate expired contract"""
        contract = create_camp_contract("fighter_001", "camp_001", 1)
        contract.record_fight()
        
        assert contract.is_expired is True
        
        contract.extend(2)
        
        assert contract.is_active is True
        assert contract.total_fights == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
