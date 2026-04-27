"""
Cage Dynasty - Flask Routes (Views/Controllers)
All route handlers for the web application.
"""

from flask import render_template, redirect, url_for, request, jsonify, flash, session
from functools import wraps
import uuid


def register_routes(app):
    """Register all routes with the Flask application."""
    
    # Helper to get the game bridge
    def get_bridge():
        return app.game_bridge
    
    # =========================================================================
    # GAME SETUP / NEW GAME FLOW
    # =========================================================================
    
    def require_game_started(f):
        """Decorator to ensure game has been set up before accessing routes."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not get_bridge().game_started:
                return redirect(url_for('new_game'))
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/new-game')
    def new_game():
        """New game start screen."""
        return render_template('new_game.html')
    
    @app.route('/setup/camp', methods=['GET', 'POST'])
    def setup_camp():
        """Step 1: Create your camp."""
        if request.method == 'POST':
            # Save camp info to session
            session['camp_name'] = request.form.get('camp_name', 'My Gym')
            session['camp_location'] = request.form.get('camp_location', 'Las Vegas, NV')
            session['camp_tier'] = request.form.get('camp_tier', 'GARAGE')
            return redirect(url_for('setup_coach'))
        
        locations = [
            "Las Vegas, NV", "Los Angeles, CA", "Miami, FL", "New York, NY",
            "Dallas, TX", "Chicago, IL", "Denver, CO", "Phoenix, AZ",
            "San Diego, CA", "Albuquerque, NM", "Sacramento, CA", "Portland, OR"
        ]
        
        # Only GARAGE tier available at start - you earn your way up!
        tiers = [
            ("GARAGE", "Garage Gym", "$50,000", "3 fighters max, basic equipment - where legends begin"),
        ]
        
        return render_template('setup_camp.html', locations=locations, tiers=tiers)
    
    @app.route('/setup/coach', methods=['GET', 'POST'])
    def setup_coach():
        """Step 2: Hire your head coach."""
        if 'camp_name' not in session:
            return redirect(url_for('setup_camp'))
        
        # Generate coaches (or get from session if already generated)
        if 'available_coaches' not in session:
            tier = session.get('camp_tier', 'GARAGE')
            coaches = _generate_available_coaches(tier)
            session['available_coaches'] = coaches
        else:
            coaches = session['available_coaches']
        
        if request.method == 'POST':
            coach_id = request.form.get('coach_id')
            # Find the selected coach and store full data
            selected_coach = next((c for c in coaches if c['id'] == coach_id), None)
            if selected_coach:
                session['selected_coach'] = selected_coach
            return redirect(url_for('setup_fighter'))
        
        return render_template('setup_coach.html', 
            coaches=coaches,
            camp_name=session.get('camp_name'),
            camp_tier=session.get('camp_tier', 'GARAGE')
        )
    
    @app.route('/setup/fighter', methods=['GET', 'POST'])
    def setup_fighter():
        """Step 3: Sign your first fighter."""
        if 'camp_name' not in session or 'selected_coach' not in session:
            return redirect(url_for('setup_camp'))
        
        # Generate prospects (or get from session if already generated)
        if 'available_prospects' not in session:
            prospects = _generate_available_prospects()
            session['available_prospects'] = prospects
        else:
            prospects = session['available_prospects']
        
        if request.method == 'POST':
            fighter_id = request.form.get('fighter_id')
            # Find the selected prospect and store full data
            selected_prospect = next((p for p in prospects if p['id'] == fighter_id), None)
            if selected_prospect:
                session['selected_fighter'] = selected_prospect
            return redirect(url_for('start_game'))
        
        return render_template('setup_fighter.html',
            prospects=prospects,
            camp_name=session.get('camp_name')
        )
    
    @app.route('/start-game')
    def start_game():
        """Finalize setup and start the game."""
        if 'camp_name' not in session:
            return redirect(url_for('setup_camp'))
        
        # Get full coach and fighter data from session
        coach_data = session.get('selected_coach', {})
        fighter_data = session.get('selected_fighter', {})
        
        # Start the game through the bridge
        bridge = get_bridge()
        success = bridge.new_game(
            camp_name=session.get('camp_name', 'My Gym'),
            camp_location=session.get('camp_location', 'Las Vegas, NV'),
            camp_tier=session.get('camp_tier', 'GARAGE'),
            coach_data=coach_data,
            fighter_data=fighter_data
        )
        
        if not success:
            flash("Error starting game. Please try again.", "error")
            return redirect(url_for('new_game'))
        
        # Clear session setup data
        for key in ['camp_name', 'camp_location', 'camp_tier', 'selected_coach', 'selected_fighter', 'available_coaches', 'available_prospects']:
            session.pop(key, None)
        
        flash(f"Welcome to the DFC! Your journey begins now.", "success")
        return redirect(url_for('dashboard'))
    
    def _generate_available_coaches(tier):
        """Generate coaches available for hiring based on tier."""
        # Try to use real game_start module
        try:
            from systems.game_start import generate_starting_coaches
            coaches = generate_starting_coaches(num_coaches=6)
            return [
                {
                    "id": c.coach_id,
                    "name": c.name,
                    "specialty": c.specialty,
                    "rating": c.skill_level,
                    "salary": c.weekly_salary,
                    "description": f"{c.personality_desc}. {c.get_bonus_description()}"
                }
                for c in coaches
            ]
        except ImportError as e:
            print(f"Could not import game_start: {e}")
        
        # Fallback to simple generation
        import random
        
        tier_ratings = {
            "GARAGE": (55, 75),
            "LOCAL": (60, 80),
            "REGIONAL": (65, 85),
            "NATIONAL": (75, 90),
            "ELITE": (85, 98),
        }
        
        min_r, max_r = tier_ratings.get(tier, (55, 75))
        
        specialties = ["Striking", "Wrestling", "BJJ", "Conditioning", "Strength", "Cornering"]
        first_names = ["Mike", "John", "Carlos", "Greg", "Dave", "Tony", "Rafael", "Alex"]
        last_names = ["Johnson", "Martinez", "Smith", "Williams", "Garcia", "Brown", "Davis", "Miller"]
        
        coaches = []
        for i in range(6):
            rating = random.randint(min_r, max_r)
            specialty = random.choice(specialties)
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            # Salary based on rating
            if rating >= 75:
                salary = 1500 + (rating - 75) * 100
            elif rating >= 65:
                salary = 1000 + (rating - 65) * 50
            else:
                salary = 600 + (rating - 55) * 40
            
            coaches.append({
                "id": f"coach_{i}",
                "name": name,
                "specialty": specialty,
                "rating": rating,
                "salary": salary,
                "description": f"Experienced {specialty.lower()} coach with {random.randint(5, 20)} years in the game."
            })
        
        coaches.sort(key=lambda c: c['rating'], reverse=True)
        return coaches
    
    def _generate_available_prospects():
        """Generate prospect fighters to choose from - one per weight class."""
        # Try to use real game_start module
        try:
            from systems.game_start import generate_starting_prospects
            prospects = generate_starting_prospects(player_region="Americas")
            return [
                {
                    "id": p.prospect_id,
                    "name": p.name,
                    "nickname": getattr(p, 'nickname', None),
                    "age": p.age,
                    "country": p.country,
                    "weight_class": p.weight_class,
                    "style": p.fighting_style,
                    "overall": p.overall_rating,
                    "potential": p.potential_ceiling,
                    "potential_grade": p.potential_grade,
                    "description": f"{p.potential_grade} potential {p.fighting_style.lower()} from {p.country}.",
                    "traits": getattr(p, 'traits', []),
                    "estimated_cost": getattr(p, 'estimated_cost', 30000),
                }
                for p in prospects
            ]
        except ImportError as e:
            print(f"Could not import game_start: {e}")
        
        # Fallback - generate 9 prospects (one per weight class)
        import random
        
        weight_classes = [
            "Strawweight", "Flyweight", "Bantamweight", "Featherweight", 
            "Lightweight", "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"
        ]
        
        styles = ["Orthodox Boxer", "Muay Thai", "Wrestler", "BJJ Specialist", "Kickboxer", "Brawler"]
        
        first_names = ["Jake", "Marcus", "Chen", "Diego", "Kenji", "Patrick", "Dmitri", "Bruno", "Rashid"]
        last_names = ["Anderson", "Silva", "Lee", "Rodriguez", "Tanaka", "O'Brien", "Volkov", "Costa", "Hassan"]
        countries = ["USA", "Brazil", "Japan", "Mexico", "Ireland", "Russia", "UK", "Thailand", "Kazakhstan"]
        
        potential_grades = ["Elite", "High", "Average", "Average", "Average", "High", "Low", "Average", "High"]
        
        prospects = []
        for i, wc in enumerate(weight_classes):
            grade = potential_grades[i]
            
            if grade == "Elite":
                potential = random.randint(88, 95)
                base_rating = potential - random.randint(12, 18)
            elif grade == "High":
                potential = random.randint(82, 90)
                base_rating = potential - random.randint(10, 15)
            elif grade == "Average":
                potential = random.randint(75, 84)
                base_rating = potential - random.randint(8, 14)
            else:
                potential = random.randint(68, 78)
                base_rating = potential - random.randint(6, 12)
            
            age = random.randint(19, 23)
            
            prospects.append({
                "id": f"prospect_{i}",
                "name": f"{random.choice(first_names)} {random.choice(last_names)}",
                "nickname": None,
                "age": age,
                "country": random.choice(countries),
                "weight_class": wc,
                "style": random.choice(styles),
                "overall": base_rating,
                "potential": potential,
                "potential_grade": grade,
                "description": f"{grade} potential prospect from {random.choice(countries)}.",
                "traits": [],
                "estimated_cost": 30000,
            })
        
        # Sort by potential (highest first)
        prospects.sort(key=lambda p: p['potential'], reverse=True)
        return prospects
    
    # =========================================================================
    # DASHBOARD
    # =========================================================================
    
    @app.route('/')
    def dashboard():
        """Main dashboard/hub view."""
        bridge = get_bridge()
        
        # If game not started, redirect to new game
        if not bridge.game_started:
            return redirect(url_for('new_game'))
        
        camp = bridge.get_player_camp()
        fighters = bridge.get_player_fighters()
        
        # Get scheduled fights for player's fighters
        scheduled_fights = bridge.get_scheduled_fights()
        
        # Add weeks_until and fighter object to each fight
        for fight in scheduled_fights:
            fight['weeks_until'] = fight['week'] - bridge.week_number
            # Find the player's fighter in this fight
            for f in fighters:
                if fight.get("fighter1_id") == f.fighter_id:
                    fight['fighter'] = f
                    break
                elif fight.get("fighter2_id") == f.fighter_id:
                    fight['fighter'] = f
                    break
        
        # Get fight offers count
        offers = bridge.get_fight_offers()
        fighter_ids = [f.fighter_id for f in fighters]
        offer_count = len([o for o in offers if o.fighter_id in fighter_ids])
        
        # Get news
        news = bridge.get_news_feed(limit=10)
        
        # Get champions
        champions = {}
        for wc in ["Lightweight", "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"]:
            champions[wc] = bridge.get_champion(wc)
        
        # Finance summary
        finances = bridge.get_camp_finances()

        # Pending interviews
        pending_interviews = bridge.get_pending_interviews()

        return render_template('dashboard.html',
            camp=camp,
            fighters=fighters,
            news=news,
            week=bridge.week_number,
            offer_count=offer_count,
            scheduled_fights=scheduled_fights,
            champions=champions,
            finances=finances,
            pending_interviews=pending_interviews,
        )
    
    # =========================================================================
    # ROSTER
    # =========================================================================
    
    @app.route('/roster')
    def roster():
        """Player's fighter roster view."""
        bridge = get_bridge()
        
        if not bridge.game_started:
            return redirect(url_for('new_game'))
            
        camp = bridge.get_player_camp()
        fighters = bridge.get_player_fighters()
        
        # Sort options
        sort_by = request.args.get('sort', 'rating')
        
        if sort_by == 'rating':
            fighters.sort(key=lambda f: f.overall_rating, reverse=True)
        elif sort_by == 'record':
            fighters.sort(key=lambda f: (f.wins, -f.losses), reverse=True)
        elif sort_by == 'name':
            fighters.sort(key=lambda f: f.name)
        elif sort_by == 'division':
            fighters.sort(key=lambda f: f.weight_class)
        
        return render_template('roster.html',
            camp=camp,
            fighters=fighters,
            sort_by=sort_by,
            week=bridge.week_number,
        )
    
    # =========================================================================
    # FIGHTER PROFILE
    # =========================================================================
    
    @app.route('/fighter/<fighter_id>')
    def fighter_profile(fighter_id):
        """Detailed fighter profile view."""
        bridge = get_bridge()
        fighter = bridge.get_fighter(fighter_id)
        
        if not fighter:
            flash("Fighter not found", "error")
            return redirect(url_for('roster'))
        
        # Get division rankings for context
        division_rankings = bridge.get_division_rankings(fighter.weight_class)
        
        # Get fighter's camp
        camp = bridge.get_camp(fighter.camp_id) if fighter.camp_id else None
        
        # Belt history placeholder (TODO: implement in bridge)
        belt_history = []
        
        # Calculate attribute categories
        attributes = {
            'physical': [
                ('Strength', fighter.strength),
                ('Speed', fighter.speed),
                ('Cardio', fighter.cardio),
                ('Chin', fighter.chin),
                ('Recovery', fighter.recovery),
            ],
            'striking': [
                ('Boxing', fighter.boxing),
                ('Kicks', fighter.kicks),
                ('Clinch', fighter.clinch_striking),
                ('Defense', fighter.striking_defense),
            ],
            'grappling': [
                ('Takedowns', fighter.takedowns),
                ('TD Defense', fighter.takedown_defense),
                ('Top Control', fighter.top_control),
                ('Submissions', fighter.submissions),
                ('Guard', fighter.guard),
            ],
            'mental': [
                ('Heart', fighter.heart),
                ('Fight IQ', fighter.fight_iq),
                ('Composure', fighter.composure),
            ],
        }
        
        # Get rival data
        rivalries = bridge.get_fighter_rivalries(fighter_id)

        # Scouting report
        scouting = bridge.get_scouting_report(fighter_id)

        # Watchlist status
        on_watchlist   = bridge.is_on_watchlist(fighter_id)
        watch_entry    = bridge._watchlist.get(fighter_id) if on_watchlist else None
        watch_categories = bridge._WATCH_CATEGORIES

        return render_template('fighter_profile.html',
            fighter=fighter,
            attributes=attributes,
            camp=camp,
            division_rankings=division_rankings[:10],
            belt_history=belt_history,
            rivalries=rivalries,
            scouting=scouting,
            on_watchlist=on_watchlist,
            watch_entry=watch_entry,
            watch_categories=watch_categories,
            week=bridge.week_number,
        )
    
    # =========================================================================
    # FIGHT OFFERS
    # =========================================================================
    
    @app.route('/offers')
    def fight_offers():
        """Fight offers/contract center view."""
        bridge = get_bridge()
        fighters = bridge.get_player_fighters()
        offers = bridge.get_fight_offers()
        
        # Group offers by fighter
        offers_by_fighter = {}
        for fighter in fighters:
            fighter_offers = [o for o in offers if o.fighter_id == fighter.fighter_id]
            if fighter_offers:
                offers_by_fighter[fighter.fighter_id] = {
                    'fighter': fighter,
                    'offers': fighter_offers
                }
        
        return render_template('offers.html',
            offers_by_fighter=offers_by_fighter,
            week=bridge.week_number,
        )
    
    @app.route('/offer/<offer_id>/accept', methods=['POST'])
    def accept_offer(offer_id):
        """Accept a fight offer — then send player to fight camp setup."""
        bridge = get_bridge()
        result = bridge.accept_fight_offer(offer_id)

        if result.get("success"):
            fight_id = result.get("fight_id")
            if fight_id:
                flash(result.get("message", "Fight scheduled!"), "success")
                return redirect(url_for('fight_camp', fight_id=fight_id))
            flash(result.get("message", "Fight scheduled!"), "success")
        else:
            flash(result.get("error", "Error accepting offer"), "error")

        return redirect(url_for('fight_offers'))
    
    @app.route('/offer/<offer_id>/decline', methods=['POST'])
    def decline_offer(offer_id):
        """Decline a fight offer."""
        bridge = get_bridge()
        result = bridge.decline_fight_offer(offer_id)
        
        if result.get("success"):
            flash("Offer declined", "info")
        else:
            flash(result.get("error", "Error declining offer"), "error")
        
        return redirect(url_for('fight_offers'))
    
    # =========================================================================
    # TRAINING
    # =========================================================================
    
    @app.route('/training')
    def training():
        """Training management view."""
        bridge = get_bridge()
        fighters = bridge.get_player_fighters()
        camp = bridge.get_player_camp()
        
        # Training focus options
        focus_options = [
            ('boxing', 'Boxing', 'Improve hand striking'),
            ('kicks', 'Kicks', 'Improve leg/body kicks'),
            ('wrestling', 'Wrestling', 'Improve takedowns and control'),
            ('bjj', 'BJJ', 'Improve submissions and guard'),
            ('cardio', 'Cardio', 'Improve stamina and recovery'),
            ('strength', 'Strength', 'Improve power and clinch'),
            ('sparring', 'Sparring', 'Balanced improvement'),
        ]
        
        # Intensity options
        intensity_options = [
            ('rest', 'Rest', '-15 fatigue, no gains'),
            ('light', 'Light', '+2 fatigue, 50% gains'),
            ('moderate', 'Moderate', '+5 fatigue, 100% gains'),
            ('intense', 'Intense', '+10 fatigue, 150% gains'),
            ('extreme', 'Extreme', '+18 fatigue, 200% gains, injury risk'),
        ]
        
        return render_template('training.html',
            fighters=fighters,
            camp=camp,
            focus_options=focus_options,
            intensity_options=intensity_options,
            week=bridge.week_number,
        )
    
    @app.route('/training/set', methods=['POST'])
    def set_training():
        """Set training for a fighter — applies gains with facility cap enforcement."""
        bridge      = get_bridge()
        fighter_id  = request.form.get('fighter_id')
        focus       = request.form.get('focus', 'boxing')
        intensity   = request.form.get('intensity', 'MODERATE')

        fighter = bridge.get_fighter(fighter_id)
        camp    = bridge.get_player_camp()

        if fighter and camp:
            camp_tier = camp.tier if camp else "GARAGE"
            result    = bridge.apply_training_week(fighter_id, focus, intensity, camp_tier)
            if result.get("success"):
                gains = result.get("actual_gains", {})
                capped = result.get("capped_stats", [])
                gain_str = ", ".join(
                    f"+{v} {k}" for k, v in gains.items() if v > 0
                ) or "no gains"
                msg = f"Training set for {fighter.name}: {focus.title()} ({intensity.title()}) — {gain_str}"
                if capped:
                    msg += f" ⚠️ Capped at facility limit: {', '.join(capped)}"
                flash(msg, "success")
            else:
                flash(f"Training set for {fighter.name}: {focus.title()} ({intensity.title()})", "success")
        elif fighter:
            flash(f"Training set for {fighter.name}: {focus.title()} ({intensity.title()})", "success")

        return redirect(url_for('training'))
    
    # =========================================================================
    # RANKINGS
    # =========================================================================
    
    @app.route('/rankings')
    @app.route('/rankings/<division>')
    def rankings(division=None):
        """Rankings view with division selector."""
        bridge = get_bridge()
        
        divisions = [
            "Strawweight", "Flyweight", "Bantamweight", "Featherweight",
            "Lightweight", "Welterweight", "Middleweight", 
            "Light Heavyweight", "Heavyweight"
        ]
        
        if division is None:
            division = "Lightweight"  # Default
        
        # Get division rankings
        division_rankings = bridge.get_division_rankings(division)
        champion = bridge.get_champion(division)
        
        # P4P rankings - get all fighters from all divisions
        all_fighters = []
        for div in divisions:
            all_fighters.extend(bridge.get_division_rankings(div))
        
        # Remove duplicates and sort by rating
        seen = set()
        unique_fighters = []
        for f in all_fighters:
            if f.fighter_id not in seen:
                seen.add(f.fighter_id)
                unique_fighters.append(f)
        
        p4p_fighters = sorted(
            [f for f in unique_fighters if f.is_active],
            key=lambda f: (f.is_champion, f.overall_rating, f.wins),
            reverse=True
        )[:15]
        
        # GOAT rankings
        goat_fighters = sorted(
            [f for f in unique_fighters if f.wins + f.losses >= 5],
            key=lambda f: (f.wins * 10 + f.ko_wins * 5 - f.losses * 2),
            reverse=True
        )[:20]
        
        return render_template('rankings.html',
            divisions=divisions,
            current_division=division,
            division_rankings=division_rankings,
            champion=champion,
            p4p_rankings=p4p_fighters,
            goat_rankings=goat_fighters,
            week=bridge.week_number,
        )
    
    # =========================================================================
    # DIVISION LADDER
    # =========================================================================
    
    @app.route('/ladder')
    @app.route('/ladder/<division>')
    def division_ladder(division=None):
        """Division ladder view."""
        bridge = get_bridge()
        player_fighters = bridge.get_player_fighters()
        
        # Default to player's fighter division
        if division is None:
            if player_fighters:
                division = player_fighters[0].weight_class
            else:
                division = "Lightweight"
        
        divisions = [
            "Strawweight", "Flyweight", "Bantamweight", "Featherweight",
            "Lightweight", "Welterweight", "Middleweight",
            "Light Heavyweight", "Heavyweight"
        ]
        
        # Get division fighters
        rankings = bridge.get_division_rankings(division)
        champion = bridge.get_champion(division)
        
        # Split into tiers
        contenders = [f for f in rankings if f.ranking and f.ranking <= 5 and not f.is_champion]
        ranked = [f for f in rankings if f.ranking and f.ranking > 5]
        unranked = [f for f in rankings if not f.ranking and not f.is_champion][:10]
        
        # Check if player has fighter in this division
        player_in_division = any(f.weight_class == division for f in player_fighters)
        player_fighter = next((f for f in player_fighters if f.weight_class == division), None)
        
        return render_template('ladder.html',
            divisions=divisions,
            current_division=division,
            champion=champion,
            contenders=contenders,
            ranked=ranked,
            unranked=unranked,
            player_fighter=player_fighter,
            player_in_division=player_in_division,
            week=bridge.week_number,
        )
    
    # =========================================================================
    # CAMPS
    # =========================================================================
    
    @app.route('/camps')
    def browse_camps():
        """Browse all training camps."""
        bridge = get_bridge()
        all_camps = bridge.get_all_camps()
        
        # Group camps by tier
        camps_by_tier = {tier: [] for tier in ["ELITE", "NATIONAL", "REGIONAL", "LOCAL", "GARAGE"]}
        
        for camp in all_camps:
            tier = camp.tier
            if tier not in camps_by_tier:
                tier = "GARAGE"  # Fallback
            
            # Get fighters for this camp
            fighters = [bridge.get_fighter(fid) for fid in camp.fighter_ids]
            fighters = [f for f in fighters if f]  # Filter None
            champions = sum(1 for f in fighters if f.is_champion)
            ranked_count = sum(1 for f in fighters if f.ranking and f.ranking <= 15)
            
            camps_by_tier[tier].append({
                'camp': camp,
                'fighter_count': len(fighters),
                'champions': champions,
                'ranked': ranked_count,
            })
        
        # Sort each tier by reputation
        for tier in camps_by_tier:
            camps_by_tier[tier].sort(key=lambda c: c['camp'].reputation, reverse=True)
        
        return render_template('camps.html',
            camps_by_tier=camps_by_tier,
            week=bridge.week_number,
        )
    
    @app.route('/camp/<camp_id>')
    def camp_detail(camp_id):
        """Detailed camp view."""
        bridge = get_bridge()
        camp = bridge.get_camp(camp_id)
        
        if not camp:
            flash("Camp not found", "error")
            return redirect(url_for('browse_camps'))
        
        # Get fighters
        fighters = [bridge.get_fighter(fid) for fid in camp.fighter_ids]
        fighters = [f for f in fighters if f]  # Filter None
        fighters.sort(key=lambda f: (not f.is_champion, -(f.ranking or 100), -f.overall_rating))
        
        # Stats
        champions = [f for f in fighters if f.is_champion]
        ranked = [f for f in fighters if f.ranking and f.ranking <= 15]
        
        return render_template('camp_detail.html',
            camp=camp,
            fighters=fighters,
            champions=champions,
            ranked=ranked,
            week=bridge.week_number,
        )
    
    # =========================================================================
    # CHAMPIONS HISTORY
    # =========================================================================
    
    @app.route('/champions')
    @app.route('/champions/<division>')
    def champions_history(division=None):
        """Champions history / belt lineage view."""
        bridge = get_bridge()
        
        divisions = [
            "Strawweight", "Flyweight", "Bantamweight", "Featherweight",
            "Lightweight", "Welterweight", "Middleweight",
            "Light Heavyweight", "Heavyweight"
        ]
        
        if division is None:
            division = "Lightweight"
        
        # Get current champion
        champion = bridge.get_champion(division)
        
        # Belt history placeholder (TODO: implement in bridge)
        reigns = []
        
        return render_template('champions.html',
            divisions=divisions,
            current_division=division,
            champion=champion,
            reigns=reigns,
            total_changes=0,
            most_defenses=0,
            week=bridge.week_number,
        )
    
    # =========================================================================
    # NEWS FEED
    # =========================================================================
    
    @app.route('/news')
    def news_feed():
        """Full news feed view with filters."""
        bridge = get_bridge()
        
        # Filter options
        category = request.args.get('category', 'all')
        
        all_news = bridge.get_news_feed(limit=100)
        
        if category == 'all':
            news = all_news
        else:
            news = [n for n in all_news if n.category == category]
        
        categories = ['all', 'title', 'fight', 'signing', 'injury', 'ranking', 'retirement']
        
        return render_template('news.html',
            news=news[:50],
            current_category=category,
            categories=categories,
            week=bridge.week_number,
        )
    
    # =========================================================================
    # EVENTS / ARCHIVES
    # =========================================================================
    
    @app.route('/events')
    def upcoming_events():
        """Upcoming events view."""
        bridge = get_bridge()
        events = bridge.get_upcoming_events()
        
        return render_template('events.html',
            events=events,
            week=bridge.week_number,
        )
    
    @app.route('/archives')
    def archives():
        """Past events archive view."""
        bridge = get_bridge()
        events = bridge.get_completed_events()
        
        # Sort by week descending
        events = sorted(events, key=lambda e: e.get('week', 0), reverse=True)
        
        return render_template('archives.html',
            events=events[:20],
            week=bridge.week_number,
        )
    
    @app.route('/event/<event_id>')
    def event_detail(event_id):
        """Event detail view with fight results."""
        bridge = get_bridge()
        events = bridge.get_completed_events()
        
        event = next((e for e in events if e.get('event_id') == event_id), None)
        
        if not event:
            flash("Event not found", "error")
            return redirect(url_for('archives'))
        
        return render_template('event_detail.html',
            event=event,
            week=bridge.week_number,
        )
    
    # =========================================================================
    # FIGHT SIMULATION
    # =========================================================================
    
    @app.route('/fight/<fight_id>')
    def fight_view(fight_id):
        """Live fight view with play-by-play."""
        bridge = get_bridge()
        # TODO: implement fight viewing in bridge
        flash("Fight viewing coming soon!", "info")
        return redirect(url_for('archives'))
    
    # =========================================================================
    # NEGOTIATION
    # =========================================================================

    @app.route('/challenge/<player_fighter_id>/<target_id>', methods=['POST'])
    def challenge_fighter(player_fighter_id, target_id):
        """Start a fight negotiation from the ladder / profile."""
        bridge = get_bridge()
        result = bridge.challenge_fighter(player_fighter_id, target_id)

        if result.get("success"):
            return redirect(url_for('negotiation', neg_id=result["neg_id"]))
        flash(result.get("error", "Could not initiate challenge"), "error")
        return redirect(url_for('division_ladder'))

    @app.route('/negotiate/<neg_id>', methods=['GET'])
    def negotiation(neg_id):
        """Show current negotiation state."""
        bridge = get_bridge()
        neg = bridge.get_negotiation(neg_id)

        if not neg:
            flash("Negotiation not found", "error")
            return redirect(url_for('fight_offers'))

        # If already resolved, redirect appropriately
        if neg["status"] == "COMPLETED" and neg.get("fight_id"):
            return redirect(url_for('fight_camp', fight_id=neg["fight_id"]))
        if neg["status"] == "BROKEN_DOWN":
            flash("Negotiations fell apart.", "warning")
            return redirect(url_for('fight_offers'))

        player_fighter = bridge.get_fighter(neg["player_fighter_id"])
        opponent       = bridge.get_fighter(neg["ai_fighter_id"])

        return render_template('negotiation.html',
            neg=neg,
            player_fighter=player_fighter,
            opponent=opponent,
            week=bridge.week_number,
        )

    @app.route('/negotiate/<neg_id>/respond', methods=['POST'])
    def negotiation_respond(neg_id):
        """Player responds to negotiation: ACCEPT / COUNTER / WALK."""
        bridge  = get_bridge()
        action  = request.form.get('action', 'WALK').upper()
        counter_purse_raw = request.form.get('counter_purse', '').strip()
        counter_purse = None
        if counter_purse_raw.isdigit():
            counter_purse = int(counter_purse_raw)

        result = bridge.respond_to_negotiation(neg_id, action, counter_purse)

        if not result.get("success"):
            flash(result.get("error", "Error processing response"), "error")
            return redirect(url_for('negotiation', neg_id=neg_id))

        outcome = result.get("outcome")

        if outcome == "ACCEPTED":
            flash("Fight booked! Time to build your camp.", "success")
            return redirect(url_for('fight_camp', fight_id=result["fight_id"]))
        elif outcome == "AI_ACCEPTED":
            neg = bridge.get_negotiation(neg_id)
            if neg and neg.get("fight_id"):
                flash("They accepted your terms. Fight booked!", "success")
                return redirect(url_for('fight_camp', fight_id=neg["fight_id"]))
            # AI accepted but we need player to formally confirm
            return redirect(url_for('negotiation', neg_id=neg_id))
        elif outcome == "WALKED":
            flash("You walked away from negotiations.", "info")
            return redirect(url_for('fight_offers'))
        elif outcome in ("BROKEN_DOWN", "AI_DECLINED"):
            flash(result.get("message", "Negotiations collapsed."), "warning")
            return redirect(url_for('fight_offers'))
        else:
            # AI countered — go back to negotiation screen
            return redirect(url_for('negotiation', neg_id=neg_id))

    # =========================================================================
    # FIGHT CAMP
    # =========================================================================

    @app.route('/fight-camp/<fight_id>', methods=['GET'])
    def fight_camp(fight_id):
        """Fight camp setup — gameplan, training focus, intensity, coach advice."""
        bridge = get_bridge()
        data   = bridge.get_fight_camp_data(fight_id)

        if not data:
            flash("Fight not found", "error")
            return redirect(url_for('dashboard'))

        # Gameplan options
        gameplan_options = [
            {
                "key":       "AGGRESSIVE",
                "name":      "Go Forward",
                "icon":      "⚡",
                "desc":      "Cut off the cage, force the fight, don't let them breathe.",
                "boosts":    "Striking offense +8, KO chance +10%",
                "sacrifices":"Striking defense -5, cardio drain +15%",
            },
            {
                "key":       "DEFENSIVE",
                "name":      "Counter Fighter",
                "icon":      "🛡️",
                "desc":      "Let them come. Make them pay for every mistake.",
                "boosts":    "Striking defense +8, KO counter chance +10%",
                "sacrifices":"Striking offense -5, grappling offense -3",
            },
            {
                "key":       "BALANCED",
                "name":      "Game Plan",
                "icon":      "⚖️",
                "desc":      "React to what the fight gives you. No bias.",
                "boosts":    "Slight all-round bonuses",
                "sacrifices":"No big edge either way",
            },
            {
                "key":       "MEASURED",
                "name":      "Patient",
                "icon":      "🎯",
                "desc":      "Pick your shots. Control output, control the fight.",
                "boosts":    "Striking defense +3, cardio efficiency +5%",
                "sacrifices":"Striking offense -2, aggression -5",
            },
        ]

        # Training focus options with display label
        focus_options = [
            ("boxing",           "Boxing",            "Punching technique and combos"),
            ("kicks",            "Kicking",           "Leg, body, and head kicks"),
            ("clinch_striking",  "Clinch",            "Knees, elbows, dirty boxing"),
            ("striking_defense", "Defense",           "Head movement, blocking, footwork"),
            ("takedowns",        "Wrestling",         "Takedowns and cage control"),
            ("takedown_defense", "TD Defense",        "Sprawl and takedown prevention"),
            ("top_control",      "Top Control",       "Holding position, GnP from top"),
            ("submissions",      "Submissions",       "Chokes and joint locks"),
            ("guard",            "Guard Work",        "Sweeps, guard retention, getups"),
            ("cardio",           "Cardio",            "Gas tank and stamina"),
            ("strength",         "Strength",          "Power and clinch strength"),
            ("fight_iq",         "IQ",                "Fight IQ and adjustments"),
        ]

        # Intensity options
        intensity_options = [
            ("REST",     "Rest",     "No gains",       "Recover -15 fatigue",        "green"),
            ("LIGHT",    "Light",    "50% gains",      "+2 fatigue, 0% injury",      "blue"),
            ("MODERATE", "Moderate", "100% gains",     "+5 fatigue, 1% injury",      "yellow"),
            ("INTENSE",  "Intense",  "150% gains",     "+10 fatigue, 3% injury",     "orange"),
            ("EXTREME",  "Extreme",  "200% gains",     "+18 fatigue, 8% injury risk","red"),
        ]

        return render_template('fight_camp.html',
            data=data,
            gameplan_options=gameplan_options,
            focus_options=focus_options,
            intensity_options=intensity_options,
            week=bridge.week_number,
        )

    @app.route('/fight-camp/<fight_id>/save', methods=['POST'])
    def save_fight_camp(fight_id):
        """Save fight camp choices and return to dashboard."""
        bridge       = get_bridge()
        gameplan     = request.form.get('gameplan',       'BALANCED')
        focus        = request.form.get('training_focus', 'boxing')
        intensity    = request.form.get('intensity',      'MODERATE')

        result = bridge.save_fight_camp(fight_id, gameplan, focus, intensity)

        if result.get("success"):
            flash("Fight camp set. Advance weeks to fight night.", "success")
        else:
            flash(result.get("error", "Error saving fight camp"), "error")

        return redirect(url_for('dashboard'))

    @app.route('/challenge/<challenger_id>/<opponent_id>', methods=['POST'])
    def challenge(challenger_id, opponent_id):
        """Initiate a challenge from the ladder — goes to negotiation flow."""
        bridge = get_bridge()
        result = bridge.initiate_challenge(challenger_id, opponent_id)
        if result.get('success'):
            neg_id = result.get('neg_id')
            return redirect(url_for('negotiation', neg_id=neg_id))
        flash(result.get('msg', 'Challenge failed'), 'error')
        return redirect(request.referrer or url_for('dashboard'))

    # =========================================================================
    # WATCHLIST
    # =========================================================================

    @app.route('/watchlist')
    def watchlist():
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('new_game'))
        entries          = bridge.get_watchlist()
        watch_categories = bridge._WATCH_CATEGORIES
        return render_template('watchlist.html',
            entries=entries,
            watch_categories=watch_categories,
            week=bridge.week_number,
        )

    @app.route('/watchlist/add/<fighter_id>', methods=['POST'])
    def watchlist_add(fighter_id):
        bridge   = get_bridge()
        category = request.form.get('category', 'SCOUT')
        priority = request.form.get('priority', 'NONE')
        result   = bridge.watchlist_add(fighter_id, category, priority)
        flash(result['msg'], 'success' if result['success'] else 'error')
        return redirect(request.referrer or url_for('watchlist'))

    @app.route('/watchlist/remove/<fighter_id>', methods=['POST'])
    def watchlist_remove(fighter_id):
        bridge = get_bridge()
        result = bridge.watchlist_remove(fighter_id)
        flash(result['msg'], 'success' if result['success'] else 'error')
        return redirect(request.referrer or url_for('watchlist'))

    @app.route('/watchlist/note/<fighter_id>', methods=['POST'])
    def watchlist_note(fighter_id):
        bridge = get_bridge()
        note   = request.form.get('note', '').strip()
        if note:
            bridge.watchlist_add_note(fighter_id, note)
            flash('Note added', 'success')
        return redirect(url_for('watchlist'))

    # =========================================================================
    # POST-FIGHT INTERVIEWS
    # =========================================================================

    @app.route('/interview/<fight_id>/<fighter_id>', methods=['GET', 'POST'])
    def interview(fight_id, fighter_id):
        bridge  = get_bridge()
        pending = bridge.get_pending_interviews()
        # Find the matching pending interview
        iv = next((p for p in pending
                   if p['fight_id'] == fight_id and p['fighter_id'] == fighter_id), None)
        if not iv:
            flash("No pending interview for this fighter.", "info")
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            choice     = request.form.get('choice', 'humble')
            call_out   = request.form.get('call_out_id')
            result     = bridge.process_interview(fight_id, fighter_id,
                                                   iv['role'], choice, call_out)
            if result.get('success'):
                quote = result.get('quote', '')
                flash(f"Interview done: {quote[:80]}{'...' if len(quote)>80 else ''}", 'success')
                if result.get('bonus'):
                    flash(f"💰 Sponsor bonus: ${result['bonus']:,}", 'success')
                if result.get('opponent_response'):
                    flash(f"🗣️ {result['opponent_response']}", 'info')
            else:
                flash("Interview error", 'error')
            return redirect(url_for('dashboard'))

        # GET — show interview form
        media_reactions = bridge.get_media_reactions(fight_id)
        return render_template('interview.html',
            iv=iv,
            fight_id=fight_id,
            media_reactions=media_reactions,
            week=bridge.week_number,
        )

    # =========================================================================
    # GAME ACTIONS
    # =========================================================================
    
    @app.route('/advance-week', methods=['POST'])
    def advance_week():
        """Advance the game by one week."""
        bridge = get_bridge()
        result = bridge.advance_week()
        
        if result.get('success'):
            flash(f"Advanced to Week {result.get('week', bridge.week_number)}", "success")
        else:
            flash("Error advancing week", "error")
        
        return redirect(url_for('dashboard'))
    
    # =========================================================================
    # API ENDPOINTS (for AJAX)
    # =========================================================================
    
    @app.route('/api/fighter/<fighter_id>')
    def api_fighter(fighter_id):
        """API endpoint for fighter data."""
        bridge = get_bridge()
        fighter = bridge.get_fighter(fighter_id)
        
        if not fighter:
            return jsonify({'error': 'Fighter not found'}), 404
        
        return jsonify({
            'id': fighter.fighter_id,
            'name': fighter.name,
            'nickname': fighter.nickname,
            'record': fighter.record_str,
            'rating': fighter.overall_rating,
            'division': fighter.weight_class,
            'style': fighter.fighting_style,
            'is_champion': fighter.is_champion,
            'ranking': fighter.ranking,
        })
    
    @app.route('/api/rankings/<division>')
    def api_rankings(division):
        """API endpoint for division rankings."""
        bridge = get_bridge()
        rankings = bridge.get_division_rankings(division)
        
        return jsonify([{
            'id': f.fighter_id,
            'name': f.name,
            'record': f.record_str,
            'rating': f.overall_rating,
            'is_champion': f.is_champion,
            'ranking': f.ranking,
        } for f in rankings[:20]])
