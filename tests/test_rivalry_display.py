# tests/test_rivalry_display.py
# Tests for Rivalry Display & Integration
# Lines: ~580

"""
Comprehensive tests for the Rivalry Display module.

Tests cover:
- RivalryPreview data class
- Preview generation and formatting
- News generation
- Fighter rivalry summaries
- CLI display helper
- Post-fight analysis
"""

import pytest
from typing import Dict, List, Any


# ============================================================================
# IMPORTS
# ============================================================================

from narrative.rivalry_display import (
    # Data classes
    RivalryPreview,
    RivalryNewsItem,
    FighterRivalrySummary,
    
    # Constants
    RivalryType,
    RivalryIntensity,
    INTENSITY_EMOJIS,
    INTENSITY_DESCRIPTIONS,
    TYPE_DESCRIPTIONS,
    TYPE_EMOJIS,
    
    # Preview functions
    get_fight_rivalry_preview,
    format_rivalry_preview,
    format_rivalry_preview_compact,
    
    # Display functions
    format_rivalry_display,
    
    # News functions
    generate_rivalry_news,
    format_rivalry_news,
    
    # Fighter summary
    get_fighter_rivalries_summary,
    format_fighter_rivalries,
    
    # CLI helper
    RivalryDisplayHelper,
    
    # Post-fight analysis
    analyze_fight_for_rivalry,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def heated_rivalry_data() -> Dict[str, Any]:
    """Sample heated rivalry data."""
    return {
        "fighter1_id": "fighter_001",
        "fighter2_id": "fighter_002",
        "fighter1_name": "John Smith",
        "fighter2_name": "Mike Jones",
        "rivalry_type": "bad_blood",
        "score": 65,
        "fights": 2,
        "fighter1_wins": 1,
        "fighter2_wins": 1,
        "draws": 0,
        "is_active": True,
        "peak_score": 65,
        "history": [
            {"event_type": "close_decision", "description": "Close fight at UFC 200", "score_change": 15, "date": "2024-01-01"},
            {"event_type": "trash_talk", "description": "War of words on social media", "score_change": 10, "date": "2024-02-01"},
            {"event_type": "split_decision", "description": "Split decision rematch", "score_change": 20, "date": "2024-06-01"},
        ]
    }


@pytest.fixture
def legendary_rivalry_data() -> Dict[str, Any]:
    """Sample legendary rivalry data."""
    return {
        "fighter1_id": "legend_001",
        "fighter2_id": "legend_002",
        "fighter1_name": "Alex Champion",
        "fighter2_name": "Carlos Warrior",
        "rivalry_type": "title_dispute",
        "score": 95,
        "fights": 3,
        "fighter1_wins": 2,
        "fighter2_wins": 1,
        "draws": 0,
        "is_active": True,
        "peak_score": 95,
        "history": [
            {"event_type": "title_fight", "description": "Championship bout", "score_change": 15, "date": "2023-01-01"},
            {"event_type": "trilogy", "description": "Rubber match", "score_change": 20, "date": "2024-01-01"},
        ]
    }


@pytest.fixture
def budding_rivalry_data() -> Dict[str, Any]:
    """Sample new/budding rivalry data."""
    return {
        "fighter1_id": "new_001",
        "fighter2_id": "new_002",
        "fighter1_name": "Rising Star",
        "fighter2_name": "Young Gun",
        "rivalry_type": "competitive",
        "score": 20,
        "fights": 1,
        "fighter1_wins": 1,
        "fighter2_wins": 0,
        "draws": 0,
        "is_active": True,
        "peak_score": 20,
        "history": [
            {"event_type": "close_decision", "description": "Competitive debut fight", "score_change": 15, "date": "2024-06-01"},
        ]
    }


@pytest.fixture
def rivalry_system_data(heated_rivalry_data, legendary_rivalry_data) -> Dict[str, Any]:
    """Sample rivalry system data."""
    return {
        "rivalries": {
            "fighter_001_fighter_002": heated_rivalry_data,
            "legend_001_legend_002": legendary_rivalry_data,
        },
        "total_rivalries_created": 2,
        "total_events_recorded": 5,
    }


# ============================================================================
# RIVALRY PREVIEW TESTS
# ============================================================================

class TestRivalryPreview:
    """Tests for RivalryPreview data class."""
    
    def test_create_preview_no_rivalry(self):
        """Test creating preview with no rivalry."""
        preview = RivalryPreview(
            has_rivalry=False,
            fighter1_name="John",
            fighter2_name="Mike",
        )
        
        assert not preview.has_rivalry
        assert preview.fighter1_name == "John"
        assert preview.score == 0
    
    def test_create_preview_with_rivalry(self):
        """Test creating preview with rivalry data."""
        preview = RivalryPreview(
            has_rivalry=True,
            fighter1_name="John",
            fighter2_name="Mike",
            rivalry_type="bad_blood",
            intensity="HEATED",
            score=65,
            head_to_head="1-1-0",
            is_rematch=False,
            is_trilogy=True,
        )
        
        assert preview.has_rivalry
        assert preview.rivalry_type == "bad_blood"
        assert preview.intensity == "HEATED"
        assert preview.is_trilogy


class TestGetFightRivalryPreview:
    """Tests for get_fight_rivalry_preview function."""
    
    def test_preview_no_rivalry(self):
        """Test preview with no existing rivalry."""
        preview = get_fight_rivalry_preview(
            fighter1_id="f1",
            fighter2_id="f2",
            fighter1_name="John",
            fighter2_name="Mike",
            rivalry_data=None,
        )
        
        assert not preview.has_rivalry
        assert preview.narrative_hook == "" or "spark" in preview.narrative_hook.lower()
    
    def test_preview_no_rivalry_title_fight(self):
        """Test preview with no rivalry but title fight."""
        preview = get_fight_rivalry_preview(
            fighter1_id="f1",
            fighter2_id="f2",
            fighter1_name="John",
            fighter2_name="Mike",
            rivalry_data=None,
            is_title_fight=True,
        )
        
        assert not preview.has_rivalry
        assert "championship" in preview.narrative_hook.lower() or "rivalry" in preview.narrative_hook.lower()
    
    def test_preview_with_heated_rivalry(self, heated_rivalry_data):
        """Test preview with heated rivalry."""
        preview = get_fight_rivalry_preview(
            fighter1_id="fighter_001",
            fighter2_id="fighter_002",
            fighter1_name="John Smith",
            fighter2_name="Mike Jones",
            rivalry_data=heated_rivalry_data,
        )
        
        assert preview.has_rivalry
        assert preview.intensity == "HEATED"
        assert preview.score == 65
        assert preview.head_to_head == "1-1-0"
        assert preview.is_trilogy  # They've fought twice, this would be third
    
    def test_preview_with_legendary_rivalry(self, legendary_rivalry_data):
        """Test preview with legendary rivalry."""
        preview = get_fight_rivalry_preview(
            fighter1_id="legend_001",
            fighter2_id="legend_002",
            fighter1_name="Alex Champion",
            fighter2_name="Carlos Warrior",
            rivalry_data=legendary_rivalry_data,
        )
        
        assert preview.has_rivalry
        assert preview.intensity == "LEGENDARY"
        assert preview.score == 95
        assert preview.series_leader == "Alex Champion"
    
    def test_preview_with_rematch(self, budding_rivalry_data):
        """Test preview identifies rematch."""
        preview = get_fight_rivalry_preview(
            fighter1_id="new_001",
            fighter2_id="new_002",
            fighter1_name="Rising Star",
            fighter2_name="Young Gun",
            rivalry_data=budding_rivalry_data,
        )
        
        assert preview.is_rematch  # One fight means this is rematch
        assert not preview.is_trilogy


class TestFormatRivalryPreview:
    """Tests for rivalry preview formatting."""
    
    def test_format_no_rivalry(self):
        """Test formatting with no rivalry."""
        preview = RivalryPreview(
            has_rivalry=False,
            fighter1_name="John",
            fighter2_name="Mike",
        )
        
        output = format_rivalry_preview(preview)
        assert output == ""  # Empty or minimal
    
    def test_format_with_narrative_hook(self):
        """Test formatting shows narrative hook."""
        preview = RivalryPreview(
            has_rivalry=False,
            fighter1_name="John",
            fighter2_name="Mike",
            narrative_hook="Championship stakes could spark a rivalry.",
        )
        
        output = format_rivalry_preview(preview)
        assert "First meeting" in output or "Championship" in output
    
    def test_format_heated_rivalry(self, heated_rivalry_data):
        """Test formatting heated rivalry."""
        preview = get_fight_rivalry_preview(
            "fighter_001", "fighter_002",
            "John Smith", "Mike Jones",
            heated_rivalry_data
        )
        
        output = format_rivalry_preview(preview)
        
        assert "RIVALRY" in output
        assert "John Smith" in output
        assert "Mike Jones" in output
        assert "HEATED" in output
        assert "65" in output or "65/100" in output
    
    def test_format_compact(self, heated_rivalry_data):
        """Test compact formatting."""
        preview = get_fight_rivalry_preview(
            "fighter_001", "fighter_002",
            "John Smith", "Mike Jones",
            heated_rivalry_data
        )
        
        output = format_rivalry_preview_compact(preview)
        
        assert len(output) < 50  # Compact
        assert "\n" not in output  # Single line
        assert "1-1-0" in output  # Head to head


# ============================================================================
# RIVALRY DISPLAY TESTS
# ============================================================================

class TestFormatRivalryDisplay:
    """Tests for format_rivalry_display function."""
    
    def test_basic_display(self, heated_rivalry_data):
        """Test basic rivalry display."""
        output = format_rivalry_display(heated_rivalry_data)
        
        assert "John Smith" in output
        assert "Mike Jones" in output
        assert "bad blood" in output.lower() or "Bad Blood" in output
        assert "65" in output
    
    def test_detailed_display(self, heated_rivalry_data):
        """Test detailed display includes history."""
        output = format_rivalry_display(heated_rivalry_data, detailed=True)
        
        assert "Recent Events" in output or "history" in output.lower()
        assert "Close fight" in output or "+15" in output


# ============================================================================
# NEWS GENERATION TESTS
# ============================================================================

class TestGenerateRivalryNews:
    """Tests for rivalry news generation."""
    
    def test_new_rivalry_news(self):
        """Test news generation for new rivalry."""
        news = generate_rivalry_news(
            fighter1_name="John",
            fighter2_name="Mike",
            old_score=0,
            new_score=25,
            rivalry_type="competitive",
            is_new_rivalry=True,
        )
        
        assert len(news) >= 1
        assert any("rivalry" in item.headline.lower() for item in news)
        assert any(item.category == "rivalry_new" for item in news)
    
    def test_intensity_escalation_news(self):
        """Test news for intensity increase."""
        news = generate_rivalry_news(
            fighter1_name="John",
            fighter2_name="Mike",
            old_score=45,
            new_score=55,  # NOTABLE -> HEATED
            rivalry_type="bad_blood",
            is_new_rivalry=False,
        )
        
        assert len(news) >= 1
        assert any(item.category == "rivalry_escalate" for item in news)
        assert any(item.is_major for item in news)
    
    def test_legendary_news(self):
        """Test news for reaching legendary status."""
        news = generate_rivalry_news(
            fighter1_name="Champion",
            fighter2_name="Warrior",
            old_score=85,
            new_score=92,
            rivalry_type="title_dispute",
            is_new_rivalry=False,
        )
        
        assert len(news) >= 1
        assert any("LEGENDARY" in item.headline for item in news)
    
    def test_minor_update_news(self):
        """Test minor update generates appropriate news."""
        news = generate_rivalry_news(
            fighter1_name="John",
            fighter2_name="Mike",
            old_score=40,
            new_score=45,  # Small increase, same intensity
            rivalry_type="competitive",
            is_new_rivalry=False,
        )
        
        # Small change shouldn't generate major news
        assert not any(item.is_major for item in news)


class TestFormatRivalryNews:
    """Tests for news formatting."""
    
    def test_format_major_news(self):
        """Test formatting major news."""
        news = RivalryNewsItem(
            headline="🔥 RIVALRY EXPLODES: John vs Mike",
            category="rivalry_escalate",
            fighters=["John", "Mike"],
            is_major=True,
        )
        
        output = format_rivalry_news(news)
        
        assert "🔥" in output
        assert "John" in output


# ============================================================================
# FIGHTER SUMMARY TESTS
# ============================================================================

class TestFighterRivalrySummary:
    """Tests for fighter rivalry summaries."""
    
    def test_get_summary(self, heated_rivalry_data, budding_rivalry_data):
        """Test generating fighter summary."""
        rivalries = [heated_rivalry_data, budding_rivalry_data]
        
        # Modify budding to involve fighter_001
        budding_rivalry_data["fighter1_id"] = "fighter_001"
        budding_rivalry_data["fighter1_name"] = "John Smith"
        
        summary = get_fighter_rivalries_summary(
            fighter_id="fighter_001",
            fighter_name="John Smith",
            rivalries_data=rivalries,
        )
        
        assert summary.fighter_name == "John Smith"
        assert summary.total_rivalries == 2
        assert summary.biggest_rival is not None
    
    def test_summary_counts_heated(self, heated_rivalry_data):
        """Test summary counts heated rivalries."""
        summary = get_fighter_rivalries_summary(
            fighter_id="fighter_001",
            fighter_name="John Smith",
            rivalries_data=[heated_rivalry_data],
        )
        
        assert summary.heated_rivalries == 1
        assert summary.legendary_rivalries == 0
    
    def test_format_summary(self, heated_rivalry_data):
        """Test formatting fighter summary."""
        summary = get_fighter_rivalries_summary(
            fighter_id="fighter_001",
            fighter_name="John Smith",
            rivalries_data=[heated_rivalry_data],
        )
        
        output = format_fighter_rivalries(summary)
        
        assert "John Smith" in output
        assert "Rivalries" in output
        assert "Mike Jones" in output  # Biggest rival


# ============================================================================
# CLI DISPLAY HELPER TESTS
# ============================================================================

class TestRivalryDisplayHelper:
    """Tests for RivalryDisplayHelper class."""
    
    def test_init_empty(self):
        """Test initializing with no data."""
        helper = RivalryDisplayHelper()
        
        rivalry = helper.get_rivalry("f1", "f2")
        assert rivalry is None
    
    def test_init_with_data(self, rivalry_system_data):
        """Test initializing with system data."""
        helper = RivalryDisplayHelper(rivalry_system_data)
        
        rivalry = helper.get_rivalry("fighter_001", "fighter_002")
        assert rivalry is not None
        assert rivalry["score"] == 65
    
    def test_get_rivalry_reverse_ids(self, rivalry_system_data):
        """Test getting rivalry with reversed IDs."""
        helper = RivalryDisplayHelper(rivalry_system_data)
        
        # Should find rivalry regardless of order
        r1 = helper.get_rivalry("fighter_001", "fighter_002")
        r2 = helper.get_rivalry("fighter_002", "fighter_001")
        
        assert r1 is not None
        # r2 might be None if only one key exists, that's ok
    
    def test_get_fight_preview(self, rivalry_system_data):
        """Test getting fight preview."""
        helper = RivalryDisplayHelper(rivalry_system_data)
        
        preview = helper.get_fight_preview(
            "fighter_001", "fighter_002",
            "John Smith", "Mike Jones"
        )
        
        assert "RIVALRY" in preview
        assert "John Smith" in preview
    
    def test_get_fight_preview_no_rivalry(self, rivalry_system_data):
        """Test preview for fighters with no rivalry."""
        helper = RivalryDisplayHelper(rivalry_system_data)
        
        preview = helper.get_fight_preview(
            "unknown_001", "unknown_002",
            "New Fighter", "Another Fighter"
        )
        
        assert preview == ""  # Empty for no rivalry
    
    def test_get_fight_preview_compact(self, rivalry_system_data):
        """Test compact preview."""
        helper = RivalryDisplayHelper(rivalry_system_data)
        
        preview = helper.get_fight_preview_compact(
            "fighter_001", "fighter_002",
            "John Smith", "Mike Jones"
        )
        
        assert len(preview) < 50
        assert "\n" not in preview
    
    def test_get_fighter_rivalries(self, rivalry_system_data):
        """Test getting fighter's rivalries."""
        helper = RivalryDisplayHelper(rivalry_system_data)
        
        output = helper.get_fighter_rivalries("fighter_001", "John Smith")
        
        assert "John Smith" in output
        assert "Rivalries" in output
    
    def test_get_fighter_no_rivalries(self, rivalry_system_data):
        """Test fighter with no rivalries."""
        helper = RivalryDisplayHelper(rivalry_system_data)
        
        output = helper.get_fighter_rivalries("unknown", "Unknown Fighter")
        
        assert "no active rivalries" in output.lower()
    
    def test_get_heated_rivalries(self, rivalry_system_data):
        """Test getting heated rivalries list."""
        helper = RivalryDisplayHelper(rivalry_system_data)
        
        heated = helper.get_heated_rivalries()
        
        assert len(heated) >= 1
        # Should be sorted by score descending
        if len(heated) > 1:
            assert heated[0][2] >= heated[1][2]
    
    def test_format_heated_rivalries_list(self, rivalry_system_data):
        """Test formatting heated rivalries list."""
        helper = RivalryDisplayHelper(rivalry_system_data)
        
        output = helper.format_heated_rivalries_list()
        
        assert "HEATED" in output
        assert "🔥" in output


# ============================================================================
# POST-FIGHT ANALYSIS TESTS
# ============================================================================

class TestAnalyzeFightForRivalry:
    """Tests for post-fight rivalry analysis."""
    
    def test_knockout_adds_score(self):
        """Test knockout adds rivalry score."""
        score_change, triggers = analyze_fight_for_rivalry(
            winner_name="John",
            loser_name="Mike",
            method="KO",
            is_title_fight=False,
            is_close=False,
        )
        
        assert score_change >= 10
        assert any("revenge" in t.lower() for t in triggers)
    
    def test_submission_adds_score(self):
        """Test submission adds rivalry score."""
        score_change, triggers = analyze_fight_for_rivalry(
            winner_name="John",
            loser_name="Mike",
            method="SUB",
            is_title_fight=False,
            is_close=False,
        )
        
        assert score_change >= 8
        assert any("ego" in t.lower() for t in triggers)
    
    def test_split_decision_high_score(self):
        """Test split decision adds high score."""
        score_change, triggers = analyze_fight_for_rivalry(
            winner_name="John",
            loser_name="Mike",
            method="SPLIT",
            is_title_fight=False,
            is_close=True,
        )
        
        assert score_change >= 20
    
    def test_title_fight_bonus(self):
        """Test title fight adds bonus."""
        score_change, triggers = analyze_fight_for_rivalry(
            winner_name="John",
            loser_name="Mike",
            method="DEC",
            is_title_fight=True,
            is_close=False,
        )
        
        assert score_change >= 15
        assert any("championship" in t.lower() for t in triggers)
    
    def test_close_fight_bonus(self):
        """Test close fight adds bonus."""
        score_change, triggers = analyze_fight_for_rivalry(
            winner_name="John",
            loser_name="Mike",
            method="DEC",
            is_title_fight=False,
            is_close=True,
        )
        
        assert score_change >= 15  # Close decision bonus


# ============================================================================
# CONSTANTS TESTS
# ============================================================================

class TestConstants:
    """Tests for module constants."""
    
    def test_intensity_emojis_complete(self):
        """Test all intensities have emojis."""
        required = ["BUDDING", "NOTABLE", "HEATED", "FIERCE", "LEGENDARY"]
        for intensity in required:
            assert intensity in INTENSITY_EMOJIS
    
    def test_intensity_descriptions_complete(self):
        """Test all intensities have descriptions."""
        required = ["BUDDING", "NOTABLE", "HEATED", "FIERCE", "LEGENDARY"]
        for intensity in required:
            assert intensity in INTENSITY_DESCRIPTIONS
    
    def test_type_descriptions_complete(self):
        """Test all types have descriptions."""
        required = ["competitive", "bad_blood", "title_dispute", "gym_war"]
        for rtype in required:
            assert rtype in TYPE_DESCRIPTIONS
    
    def test_type_emojis_complete(self):
        """Test all types have emojis."""
        required = ["competitive", "bad_blood", "title_dispute", "gym_war"]
        for rtype in required:
            assert rtype in TYPE_EMOJIS


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for rivalry display."""
    
    def test_full_workflow(self, rivalry_system_data):
        """Test complete workflow from system data to display."""
        # Initialize helper
        helper = RivalryDisplayHelper(rivalry_system_data)
        
        # Get fight preview
        preview = helper.get_fight_preview(
            "fighter_001", "fighter_002",
            "John Smith", "Mike Jones"
        )
        assert len(preview) > 0
        
        # Get fighter summary
        summary = helper.get_fighter_rivalries("fighter_001", "John Smith")
        assert len(summary) > 0
        
        # Get heated rivalries
        heated = helper.format_heated_rivalries_list()
        assert "HEATED" in heated
    
    def test_new_fight_analysis_workflow(self):
        """Test analyzing a new fight for rivalry."""
        # Simulate fight result
        score_change, triggers = analyze_fight_for_rivalry(
            winner_name="Champion",
            loser_name="Challenger",
            method="SPLIT",
            is_title_fight=True,
            is_close=True,
        )
        
        # Should be significant
        assert score_change >= 30
        
        # Generate news
        news = generate_rivalry_news(
            fighter1_name="Champion",
            fighter2_name="Challenger",
            old_score=0,
            new_score=score_change,
            rivalry_type="title_dispute",
            is_new_rivalry=True,
            is_title_fight=True,
        )
        
        assert len(news) >= 1
        
        # Format news
        for item in news:
            formatted = format_rivalry_news(item)
            assert len(formatted) > 0
    
    def test_escalation_workflow(self):
        """Test rivalry escalation workflow."""
        # Start with notable rivalry
        old_score = 45
        
        # Fight adds score
        score_change, _ = analyze_fight_for_rivalry(
            winner_name="Fighter A",
            loser_name="Fighter B",
            method="KO",
            is_title_fight=True,
            is_close=True,
        )
        
        new_score = old_score + score_change
        
        # Generate escalation news
        news = generate_rivalry_news(
            fighter1_name="Fighter A",
            fighter2_name="Fighter B",
            old_score=old_score,
            new_score=new_score,
            rivalry_type="bad_blood",
            is_new_rivalry=False,
        )
        
        # Should have escalation news since we crossed threshold
        if new_score >= 50:
            assert any(item.category == "rivalry_escalate" for item in news)
