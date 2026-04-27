"""
News Engine for Campus Dynasty 2.0
Generates dynamic news stories based on game results, streaks, milestones, and tournament drama.
"""

import random
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid


class NewsCategory(Enum):
    UPSET = "upset"
    BUZZER_BEATER = "buzzer_beater"
    BLOWOUT = "blowout"
    HIGH_SCORE = "high_score"
    CAREER_HIGH = "career_high"
    MILESTONE = "milestone"
    STREAK = "streak"
    TOURNAMENT = "tournament"
    BUBBLE = "bubble"
    RIVALRY = "rivalry"
    DEFENSIVE_GEM = "defensive_gem"
    TRIPLE_DOUBLE = "triple_double"
    YOUR_TEAM = "your_team"
    GENERAL = "general"
    # Non-game events
    COACHING = "coaching"
    PORTAL = "portal"
    RECRUITING = "recruiting"
    AWARDS = "awards"
    RANKINGS = "rankings"
    INJURY = "injury"
    DEVELOPMENT = "development"


@dataclass
class NewsStory:
    """A single news story"""
    id: str
    headline: str
    body: str
    category: NewsCategory
    priority: int  # 1-10, higher = more important
    week: int
    season: int
    game_id: Optional[str] = None
    team_ids: List[str] = field(default_factory=list)
    player_ids: List[str] = field(default_factory=list)
    is_user_team: bool = False
    emoji: str = "📰"
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'headline': self.headline,
            'body': self.body,
            'category': self.category.value,
            'priority': self.priority,
            'week': self.week,
            'season': self.season,
            'game_id': self.game_id,
            'team_ids': self.team_ids,
            'player_ids': self.player_ids,
            'is_user_team': self.is_user_team,
            'emoji': self.emoji
        }


class NewsEngine:
    """
    Generates news stories from game results and league events.
    Stories are prioritized and categorized for display.
    """
    
    def __init__(self):
        self.stories: List[NewsStory] = []
        self.story_templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, List[str]]:
        """Load headline and body templates for variety"""
        return {
            'upset_headline': [
                "UPSET ALERT: {winner} stuns {loser}!",
                "STUNNER! {winner} takes down {loser}",
                "Shock result: {winner} upsets {loser}",
                "Nobody saw this coming: {winner} over {loser}",
                "{winner} pulls off massive upset against {loser}",
            ],
            'upset_body': [
                "In one of the biggest surprises of the season, {winner} defeated {loser} {score}. {detail}",
                "The college basketball world was shocked as {winner} knocked off {loser} {score}. {detail}",
                "{winner} proved the doubters wrong with a stunning {score} victory over {loser}. {detail}",
            ],
            'buzzer_beater_headline': [
                "At the buzzer! {winner} wins on {player}'s heroics",
                "BUZZER BEATER! {player} lifts {winner} past {loser}",
                "Incredible finish: {player}'s shot sinks {loser}",
                "Heartbreak for {loser} as {player} hits game-winner",
                "{player} delivers in the clutch for {winner}",
            ],
            'buzzer_beater_body': [
                "{player} hit the game-winning shot as time expired, lifting {winner} to a thrilling {score} victory over {loser}. The crowd erupted as the ball went through the net.",
                "With the game on the line, {player} delivered. The {winner} star knocked down the biggest shot of the season, a {shot_type} at the buzzer to defeat {loser} {score}.",
            ],
            'blowout_headline': [
                "{winner} dominates {loser} in lopsided affair",
                "Rout: {winner} cruises past {loser}",
                "{winner} rolls over {loser} by {margin}",
                "No contest: {winner} blows out {loser}",
                "{winner} makes statement with blowout of {loser}",
            ],
            'blowout_body': [
                "{winner} was never challenged in a dominant {score} victory over {loser}. {detail}",
                "It was men against boys as {winner} crushed {loser} {score}. The {margin}-point margin tells the whole story.",
            ],
            'high_score_headline': [
                "{player} explodes for {points} points!",
                "Career night! {player} drops {points}",
                "{player} catches fire with {points}-point outburst",
                "Unstoppable: {player} pours in {points}",
                "{player} puts on a show with {points} points",
            ],
            'high_score_body': [
                "{player} was unconscious, scoring {points} points to lead {team} to victory. The {position} shot {fg} from the field and couldn't be stopped.",
                "It was a historic night for {player}, who erupted for {points} points in {team}'s win. {detail}",
            ],
            'streak_win_headline': [
                "{team} extends winning streak to {count} games",
                "Rolling: {team} wins {count}th straight",
                "{team} keeps rolling with {count}th consecutive victory",
                "Hot streak: {team} makes it {count} in a row",
            ],
            'streak_loss_headline': [
                "{team}'s struggles continue with {count}th straight loss",
                "Skid continues: {team} drops {count}th in a row",
                "Free fall: {team} loses {count}th consecutive game",
            ],
            'tournament_upset_headline': [
                "MADNESS! #{loser_seed} {loser} falls to #{winner_seed} {winner}",
                "Bracket buster: #{winner_seed} {winner} knocks off #{loser_seed} {loser}",
                "Cinderella alert: {winner} advances past {loser}",
                "Dance continues for {winner} after stunning {loser}",
            ],
            'tournament_upset_body': [
                "March Madness lived up to its name as #{winner_seed} seed {winner} eliminated #{loser_seed} seed {loser} {score}. Brackets everywhere are in shambles.",
                "The Cinderella story continues for {winner}, who punched their ticket to the next round with a {score} win over heavily favored {loser}.",
            ],
            'milestone_headline': [
                "Milestone: {coach} earns {count}th career victory",
                "Historic night for {coach}: Win #{count}",
                "{coach} joins elite company with win #{count}",
            ],
            'triple_double_headline': [
                "Rare feat: {player} records triple-double",
                "Triple-double! {player} does it all for {team}",
                "{player} stuffs the stat sheet with triple-double",
            ],
            'defensive_gem_headline': [
                "{team} clamps down on {player}",
                "Lockdown D: {team} holds {player} to {points} points",
                "{player} shut down by {team}'s defense",
            ],
            'rivalry_headline': [
                "{winner} claims bragging rights over {loser}",
                "Rivalry renewed: {winner} edges {loser}",
                "{winner} takes down rival {loser} in thriller",
            ],
            # === NON-GAME EVENT TEMPLATES ===
            'coaching_fired_headline': [
                "{team} parts ways with {coach}",
                "OUT: {coach} fired at {team}",
                "{team} makes coaching change, dismisses {coach}",
                "End of an era: {coach} out at {team}",
            ],
            'coaching_retired_headline': [
                "{coach} announces retirement after {seasons} seasons",
                "Legend retires: {coach} steps away from {team}",
                "{coach} hangs it up at {team}",
            ],
            'coaching_hired_headline': [
                "{team} hires {coach} as new head coach",
                "It's official: {coach} takes over at {team}",
                "New era: {coach} named head coach at {team}",
                "{team} tabs {coach} to lead program",
            ],
            'coaching_poached_headline': [
                "{coach} leaves {from_team} for {to_team}",
                "POACHED: {to_team} lures {coach} away from {from_team}",
                "{coach} jumps ship from {from_team} to {to_team}",
            ],
            'portal_entry_headline': [
                "{player} enters transfer portal from {team}",
                "Portal: {player} ({team}) looking for new home",
                "{team}'s {player} hits the portal",
            ],
            'portal_star_headline': [
                "BIG NAME IN PORTAL: {player} leaves {team}",
                "Major portal entry: {team}'s {player} seeking transfer",
                "Star on the move: {player} entering portal from {team}",
            ],
            'recruiting_commit_headline': [
                "{stars} {player} commits to {team}!",
                "COMMITTED: {player} chooses {team}",
                "{team} lands {stars} {player}",
            ],
            'recruiting_class_headline': [
                "{team} wraps up #{rank} recruiting class",
                "Signing Day: {team} finishes with {count} signees",
                "{team}'s recruiting class ranks #{rank} nationally",
            ],
            'award_poy_headline': [
                "{player} named National Player of the Year",
                "Player of the Year: {player} takes home top honor",
                "{player} wins Player of the Year award",
            ],
            'award_all_american_headline': [
                "All-American Team announced: {player} leads the way",
                "{player} earns First Team All-American honors",
                "Best of the best: All-American teams revealed",
            ],
            'rankings_new_no1_headline': [
                "{team} rises to #1 in the AP Poll",
                "New No. 1: {team} takes over the top spot",
                "{team} climbs to the top of the rankings",
            ],
            'rankings_big_mover_headline': [
                "{team} surges {spots} spots to #{new_rank}",
                "On the rise: {team} jumps to #{new_rank}",
                "{team} makes big move, now ranked #{new_rank}",
            ],
            'rankings_dropped_headline': [
                "{team} falls out of the Top 25",
                "Freefall: {team} drops from rankings",
                "{team} tumbles out of the AP Poll",
            ],
        }
    
    def generate_game_stories(self, game_result: Dict, league: Any, user_team_id: Optional[str] = None) -> List[NewsStory]:
        """Generate news stories from a single game result"""
        stories = []
        
        home_team = game_result.get('home_team')
        away_team = game_result.get('away_team')
        home_score = game_result.get('home_score', 0)
        away_score = game_result.get('away_score', 0)
        winner = game_result.get('winner')
        game_id = game_result.get('id')
        week = game_result.get('week', league.current_week if league else 1)
        season = league.current_season if league else 2025
        
        if not winner or not home_team or not away_team:
            return stories
        
        loser = away_team if winner.id == home_team.id else home_team
        winner_score = home_score if winner.id == home_team.id else away_score
        loser_score = away_score if winner.id == home_team.id else home_score
        margin = winner_score - loser_score
        
        is_user_game = user_team_id and (home_team.id == user_team_id or away_team.id == user_team_id)
        user_won = is_user_game and winner.id == user_team_id
        
        # Check for various story types
        
        # 1. UPSET - Based on win differential and prestige
        upset_story = self._check_upset(winner, loser, winner_score, loser_score, 
                                         game_id, week, season, is_user_game, league)
        if upset_story:
            stories.append(upset_story)
        
        # 2. BLOWOUT - 20+ point margin
        if margin >= 20:
            stories.append(self._create_blowout_story(
                winner, loser, winner_score, loser_score, margin,
                game_id, week, season, is_user_game
            ))
        
        # 3. BUZZER BEATER - Close game (1-3 points)
        if margin <= 3 and margin > 0:
            buzzer_story = self._create_buzzer_beater_story(
                winner, loser, winner_score, loser_score, game_result,
                game_id, week, season, is_user_game
            )
            if buzzer_story:
                stories.append(buzzer_story)
        
        # 4. HIGH SCORER - Check for 30+ point performances
        high_score_stories = self._check_high_scorers(game_result, game_id, week, season, user_team_id)
        stories.extend(high_score_stories)
        
        # 5. TRIPLE DOUBLE
        triple_double_stories = self._check_triple_doubles(game_result, game_id, week, season, user_team_id)
        stories.extend(triple_double_stories)
        
        # 6. STREAK updates
        streak_story = self._check_streaks(winner, loser, game_id, week, season, user_team_id)
        if streak_story:
            stories.append(streak_story)
        
        return stories
    
    def _check_upset(self, winner, loser, winner_score, loser_score, 
                     game_id, week, season, is_user_game, league) -> Optional[NewsStory]:
        """Check if this game qualifies as an upset"""
        
        # Calculate "expected" winner based on record and prestige
        winner_strength = winner.wins - winner.losses + self._prestige_bonus(winner)
        loser_strength = loser.wins - loser.losses + self._prestige_bonus(loser)
        
        upset_magnitude = loser_strength - winner_strength
        
        # Need significant difference to be an upset
        if upset_magnitude < 5:
            return None
        
        # Determine priority based on magnitude
        if upset_magnitude >= 15:
            priority = 10
            emoji = "🚨"
        elif upset_magnitude >= 10:
            priority = 8
            emoji = "😱"
        else:
            priority = 6
            emoji = "⚡"
        
        headline = random.choice(self.story_templates['upset_headline']).format(
            winner=winner.school,
            loser=loser.school
        )
        
        details = []
        if winner.wins < loser.wins:
            details.append(f"{winner.school} came in with just {winner.wins} wins on the season")
        if hasattr(loser, 'ranking') and loser.ranking and loser.ranking <= 25:
            details.append(f"The loss drops #{loser.ranking} {loser.school} out of the rankings picture")
        
        detail_text = ". ".join(details) if details else f"{winner.school} controlled the game from start to finish"
        
        body = random.choice(self.story_templates['upset_body']).format(
            winner=winner.full_name,
            loser=loser.full_name,
            score=f"{winner_score}-{loser_score}",
            detail=detail_text
        )
        
        return NewsStory(
            id=str(uuid.uuid4()),
            headline=headline,
            body=body,
            category=NewsCategory.UPSET,
            priority=priority,
            week=week,
            season=season,
            game_id=game_id,
            team_ids=[winner.id, loser.id],
            is_user_team=is_user_game,
            emoji=emoji
        )
    
    def _prestige_bonus(self, team) -> int:
        """Get prestige bonus for strength calculation"""
        prestige_map = {
            'blue_blood': 15,
            'elite': 12,
            'power': 10,
            'high_major': 6,
            'mid_major': 3,
            'low_major': 1,
            'small_conference': 0
        }
        tier = getattr(team, 'prestige_tier', None)
        if tier:
            tier_name = tier.value if hasattr(tier, 'value') else str(tier)
            return prestige_map.get(tier_name.lower(), 5)
        return 5
    
    def _create_blowout_story(self, winner, loser, winner_score, loser_score, margin,
                              game_id, week, season, is_user_game) -> NewsStory:
        """Create a blowout story"""
        priority = 5 if margin >= 30 else 4
        
        headline = random.choice(self.story_templates['blowout_headline']).format(
            winner=winner.school,
            loser=loser.school,
            margin=margin
        )
        
        body = random.choice(self.story_templates['blowout_body']).format(
            winner=winner.full_name,
            loser=loser.full_name,
            score=f"{winner_score}-{loser_score}",
            margin=margin,
            detail=f"The {margin}-point victory improves {winner.school} to {winner.wins}-{winner.losses}."
        )
        
        return NewsStory(
            id=str(uuid.uuid4()),
            headline=headline,
            body=body,
            category=NewsCategory.BLOWOUT,
            priority=priority,
            week=week,
            season=season,
            game_id=game_id,
            team_ids=[winner.id, loser.id],
            is_user_team=is_user_game,
            emoji="💪"
        )
    
    def _create_buzzer_beater_story(self, winner, loser, winner_score, loser_score, 
                                     game_result, game_id, week, season, is_user_game) -> Optional[NewsStory]:
        """Create a buzzer beater / close game story"""
        
        # Try to find the top scorer on winning team as the "hero"
        hero = None
        hero_points = 0
        
        home_stats = game_result.get('home_stats')
        away_stats = game_result.get('away_stats')
        
        winner_stats = home_stats if winner.id == game_result.get('home_team').id else away_stats
        
        if winner_stats and hasattr(winner_stats, 'player_stats'):
            for player_id, ps in winner_stats.player_stats.items():
                points = getattr(ps, 'points', 0)
                if points > hero_points:
                    hero_points = points
                    hero = getattr(ps, 'player', None)
        
        if not hero:
            return None
        
        shot_types = ["three-pointer", "jumper", "floater", "fadeaway"]
        
        headline = random.choice(self.story_templates['buzzer_beater_headline']).format(
            winner=winner.school,
            loser=loser.school,
            player=hero.name
        )
        
        body = random.choice(self.story_templates['buzzer_beater_body']).format(
            winner=winner.full_name,
            loser=loser.full_name,
            player=hero.name,
            score=f"{winner_score}-{loser_score}",
            shot_type=random.choice(shot_types)
        )
        
        return NewsStory(
            id=str(uuid.uuid4()),
            headline=headline,
            body=body,
            category=NewsCategory.BUZZER_BEATER,
            priority=7,
            week=week,
            season=season,
            game_id=game_id,
            team_ids=[winner.id, loser.id],
            player_ids=[hero.id] if hero else [],
            is_user_team=is_user_game,
            emoji="⏰"
        )
    
    def _check_high_scorers(self, game_result, game_id, week, season, user_team_id) -> List[NewsStory]:
        """Check for high-scoring individual performances (30+ points)"""
        stories = []
        
        for team_key in ['home_stats', 'away_stats']:
            stats = game_result.get(team_key)
            if not stats or not hasattr(stats, 'player_stats'):
                continue
            
            team = game_result.get('home_team') if team_key == 'home_stats' else game_result.get('away_team')
            
            for player_id, ps in stats.player_stats.items():
                points = getattr(ps, 'points', 0)
                player = getattr(ps, 'player', None)
                
                if points >= 30 and player:
                    fg_made = getattr(ps, 'field_goals_made', 0)
                    fg_att = getattr(ps, 'field_goals_attempted', 1)
                    fg_pct = f"{fg_made}-{fg_att}"
                    
                    priority = 6 if points >= 40 else 5
                    
                    headline = random.choice(self.story_templates['high_score_headline']).format(
                        player=player.name,
                        points=points
                    )
                    
                    body = random.choice(self.story_templates['high_score_body']).format(
                        player=player.name,
                        points=points,
                        team=team.school if team else "his team",
                        position=player.position.value if hasattr(player, 'position') else "guard",
                        fg=fg_pct,
                        detail=f"It was a masterful performance that had the crowd on their feet."
                    )
                    
                    is_user = user_team_id and team and team.id == user_team_id
                    
                    stories.append(NewsStory(
                        id=str(uuid.uuid4()),
                        headline=headline,
                        body=body,
                        category=NewsCategory.HIGH_SCORE,
                        priority=priority,
                        week=week,
                        season=season,
                        game_id=game_id,
                        team_ids=[team.id] if team else [],
                        player_ids=[player.id],
                        is_user_team=is_user,
                        emoji="🔥"
                    ))
        
        return stories
    
    def _check_triple_doubles(self, game_result, game_id, week, season, user_team_id) -> List[NewsStory]:
        """Check for triple-doubles (10+ in 3 categories)"""
        stories = []
        
        for team_key in ['home_stats', 'away_stats']:
            stats = game_result.get(team_key)
            if not stats or not hasattr(stats, 'player_stats'):
                continue
            
            team = game_result.get('home_team') if team_key == 'home_stats' else game_result.get('away_team')
            
            for player_id, ps in stats.player_stats.items():
                points = getattr(ps, 'points', 0)
                rebounds = getattr(ps, 'total_rebounds', 0) or getattr(ps, 'rebounds', 0)
                assists = getattr(ps, 'assists', 0)
                steals = getattr(ps, 'steals', 0)
                blocks = getattr(ps, 'blocks', 0)
                player = getattr(ps, 'player', None)
                
                # Count categories with 10+
                categories_10_plus = sum([
                    points >= 10,
                    rebounds >= 10,
                    assists >= 10,
                    steals >= 10,
                    blocks >= 10
                ])
                
                if categories_10_plus >= 3 and player:
                    headline = random.choice(self.story_templates['triple_double_headline']).format(
                        player=player.name,
                        team=team.school if team else "his team"
                    )
                    
                    stat_line = f"{points} points, {rebounds} rebounds, {assists} assists"
                    if steals >= 10:
                        stat_line += f", {steals} steals"
                    if blocks >= 10:
                        stat_line += f", {blocks} blocks"
                    
                    body = f"{player.name} recorded a rare triple-double with {stat_line}, leading {team.school if team else 'his team'} to victory. Triple-doubles are among the rarest achievements in college basketball."
                    
                    is_user = user_team_id and team and team.id == user_team_id
                    
                    stories.append(NewsStory(
                        id=str(uuid.uuid4()),
                        headline=headline,
                        body=body,
                        category=NewsCategory.TRIPLE_DOUBLE,
                        priority=8,
                        week=week,
                        season=season,
                        game_id=game_id,
                        team_ids=[team.id] if team else [],
                        player_ids=[player.id],
                        is_user_team=is_user,
                        emoji="👑"
                    ))
        
        return stories
    
    def _check_streaks(self, winner, loser, game_id, week, season, user_team_id) -> Optional[NewsStory]:
        """Check for notable winning or losing streaks"""
        
        # Check winner's streak (consecutive wins)
        # We'll estimate based on recent record - in real impl, track actual streak
        if winner.wins >= 5:
            # Estimate streak - this is simplified
            estimated_streak = min(winner.wins, 10)  # Cap at 10 for story purposes
            
            if estimated_streak >= 5:
                is_user = user_team_id and winner.id == user_team_id
                
                headline = random.choice(self.story_templates['streak_win_headline']).format(
                    team=winner.school,
                    count=estimated_streak
                )
                
                body = f"{winner.full_name} continues to roll, extending their winning streak to {estimated_streak} games. The team now sits at {winner.wins}-{winner.losses} on the season and is playing their best basketball of the year."
                
                return NewsStory(
                    id=str(uuid.uuid4()),
                    headline=headline,
                    body=body,
                    category=NewsCategory.STREAK,
                    priority=4,
                    week=week,
                    season=season,
                    game_id=game_id,
                    team_ids=[winner.id],
                    is_user_team=is_user,
                    emoji="📈"
                )
        
        # Check loser's losing streak
        if loser.losses >= 5:
            estimated_streak = min(loser.losses, 10)
            
            if estimated_streak >= 5:
                is_user = user_team_id and loser.id == user_team_id
                
                headline = random.choice(self.story_templates['streak_loss_headline']).format(
                    team=loser.school,
                    count=estimated_streak
                )
                
                body = f"The struggles continue for {loser.full_name}, who have now dropped {estimated_streak} consecutive games. At {loser.wins}-{loser.losses}, the season has not gone as planned."
                
                return NewsStory(
                    id=str(uuid.uuid4()),
                    headline=headline,
                    body=body,
                    category=NewsCategory.STREAK,
                    priority=3,
                    week=week,
                    season=season,
                    game_id=game_id,
                    team_ids=[loser.id],
                    is_user_team=is_user,
                    emoji="📉"
                )
        
        return None
    
    def generate_tournament_stories(self, tournament_result: Dict, tournament_type: str,
                                     week: int, season: int, user_team_id: Optional[str] = None) -> List[NewsStory]:
        """Generate stories specific to tournament games"""
        stories = []
        
        winner = tournament_result.get('winner')
        loser = tournament_result.get('loser')
        score = tournament_result.get('score', '')
        round_name = tournament_result.get('round', '')
        winner_seed = tournament_result.get('winner_seed')
        loser_seed = tournament_result.get('loser_seed')
        
        if not winner or not loser:
            return stories
        
        is_user = user_team_id and (winner.id == user_team_id or loser.id == user_team_id)
        
        # Check for tournament upset (seed differential)
        if winner_seed and loser_seed:
            seed_diff = loser_seed - winner_seed  # Negative means upset
            
            if seed_diff < -4:  # Significant upset
                priority = 9 if seed_diff < -8 else 7
                
                headline = random.choice(self.story_templates['tournament_upset_headline']).format(
                    winner=winner.school,
                    loser=loser.school,
                    winner_seed=winner_seed,
                    loser_seed=loser_seed
                )
                
                body = random.choice(self.story_templates['tournament_upset_body']).format(
                    winner=winner.full_name,
                    loser=loser.full_name,
                    winner_seed=winner_seed,
                    loser_seed=loser_seed,
                    score=score
                )
                
                stories.append(NewsStory(
                    id=str(uuid.uuid4()),
                    headline=headline,
                    body=body,
                    category=NewsCategory.TOURNAMENT,
                    priority=priority,
                    week=week,
                    season=season,
                    team_ids=[winner.id, loser.id],
                    is_user_team=is_user,
                    emoji="🏆"
                ))
        
        # Championship game story
        if 'championship' in round_name.lower() or 'final' in round_name.lower():
            headline = f"🏆 {winner.school} wins {tournament_type}!"
            body = f"{winner.full_name} has won the {tournament_type}, defeating {loser.full_name} {score} in the championship game. What a season for this program!"
            
            stories.append(NewsStory(
                id=str(uuid.uuid4()),
                headline=headline,
                body=body,
                category=NewsCategory.TOURNAMENT,
                priority=10,
                week=week,
                season=season,
                team_ids=[winner.id, loser.id],
                is_user_team=is_user,
                emoji="🏆"
            ))
        
        return stories
    
    # =================================================================
    # NON-GAME EVENT GENERATORS
    # =================================================================
    
    def generate_coaching_carousel_stories(self, carousel, week: int, season: int,
                                            user_team_id: Optional[str] = None) -> List[NewsStory]:
        """Generate news stories from coaching carousel results."""
        stories = []
        
        # Firings
        if hasattr(carousel, 'fired_coaches'):
            for coach in carousel.fired_coaches:
                team_name = "Unknown"
                for change in (carousel.new_hires if hasattr(carousel, 'new_hires') else []):
                    if change.old_coach_name == coach.name and change.change_type == 'firing':
                        team_name = change.team_name
                        break
                
                record = f"{coach.career_stats.career_wins}-{coach.career_stats.career_losses}" if hasattr(coach, 'career_stats') else ""
                headline = random.choice(self.story_templates['coaching_fired_headline']).format(
                    team=team_name, coach=coach.name
                )
                body = f"{coach.name} has been relieved of duties at {team_name}."
                if record:
                    body += f" He leaves with a career record of {record}."
                
                stories.append(NewsStory(
                    id=str(uuid.uuid4()), headline=headline, body=body,
                    category=NewsCategory.COACHING, priority=7,
                    week=week, season=season, emoji="🔥"
                ))
        
        # Retirements
        if hasattr(carousel, 'retired_coaches'):
            for coach in carousel.retired_coaches:
                team_name = "Unknown"
                for change in (carousel.new_hires if hasattr(carousel, 'new_hires') else []):
                    if change.old_coach_name == coach.name and change.change_type == 'retirement':
                        team_name = change.team_name
                        break
                
                seasons = coach.career_stats.seasons_coached if hasattr(coach, 'career_stats') else 0
                headline = random.choice(self.story_templates['coaching_retired_headline']).format(
                    coach=coach.name, team=team_name, seasons=seasons
                )
                body = f"After {seasons} seasons, {coach.name} is hanging up the clipboard at {team_name}."
                
                stories.append(NewsStory(
                    id=str(uuid.uuid4()), headline=headline, body=body,
                    category=NewsCategory.COACHING, priority=6,
                    week=week, season=season, emoji="👋"
                ))
        
        # Poachings (high priority — big storyline)
        if hasattr(carousel, 'poached_coaches'):
            for poach in carousel.poached_coaches:
                coach = poach.get('coach')
                from_team = poach.get('from_team')
                to_team = poach.get('to_team')
                if not coach or not from_team or not to_team:
                    continue
                
                is_user = user_team_id and (from_team.id == user_team_id or to_team.id == user_team_id)
                headline = random.choice(self.story_templates['coaching_poached_headline']).format(
                    coach=coach.name, from_team=from_team.school, to_team=to_team.school
                )
                body = f"{coach.name} has accepted the head coaching position at {to_team.school}, leaving {from_team.school} in need of a new coach."
                
                stories.append(NewsStory(
                    id=str(uuid.uuid4()), headline=headline, body=body,
                    category=NewsCategory.COACHING, priority=8,
                    week=week, season=season, is_user_team=is_user,
                    team_ids=[from_team.id, to_team.id], emoji="💼"
                ))
        
        # New hires
        if hasattr(carousel, 'new_hires'):
            for hire in carousel.new_hires:
                if not hire.new_coach_name:
                    continue
                headline = random.choice(self.story_templates['coaching_hired_headline']).format(
                    team=hire.team_name, coach=hire.new_coach_name
                )
                body = f"{hire.team_name} has named {hire.new_coach_name} as their new head coach."
                
                stories.append(NewsStory(
                    id=str(uuid.uuid4()), headline=headline, body=body,
                    category=NewsCategory.COACHING, priority=5,
                    week=week, season=season, emoji="📋"
                ))
        
        return stories
    
    def generate_portal_stories(self, portal_entries: list, week: int, season: int,
                                 user_team_id: Optional[str] = None) -> List[NewsStory]:
        """Generate news from transfer portal entries. portal_entries = list of dicts with player, from_team, etc."""
        stories = []
        
        for entry in portal_entries:
            player = entry.get('player')
            from_team = entry.get('from_team', entry.get('from_team_id', 'Unknown'))
            if not player:
                continue
            
            ovr = player.overall if hasattr(player, 'overall') else 0
            team_name = from_team if isinstance(from_team, str) else getattr(from_team, 'school', str(from_team))
            is_user = user_team_id and entry.get('from_team_id') == user_team_id
            
            # Star players get bigger headlines
            if ovr >= 78:
                headline = random.choice(self.story_templates['portal_star_headline']).format(
                    player=player.name, team=team_name
                )
                priority = 7
            else:
                headline = random.choice(self.story_templates['portal_entry_headline']).format(
                    player=player.name, team=team_name
                )
                priority = 3
            
            body = f"{player.name} ({player.position.value if hasattr(player.position, 'value') else player.position}, {ovr} OVR) has entered the transfer portal from {team_name}."
            
            stories.append(NewsStory(
                id=str(uuid.uuid4()), headline=headline, body=body,
                category=NewsCategory.PORTAL, priority=priority,
                week=week, season=season, is_user_team=is_user,
                player_ids=[player.id] if hasattr(player, 'id') else [],
                emoji="🚪"
            ))
        
        # Cap at top 10 portal stories to avoid flood
        stories.sort(key=lambda s: s.priority, reverse=True)
        return stories[:10]
    
    def generate_recruiting_stories(self, commits: list, user_team_id: Optional[str] = None,
                                     week: int = 0, season: int = 0) -> List[NewsStory]:
        """Generate news from recruiting commits."""
        stories = []
        
        for commit in commits:
            recruit = commit.get('recruit') or commit
            team = commit.get('team')
            
            name = getattr(recruit, 'name', str(recruit))
            stars = getattr(recruit, 'stars', 3)
            team_name = getattr(team, 'school', 'Unknown') if team else 'Unknown'
            team_id = getattr(team, 'id', '') if team else ''
            is_user = user_team_id and team_id == user_team_id
            
            # Only generate headlines for 4★+ or user team commits
            if stars >= 4 or is_user:
                star_str = "⭐" * stars
                headline = random.choice(self.story_templates['recruiting_commit_headline']).format(
                    stars=star_str, player=name, team=team_name
                )
                body = f"{stars}-star {name} has committed to {team_name}."
                priority = 5 + stars  # 5★ = priority 10, 4★ = 9, etc.
                
                stories.append(NewsStory(
                    id=str(uuid.uuid4()), headline=headline, body=body,
                    category=NewsCategory.RECRUITING, priority=priority,
                    week=week, season=season, is_user_team=is_user,
                    team_ids=[team_id] if team_id else [],
                    emoji="✍️"
                ))
        
        return stories
    
    def generate_signing_day_stories(self, class_rankings: list, user_team_id: Optional[str] = None,
                                      week: int = 0, season: int = 0) -> List[NewsStory]:
        """
        Generate signing day summary stories.
        class_rankings = list of dicts with 'team', 'rank', 'count', 'avg_stars'
        """
        stories = []
        
        # Top 5 classes
        for entry in class_rankings[:5]:
            team = entry.get('team')
            rank = entry.get('rank', 0)
            count = entry.get('count', 0)
            team_name = getattr(team, 'school', 'Unknown') if team else 'Unknown'
            team_id = getattr(team, 'id', '') if team else ''
            is_user = user_team_id and team_id == user_team_id
            
            headline = random.choice(self.story_templates['recruiting_class_headline']).format(
                team=team_name, rank=rank, count=count
            )
            body = f"{team_name} finished with the #{rank} recruiting class in the nation, signing {count} players."
            
            stories.append(NewsStory(
                id=str(uuid.uuid4()), headline=headline, body=body,
                category=NewsCategory.RECRUITING, priority=8 if rank <= 3 else 6,
                week=week, season=season, is_user_team=is_user,
                team_ids=[team_id] if team_id else [],
                emoji="📝"
            ))
        
        return stories
    
    def generate_award_stories(self, awards_data: dict, week: int = 0, season: int = 0,
                                user_team_id: Optional[str] = None) -> List[NewsStory]:
        """
        Generate award announcement stories.
        awards_data = dict with keys like 'poy', 'dpoy', 'all_americans', etc.
        """
        stories = []
        
        # Player of the Year
        poy = awards_data.get('poy')
        if poy:
            name = poy.get('name', 'Unknown')
            team = poy.get('team', 'Unknown')
            ppg = poy.get('ppg', 0)
            is_user = user_team_id and poy.get('team_id') == user_team_id
            
            headline = random.choice(self.story_templates['award_poy_headline']).format(player=name)
            body = f"{name} of {team} has been named the National Player of the Year, averaging {ppg:.1f} points per game."
            
            stories.append(NewsStory(
                id=str(uuid.uuid4()), headline=headline, body=body,
                category=NewsCategory.AWARDS, priority=10,
                week=week, season=season, is_user_team=is_user,
                emoji="🏆"
            ))
        
        # Defensive Player of the Year
        dpoy = awards_data.get('dpoy')
        if dpoy:
            name = dpoy.get('name', 'Unknown')
            team = dpoy.get('team', 'Unknown')
            headline = f"Defensive Player of the Year: {name} ({team})"
            body = f"{name} of {team} takes home the Defensive Player of the Year award."
            
            stories.append(NewsStory(
                id=str(uuid.uuid4()), headline=headline, body=body,
                category=NewsCategory.AWARDS, priority=8,
                week=week, season=season, emoji="🛡️"
            ))
        
        # All-Americans (just announce, don't list everyone)
        all_americans = awards_data.get('all_americans', [])
        if all_americans:
            top_player = all_americans[0] if all_americans else None
            if top_player:
                name = top_player.get('name', 'Unknown')
                headline = random.choice(self.story_templates['award_all_american_headline']).format(player=name)
                body = f"The All-American teams have been announced. {name} leads the First Team selections."
                
                stories.append(NewsStory(
                    id=str(uuid.uuid4()), headline=headline, body=body,
                    category=NewsCategory.AWARDS, priority=9,
                    week=week, season=season, emoji="⭐"
                ))
        
        return stories
    
    def generate_rankings_stories(self, old_rankings: list, new_rankings: list,
                                   week: int = 0, season: int = 0,
                                   user_team_id: Optional[str] = None) -> List[NewsStory]:
        """
        Generate stories from AP Poll changes.
        old_rankings and new_rankings are lists of Team objects (index 0 = #1).
        """
        stories = []
        
        if not new_rankings or not old_rankings:
            return stories
        
        # Build old rank lookup
        old_rank = {}
        for i, t in enumerate(old_rankings[:25], 1):
            if hasattr(t, 'id'):
                old_rank[t.id] = i
        
        # New #1 team
        new_no1 = new_rankings[0] if new_rankings else None
        if new_no1 and hasattr(new_no1, 'id'):
            old_no1 = old_rankings[0] if old_rankings else None
            if old_no1 and hasattr(old_no1, 'id') and new_no1.id != old_no1.id:
                is_user = user_team_id and new_no1.id == user_team_id
                headline = random.choice(self.story_templates['rankings_new_no1_headline']).format(
                    team=new_no1.school
                )
                body = f"{new_no1.full_name} ({new_no1.wins}-{new_no1.losses}) has ascended to the top of the AP Poll."
                
                stories.append(NewsStory(
                    id=str(uuid.uuid4()), headline=headline, body=body,
                    category=NewsCategory.RANKINGS, priority=9,
                    week=week, season=season, is_user_team=is_user,
                    team_ids=[new_no1.id], emoji="👑"
                ))
        
        # Big movers (jumped 5+ spots into top 25)
        for i, t in enumerate(new_rankings[:25], 1):
            if not hasattr(t, 'id'):
                continue
            prev = old_rank.get(t.id)
            if prev and prev - i >= 5:
                is_user = user_team_id and t.id == user_team_id
                headline = random.choice(self.story_templates['rankings_big_mover_headline']).format(
                    team=t.school, spots=prev - i, new_rank=i
                )
                body = f"{t.school} jumped {prev - i} spots from #{prev} to #{i} in this week's AP Poll."
                
                stories.append(NewsStory(
                    id=str(uuid.uuid4()), headline=headline, body=body,
                    category=NewsCategory.RANKINGS, priority=6,
                    week=week, season=season, is_user_team=is_user,
                    team_ids=[t.id], emoji="📈"
                ))
        
        # Teams that dropped out of top 25
        new_ids = {t.id for t in new_rankings[:25] if hasattr(t, 'id')}
        for t_id, prev_rank in old_rank.items():
            if t_id not in new_ids:
                # Find the team object
                dropped_team = None
                for t in old_rankings:
                    if hasattr(t, 'id') and t.id == t_id:
                        dropped_team = t
                        break
                if dropped_team and prev_rank <= 15:  # Only notable if they were top 15
                    is_user = user_team_id and t_id == user_team_id
                    headline = random.choice(self.story_templates['rankings_dropped_headline']).format(
                        team=dropped_team.school
                    )
                    body = f"{dropped_team.school}, previously ranked #{prev_rank}, has fallen out of the AP Top 25."
                    
                    stories.append(NewsStory(
                        id=str(uuid.uuid4()), headline=headline, body=body,
                        category=NewsCategory.RANKINGS, priority=5,
                        week=week, season=season, is_user_team=is_user,
                        team_ids=[t_id], emoji="📉"
                    ))
        
        return stories
    
    def generate_injury_stories(self, injuries: list, week: int = 0, season: int = 0,
                                 user_team_id: Optional[str] = None) -> List[NewsStory]:
        """Generate stories from significant injuries."""
        stories = []
        
        for inj in injuries:
            player = inj.get('player')
            team = inj.get('team')
            injury_obj = inj.get('injury')
            if not player or not team or not injury_obj:
                continue
            
            severity = injury_obj.severity.value if hasattr(injury_obj.severity, 'value') else str(injury_obj.severity)
            games_out = injury_obj.games_remaining if hasattr(injury_obj, 'games_remaining') else 0
            is_user = user_team_id and team.id == user_team_id
            
            # Only generate stories for serious+ injuries or user team
            if severity in ('Serious', 'Severe', 'Career-Threatening') or is_user:
                headline = f"🏥 {team.school}'s {player.name} out with {injury_obj.name}"
                body = f"{player.name} has suffered a {severity.lower()} {injury_obj.name} and will miss approximately {games_out} games."
                priority = 8 if severity in ('Severe', 'Career-Threatening') else 6
                
                stories.append(NewsStory(
                    id=str(uuid.uuid4()), headline=headline, body=body,
                    category=NewsCategory.INJURY, priority=priority,
                    week=week, season=season, is_user_team=is_user,
                    team_ids=[team.id], player_ids=[player.id] if hasattr(player, 'id') else [],
                    emoji="🏥"
                ))
        
        return stories
    
    def generate_development_stories(self, gains: list, week: int = 0, season: int = 0,
                                      user_team_id: Optional[str] = None) -> List[NewsStory]:
        """
        Generate news stories from in-season player development.
        
        Focuses on user team players — the coach wants to see their guys improving.
        Stories are generated for:
        - Any OVR increase (always newsworthy)
        - Significant attribute gains (+2 for freshmen)
        - Multiple gains in the same week (breakout week)
        
        For non-user teams, only generates stories for major developments
        (OVR jumps on ranked teams, breakout freshmen on rivals).
        """
        stories = []
        if not gains:
            return stories
        
        # Group gains by player
        player_gains = {}
        for g in gains:
            player = g.get('player')
            if not player:
                continue
            pid = getattr(player, 'id', None)
            if pid not in player_gains:
                player_gains[pid] = {
                    'player': player,
                    'team': None,
                    'gains': [],
                    'ovr_changed': False,
                    'old_ovr': g.get('old_ovr', 0),
                    'new_ovr': g.get('new_ovr', 0),
                }
            player_gains[pid]['gains'].append(g)
            if g.get('new_ovr', 0) > g.get('old_ovr', 0):
                player_gains[pid]['ovr_changed'] = True
                player_gains[pid]['new_ovr'] = g['new_ovr']
                player_gains[pid]['old_ovr'] = g['old_ovr']
        
        # Resolve team for each player
        for pid, pdata in player_gains.items():
            player = pdata['player']
            # Try to find team from the gain data
            for g in pdata['gains']:
                if g.get('team'):
                    pdata['team'] = g['team']
                    break
            # Fallback: check player.team
            if not pdata['team'] and hasattr(player, 'team'):
                pdata['team'] = player.team
        
        # Attribute display names
        ATTR_DISPLAY = {
            'inside_scoring': 'Inside Scoring', 'three_point': 'Three-Point Shooting',
            'mid_range': 'Mid-Range', 'free_throw': 'Free Throw',
            'ball_handling': 'Ball Handling', 'passing': 'Passing',
            'speed': 'Speed', 'vertical': 'Vertical', 'stamina': 'Stamina',
            'strength': 'Strength',
            'perimeter_defense': 'Perimeter Defense', 'interior_defense': 'Interior Defense',
            'steal': 'Steal', 'block': 'Block',
            'offensive_rebound': 'Offensive Rebounding',
            'defensive_rebound': 'Defensive Rebounding',
            'basketball_iq': 'Basketball IQ',
            'offensive_iq': 'Offensive IQ', 'defensive_iq': 'Defensive IQ',
        }
        
        # Year display
        YEAR_DISPLAY = {0: 'Fr.', 1: 'So.', 2: 'Jr.', 3: 'Sr.'}
        
        # Headline templates for variety
        ovr_headlines = [
            "📈 {name} continues to develop, now a {ovr} OVR {position}",
            "📈 {name} making strides — overall climbs to {ovr}",
            "📈 {name}'s hard work paying off, rated {ovr} OVR",
            "📈 {team}'s {name} improving, now {ovr} overall",
        ]
        
        attr_headlines = [
            "🔧 {name} showing improvement in {attr}",
            "🔧 {name} working on {attr} in practice",
            "🔧 {team}'s {name} developing {attr}",
        ]
        
        breakout_headlines = [
            "🌟 {name} having a breakout week in practice",
            "🌟 {name} impressing coaches with rapid development",
            "🌟 Big week for {team}'s {name} — multiple areas improving",
        ]
        
        freshman_headlines = [
            "🔥 Freshman {name} adjusting fast, {attr} jumps +{gain}",
            "🔥 {team}'s {name} developing quickly as a freshman",
            "🔥 Freshman {name} showing flashes — {attr} on the rise",
        ]
        
        for pid, pdata in player_gains.items():
            player = pdata['player']
            team = pdata['team']
            gain_list = pdata['gains']
            is_user = bool(user_team_id and team and getattr(team, 'id', None) == user_team_id)
            
            team_name = getattr(team, 'school', 'Unknown') if team else 'Unknown'
            team_id = getattr(team, 'id', '') if team else ''
            position = getattr(player, 'position', None)
            pos_str = position.value if hasattr(position, 'value') else str(position) if position else 'player'
            year = getattr(player, 'year', None)
            year_str = ''
            if year is not None:
                year_val = year.value if hasattr(year, 'value') else year
                year_str = YEAR_DISPLAY.get(year_val, '')
            is_freshman = year_str == 'Fr.'
            
            # Format attribute gains
            attr_details = []
            for g in gain_list:
                attr_name = ATTR_DISPLAY.get(g['attr'], g['attr'].replace('_', ' ').title())
                attr_details.append({
                    'name': attr_name,
                    'gain': g['gain'],
                    'old': g['old_val'],
                    'new': g['new_val'],
                    'path': g.get('path', 'game'),
                })
            
            # --- USER TEAM: Always generate stories ---
            if is_user:
                if pdata['ovr_changed']:
                    # OVR increase — most exciting
                    headline = random.choice(ovr_headlines).format(
                        name=player.name, ovr=pdata['new_ovr'],
                        position=pos_str, team=team_name
                    )
                    
                    attr_lines = []
                    for ad in attr_details:
                        source = "game reps" if ad['path'] == 'game' else "practice"
                        attr_lines.append(f"{ad['name']} +{ad['gain']} ({ad['old']}→{ad['new']}) via {source}")
                    
                    body = (f"{year_str} {pos_str} {player.name} improved to {pdata['new_ovr']} OVR "
                            f"(from {pdata['old_ovr']}). "
                            f"This week's gains: {'; '.join(attr_lines)}.")
                    
                    stories.append(NewsStory(
                        id=str(uuid.uuid4()), headline=headline, body=body,
                        category=NewsCategory.DEVELOPMENT, priority=7,
                        week=week, season=season, is_user_team=True,
                        team_ids=[team_id], player_ids=[pid] if pid else [],
                        emoji="📈"
                    ))
                
                elif len(gain_list) >= 2:
                    # Multiple gains in one week — breakout
                    headline = random.choice(breakout_headlines).format(
                        name=player.name, team=team_name
                    )
                    
                    attr_lines = []
                    for ad in attr_details:
                        source = "game reps" if ad['path'] == 'game' else "practice"
                        attr_lines.append(f"{ad['name']} +{ad['gain']} ({ad['old']}→{ad['new']})")
                    
                    body = (f"{year_str} {pos_str} {player.name} had a productive week. "
                            f"Improvements: {'; '.join(attr_lines)}.")
                    
                    stories.append(NewsStory(
                        id=str(uuid.uuid4()), headline=headline, body=body,
                        category=NewsCategory.DEVELOPMENT, priority=5,
                        week=week, season=season, is_user_team=True,
                        team_ids=[team_id], player_ids=[pid] if pid else [],
                        emoji="🌟"
                    ))
                
                elif is_freshman and gain_list[0].get('gain', 1) >= 2:
                    # Freshman +2 gain — exciting development
                    ad = attr_details[0]
                    headline = random.choice(freshman_headlines).format(
                        name=player.name, team=team_name,
                        attr=ad['name'], gain=ad['gain']
                    )
                    body = (f"Freshman {player.name} jumped +{ad['gain']} in {ad['name']} "
                            f"({ad['old']}→{ad['new']}) through {ad['path']}. "
                            f"The {pos_str} is adjusting quickly to the college game.")
                    
                    stories.append(NewsStory(
                        id=str(uuid.uuid4()), headline=headline, body=body,
                        category=NewsCategory.DEVELOPMENT, priority=6,
                        week=week, season=season, is_user_team=True,
                        team_ids=[team_id], player_ids=[pid] if pid else [],
                        emoji="🔥"
                    ))
                
                else:
                    # Single attribute gain — routine but still reported for user team
                    ad = attr_details[0]
                    headline = random.choice(attr_headlines).format(
                        name=player.name, team=team_name, attr=ad['name']
                    )
                    source = "game reps" if ad['path'] == 'game' else "practice"
                    body = (f"{year_str} {pos_str} {player.name}'s {ad['name']} "
                            f"improved +{ad['gain']} ({ad['old']}→{ad['new']}) through {source}.")
                    
                    stories.append(NewsStory(
                        id=str(uuid.uuid4()), headline=headline, body=body,
                        category=NewsCategory.DEVELOPMENT, priority=3,
                        week=week, season=season, is_user_team=True,
                        team_ids=[team_id], player_ids=[pid] if pid else [],
                        emoji="🔧"
                    ))
        
        return stories
    
    def generate_season_recap_stories(self, league, user_team_id: Optional[str] = None,
                                       season: int = 0) -> List[NewsStory]:
        """Generate end-of-season recap stories — champion, best records, surprises."""
        stories = []
        week = getattr(league, 'current_week', 0)
        
        # National champion story
        champion = None
        if hasattr(league, 'ncaa_tournament') and league.ncaa_tournament:
            champion = getattr(league.ncaa_tournament, 'champion', None)
        
        if champion:
            is_user = user_team_id and champion.id == user_team_id
            wins = getattr(champion, 'wins', 0)
            losses = getattr(champion, 'losses', 0)
            headline = f"🏆 {champion.school} wins the National Championship!"
            body = f"{champion.school} ({wins}-{losses}) cuts down the nets as national champions."
            stories.append(NewsStory(
                id=str(uuid.uuid4()), headline=headline, body=body,
                category=NewsCategory.AWARDS, priority=10,
                week=week, season=season, is_user_team=is_user,
                team_ids=[champion.id], emoji="🏆"
            ))
        
        # Best record in the nation
        teams_by_wins = sorted(league.teams, key=lambda t: (-t.wins, t.losses))
        if teams_by_wins:
            best = teams_by_wins[0]
            if best.wins >= 25:
                is_user = user_team_id and best.id == user_team_id
                headline = f"📊 {best.school} finishes with nation's best record at {best.wins}-{best.losses}"
                body = f"{best.school} posted the most wins in the country this season."
                stories.append(NewsStory(
                    id=str(uuid.uuid4()), headline=headline, body=body,
                    category=NewsCategory.RANKINGS, priority=6,
                    week=week, season=season, is_user_team=is_user,
                    team_ids=[best.id], emoji="📊"
                ))
        
        # Surprise teams (low prestige, high wins)
        for team in league.teams:
            if team.prestige < 55 and team.wins >= 22:
                is_user = user_team_id and team.id == user_team_id
                headline = f"⬆️ Cinderella season: {team.school} finishes {team.wins}-{team.losses}"
                body = f"{team.school} exceeded all expectations with a breakout season."
                stories.append(NewsStory(
                    id=str(uuid.uuid4()), headline=headline, body=body,
                    category=NewsCategory.RANKINGS, priority=5,
                    week=week, season=season, is_user_team=is_user,
                    team_ids=[team.id], emoji="⬆️"
                ))
        
        return stories
    
    def add_story(self, story: NewsStory):
        """Add a story to the collection"""
        self.stories.append(story)
    
    def add_stories(self, stories: List[NewsStory]):
        """Add multiple stories"""
        self.stories.extend(stories)
    
    def get_top_stories(self, count: int = 5, user_team_id: Optional[str] = None,
                        week: Optional[int] = None, category: Optional[NewsCategory] = None) -> List[NewsStory]:
        """Get top stories by priority, optionally filtered"""
        filtered = self.stories
        
        if week is not None:
            filtered = [s for s in filtered if s.week == week]
        
        if category:
            filtered = [s for s in filtered if s.category == category]
        
        # Boost user team stories
        def sort_key(story):
            boost = 2 if story.is_user_team else 0
            return story.priority + boost
        
        sorted_stories = sorted(filtered, key=sort_key, reverse=True)
        return sorted_stories[:count]
    
    def get_stories_by_week(self, week: int) -> List[NewsStory]:
        """Get all stories from a specific week"""
        return [s for s in self.stories if s.week == week]
    
    def get_user_team_stories(self, user_team_id: str, count: int = 10) -> List[NewsStory]:
        """Get stories involving the user's team"""
        user_stories = [s for s in self.stories if user_team_id in s.team_ids or s.is_user_team]
        return sorted(user_stories, key=lambda s: (s.week, s.priority), reverse=True)[:count]
    
    def clear_old_stories(self, keep_weeks: int = 4, current_week: int = 1):
        """Remove stories older than keep_weeks"""
        cutoff = current_week - keep_weeks
        self.stories = [s for s in self.stories if s.week >= cutoff]
    
    def to_dict(self) -> Dict:
        """Serialize for saving"""
        return {
            'stories': [s.to_dict() for s in self.stories]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NewsEngine':
        """Deserialize from saved data"""
        engine = cls()
        for story_data in data.get('stories', []):
            story = NewsStory(
                id=story_data['id'],
                headline=story_data['headline'],
                body=story_data['body'],
                category=NewsCategory(story_data['category']),
                priority=story_data['priority'],
                week=story_data['week'],
                season=story_data['season'],
                game_id=story_data.get('game_id'),
                team_ids=story_data.get('team_ids', []),
                player_ids=story_data.get('player_ids', []),
                is_user_team=story_data.get('is_user_team', False),
                emoji=story_data.get('emoji', '📰')
            )
            engine.stories.append(story)
        return engine


# Convenience function for generating stories from a game
def generate_news_from_game(game_result: Dict, league: Any, news_engine: NewsEngine,
                            user_team_id: Optional[str] = None) -> List[NewsStory]:
    """Helper function to generate and add news from a game result"""
    stories = news_engine.generate_game_stories(game_result, league, user_team_id)
    news_engine.add_stories(stories)
    return stories
