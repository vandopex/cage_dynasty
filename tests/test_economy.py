# tests/test_economy.py
# Complete test suite for economy system
# Lines: ~730

"""
Tests for the economy system.
"""

import pytest
from typing import Dict, Any

from systems.economy import (
    TransactionType, LoanStatus, SponsorTier,
    Transaction, Loan, Sponsorship, CampSponsorship, UpgradeRequirement,
    CampFinanceState, FightEarnings, WeeklyFinanceSummary,
    EconomyManager, create_economy_manager,
    get_purse_tier, calculate_base_purse, calculate_main_event_bonus,
    determine_sponsor_tier, generate_sponsorship_offer, generate_camp_sponsorship_offer,
    get_upgrade_requirement, get_next_tier, format_money, get_fighter_overhead_cost,
    BASE_PURSE_BY_TIER, CAMP_MONTHLY_COSTS, FIGHTER_OVERHEAD_BY_TIER,
    LOAN_CONFIG, UPGRADE_REQUIREMENTS, PERFORMANCE_BONUSES,
    WIN_BONUS_MULTIPLIER, TITLE_FIGHT_MULTIPLIER,
    MAIN_EVENT_BONUS, MAIN_EVENT_TITLE_BONUS, CO_MAIN_EVENT_BONUS,
)


@pytest.fixture
def economy_manager():
    return create_economy_manager()


class TestFormatMoney:
    def test_format_positive_with_sign(self):
        assert format_money(500) == "+$500"
    
    def test_format_positive_thousands(self):
        assert format_money(1000) == "+$1,000"
    
    def test_format_positive_millions(self):
        assert format_money(1000000) == "+$1,000,000"
    
    def test_format_positive_without_sign(self):
        assert format_money(500, include_sign=False) == "$500"
    
    def test_format_negative(self):
        assert format_money(-500) == "-$500"
    
    def test_format_zero(self):
        assert format_money(0) == "$0"


class TestGetPurseTier:
    def test_champion_tier(self):
        assert get_purse_tier(1, True, 10) == "champion"
    
    def test_debut_tier(self):
        assert get_purse_tier(None, False, 0) == "debut"
    
    def test_ranked_tiers(self):
        assert get_purse_tier(1, False, 10) == "top_5"
        assert get_purse_tier(6, False, 10) == "top_10"
        assert get_purse_tier(11, False, 10) == "top_15"
        assert get_purse_tier(16, False, 10) == "ranked"
    
    def test_unranked_tier(self):
        assert get_purse_tier(None, False, 5) == "unranked"


class TestCalculateBasePurse:
    def test_champion_purse(self):
        purse = calculate_base_purse(rank=1, is_champion=True, total_fights=20)
        assert purse == BASE_PURSE_BY_TIER["champion"]
    
    def test_title_fight_multiplier(self):
        base = calculate_base_purse(rank=3, is_champion=False, total_fights=10)
        title = calculate_base_purse(rank=3, is_champion=False, total_fights=10, is_title_fight=True)
        assert title == int(base * TITLE_FIGHT_MULTIPLIER)


class TestCalculateMainEventBonus:
    def test_main_event_bonus(self):
        assert calculate_main_event_bonus(is_main_event=True, is_title_fight=False) == MAIN_EVENT_BONUS
    
    def test_main_event_title_bonus(self):
        assert calculate_main_event_bonus(is_main_event=True, is_title_fight=True) == MAIN_EVENT_TITLE_BONUS
    
    def test_co_main_bonus(self):
        assert calculate_main_event_bonus(is_co_main=True) == CO_MAIN_EVENT_BONUS
    
    def test_regular_fight_no_bonus(self):
        assert calculate_main_event_bonus() == 0


class TestDetermineSponsorTier:
    def test_champion_gets_elite(self):
        assert determine_sponsor_tier(rank=1, is_champion=True) == SponsorTier.ELITE
    
    def test_ranked_gets_ranked(self):
        assert determine_sponsor_tier(rank=10, is_champion=False) == SponsorTier.RANKED
    
    def test_unranked_low_market_gets_local(self):
        assert determine_sponsor_tier(rank=None, is_champion=False, marketability=40) == SponsorTier.LOCAL


class TestFighterOverheadCost:
    def test_overhead_by_tier(self):
        assert get_fighter_overhead_cost("GARAGE") == FIGHTER_OVERHEAD_BY_TIER["GARAGE"]
        assert get_fighter_overhead_cost("ELITE") == FIGHTER_OVERHEAD_BY_TIER["ELITE"]
    
    def test_overhead_increases_with_tier(self):
        assert get_fighter_overhead_cost("GARAGE") < get_fighter_overhead_cost("LOCAL")
        assert get_fighter_overhead_cost("LOCAL") < get_fighter_overhead_cost("ELITE")


class TestGetNextTier:
    def test_progression(self):
        assert get_next_tier("GARAGE") == "LOCAL"
        assert get_next_tier("NATIONAL") == "ELITE"
    
    def test_elite_has_no_next(self):
        assert get_next_tier("ELITE") is None


class TestTransaction:
    def test_create_transaction(self):
        trans = Transaction(
            transaction_id="tx_001",
            transaction_type=TransactionType.FIGHT_PURSE,
            amount=50000,
            description="Fight purse",
            camp_id="camp_001",
        )
        assert trans.amount == 50000
        assert trans.is_income is True
    
    def test_formatted_amount(self):
        income = Transaction(
            transaction_id="tx_003",
            transaction_type=TransactionType.WIN_BONUS,
            amount=10000,
            description="Win bonus",
            camp_id="camp_001",
        )
        assert income.formatted_amount == "+$10,000"
    
    def test_serialization(self):
        trans = Transaction(
            transaction_id="tx_005",
            transaction_type=TransactionType.SPONSORSHIP_PAYMENT,
            amount=5000,
            description="Sponsor payment",
            camp_id="camp_001",
        )
        data = trans.to_dict()
        restored = Transaction.from_dict(data)
        assert restored.transaction_id == trans.transaction_id


class TestLoan:
    def test_create_loan(self):
        loan = Loan(
            loan_id="loan_001",
            camp_id="camp_001",
            principal=20000,
            current_balance=20000,
            interest_rate=0.06,
            min_payment_pct=0.05,
        )
        assert loan.principal == 20000
        assert loan.status == LoanStatus.ACTIVE
    
    def test_weekly_interest(self):
        loan = Loan(
            loan_id="loan_002",
            camp_id="camp_001",
            principal=20000,
            current_balance=20000,
            interest_rate=0.08,
            min_payment_pct=0.05,
        )
        expected = int(20000 * (0.08 / 4))
        assert loan.weekly_interest == expected
    
    def test_make_payment(self):
        loan = Loan(
            loan_id="loan_003",
            camp_id="camp_001",
            principal=10000,
            current_balance=10000,
            interest_rate=0.04,
            min_payment_pct=0.05,
        )
        initial_balance = loan.current_balance
        loan.make_payment(2000)
        assert loan.current_balance < initial_balance
    
    def test_pay_off_loan(self):
        loan = Loan(
            loan_id="loan_004",
            camp_id="camp_001",
            principal=5000,
            current_balance=5000,
            interest_rate=0.04,
            min_payment_pct=0.05,
        )
        loan.make_payment(6000)
        assert loan.is_paid_off is True


class TestSponsorship:
    def test_create_sponsorship(self):
        sponsor = Sponsorship(
            company_name="Test Sponsor",
            payment_per_fight=5000,
            fights_total=4,
            fights_remaining=4,
            tier=SponsorTier.RANKED,
        )
        assert sponsor.payment_per_fight == 5000
        assert sponsor.is_active is True
    
    def test_process_fight(self):
        sponsor = Sponsorship(
            company_name="Test Sponsor",
            payment_per_fight=3000,
            fights_total=3,
            fights_remaining=3,
        )
        payment = sponsor.process_fight()
        assert payment == 3000
        assert sponsor.fights_remaining == 2
    
    def test_expired_sponsorship(self):
        sponsor = Sponsorship(
            company_name="Test Sponsor",
            payment_per_fight=2000,
            fights_total=1,
            fights_remaining=1,
        )
        sponsor.process_fight()
        assert sponsor.is_active is False


class TestUpgradeRequirement:
    def test_check_eligibility_all_met(self):
        req = UpgradeRequirement(
            target_tier="LOCAL",
            cost=50000,
            reputation_needed=40,
            championships_needed=1,
            min_roster=5,
        )
        eligible, unmet = req.check_eligibility(
            balance=60000, reputation=50, championships=0, roster_size=3,
        )
        assert eligible is True
    
    def test_check_eligibility_insufficient_funds(self):
        req = UpgradeRequirement(
            target_tier="LOCAL",
            cost=50000,
            reputation_needed=40,
            championships_needed=1,
            min_roster=5,
        )
        eligible, unmet = req.check_eligibility(
            balance=30000, reputation=50, championships=0, roster_size=3,
        )
        assert eligible is False
    
    def test_check_eligibility_by_championships(self):
        req = UpgradeRequirement(
            target_tier="REGIONAL",
            cost=150000,
            reputation_needed=55,
            championships_needed=2,
            min_roster=10,
        )
        eligible, unmet = req.check_eligibility(
            balance=200000, reputation=40, championships=3, roster_size=5,
        )
        assert eligible is True


class TestCampFinanceState:
    def test_create_state(self):
        state = CampFinanceState(camp_id="camp1", balance=50000)
        assert state.balance == 50000
        assert state.total_debt == 0
        assert state.net_worth == 50000
    
    def test_debt_calculation(self):
        state = CampFinanceState(camp_id="camp1", balance=100000)
        state.active_loans.append(Loan(
            loan_id="loan1",
            camp_id="camp1",
            principal=20000,
            current_balance=18000,
            interest_rate=0.05,
            min_payment_pct=0.05,
        ))
        assert state.total_debt == 18000
        assert state.has_active_loan is True
    
    def test_is_in_debt(self):
        state = CampFinanceState(camp_id="camp1", balance=-5000)
        assert state.is_in_debt is True


class TestEconomyManagerBasics:
    def test_create_manager(self):
        manager = create_economy_manager()
        assert manager is not None
    
    def test_get_camp_finances(self):
        manager = create_economy_manager()
        state = manager.get_camp_finances("new_camp")
        assert state.camp_id == "new_camp"
        assert state.balance == 0
    
    def test_set_camp_balance(self):
        manager = create_economy_manager()
        manager.set_camp_balance("camp1", 50000)
        assert manager.get_balance("camp1") == 50000
    
    def test_add_income(self):
        manager = create_economy_manager()
        manager.set_camp_balance("camp1", 10000)
        manager.add_income("camp1", 5000, TransactionType.WIN_BONUS, "Test bonus")
        assert manager.get_balance("camp1") == 15000
    
    def test_deduct_expense(self):
        manager = create_economy_manager()
        manager.set_camp_balance("camp1", 10000)
        manager.deduct_expense("camp1", 3000, TransactionType.FACILITY_COST, "Test cost")
        assert manager.get_balance("camp1") == 7000


class TestWeeklyFinanceProcessing:
    def test_process_basic_week(self):
        manager = create_economy_manager()
        manager.set_camp_balance("camp1", 50000)
        
        summary = manager.process_weekly_finances(
            camp_id="camp1",
            tier="GARAGE",
            roster_size=3,
            coach_count=1,
            coach_salaries=2000,
            week=1,
            date="Week 1",
        )
        
        assert summary.opening_balance == 50000
        assert summary.facility_costs == CAMP_MONTHLY_COSTS["GARAGE"] // 4
        expected_overhead = 3 * FIGHTER_OVERHEAD_BY_TIER["GARAGE"]
        assert summary.fighter_overhead == expected_overhead
        assert summary.closing_balance < 50000


class TestLoanSystem:
    def test_take_loan(self):
        manager = create_economy_manager()
        manager.set_camp_balance("camp1", 10000)
        
        loan = manager.take_loan(camp_id="camp1", amount=20000, tier="GARAGE")
        
        assert loan is not None
        assert loan.principal == 20000
        assert manager.get_balance("camp1") == 30000
    
    def test_take_loan_over_limit(self):
        manager = create_economy_manager()
        loan = manager.take_loan(camp_id="camp1", amount=100000, tier="GARAGE")
        assert loan is not None
        assert loan.principal <= LOAN_CONFIG["GARAGE"]["max_loan"]
    
    def test_cannot_take_second_loan(self):
        manager = create_economy_manager()
        first = manager.take_loan("camp1", 15000, "GARAGE")
        second = manager.take_loan("camp1", 10000, "GARAGE")
        assert first is not None
        assert second is None
    
    def test_loan_reduces_available(self):
        manager = create_economy_manager()
        manager.take_loan("camp1", 15000, "GARAGE")
        options = manager.get_loan_options("camp1", "GARAGE")
        assert options["can_take_loan"] is False
        assert options["has_active_loan"] is True


class TestUpgradeSystem:
    def test_check_upgrade_eligibility_success(self):
        manager = create_economy_manager()
        manager.set_camp_balance("camp1", 60000)
        
        eligible, unmet = manager.check_upgrade_eligibility(
            camp_id="camp1",
            target_tier="LOCAL",
            reputation=50,
            championships=0,
            roster_size=3,
        )
        assert eligible is True
    
    def test_check_upgrade_eligibility_insufficient_funds(self):
        manager = create_economy_manager()
        manager.set_camp_balance("camp1", 30000)
        
        eligible, unmet = manager.check_upgrade_eligibility(
            camp_id="camp1",
            target_tier="LOCAL",
            reputation=50,
            championships=0,
            roster_size=3,
        )
        assert eligible is False


class TestSponsorshipSystem:
    def test_set_fighter_sponsor(self):
        manager = create_economy_manager()
        
        sponsor = Sponsorship(
            company_name="Test Co",
            payment_per_fight=5000,
            fights_total=4,
            fights_remaining=4,
            tier=SponsorTier.RANKED,
            fighter_id="f1",
        )
        
        manager.set_fighter_sponsor("f1", sponsor)
        retrieved = manager.get_fighter_sponsor("f1")
        
        assert retrieved is not None
        assert retrieved.company_name == "Test Co"
    
    def test_generate_sponsorship(self):
        offers = []
        for _ in range(20):
            offer = generate_sponsorship_offer(
                rank=1, is_champion=True, marketability=80, wins=15, fighter_id="f1",
            )
            if offer:
                offers.append(offer)
        assert len(offers) > 0


class TestSerializationRoundTrip:
    def test_manager_serialization(self):
        manager = create_economy_manager()
        manager.set_camp_balance("camp1", 75000)
        manager.add_income("camp1", 10000, TransactionType.FIGHT_PURSE, "Test")
        manager.take_loan("camp1", 15000, "GARAGE")
        
        data = manager.to_dict()
        restored = EconomyManager.from_dict(data)
        
        assert restored.get_balance("camp1") == manager.get_balance("camp1")
        state = restored.get_camp_finances("camp1")
        assert len(state.active_loans) == 1


class TestFinancialSummaries:
    def test_get_financial_summary(self):
        manager = create_economy_manager()
        manager.set_camp_balance("camp1", 50000)
        manager.add_income("camp1", 20000, TransactionType.FIGHT_PURSE, "Purse")
        manager.deduct_expense("camp1", 5000, TransactionType.FACILITY_COST, "Costs")
        
        summary = manager.get_financial_summary("camp1")
        
        assert summary["balance"] == 65000
        assert summary["total_earnings"] == 20000
        assert summary["total_expenses"] == 5000
