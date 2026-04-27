# tests/test_news.py
# Tests for News & Rumor Mill System
# Lines: ~550
#
# Tests news generation, rumor mill, media personalities, and filtering

"""
Tests for the news and rumor mill system:
- Fighter context formatting (Format D)
- Media personality selection
- News generation (fights, signings, retirements, etc.)
- Rumor generation and resolution
- News filtering
- Display formatting
"""

import pytest
import random
from typing import Dict, List

# Import with fallback for different project structures
try:
    from narrative.news import (
        # Enums
        NewsPriority, NewsCategory, RumorType, NewsFilter,
        # Data classes
        NewsItem, MediaPersonality,
        # System
        NewsSystem,
        # Generators
        generate_fight_result_news, generate_signing_news,
        generate_retirement_news, generate_ranking_news,
        generate_contract_news, generate_milestone_news,
        generate_rumor,
        # Formatting
        format_fighter_context, format_fighter_brief, format_champion,
        format_news_display, format_condensed_results, format_filter_menu,
        get_division_abbrev,
        # Constants
        MEDIA_PERSONALITIES, DIVISION_ABBREV, RUMOR_ACCURACY,
    )
except ImportError:
    from news import (
        NewsPriority, NewsCategory, RumorType, NewsFilter,
        NewsItem, MediaPersonality,
        NewsSystem,
        generate_fight_result_news, generate_signing_news,
        generate_retirement_news, generate_ranking_news,
        generate_contract_news, generate_milestone_news,
        generate_rumor,
        format_fighter_context, format_fighter_brief, format_champion,
        format_news_display, format_condensed_results, format_filter_menu,
        get_division_abbrev,
        MEDIA_PERSONALITIES, DIVISION_ABBREV, RUMOR_ACCURACY,
    )


# ============================================================================
# FIGHTER CONTEXT FORMATTING TESTS (Format D)
# ============================================================================

class TestFighterContextFormatting:
    """Tests for Format D: 'Name (Record, #Rank DIV)' or 'Name (Record, Unranked)'"""
    
    def test_ranked_fighter_with_division(self):
        """Ranked fighter shows rank and division abbreviation."""
        result = format_fighter_context(
            name="Marcus Jones",
            wins=12,
            losses=3,
            rank=5,
            division="Welterweight",
        )
        assert result == "Marcus Jones (12-3, #5 WW)"
    
    def test_unranked_fighter(self):
        """Unranked fighter shows 'Unranked'."""
        result = format_fighter_context(
            name="Tommy Chen",
            wins=8,
            losses=5,
            rank=None,
            division="Lightweight",
        )
        assert result == "Tommy Chen (8-5, Unranked)"
    
    def test_rank_outside_top_15(self):
        """Rank > 15 shows as Unranked."""
        result = format_fighter_context(
            name="Jake Wilson",
            wins=6,
            losses=2,
            rank=20,
            division="Middleweight",
        )
        assert result == "Jake Wilson (6-2, Unranked)"
    
    def test_champion_rank_1(self):
        """#1 ranked fighter."""
        result = format_fighter_context(
            name="Champion Fighter",
            wins=20,
            losses=2,
            rank=1,
            division="Heavyweight",
        )
        assert result == "Champion Fighter (20-2, #1 HW)"
    
    def test_record_with_draws(self):
        """Record includes draws when provided."""
        result = format_fighter_context(
            name="Draw Master",
            wins=10,
            losses=5,
            rank=8,
            division="Bantamweight",
            draws=3,
        )
        assert result == "Draw Master (10-5-3, #8 BW)"
    
    def test_without_division_abbreviation(self):
        """Can hide division abbreviation."""
        result = format_fighter_context(
            name="Test Fighter",
            wins=5,
            losses=2,
            rank=10,
            division="Lightweight",
            include_division=False,
        )
        assert result == "Test Fighter (5-2, #10)"
    
    def test_format_fighter_brief_ranked(self):
        """Brief format shows rank in brackets."""
        result = format_fighter_brief("Marcus Jones", rank=5)
        assert result == "Marcus Jones [#5]"
    
    def test_format_fighter_brief_unranked(self):
        """Brief format for unranked shows just name."""
        result = format_fighter_brief("Tommy Chen", rank=None)
        assert result == "Tommy Chen"
    
    def test_format_champion(self):
        """Champion format includes emoji and title."""
        result = format_champion("The Champ", 25, 3, "Lightweight")
        assert "🏆" in result
        assert "The Champ" in result
        assert "25-3" in result
        assert "LW" in result or "Champ" in result


class TestDivisionAbbreviations:
    """Tests for division abbreviation mapping."""
    
    def test_all_divisions_have_abbreviations(self):
        """All standard divisions should have abbreviations."""
        divisions = [
            "Strawweight", "Flyweight", "Bantamweight", "Featherweight",
            "Lightweight", "Welterweight", "Middleweight", 
            "Light Heavyweight", "Heavyweight"
        ]
        for div in divisions:
            abbrev = get_division_abbrev(div)
            assert len(abbrev) <= 3
            assert abbrev.isupper()
    
    def test_specific_abbreviations(self):
        """Test specific known abbreviations."""
        assert get_division_abbrev("Lightweight") == "LW"
        assert get_division_abbrev("Welterweight") == "WW"
        assert get_division_abbrev("Heavyweight") == "HW"
        assert get_division_abbrev("Bantamweight") == "BW"
    
    def test_unknown_division_fallback(self):
        """Unknown division uses first 3 letters."""
        result = get_division_abbrev("SuperHeavyweight")
        assert len(result) == 3


# ============================================================================
# MEDIA PERSONALITY TESTS
# ============================================================================

class TestMediaPersonalities:
    """Tests for fictional MMA media personalities."""
    
    def test_all_personalities_exist(self):
        """All expected personalities should be defined."""
        expected = [
            "insider_mike", "carla", "frank", 
            "ricky", "chloe", "dfc_official"
        ]
        for key in expected:
            assert key in MEDIA_PERSONALITIES
    
    def test_personality_has_required_fields(self):
        """Each personality has all required attributes."""
        for key, person in MEDIA_PERSONALITIES.items():
            assert person.name, f"{key} missing name"
            assert person.handle, f"{key} missing handle"
            assert person.handle.startswith("@"), f"{key} handle should start with @"
            assert 0 <= person.accuracy <= 1, f"{key} accuracy out of range"
            assert len(person.catchphrases) > 0, f"{key} missing catchphrases"
            assert person.emoji, f"{key} missing emoji"
    
    def test_insider_mike_most_reliable(self):
        """Mike Reeves should be highly reliable."""
        mike = MEDIA_PERSONALITIES["insider_mike"]
        assert mike.accuracy >= 0.75
        assert "insider" in mike.style or "breaking" in mike.focus
    
    def test_ricky_least_reliable(self):
        """Ricky Diaz should be less reliable (rumor mill)."""
        ricky = MEDIA_PERSONALITIES["ricky"]
        assert ricky.accuracy <= 0.50
        assert "rumor" in ricky.focus or "speculation" in ricky.focus
    
    def test_dfc_official_always_accurate(self):
        """Official DFC account should be 100% accurate."""
        official = MEDIA_PERSONALITIES["dfc_official"]
        assert official.accuracy == 1.0
    
    def test_personality_attribution(self):
        """Get attribution should return formatted string."""
        mike = MEDIA_PERSONALITIES["insider_mike"]
        attr = mike.get_attribution()
        assert "@MMAInsiderMike" in attr


# ============================================================================
# NEWS GENERATION TESTS
# ============================================================================

class TestFightResultNews:
    """Tests for fight result news generation."""
    
    def test_regular_fight_result(self):
        """Generate news for a regular fight."""
        news = generate_fight_result_news(
            winner_name="Marcus Jones",
            winner_record=(12, 3),
            winner_rank=5,
            loser_name="Tommy Chen",
            loser_record=(8, 5),
            loser_rank=12,
            division="Welterweight",
            method="TKO",
            round_num=2,
            winner_id="w1",
            loser_id="l1",
            week=10,
            year=1,
        )
        
        assert news.category == NewsCategory.RESULT
        assert "Marcus Jones" in news.headline
        assert "12-3" in news.headline
        assert "#5 WW" in news.headline
        assert "Tommy Chen" in news.headline or news.body
        assert news.emoji == "🥊"
    
    def test_title_fight_result(self):
        """Title fights get special treatment."""
        news = generate_fight_result_news(
            winner_name="Champion",
            winner_record=(20, 2),
            winner_rank=1,
            loser_name="Challenger",
            loser_record=(15, 3),
            loser_rank=2,
            division="Lightweight",
            method="Submission",
            round_num=3,
            is_title_fight=True,
            week=10,
            year=1,
        )
        
        assert news.category == NewsCategory.TITLE
        assert news.priority == NewsPriority.CRITICAL
        assert news.emoji == "🏆"
        assert "gold" in news.headline.lower() or "champion" in news.headline.lower()
    
    def test_upset_result(self):
        """Upsets get dramatic treatment."""
        news = generate_fight_result_news(
            winner_name="Underdog",
            winner_record=(5, 3),
            winner_rank=15,
            loser_name="Favorite",
            loser_record=(18, 2),
            loser_rank=2,
            division="Middleweight",
            method="KO",
            round_num=1,
            is_upset=True,
            week=10,
            year=1,
        )
        
        assert news.category == NewsCategory.UPSET
        assert news.priority in [NewsPriority.HIGH, NewsPriority.CRITICAL]
        assert news.emoji == "⚡"
        assert "UPSET" in news.headline
    
    def test_player_fight_always_critical(self):
        """Player's fights are always critical priority."""
        news = generate_fight_result_news(
            winner_name="Player Fighter",
            winner_record=(5, 1),
            winner_rank=None,
            loser_name="Opponent",
            loser_record=(3, 3),
            loser_rank=None,
            division="Flyweight",
            method="Decision",
            round_num=3,
            winner_camp_id="player_camp",
            player_camp_id="player_camp",
            week=10,
            year=1,
        )
        
        assert news.priority == NewsPriority.CRITICAL
        assert news.is_player_relevant


class TestSigningNews:
    """Tests for signing news generation."""
    
    def test_regular_signing(self):
        """Generate news for regular signing."""
        news = generate_signing_news(
            fighter_name="New Fighter",
            fighter_record=(5, 2),
            fighter_rank=None,
            division="Lightweight",
            camp_name="Test Camp",
            camp_id="camp1",
            fighter_id="f1",
            week=10,
            year=1,
        )
        
        assert news.category == NewsCategory.SIGNING
        assert "New Fighter" in news.headline
        assert "Test Camp" in news.headline
        assert news.emoji == "✍️"
    
    def test_player_signing_is_critical(self):
        """Player signings are critical."""
        news = generate_signing_news(
            fighter_name="New Fighter",
            fighter_record=(5, 2),
            fighter_rank=10,
            division="Welterweight",
            camp_name="Player Camp",
            camp_id="player_camp",
            fighter_id="f1",
            week=10,
            year=1,
            player_camp_id="player_camp",
        )
        
        assert news.priority == NewsPriority.CRITICAL
        assert news.is_player_relevant
        assert "SIGNED" in news.headline
    
    def test_prospect_signing(self):
        """Prospect signings show potential."""
        news = generate_signing_news(
            fighter_name="Young Prospect",
            fighter_record=(2, 0),
            fighter_rank=None,
            division="Bantamweight",
            camp_name="Test Camp",
            camp_id="camp1",
            fighter_id="f1",
            week=10,
            year=1,
            is_prospect=True,
            potential_grade="Elite",
        )
        
        assert "Elite" in news.body or "prospect" in news.body.lower()


class TestOtherNewsTypes:
    """Tests for other news generation functions."""
    
    def test_retirement_news(self):
        """Generate retirement news."""
        news = generate_retirement_news(
            fighter_name="Old Veteran",
            fighter_record=(25, 10),
            division="Heavyweight",
            fighter_id="f1",
            week=10,
            year=1,
            was_champion=True,
        )
        
        assert news.category == NewsCategory.RETIREMENT
        assert "retire" in news.headline.lower()
        assert news.emoji == "👋"
    
    def test_ranking_news_entered(self):
        """News for entering rankings."""
        news = generate_ranking_news(
            fighter_name="Rising Star",
            fighter_record=(8, 1),
            division="Lightweight",
            old_rank=None,
            new_rank=15,
            fighter_id="f1",
            week=10,
            year=1,
        )
        
        assert news.category == NewsCategory.RANKING
        assert "NEW CONTENDER" in news.headline or "#15" in news.headline
        assert news.emoji == "📈"
    
    def test_ranking_news_big_jump(self):
        """News for big ranking jump."""
        news = generate_ranking_news(
            fighter_name="Mover",
            fighter_record=(10, 2),
            division="Welterweight",
            old_rank=12,
            new_rank=5,
            fighter_id="f1",
            week=10,
            year=1,
        )
        
        assert "7" in news.headline or "jump" in news.headline.lower()
        assert news.priority == NewsPriority.HIGH
    
    def test_contract_warning(self):
        """Contract expiration warning."""
        news = generate_contract_news(
            fighter_name="Soon Free",
            fighter_record=(10, 5),
            fighter_rank=8,
            division="Middleweight",
            fighter_id="f1",
            camp_name="Current Camp",
            camp_id="camp1",
            weeks_remaining=2,
            week=10,
            year=1,
            player_camp_id="camp1",
        )
        
        assert news.category == NewsCategory.CONTRACT
        assert "EXPIR" in news.headline.upper()
        assert news.priority == NewsPriority.CRITICAL
    
    def test_milestone_news(self):
        """Milestone achievement news."""
        news = generate_milestone_news(
            fighter_name="Streak Fighter",
            fighter_record=(10, 0),
            fighter_rank=3,
            division="Featherweight",
            fighter_id="f1",
            milestone_type="win_streak",
            milestone_detail="10",
            week=10,
            year=1,
        )
        
        assert news.category == NewsCategory.MILESTONE
        assert "streak" in news.headline.lower()


# ============================================================================
# RUMOR TESTS
# ============================================================================

class TestRumorGeneration:
    """Tests for rumor generation."""
    
    def test_generate_transfer_rumor(self):
        """Generate transfer rumor."""
        news = generate_rumor(
            rumor_type=RumorType.TRANSFER,
            fighter_name="Unhappy Fighter",
            fighter_id="f1",
            division="Lightweight",
            week=10,
            year=1,
            camp_name="Current Camp",
        )
        
        assert news.category == NewsCategory.RUMOR
        assert news.rumor_type == RumorType.TRANSFER
        assert "Unhappy Fighter" in news.headline
        assert news.emoji == "💬"
        assert news.rumor_accuracy > 0
    
    def test_generate_fight_talks_rumor(self):
        """Generate fight talks rumor."""
        news = generate_rumor(
            rumor_type=RumorType.FIGHT_TALKS,
            fighter_name="Fighter A",
            fighter_id="f1",
            division="Welterweight",
            week=10,
            year=1,
            fighter2_name="Fighter B",
            fighter2_id="f2",
        )
        
        assert news.rumor_type == RumorType.FIGHT_TALKS
        assert "Fighter A" in news.headline
        assert "Fighter B" in news.headline
        assert len(news.fighter_ids) == 2
    
    def test_rumor_has_personality_attribution(self):
        """Rumors should have media personality attribution."""
        news = generate_rumor(
            rumor_type=RumorType.RETIREMENT,
            fighter_name="Old Timer",
            fighter_id="f1",
            division="Heavyweight",
            week=10,
            year=1,
        )
        
        assert news.attribution
        assert "@" in news.attribution
    
    def test_rumor_accuracy_varies_by_type(self):
        """Different rumor types have different accuracy."""
        injury_rumor = generate_rumor(
            rumor_type=RumorType.INJURY,
            fighter_name="Fighter",
            fighter_id="f1",
            division="LW",
            week=1,
            year=1,
        )
        
        superfight_rumor = generate_rumor(
            rumor_type=RumorType.SUPERFIGHT,
            fighter_name="Fighter",
            fighter_id="f1",
            division="LW",
            week=1,
            year=1,
        )
        
        # Injury rumors more accurate than superfight rumors
        assert injury_rumor.rumor_accuracy > superfight_rumor.rumor_accuracy


# ============================================================================
# NEWS SYSTEM TESTS
# ============================================================================

class TestNewsSystem:
    """Tests for the NewsSystem class."""
    
    def test_create_news_system(self):
        """Create a news system."""
        system = NewsSystem()
        assert system is not None
    
    def test_add_news(self):
        """Add news to the system."""
        system = NewsSystem()
        
        news = generate_fight_result_news(
            winner_name="Winner",
            winner_record=(10, 2),
            winner_rank=5,
            loser_name="Loser",
            loser_record=(8, 4),
            loser_rank=10,
            division="Lightweight",
            method="KO",
            round_num=1,
            week=1,
            year=1,
        )
        
        system.add_news(news)
        
        all_news = system.get_filtered_news(NewsFilter.ALL_NEWS)
        assert len(all_news) == 1
    
    def test_player_context_affects_priority(self):
        """Player context should boost priority of relevant news."""
        system = NewsSystem()
        system.set_player_context(
            camp_id="player_camp",
            divisions=["Lightweight"],
            fighter_ids=["player_fighter"],
        )
        
        # Add news about player's fighter
        news = NewsItem(
            news_id="test1",
            category=NewsCategory.RESULT,
            priority=NewsPriority.LOW,
            headline="Test",
            body="",
            week=1,
            year=1,
            fighter_ids=["player_fighter"],
        )
        
        system.add_news(news)
        
        # Should be boosted to critical
        result = system.get_filtered_news(NewsFilter.ALL_NEWS)
        assert result[0].priority == NewsPriority.CRITICAL
        assert result[0].is_player_relevant
    
    def test_filter_headlines(self):
        """Headlines filter returns top 5."""
        system = NewsSystem()
        
        # Add 10 news items
        for i in range(10):
            news = NewsItem(
                news_id=f"news_{i}",
                category=NewsCategory.RESULT,
                priority=NewsPriority.MEDIUM if i < 5 else NewsPriority.LOW,
                headline=f"News {i}",
                body="",
                week=1,
                year=1,
            )
            system.add_news(news)
        
        headlines = system.get_filtered_news(NewsFilter.HEADLINES)
        assert len(headlines) == 5
    
    def test_filter_my_camp(self):
        """My Camp filter returns only player-relevant news."""
        system = NewsSystem()
        system.set_player_context("player_camp", [], ["player_fighter"])
        
        # Add player news
        player_news = NewsItem(
            news_id="player",
            category=NewsCategory.RESULT,
            priority=NewsPriority.LOW,
            headline="Player news",
            body="",
            week=1,
            year=1,
            fighter_ids=["player_fighter"],
        )
        system.add_news(player_news)
        
        # Add other news
        other_news = NewsItem(
            news_id="other",
            category=NewsCategory.RESULT,
            priority=NewsPriority.HIGH,
            headline="Other news",
            body="",
            week=1,
            year=1,
            fighter_ids=["other_fighter"],
        )
        system.add_news(other_news)
        
        my_camp = system.get_filtered_news(NewsFilter.MY_CAMP)
        assert len(my_camp) == 1
        assert my_camp[0].news_id == "player"
    
    def test_filter_rumors_only(self):
        """Rumors filter returns only rumors."""
        system = NewsSystem()
        
        # Add rumor
        rumor = generate_rumor(
            RumorType.TRANSFER, "Fighter", "f1", "LW", 1, 1
        )
        system.add_news(rumor)
        
        # Add regular news
        regular = NewsItem(
            news_id="regular",
            category=NewsCategory.RESULT,
            priority=NewsPriority.HIGH,
            headline="Regular",
            body="",
            week=1,
            year=1,
        )
        system.add_news(regular)
        
        rumors = system.get_filtered_news(NewsFilter.RUMORS_ONLY)
        assert len(rumors) == 1
        assert rumors[0].category == NewsCategory.RUMOR
    
    def test_end_week_archives_news(self):
        """End week moves news to archive."""
        system = NewsSystem()
        
        news = NewsItem(
            news_id="test",
            category=NewsCategory.RESULT,
            priority=NewsPriority.MEDIUM,
            headline="Test",
            body="",
            week=1,
            year=1,
        )
        system.add_news(news)
        
        assert len(system._current_week_news) == 1
        
        system.end_week()
        
        assert len(system._current_week_news) == 0
        assert len(system._news_archive) == 1
    
    def test_serialization(self):
        """System should serialize and deserialize."""
        system = NewsSystem()
        system.set_player_context("camp1", ["LW", "WW"], ["f1", "f2"])
        
        news = generate_fight_result_news(
            "Winner", (10, 2), 5, "Loser", (8, 4), 10,
            "Lightweight", "KO", 1, week=1, year=1
        )
        system.add_news(news)
        
        rumor = generate_rumor(
            RumorType.TRANSFER, "Fighter", "f1", "LW", 1, 1
        )
        system.add_news(rumor)
        
        # Serialize and restore
        data = system.to_dict()
        restored = NewsSystem.from_dict(data)
        
        assert len(restored._current_week_news) == 2
        assert restored._player_camp_id == "camp1"
        assert "LW" in restored._player_divisions


# ============================================================================
# DISPLAY FORMATTING TESTS
# ============================================================================

class TestDisplayFormatting:
    """Tests for display formatting functions."""
    
    def test_format_news_display(self):
        """Format news for display."""
        news_items = [
            NewsItem(
                news_id="1",
                category=NewsCategory.TITLE,
                priority=NewsPriority.CRITICAL,
                headline="Champion wins!",
                body="Dominant performance",
                week=1,
                year=1,
                emoji="🏆",
            ),
            NewsItem(
                news_id="2",
                category=NewsCategory.RUMOR,
                priority=NewsPriority.LOW,
                headline="Rumor: Something happening",
                body="",
                week=1,
                year=1,
                emoji="💬",
                attribution="- @MMAInsiderMike",
            ),
        ]
        
        lines = format_news_display(news_items, week=1, year=1)
        
        assert len(lines) > 0
        output = "\n".join(lines)
        assert "NEWS & RUMORS" in output
        assert "Champion wins!" in output
        assert "BREAKING" in output
    
    def test_format_condensed_results(self):
        """Format condensed results."""
        results = {
            "Lightweight": {"total": 3, "finishes": 2, "decisions": 1},
            "Welterweight": {"total": 2, "finishes": 1, "decisions": 1},
        }
        
        lines = format_condensed_results(results)
        
        output = "\n".join(lines)
        assert "Lightweight" in output
        assert "3 fights" in output
        assert "2 finish" in output
    
    def test_format_filter_menu(self):
        """Filter menu should show all options."""
        lines = format_filter_menu()
        output = "\n".join(lines)
        
        assert "Headlines" in output
        assert "My Camp" in output
        assert "Rumors" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
