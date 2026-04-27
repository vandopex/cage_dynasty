"""
Cage Dynasty - Flask Routes (Views/Controllers)
All route handlers for the web application.
"""

from flask import render_template, redirect, url_for, request, jsonify, flash, session
from functools import wraps
import uuid
import sys
import traceback


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
    
    def _ceiling_to_display_grade(ceiling: int) -> str:
        """Local alias — must match ceiling_to_display_grade in game_bridge.py."""
        if ceiling >= 94: return "A+"
        if ceiling >= 88: return "A"
        if ceiling >= 83: return "A-"
        if ceiling >= 78: return "B+"
        if ceiling >= 73: return "B"
        if ceiling >= 65: return "B-"
        if ceiling >= 58: return "C+"
        if ceiling >= 50: return "C"
        if ceiling >= 42: return "C-"
        return "D"

    @app.route('/setup/camp', methods=['GET', 'POST'])
    def setup_camp():
        """Step 1: Create your camp."""
        if request.method == 'POST':
            # Save camp info to session
            session['camp_name'] = request.form.get('camp_name', 'My Gym')
            session['camp_location'] = request.form.get('camp_location', 'Las Vegas, NV')
            session['camp_tier'] = request.form.get('camp_tier', 'GARAGE')
            return redirect(url_for('setup_fighter'))
        
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
        """Step 3: Hire your head coach."""
        if 'camp_name' not in session or 'selected_fighter' not in session:
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
            return redirect(url_for('start_game'))
        
        return render_template('setup_coach.html', 
            coaches=coaches,
            camp_name=session.get('camp_name'),
            camp_tier=session.get('camp_tier', 'GARAGE')
        )
    
    @app.route('/setup/fighter', methods=['GET', 'POST'])
    def setup_fighter():
        """Step 2: Sign your first fighter."""
        if 'camp_name' not in session:
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
            return redirect(url_for('setup_coach'))
        
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
            _SPEC_LABEL = {
                "striking": ("Striking Coach", "🥊"),
                "boxing": ("Striking Coach", "🥊"),
                "kickboxing": ("Striking Coach", "🥊"),
                "muay thai": ("Striking Coach", "🥊"),
                "wrestling": ("Grappling Coach", "🤼"),
                "grappling": ("Grappling Coach", "🤼"),
                "bjj": ("Grappling Coach", "🤼"),
                "submissions": ("Grappling Coach", "🤼"),
                "conditioning": ("Strength & Conditioning Coach", "💪"),
                "strength": ("Strength & Conditioning Coach", "💪"),
                "cardio": ("Strength & Conditioning Coach", "💪"),
                "s&c": ("Strength & Conditioning Coach", "💪"),
                "mma": ("Head Coach", "🧠"),
                "cornering": ("Head Coach", "🧠"),
                "strategy": ("Head Coach", "🧠"),
            }
            result = []
            for c in coaches:
                spec = getattr(c, "specialty", "mma").lower()
                label, icon = _SPEC_LABEL.get(spec, ("Head Coach", "🧠"))
                result.append({
                    "id":          c.coach_id,
                    "name":        c.name,
                    "specialty":   spec,
                    "label":       label,
                    "icon":        icon,
                    "rating":      c.skill_level,
                    "salary":      c.weekly_salary,
                    "description": f"{c.personality_desc}. {c.get_bonus_description()}"
                })
            return result
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
        
        # Four archetypes — always show one of each plus 2 alternates
        ARCHETYPES = [
            {
                "specialty": "Striking",
                "label":     "Striking Coach",
                "icon":      "🥊",
                "desc":      "Develops boxing, kicks, clinch striking and defensive footwork.",
                "focus":     ["Boxing", "Kicks", "Clinch", "Defense"],
            },
            {
                "specialty": "Grappling",
                "label":     "Grappling Coach",
                "icon":      "🤼",
                "desc":      "Builds wrestling takedowns, takedown defense, BJJ and submission game.",
                "focus":     ["Takedowns", "TD Defense", "Submissions", "Guard"],
            },
            {
                "specialty": "S&C",
                "label":     "Strength & Conditioning Coach",
                "icon":      "💪",
                "desc":      "Improves strength, cardio, chin and recovery. Builds physical durability.",
                "focus":     ["Strength", "Cardio", "Chin", "Recovery"],
            },
            {
                "specialty": "MMA",
                "label":     "Head Coach",
                "icon":      "🧠",
                "desc":      "Shapes overall game plan and mental game — fight IQ, composure and heart.",
                "focus":     ["Fight IQ", "Composure", "Heart"],
            },
        ]

        first_names = ["Mike", "John", "Carlos", "Greg", "Dave", "Tony",
                       "Rafael", "Alex", "Firas", "Mark", "Jackson", "Duke"]
        last_names  = ["Johnson", "Martinez", "Smith", "Williams", "Garcia",
                       "Brown", "Davis", "Miller", "Zahabi", "DellaGrotte"]

        coaches = []
        used_archetypes = set()

        # Always include one of each archetype
        for i, arch in enumerate(ARCHETYPES):
            rating = random.randint(min_r, max_r)
            name   = f"{random.choice(first_names)} {random.choice(last_names)}"
            if rating >= 80:
                salary = 2000 + (rating - 80) * 150
            elif rating >= 70:
                salary = 1200 + (rating - 70) * 80
            else:
                salary = 600  + (rating - 50) * 30
            coaches.append({
                "id":          f"coach_{i}",
                "name":        name,
                "specialty":   arch["specialty"],
                "label":       arch["label"],
                "icon":        arch["icon"],
                "rating":      rating,
                "salary":      salary,
                "description": arch["desc"],
                "focus":       arch["focus"],
            })
            used_archetypes.add(arch["specialty"])

        # Two additional alternates (random archetype, different names)
        for i in range(2):
            arch   = random.choice(ARCHETYPES)
            rating = random.randint(min_r, max_r)
            name   = f"{random.choice(first_names)} {random.choice(last_names)}"
            if rating >= 80:
                salary = 2000 + (rating - 80) * 150
            elif rating >= 70:
                salary = 1200 + (rating - 70) * 80
            else:
                salary = 600  + (rating - 50) * 30
            coaches.append({
                "id":          f"coach_alt_{i}",
                "name":        name,
                "specialty":   arch["specialty"],
                "label":       arch["label"],
                "icon":        arch["icon"],
                "rating":      rating,
                "salary":      salary,
                "description": arch["desc"],
                "focus":       arch["focus"],
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
                    "display_grade": _ceiling_to_display_grade(p.potential_ceiling),
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
                "display_grade": _ceiling_to_display_grade(potential),
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

        if not bridge.game_started:
            return redirect(url_for('new_game'))

        camp      = bridge.get_player_camp()
        fighters  = bridge.get_player_fighters()
        finances  = bridge.get_camp_finances()
        news      = bridge.get_news_feed(limit=8)
        offers    = bridge.get_fight_offers()

        fighter_ids = [f.fighter_id for f in fighters]
        offer_count = len([o for o in offers if o.fighter_id in fighter_ids])

        # Scheduled fights + weeks_until
        scheduled_fights = bridge.get_scheduled_fights()
        for fight in scheduled_fights:
            fight['weeks_until'] = fight['week'] - bridge.week_number
            for f in fighters:
                if fight.get('fighter1_id') == f.fighter_id or \
                   fight.get('fighter2_id') == f.fighter_id:
                    fight['fighter'] = f
                    break

        # Training plans per fighter
        training_plans = {}
        for f in fighters:
            plan = bridge.get_training_plan(f.fighter_id)
            training_plans[f.fighter_id] = {
                'intensity': plan.get('intensity', 'MODERATE'),
                'focus':     plan.get('focus', 'balanced'),
            }

        # Upcoming card that has a player fight
        upcoming_events = bridge.get_upcoming_events(limit=8)
        player_card = None
        for ev in upcoming_events:
            for fight in ev.get('fights', []):
                if fight.get('fighter1_id') in fighter_ids or \
                   fight.get('fighter2_id') in fighter_ids:
                    player_card = ev
                    break
            if player_card:
                break

        # Enrich player_card fights with rank data for display
        if player_card:
            div_rank_cache = {}
            for fight in player_card.get('fights', []):
                wc = fight.get('weight_class', '')
                if wc and wc not in div_rank_cache:
                    div_rank_cache[wc] = {
                        f.fighter_id: f.ranking
                        for f in bridge.get_division_rankings(wc)
                        if f.ranking
                    }
                ranks = div_rank_cache.get(wc, {})
                fight['fighter1_rank'] = ranks.get(fight.get('fighter1_id'))
                fight['fighter2_rank'] = ranks.get(fight.get('fighter2_id'))

        # Financial runway
        balance  = finances.get('balance', 0)
        overhead = finances.get('camp_overhead', 1)
        runway   = int(balance / overhead) if overhead > 0 else 999

        # Pending interviews
        pending_interviews = bridge.get_pending_interviews()

        # Fresh scout tips (scouting news from last 3 weeks)
        scout_tips = [n for n in news
                      if n.category == 'scouting'
                      and bridge.week_number - n.week <= 3]

        # Coach's Corner digest
        try:
            digest = bridge.get_weekly_digest()
        except Exception as exc:
            print(f"⚠️ [DASHBOARD] get_weekly_digest failed: {exc!r}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            digest = {}

        return render_template('dashboard.html',
            camp=camp,
            fighters=fighters,
            news=news,
            week=bridge.week_number,
            offer_count=offer_count,
            scheduled_fights=scheduled_fights,
            finances=finances,
            pending_interviews=pending_interviews,
            training_plans=training_plans,
            player_card=player_card,
            balance=balance,
            overhead=overhead,
            runway=runway,
            scout_tips=scout_tips,
            digest=digest,
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
        
        # Build scheduled_map: fighter_id -> fight dict
        scheduled = bridge.get_scheduled_fights()
        scheduled_map = {}
        for sf in scheduled:
            for fid in [sf.get('fighter1_id'), sf.get('fighter2_id')]:
                if fid:
                    scheduled_map[fid] = sf

        # Training plans
        training_plans = {}
        for f in fighters:
            plan = bridge.get_training_plan(f.fighter_id)
            training_plans[f.fighter_id] = plan

        return render_template('roster.html',
            camp=camp,
            fighters=fighters,
            sort_by=sort_by,
            scheduled_map=scheduled_map,
            training_plans=training_plans,
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

        # Contract status — only for player fighters
        player_ids = {f.fighter_id for f in bridge.get_player_fighters()}
        contract_status  = bridge.get_contract_status(fighter_id) if fighter_id in player_ids else None
        contract_options = bridge.get_contract_options_for_tier() if fighter_id in player_ids else []

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
            contract_status=contract_status,
            contract_options=contract_options,
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
            # Striking
            ('boxing',           'Boxing',       'Hands, combinations'),
            ('kicks',            'Kicks',         'Leg & body kicks'),
            ('clinch_striking',  'Clinch',        'Dirty boxing, elbows'),
            ('striking_defense', 'Strike Def',    'Head movement, blocks'),
            ('muay_thai',        'Muay Thai',     'Kicks + clinch together'),
            # Grappling
            ('wrestling',        'Wrestling',     'Takedowns & defense'),
            ('top_control',      'Top Control',   'Ground control, GnP'),
            ('bjj',              'BJJ',           'Submissions & guard'),
            ('takedown_defense', 'TD Defense',    'Sprawls, stuffing shots'),
            # Physical & Mental
            ('cardio',           'Cardio',        'Stamina & recovery'),
            ('strength',         'Strength',      'Power & clinch'),
            ('fight_iq',         'Fight IQ',      'Game plan & composure'),
            # Balanced
            ('sparring',         'Sparring',      'Balanced all-around'),
        ]
        
        # Intensity options
        intensity_options = [
            ('rest', 'Rest', '-15 fatigue, no gains'),
            ('light', 'Light', '+2 fatigue, 50% gains'),
            ('moderate', 'Moderate', '+5 fatigue, 100% gains'),
            ('intense', 'Intense', '+10 fatigue, 150% gains'),
            ('extreme', 'Extreme', '+18 fatigue, 200% gains, injury risk'),
        ]
        
        # Coach data
        coach = bridge._coach if hasattr(bridge, '_coach') else {}

        # Training plans per fighter
        training_plans = {}
        for f in fighters:
            plan = bridge.get_training_plan(f.fighter_id)
            training_plans[f.fighter_id] = plan

        return render_template('training.html',
            fighters=fighters,
            camp=camp,
            coach=coach,
            training_plans=training_plans,
            focus_options=focus_options,
            intensity_options=intensity_options,
            week=bridge.week_number,
        )
    
    @app.route('/training/set', methods=['POST'])
    def set_training():
        """Store a fighter's weekly training plan — applied automatically each advance_week."""
        bridge     = get_bridge()
        fighter_id = request.form.get('fighter_id')
        focus      = request.form.get('focus', 'sparring')
        intensity  = request.form.get('intensity', 'MODERATE')

        fighter = bridge.get_fighter(fighter_id)
        if fighter:
            result = bridge.set_training_plan(fighter_id, focus, intensity)
            if result.get("success"):
                focus_label = focus.replace('_', ' ').title()
                flash(f"{fighter.name}: {focus_label} · {intensity.title()} — plan saved. Takes effect next week.", "success")
            else:
                flash(result.get("message", "Training plan updated."), "success")
        else:
            flash("Fighter not found.", "error")

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
        ranked     = [f for f in rankings if f.ranking and f.ranking > 5]
        unranked   = bridge.get_division_unranked(division, limit=15)
        
        # Check if player has fighter in this division
        player_in_division = any(f.weight_class == division for f in player_fighters)
        player_fighter = next((f for f in player_fighters if f.weight_class == division), None)
        
        # Build scheduled fight map — {fighter_id: {opponent_name, event, week}}
        scheduled_map = {}
        current_week  = bridge.week_number
        # Player scheduled fights
        for sf in bridge.get_scheduled_fights():
            f1id = sf.get('fighter1_id','')
            f2id = sf.get('fighter2_id','')
            f1n  = sf.get('fighter1_name','?')
            f2n  = sf.get('fighter2_name','?')
            wk   = sf.get('week', 0)
            ev   = sf.get('event_name','')
            if f1id:
                scheduled_map[f1id] = {'opponent': f2n, 'event': ev, 'week': wk}
            if f2id:
                scheduled_map[f2id] = {'opponent': f1n, 'event': ev, 'week': wk}
        # AI upcoming card fights
        if hasattr(bridge, '_upcoming_cards'):
            for wk, card in bridge._upcoming_cards.items():
                for fight in card.get('fights', []):
                    f1id = fight.get('fighter1_id','')
                    f2id = fight.get('fighter2_id','')
                    f1n  = fight.get('fighter1_name','?')
                    f2n  = fight.get('fighter2_name','?')
                    ev   = fight.get('event_name','')
                    if f1id and f1id not in scheduled_map:
                        scheduled_map[f1id] = {'opponent': f2n, 'event': ev, 'week': wk}
                    if f2id and f2id not in scheduled_map:
                        scheduled_map[f2id] = {'opponent': f1n, 'event': ev, 'week': wk}

        cooldowns = bridge._fighter_cooldowns if hasattr(bridge, '_fighter_cooldowns') else {}

        # Player fighter availability
        player_available = True
        player_status    = None
        if player_fighter:
            pfid = player_fighter.fighter_id
            if pfid in scheduled_map:
                player_available = False
                s = scheduled_map[pfid]
                player_status = f"Scheduled vs {s['opponent']} · Wk {s['week']}"
            elif cooldowns.get(pfid, 0) > current_week:
                player_available = False
                avail_wk = cooldowns[pfid]
                player_status = f"On cooldown · Available Wk {avail_wk}"

        return render_template('ladder.html',
            divisions=divisions,
            current_division=division,
            champion=champion,
            contenders=contenders,
            ranked=ranked,
            unranked=unranked,
            player_fighter=player_fighter,
            player_in_division=player_in_division,
            player_available=player_available,
            player_status=player_status,
            cooldowns=cooldowns,
            scheduled_map=scheduled_map,
            week=current_week,
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
        fighters = [f for f in fighters if f]
        fighters.sort(key=lambda f: (not f.is_champion, -(f.ranking or 100), -f.overall_rating))

        # Stats
        champions = [f for f in fighters if f.is_champion]
        ranked    = [f for f in fighters if f.ranking and f.ranking <= 15]

        # Camp personality archetype
        arch_name = bridge._get_camp_archetype(camp_id) if hasattr(bridge, '_get_camp_archetype') else "Numbers Game"
        from game_bridge import CAMP_ARCHETYPES
        arch_data = CAMP_ARCHETYPES.get(arch_name, {})

        return render_template('camp_detail.html',
            camp=camp,
            fighters=fighters,
            champions=champions,
            ranked=ranked,
            arch_name=arch_name,
            arch_emoji=arch_data.get("emoji", "🏟️"),
            arch_desc=arch_data.get("desc", ""),
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

        # Get real belt history from bridge
        history_data = bridge.get_champions_history(division) if hasattr(bridge, 'get_champions_history') else {}
        reigns        = history_data.get("reigns", [])
        total_changes = history_data.get("total_changes", 0)
        most_defenses = history_data.get("most_defenses", 0)

        return render_template('champions.html',
            divisions=divisions,
            current_division=division,
            champion=champion,
            reigns=reigns,
            total_changes=total_changes,
            most_defenses=most_defenses,
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

        # Build rankings as plain dicts so templates can use .get()
        rankings = {}
        if bridge.game_started and bridge._game_state:
            WEIGHT_CLASSES = getattr(bridge._game_state, 'WEIGHT_CLASSES',
                ["Strawweight","Flyweight","Bantamweight","Featherweight",
                 "Lightweight","Welterweight","Middleweight","Light Heavyweight","Heavyweight"])
            for wc in WEIGHT_CLASSES:
                try:
                    for f in bridge.get_division_rankings(wc):
                        rankings[f.fighter_id] = {
                            'name': f.name,
                            'ranking': f.ranking,
                            'is_champion': f.is_champion,
                            'record_str': f.record_str,
                            'overall_rating': f.overall_rating,
                            'weight_class': f.weight_class,
                            'fighting_style': f.fighting_style,
                        }
                    for f in bridge.get_division_unranked(wc, limit=20):
                        rankings[f.fighter_id] = {
                            'name': f.name,
                            'ranking': None,
                            'is_champion': False,
                            'record_str': f.record_str,
                            'overall_rating': f.overall_rating,
                            'weight_class': f.weight_class,
                            'fighting_style': f.fighting_style,
                        }
                except Exception:
                    pass

        return render_template('events.html',
            events=events,
            rankings=rankings,
            week=bridge.week_number,
        )
    
    @app.route('/archives')
    def archives():
        """Past events archive view."""
        bridge = get_bridge()
        events = bridge.get_completed_events()
        
        # Sort by week descending
        events = sorted(events, key=lambda e: e.get('week', 0), reverse=True)
        
        rankings = {}
        if bridge.game_started and bridge._game_state:
            WC2 = getattr(bridge._game_state, 'WEIGHT_CLASSES',
                ["Strawweight","Flyweight","Bantamweight","Featherweight",
                 "Lightweight","Welterweight","Middleweight","Light Heavyweight","Heavyweight"])
            for wc in WC2:
                try:
                    for f in bridge.get_division_rankings(wc):
                        rankings[f.fighter_id] = {
                            'name': f.name, 'ranking': f.ranking,
                            'is_champion': f.is_champion, 'record_str': f.record_str,
                            'overall_rating': f.overall_rating, 'weight_class': f.weight_class,
                            'fighting_style': getattr(f, 'fighting_style', ''),
                        }
                except Exception:
                    pass

        return render_template('archives.html',
            events=events[:20],
            rankings=rankings,
            week=bridge.week_number,
        )
    
    @app.route('/event/<event_id>')
    def event_detail(event_id):
        """Event detail view with fight results."""
        bridge = get_bridge()
        events = bridge.get_completed_events()
        event  = next((e for e in events if e.get('event_id') == event_id), None)

        if not event:
            flash("Event not found", "error")
            return redirect(url_for('archives'))

        # Rankings as plain dicts for template
        rankings = {}
        player_ids = set()
        if bridge.game_started and bridge._game_state:
            WC = getattr(bridge._game_state, 'WEIGHT_CLASSES',
                ["Strawweight","Flyweight","Bantamweight","Featherweight",
                 "Lightweight","Welterweight","Middleweight","Light Heavyweight","Heavyweight"])
            for wc in WC:
                try:
                    for f in bridge.get_division_rankings(wc):
                        rankings[f.fighter_id] = {
                            'name': f.name, 'ranking': f.ranking,
                            'is_champion': f.is_champion, 'record_str': f.record_str,
                            'overall_rating': f.overall_rating,
                        }
                except Exception:
                    pass
            player_ids = {f.fighter_id for f in bridge.get_player_fighters()}

        return render_template('event_detail.html',
            event=event,
            rankings=rankings,
            player_ids=player_ids,
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
            neg_id = result.get("neg_id")
            if not neg_id:
                flash("Something went wrong with that challenge. Try again.", "error")
                return redirect(url_for('division_ladder'))
            return redirect(url_for('negotiation', neg_id=neg_id))
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

        status            = neg.get("status")
        player_fighter_id = neg.get("player_fighter_id")
        ai_fighter_id     = neg.get("ai_fighter_id")

        if not status or not player_fighter_id or not ai_fighter_id:
            flash("We couldn't find the details for that negotiation.", "error")
            return redirect(url_for('fight_offers'))

        # If already resolved, redirect appropriately
        if status == "COMPLETED" and neg.get("fight_id"):
            return redirect(url_for('fight_camp', fight_id=neg["fight_id"]))
        if status == "BROKEN_DOWN":
            flash("Negotiations fell apart.", "warning")
            return redirect(url_for('fight_offers'))

        player_fighter = bridge.get_fighter(player_fighter_id)
        opponent       = bridge.get_fighter(ai_fighter_id)

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
            fight_id = result.get("fight_id")
            if not fight_id:
                flash("Something went wrong booking that fight. Check your offers.", "error")
                return redirect(url_for('fight_offers'))
            flash("Fight booked! Time to build your camp.", "success")
            return redirect(url_for('fight_camp', fight_id=fight_id))
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

        cs = data.get('coach_suggestion', {})
        rec_gameplan  = cs.get('gameplan',   'BALANCED')
        rec_focus     = cs.get('focus',      'boxing')
        rec_intensity = cs.get('intensity',  'MODERATE')

        # All 8 gameplans the engine supports
        gameplan_options = [
            {
                "key":       "AGGRESSIVE",
                "name":      "Go Forward",
                "icon":      "⚡",
                "style":     "Pressure",
                "desc":      "Cut off the cage, force the fight, don't let them breathe.",
                "boosts":    "Striking offense +8, KO chance +10%",
                "sacrifices":"Striking defense -5, cardio drain +15%",
                "best_for":  "Muay Thai, Pressure Fighter, Brawler",
            },
            {
                "key":       "DEFENSIVE",
                "name":      "Counter & Punish",
                "icon":      "🛡️",
                "style":     "Counter",
                "desc":      "Let them come. Make them pay for every mistake.",
                "boosts":    "Striking defense +8, counter KO chance +10%",
                "sacrifices":"Striking offense -5, grappling offense -3",
                "best_for":  "Counter Striker, Point Fighter, Sprawl & Brawl",
            },
            {
                "key":       "BALANCED",
                "name":      "Pace & Control",
                "icon":      "⚖️",
                "style":     "Balanced",
                "desc":      "React to what the fight gives you. Stay efficient.",
                "boosts":    "Slight all-round bonuses, cardio efficiency",
                "sacrifices":"No big edge either way",
                "best_for":  "Any style",
            },
            {
                "key":       "MEASURED",
                "name":      "Patient & Sharp",
                "icon":      "🎯",
                "style":     "Patient",
                "desc":      "Pick your shots. Control output, win the rounds.",
                "boosts":    "Striking defense +3, cardio efficiency +5%",
                "sacrifices":"Striking offense -2, low finish rate",
                "best_for":  "Point Fighter, Boxer, Counter Striker",
            },
            {
                "key":       "TAKEDOWN",
                "name":      "Wrestle Up",
                "icon":      "🤼",
                "style":     "Wrestling",
                "desc":      "Take them down and control the fight on the mat.",
                "boosts":    "Takedown offense +10, control time +20%",
                "sacrifices":"Standing striking reduced, energy intensive",
                "best_for":  "Wrestler, Sambo, Ground & Pound",
            },
            {
                "key":       "GNP",
                "name":      "Ground & Pound",
                "icon":      "👊",
                "style":     "GnP",
                "desc":      "Get them down and finish with ground strikes.",
                "boosts":    "GnP damage +15%, TKO chance highest ceiling",
                "sacrifices":"Sub defense reduced while attacking",
                "best_for":  "Wrestler, Sambo, Pressure Fighter",
            },
            {
                "key":       "SUBMISSION",
                "name":      "Hunt the Finish",
                "icon":      "🥋",
                "style":     "Submission",
                "desc":      "Drag it to the mat and hunt for the tap.",
                "boosts":    "Sub attempt rate +20%, position aggression +10%",
                "sacrifices":"Position risk — can be reversed if sub fails",
                "best_for":  "BJJ Specialist, Judo, Sambo",
            },
            {
                "key":       "CLINCH",
                "name":      "Clinch War",
                "icon":      "💪",
                "style":     "Clinch",
                "desc":      "Smother them in the clinch. Knees, elbows, dirty boxing.",
                "boosts":    "Clinch striking +12%, takedown setups from clinch",
                "sacrifices":"Distance striking reduced, referee standup risk",
                "best_for":  "Muay Thai, Clinch Fighter, Wrestler",
            },
        ]

        # Grouped focus options (3 groups, 4 each = 12 total but scannable)
        focus_groups = [
            {
                "label": "⚔️ Striking",
                "color": "var(--blood-red)",
                "options": [
                    ("boxing",           "Boxing",    "🥊", "Punching technique, combos, distance"),
                    ("kicks",            "Kicking",   "🦵", "Leg, body, and head kicks"),
                    ("clinch_striking",  "Clinch",    "👊", "Knees, elbows, dirty boxing"),
                    ("striking_defense", "Defense",   "🛡", "Head movement, blocking, footwork"),
                ],
            },
            {
                "label": "🥋 Grappling",
                "color": "var(--info)",
                "options": [
                    ("takedowns",        "Wrestling",    "🤼", "Takedowns and cage control"),
                    ("takedown_defense", "TD Defense",   "🦅", "Sprawl and takedown prevention"),
                    ("submissions",      "Submissions",  "🔒", "Chokes and joint locks"),
                    ("guard",            "Guard Work",   "🛡", "Sweeps, guard retention, getups"),
                ],
            },
            {
                "label": "💪 Physical",
                "color": "var(--neon-green)",
                "options": [
                    ("cardio",   "Cardio",   "❤️", "Gas tank and stamina"),
                    ("strength", "Strength", "⚡", "Power and clinch strength"),
                    ("fight_iq", "Fight IQ", "🧠", "Adjustments and ring generalship"),
                    ("top_control", "Top Control", "⬇️", "GnP position and pressure"),
                ],
            },
        ]

        # Fight camp intensity — NO REST (that's for off-weeks, not fight prep)
        intensity_options = [
            ("LIGHT",    "Light",    "50% gains",  "+2 fatigue, no injury risk",   "blue"),
            ("MODERATE", "Moderate", "100% gains", "+5 fatigue, 1% injury risk",   "yellow"),
            ("INTENSE",  "Intense",  "150% gains", "+10 fatigue, 3% injury risk",  "orange"),
            ("EXTREME",  "Extreme",  "200% gains", "+18 fatigue, 8% injury risk",  "red"),
        ]

        # Fighter current condition
        player_fighter = data.get('player')
        fatigue = getattr(player_fighter, 'fatigue', 0) if player_fighter else 0
        condition_pct = 100 - fatigue

        return render_template('fight_camp.html',
            data=data,
            gameplan_options=gameplan_options,
            focus_groups=focus_groups,
            intensity_options=intensity_options,
            rec_gameplan=rec_gameplan,
            rec_focus=rec_focus,
            rec_intensity=rec_intensity,
            condition_pct=condition_pct,
            fatigue=fatigue,
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
    # PROSPECTS & AMATEUR CIRCUIT
    # =========================================================================

    @app.route('/prospects')
    def prospects():
        """Scouting / prospect pipeline page."""
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('new_game'))
        try:
            scouting = bridge.get_scouting_data()
        except Exception:
            scouting = {}
        fighters  = bridge.get_player_fighters()
        watchlist = bridge.get_watchlist()
        return render_template('prospects.html',
            week=bridge.week_number,
            scouting=scouting,
            fighters=fighters,
            watchlist=watchlist,
        )

    @app.route('/amateur-circuit')
    def amateur_circuit():
        """Amateur circuit overview — rankings, tournaments, eligible prospects."""
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('new_game'))
        try:
            data = bridge.get_amateur_data()
        except Exception:
            data = {"available": False}
        return render_template('amateur.html',
            week=bridge.week_number,
            amateur=data,
        )

    @app.route('/amateur/sign/<amateur_id>', methods=['POST'])
    def sign_amateur(amateur_id):
        """Sign an amateur fighter to the player's camp."""
        bridge = get_bridge()
        result = bridge.sign_amateur(amateur_id)
        if result.get('success'):
            from flask import flash
            flash(result.get('message', 'Fighter signed!'), 'success')
        else:
            from flask import flash
            flash(result.get('error', 'Could not sign fighter.'), 'error')
        return redirect(url_for('amateur_circuit'))

    @app.route('/fighter/<fighter_id>/resign', methods=['POST'])
    def resign_fighter(fighter_id):
        """Re-sign a player fighter to a new contract."""
        bridge = get_bridge()
        contract_fights = int(request.form.get('contract_fights', 3))
        result = bridge.resign_fighter(fighter_id, contract_fights)
        if result.get('success'):
            from flask import flash
            flash(result['message'], 'success')
        else:
            from flask import flash
            flash(result.get('error', 'Could not re-sign.'), 'error')
        return redirect(url_for('fighter_profile', fighter_id=fighter_id))

    # =========================================================================
    # RECORD BOOK, COMPARE, FACILITY, SAVES
    # =========================================================================

    @app.route('/record-book')
    def record_book():
        """DFC record book — all-time stats and records."""
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('new_game'))
        try:
            records = bridge.get_record_book() if hasattr(bridge, 'get_record_book') else {}
        except Exception:
            records = {}
        return render_template('record_book.html',
            week=bridge.week_number,
            records=records,
        )

    @app.route('/compare')
    def compare_fighters():
        """Compare two fighters side-by-side."""
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('new_game'))
        fighters = []
        if bridge._game_state:
            WEIGHT_CLASSES = getattr(bridge._game_state, 'WEIGHT_CLASSES',
                ["Strawweight","Flyweight","Bantamweight","Featherweight",
                 "Lightweight","Welterweight","Middleweight","Light Heavyweight","Heavyweight"])
            for wc in WEIGHT_CLASSES:
                try:
                    fighters.extend(bridge.get_division_rankings(wc))
                    fighters.extend(bridge.get_division_unranked(wc, limit=10))
                except Exception:
                    pass
        f1_id = request.args.get('f1')
        f2_id = request.args.get('f2')
        f1 = next((f for f in fighters if f.fighter_id == f1_id), None) if f1_id else None
        f2 = next((f for f in fighters if f.fighter_id == f2_id), None) if f2_id else None
        return render_template('compare.html',
            week=bridge.week_number,
            fighters=fighters,
            f1=f1, f2=f2,
        )

    @app.route('/facility/upgrade', methods=['POST'])
    def facility_upgrade():
        """Execute facility upgrade."""
        bridge = get_bridge()
        result = bridge.upgrade_facility()
        if result.get('success'):
            flash(result.get('message', 'Facility upgraded!'), 'success')
        else:
            flash(result.get('error', 'Upgrade failed.'), 'error')
        return redirect(url_for('facility'))

    @app.route('/facility')
    def facility():
        """Camp facility upgrades."""
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('new_game'))
        try:
            fdata = bridge.get_facility_data() if hasattr(bridge, 'get_facility_data') else {}
        except Exception:
            fdata = {}
        return render_template('facility.html',
            week=bridge.week_number,
            facility=fdata,
        )

    @app.route('/saves')
    def saves_menu():
        """Save / load game."""
        bridge = get_bridge()
        saves = bridge.get_web_saves()
        return render_template('saves.html',
            week=bridge.week_number if bridge.game_started else 0,
            saves=saves,
        )

    @app.route('/saves/save/<slot>', methods=['POST'])
    def save_game_slot(slot):
        bridge = get_bridge()
        result = bridge.web_save(slot)
        if result.get('success'):
            flash(f"Game saved to {slot.replace('slot','Slot ')}.", 'success')
        else:
            flash(f"Save failed: {result.get('error','unknown error')}", 'error')
        return redirect(url_for('saves_menu'))

    @app.route('/saves/load/<slot>', methods=['POST'])
    def load_game_slot(slot):
        bridge = get_bridge()
        result = bridge.web_load(slot)
        if result.get('success'):
            meta = result.get('meta', {})
            flash(f"Loaded {meta.get('camp_name','game')} — Week {meta.get('week','?')}", 'success')
            return redirect(url_for('dashboard'))
        flash(f"Load failed: {result.get('error','unknown error')}", 'error')
        return redirect(url_for('saves_menu'))

    # =========================================================================
    # GAME ACTIONS
    # =========================================================================
    
    @app.route('/advance-week', methods=['POST'])
    def advance_week():
        """Advance the game by one week — redirect to recap screen."""
        bridge = get_bridge()
        result = bridge.advance_week()

        if not result.get('success'):
            err = result.get('error', 'Unknown error')
            flash(f"Error advancing week: {err}", "error")
            return redirect(url_for('dashboard'))

        week    = result.get('week', bridge.week_number)
        fights  = result.get('fights_completed', [])
        training_report = result.get('training_report', {})

        # Autosave handled inside bridge.advance_week() via autosave_if_due()

        # Identify player fights — check multiple sources to avoid misses
        player_fighters = bridge.get_player_fighters()
        player_ids      = {f.fighter_id for f in player_fighters}
        # Also collect fighter_ids stored in _fighter_data (bridge-level registry)
        player_fight_ids = {f.get('fight_id', '') for f in bridge._scheduled_fights} \
                           if hasattr(bridge, '_scheduled_fights') else set()

        player_fights = [f for f in fights if
                         f.get('is_player_fight') or
                         f.get('winner_id') in player_ids or
                         f.get('loser_id')  in player_ids]
        ai_fights     = [f for f in fights if f not in player_fights]

        # Get last completed event for AI card results
        completed = bridge.get_completed_events()
        ai_event  = next((e for e in reversed(completed) if e.get('is_ai_event')), None)

        # Finances summary for the week
        finances  = bridge.get_camp_finances()

        # Collect media reactions for player fights
        media_reactions = {}
        for fight in player_fights:
            fid = fight.get('fight_id', '')
            if fid:
                media_reactions[fid] = bridge.get_media_reactions(fid)

        # Rankings snapshot for player fighters after fights
        player_rankings = {}
        for f in bridge.get_player_fighters():
            div_rankings  = bridge.get_division_rankings(f.weight_class)
            total_ranked  = len([r for r in div_rankings if r.ranking])
            player_rankings[f.fighter_id] = {
                'name':         f.name,
                'ranking':      f.ranking,
                'record':       f.record_str,
                'weight_class': f.weight_class,
                'overall':      f.overall_rating,
                'total_ranked': total_ranked,
            }

        # Closest upcoming player fight
        scheduled      = bridge.get_scheduled_fights()
        upcoming_fight = None
        for sf in sorted(scheduled, key=lambda x: x.get('weeks_until', 99)):
            if (sf.get('fighter1_id') in player_ids or
                    sf.get('fighter2_id') in player_ids):
                sf['weeks_until'] = max(0, sf.get('week', 0) - bridge.week_number)
                upcoming_fight = sf
                break

        bridge.store_week_recap({
            'week':             week,
            'player_fights':    player_fights,
            'training_report':  training_report,
            'ai_fights':       [{
                'fight_id':      f.get('fight_id',''),
                'fighter1_name': f.get('fighter1_name',''),
                'fighter2_name': f.get('fighter2_name',''),
                'winner_name':   f.get('winner_name',''),
                'method':        f.get('method',''),
                'round':         f.get('round', f.get('round_finished', 0)),
                'weight_class':  f.get('weight_class',''),
                'card_slot':     f.get('card_slot',''),
                'fighter1_id':   f.get('fighter1_id',''),
                'fighter2_id':   f.get('fighter2_id',''),
                'winner_id':     f.get('winner_id',''),
                'loser_id':      f.get('loser_id',''),
                'loser_name':    f.get('loser_name',''),
                'event_id':      f.get('event_id', f.get('fight_id','').split('_')[0] if f.get('fight_id') else ''),
                'ranking_change':f.get('ranking_change',''),
                'is_fotn':       f.get('is_fotn', False),
                'winner_new_rank':  f.get('winner_new_rank'),
                'loser_new_rank':   f.get('loser_new_rank'),
                'winner_rank_delta':f.get('winner_rank_delta'),
                'loser_rank_delta': f.get('loser_rank_delta'),
            } for f in ai_fights[:20]],
            'ai_event':        ai_event,
            'balance':         finances.get('balance', 0),
            'overhead':        finances.get('camp_overhead', 0),
            'purses_earned':   finances.get('week_purses_earned', 0),
            'media_reactions': media_reactions,
            'player_rankings': player_rankings,
            'upcoming_fight':  upcoming_fight,
        })

        # ── If player had a fight this week → Fight Night page ──
        # player_fights already resolved from advance_week results.
        # Don't search scheduled_fights — those are already removed after simulation.
        if player_fights:
            pf = player_fights[0]  # primary player fight
            f1_id = pf.get('fighter1_id', '')
            f2_id = pf.get('fighter2_id', '')
            f1    = bridge.get_fighter(f1_id)
            f2    = bridge.get_fighter(f2_id)
            bridge.store_fight_night({
                'fight_id':       pf.get('fight_id', ''),
                'fighter1_id':    f1_id,
                'fighter2_id':    f2_id,
                'fighter1_name':  f1.name if f1 else pf.get('fighter1_name', ''),
                'fighter2_name':  f2.name if f2 else pf.get('fighter2_name', ''),
                'weight_class':   pf.get('weight_class', ''),
                'event_name':     pf.get('event_name', ''),
                'week':           week,
                'player_fights':  player_fights,
                'ai_fights':      ai_fights,
                'is_title_fight': pf.get('is_title_fight', False),
                'training_report':training_report,
            })
            return redirect(url_for('fight_night'))

        return redirect(url_for('week_results'))

    @app.route('/week-results')
    def week_results():
        """Weekly recap page — fight results, training, finances."""
        bridge = get_bridge()
        recap  = bridge.get_week_recap()
        if not recap:
            return redirect(url_for('dashboard'))

        # Build a digest for Coach's Corner
        try:
            digest = bridge.get_weekly_digest() if hasattr(bridge, 'get_weekly_digest') else None
        except Exception:
            digest = None

        # Rankings lookup for AI fight cards — plain dicts so templates can use .get()
        rankings = {}
        if bridge.game_started and bridge._game_state:
            WC_LIST = getattr(bridge._game_state, 'WEIGHT_CLASSES',
                ["Strawweight","Flyweight","Bantamweight","Featherweight",
                 "Lightweight","Welterweight","Middleweight","Light Heavyweight","Heavyweight"])
            for wc in WC_LIST:
                try:
                    for f in bridge.get_division_rankings(wc):
                        rankings[f.fighter_id] = {
                            'name': f.name, 'ranking': f.ranking,
                            'is_champion': f.is_champion, 'record_str': f.record_str,
                            'overall_rating': f.overall_rating, 'weight_class': f.weight_class,
                            'fighting_style': getattr(f, 'fighting_style', ''),
                        }
                except Exception:
                    pass

        # Player IDs needed for template to identify player fights
        player_ids = {f.fighter_id for f in bridge.get_player_fighters()}

        # News from this week
        all_news = bridge.get_news_feed(limit=20)
        this_week = recap.get('week', bridge.week_number)
        week_news = [n for n in all_news if n.week >= this_week - 1]

        # Detect if player fight was FOTN
        fotn_player_fight = None
        for fight in recap.get('player_fights', []):
            if fight.get('is_fotn'):
                fotn_player_fight = fight
                break

        # Detect notable moments from AI fights
        notable = []
        for fight in recap.get('ai_fights', []):
            w_rank    = fight.get('winner_new_rank')
            l_rank    = fight.get('loser_new_rank')
            w_delta   = fight.get('winner_rank_delta') or 0
            l_delta   = fight.get('loser_rank_delta')  or 0
            # Pre-fight ranks (None = unranked = treat as 16 for comparison)
            w_pre     = ((w_rank or 16) + w_delta) if w_rank is not None else 16
            l_pre     = ((l_rank or 16) + l_delta) if l_rank is not None else 16
            method    = fight.get('method', 'DEC')
            # Upset: winner was ranked significantly lower than loser pre-fight
            if w_pre > l_pre + 4 and l_pre < 10:
                notable.append({
                    'icon': '😱', 'color': 'var(--gold)',
                    'text': f"UPSET: {fight.get('winner_name')} defeats "
                            f"{fight.get('loser_name')} — {method}"
                })
            # New #1 contender
            if w_rank == 1 and (fight.get('winner_rank_delta') or 0) > 0:
                notable.append({
                    'icon': '⬆️', 'color': 'var(--blood-red)',
                    'text': f"{fight.get('winner_name')} is the new #1 contender!"
                })
            # Title change
            if fight.get('winner_new_rank') == 0 and fight.get('is_title_fight'):
                notable.append({
                    'icon': '🏆', 'color': 'var(--gold)',
                    'text': f"NEW CHAMPION: {fight.get('winner_name')} wins the belt!"
                })
            # AI fight FOTN
            if fight.get('is_fotn'):
                notable.append({
                    'icon': '🔥', 'color': 'var(--warning)',
                    'text': f"FOTN: {fight.get('fighter1_name')} vs "
                            f"{fight.get('fighter2_name')} — {method}"
                })

        return render_template('week_results.html',
            recap=recap,
            digest=digest,
            rankings=rankings,
            week=recap.get('week', bridge.week_number),
            player_ids=player_ids,
            news=week_news,
            notable=notable,
            fotn_player_fight=fotn_player_fight,
            training_report=recap.get('training_report', {}),
            finances={
                'balance':       recap.get('balance', 0),
                'overhead':      recap.get('overhead', 0),
                'weeks_runway':  int(recap.get('balance', 0) / max(recap.get('overhead', 1), 1)),
                'purses_earned': recap.get('purses_earned', 0),
            },
        )
    
    @app.route('/fight-night')
    def fight_night():
        """Fight Night — player chooses Watch or Sim."""
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('new_game'))
        data = bridge.get_fight_night()
        if not data:
            return redirect(url_for('dashboard'))
        f1 = bridge.get_fighter(data.get('fighter1_id', ''))
        f2 = bridge.get_fighter(data.get('fighter2_id', ''))
        return render_template('fight_night.html',
            week=bridge.week_number,
            fight=data,
            fighter1=f1,
            fighter2=f2,
        )

    @app.route('/sim-fight', methods=['POST'])
    def sim_fight():
        """Simulate the player's fight and go to recap."""
        bridge  = get_bridge()
        data    = bridge.get_fight_night()
        bridge.clear_fight_night()
        finances = bridge.get_camp_finances()
        player_ids = {f.fighter_id for f in bridge.get_player_fighters()}
        media_reactions = {}
        for fight in data.get('player_fights', []):
            fid = fight.get('fight_id', '')
            if fid:
                media_reactions[fid] = bridge.get_media_reactions(fid)
        player_rankings = {}
        for f in bridge.get_player_fighters():
            div_rankings = bridge.get_division_rankings(f.weight_class)
            total_ranked = len([r for r in div_rankings if r.ranking])
            player_rankings[f.fighter_id] = {
                'name': f.name, 'ranking': f.ranking, 'record': f.record_str,
                'weight_class': f.weight_class, 'overall': f.overall_rating,
                'total_ranked': total_ranked,
            }
        completed = bridge.get_completed_events()
        ai_event  = next((e for e in reversed(completed) if e.get('is_ai_event')), None)
        bridge.store_week_recap({
            'week':            data.get('week', bridge.week_number),
            'player_fights':   data.get('player_fights', []),
            'training_report': data.get('training_report', {}),
            'ai_fights':       data.get('ai_fights', []),
            'ai_event':        ai_event,
            'balance':         finances.get('balance', 0),
            'overhead':        finances.get('camp_overhead', 0),
            'purses_earned':   finances.get('week_purses_earned', 0),
            'media_reactions': media_reactions,
            'player_rankings': player_rankings,
            'upcoming_fight':  None,
        })
        return redirect(url_for('week_results'))

    @app.route('/watch-fight/<fight_id>')
    def watch_fight(fight_id):
        """Full play-by-play commentary for a fight."""
        bridge = get_bridge()

        # Find the fight result in completed events
        fight_result = None
        for ev in bridge.get_completed_events():
            for f in ev.get('fights', []):
                if f.get('fight_id') == fight_id:
                    fight_result = f
                    break
            if fight_result:
                break

        if not fight_result:
            flash("Fight not found.", "error")
            return redirect(url_for('dashboard'))

        # Get commentary lines
        commentary = bridge.get_fight_commentary(fight_id)

        # Parse commentary into rounds
        rounds = []
        current_round = []
        current_round_num = 0
        for line in commentary:
            line = line.strip()
            if not line:
                continue
            # Detect round header
            if line.startswith('=== ROUND') or line.lower().startswith('round '):
                if current_round:
                    rounds.append({'num': current_round_num, 'lines': current_round})
                current_round = []
                # Extract round number
                import re
                m = re.search(r'\d+', line)
                current_round_num = int(m.group()) if m else current_round_num + 1
                current_round.append(line)
            else:
                current_round.append(line)
        if current_round:
            rounds.append({'num': current_round_num, 'lines': current_round})

        # If no round structure, treat as single block
        if not rounds and commentary:
            rounds = [{'num': 0, 'lines': commentary}]

        # Get scorecard if available
        scorecard = fight_result.get('scorecard')

        return render_template('watch_fight.html',
            fight=fight_result,
            rounds=rounds,
            commentary=commentary,
            scorecard=scorecard,
            week=bridge.week_number,
        )


    
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
