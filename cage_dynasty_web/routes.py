"""
Cage Dynasty - Flask Routes (Views/Controllers)
All route handlers for the web application.
"""

from flask import render_template, redirect, url_for, request, jsonify, flash, session
from functools import wraps
import uuid
import sys
import traceback
import subprocess  # NEW — for /api/git-pull webhook


# Trait display labels — maps internal enum strings to (label, category)
# pairs. Category drives pill color in templates (positive/negative/
# personality/special). Kept route-side so the bridge stays template-agnostic.
_TRAIT_DISPLAY = {
    # training multipliers — blue
    "TECHNICAL_GENIUS":    ("Technical Genius",    "training"),
    "DIAMOND_POLISHER":    ("Diamond Polisher",    "training"),
    "VETERANS_TOUCH":      ("Veterans Touch",      "training"),
    "IRON_SHARPENER":      ("Iron Sharpener",      "training"),
    "OLD_SCHOOL":          ("Old School",          "training"),
    "MODERN_METHODS":      ("Modern Methods",      "training"),
    "ANALYTICAL":          ("Analytical",          "training"),
    "CONDITIONING_COACH":  ("Conditioning Coach",  "training"),
    "GRAPPLING_SPECIALIST":("Grappling Specialist","training"),
    "STRIKING_SPECIALIST": ("Striking Specialist", "training"),
    "FINISHER":            ("Finisher",            "training"),
    "DEFENSIVE_MINDED":    ("Defensive Minded",    "training"),
    # morale / personality — green
    "MOTIVATOR":           ("Motivator",           "personality"),
    "PLAYERS_COACH":       ("Players Coach",       "personality"),
    "SUPPORTIVE":          ("Supportive",          "personality"),
    "CALM_CORNER":         ("Calm Corner",         "personality"),
    "PATIENT":             ("Patient",             "personality"),
    "CORNER_MAN":          ("Corner Man",          "personality"),
    # mixed — orange
    "INTENSE":             ("Intense",             "mixed"),
    "DISCIPLINARIAN":      ("Disciplinarian",      "mixed"),
    # negatives — red
    "TASKMASTER":          ("Taskmaster",          "negative"),
    "BURNED_OUT":          ("Burned Out",          "negative"),
    "FAIR_WEATHER":        ("Fair Weather",        "negative"),
    "INJURY_RISK":         ("Injury Risk",         "negative"),
}


# Ship MC1b — archetype → (label, icon) for adapting bridge market dicts
# to the template render shape (setup_coach.html + hire_coach.html).
_ARCHETYPE_LABEL = {
    'striking':  ('Striking Coach', '🥊'),
    'grappling': ('Grappling Coach', '🤼'),
    'sc':        ('Strength & Conditioning Coach', '💪'),
    'mma_head':  ('Head Coach', '🧠'),
}


def _enrich_market_entry(c):
    """Adapt a bridge market dict to the shape templates expect.
    Adds: id (alias to coach_id), label, icon, description, trait_display.
    Ship MC1b — bridge owns data, routes own presentation.
    Ship Coach-3 — surfaces type_name/type_icon/primary_stats from
    COACH_TYPES so setup_coach.html can show specialist labels."""
    archetype = c.get('archetype', 'mma_head')
    label, icon = _ARCHETYPE_LABEL.get(archetype, ('Head Coach', '🧠'))
    traits = c.get('traits', []) or []
    # Ship Coach-3 — resolve coach_type (added at market gen in Ship 1)
    from game_bridge import COACH_TYPES
    ct_key = c.get('coach_type', 'boxing_coach')
    ct_def = COACH_TYPES.get(ct_key, COACH_TYPES.get('boxing_coach', {}))
    type_name = ct_def.get('name', label)
    type_icon = ct_def.get('icon', icon)
    return {
        **c,
        'id':              c.get('coach_id'),
        'label':           label,
        'icon':            type_icon,  # prefer specialist icon
        'description':     f"{c.get('rating', 60)} rating · ${c.get('salary', 800):,}/wk",
        'trait_display':   [_TRAIT_DISPLAY.get(t, (t.replace('_', ' ').title(), 'personality'))
                            for t in traits],
        # Ship Coach-3 specialist surface
        'type_name':       type_name,
        'type_icon':       type_icon,
        'type_desc':       ct_def.get('desc', ''),
        'primary_stats':   list(ct_def.get('primary', [])),
        'secondary_stats': list(ct_def.get('secondary', [])),
    }


def _generate_available_coaches(tier):
    """Generate coaches available for hiring based on tier.

    Hoisted to module level (Ship C2) so mid-game `/coach/hire` can reuse
    the same pool generator the new-game setup flow uses.
    """
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
            # Normalize traits: accept enum values, enum objects, or strings.
            _raw_traits = getattr(c, 'traits', []) or []
            _traits = []
            for _t in _raw_traits:
                _key = _t if isinstance(_t, str) else getattr(_t, 'name', None) or getattr(_t, 'value', None) or str(_t)
                # Try uppercase enum-name lookup first (e.g. TECHNICAL_GENIUS),
                # then the display-name as-is (e.g. "Technical Genius").
                _key_upper = _key.upper().replace(' ', '_').replace("'", '')
                _traits.append(_key_upper)
            result.append({
                "id":            c.coach_id,
                "name":          c.name,
                "specialty":     spec,
                "label":         label,
                "icon":          icon,
                "rating":        c.skill_level,
                "salary":        c.weekly_salary,
                "description":   f"{c.personality_desc}. {c.get_bonus_description()}",
                "traits":        _traits,
                "trait_display": [_TRAIT_DISPLAY.get(t, (t.replace('_',' ').title(), 'personality'))
                                  for t in _traits],
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


def register_routes(app):
    """Register all routes with the Flask application."""

    # Helper to get the game bridge
    def get_bridge():
        return app.game_bridge

    # Ship S2: inject sidebar badge counts into every template render
    # so nav badges work on all pages, not just the dashboard route.
    @app.context_processor
    def _inject_nav_counts():
        try:
            bridge = get_bridge()
            if not bridge.game_started:
                return {}
            fighters = bridge.get_player_fighters()
            fighter_ids = {f.fighter_id for f in fighters}
            offers = bridge.get_fight_offers()
            offer_count = len([o for o in offers
                               if o.fighter_id in fighter_ids])
            sponsor_offer_count = len(bridge.get_pending_sponsor_offers())
            return {
                'offer_count': offer_count,
                'sponsor_offer_count': sponsor_offer_count,
            }
        except Exception:
            return {}
    
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

    @app.route('/new-game-session', methods=['POST'])
    def new_game_session():
        """Clear active in-memory session, redirect to new game setup.
        Save files are NOT deleted."""
        app.game_bridge = type(app.game_bridge)()
        session.clear()
        return redirect(url_for('new_game'))

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
        """Step 3: Hire your head coach. Ship MC1b: uses bridge market."""
        if 'camp_name' not in session or 'selected_fighter' not in session:
            return redirect(url_for('setup_camp'))

        bridge = get_bridge()
        coaches = [_enrich_market_entry(c) for c in bridge.get_coach_market()]

        if request.method == 'POST':
            coach_id = request.form.get('coach_id')
            selected_coach = next((c for c in coaches if c['id'] == coach_id), None)
            if selected_coach:
                session['selected_coach'] = selected_coach
                bridge.remove_from_coach_market(selected_coach['coach_id'])
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
        
        flash(f"Welcome to Cage Dynasty! Your journey begins now.", "success")
        return redirect(url_for('dashboard'))
    
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

        # Ship A: rolling 4-week training history per fighter
        training_history = bridge.get_training_history()

        # Expiring contracts — fighters with <=2 fights left on their deals
        expiring_contracts = bridge.get_expiring_contracts()

        # Ship IN1: surface injury-vs-fight collisions for dashboard warning.
        # Auto-cancellation (long-recovery cases) happens in the bridge during
        # advance_week; this alert covers short-recovery cases where the fight
        # is still scheduled but the player should know about the risk.
        injury_alerts = []
        _isys = getattr(bridge, '_injury_system', None)
        if _isys:
            for pf in fighters:
                pf_id = pf.fighter_id
                try:
                    inj = _isys.get_worst_injury(pf_id)
                except Exception:
                    inj = None
                if inj:
                    for sf in scheduled_fights:
                        if (sf.get('fighter1_id') == pf_id
                                or sf.get('fighter2_id') == pf_id):
                            injury_alerts.append({
                                "fighter_name":   pf.name,
                                "opponent":       (sf.get('fighter2_name')
                                                   if sf.get('fighter1_id') == pf_id
                                                   else sf.get('fighter1_name')),
                                "weeks_until":    sf.get('weeks_until', 0),
                                "recovery_weeks": getattr(inj, 'recovery_weeks',
                                                          getattr(inj, 'weeks', 0)),
                            })

        # Ship K5: pending challenges awaiting AI response
        pending_challenges = bridge.get_pending_challenges()
        # Ship K5b: accepted challenges awaiting player to finalize negotiation
        pending_negotiations = bridge.get_pending_negotiations()

        # Player-fighter retirement decision prompts — surfaced as
        # high-priority cards above the weekly news feed.
        retirement_prompts = bridge.get_pending_retirement_prompts()

        return render_template('dashboard.html',
            camp=camp,
            fighters=fighters,
            news=news,
            week=bridge.week_number,
            offer_count=offer_count,
            scheduled_fights=scheduled_fights,
            finances=finances,
            pending_interviews=pending_interviews,
            retirement_prompts=retirement_prompts,
            training_plans=training_plans,
            player_card=player_card,
            balance=balance,
            overhead=overhead,
            runway=runway,
            scout_tips=scout_tips,
            digest=digest,
            training_history=training_history,
            expiring_contracts=expiring_contracts,
            pending_challenges=pending_challenges,
            pending_negotiations=pending_negotiations,
            injury_alerts=injury_alerts,
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

        # Roster enrichment — contract fights remaining
        contracts_map = {}
        for f in fighters:
            try:
                contract = bridge.get_contract_status(f.fighter_id)
                if contract:
                    contracts_map[f.fighter_id] = contract
            except Exception:
                pass

        return render_template('roster.html',
            camp=camp,
            fighters=fighters,
            sort_by=sort_by,
            scheduled_map=scheduled_map,
            training_plans=training_plans,
            contracts_map=contracts_map,
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
        
        # Ship #29: belt history reigns for this fighter (sim'd lineage from
        # Ship #28's WorldInitializer + any future runtime-tracked reigns).
        # Empty list if fighter never held a belt or belt_history unavailable.
        # Ship #30 will surface this on the fighter_profile template.
        belt_history = bridge.get_fighter_reigns(fighter_id)
        
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
                ('Clinch Ctrl', fighter.clinch_control),
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

        # Amateur credential — Sherdog-style, only if fighter has amateur history
        amateur_record = None
        try:
            sys = bridge._get_amateur_system()
            if sys:
                amateur = sys.amateurs.get(fighter_id)
                if amateur:
                    amateur_record = {
                        "wins":            amateur.wins,
                        "losses":          amateur.losses,
                        "draws":           getattr(amateur, 'draws', 0),
                        "tournament_wins": getattr(amateur, 'tournament_wins', 0),
                    }
        except Exception:
            pass

        # Scouting report
        scouting = bridge.get_scouting_report(fighter_id)

        # Watchlist status
        on_watchlist   = bridge.is_on_watchlist(fighter_id)
        watch_entry    = bridge._watchlist.get(fighter_id) if on_watchlist else None
        watch_categories = bridge._WATCH_CATEGORIES

        # Contract status — only for player fighters
        player_ids = {f.fighter_id for f in bridge.get_player_fighters()}
        contract_status  = bridge.get_contract_status(fighter_id) if fighter_id in player_ids else None
        contract_options = bridge.get_contract_options_for_tier(fighter_id) if fighter_id in player_ids else []

        # Contract ask — flavored re-sign message when contract is winding down
        contract_ask = None
        if (contract_status
                and contract_status.get('fights_remaining', 99) <= 2
                and fighter_id in player_ids):
            contract_ask = bridge.get_contract_ask(fighter_id)

        # Ship S1: per-fighter sponsor list (player fighters only)
        fighter_sponsors = []
        if fighter_id in player_ids:
            fighter_sponsors = [
                s for s in bridge.get_player_sponsors()
                if s["fighter_id"] == fighter_id
            ]

        # Free agent sign-from-profile flags
        is_free_agent = (
            bridge._game_state is not None
            and fighter.fighter_id in bridge._game_state.free_agents
        )
        can_sign = (
            is_free_agent
            and fighter.fighter_id not in player_ids
        )

        # Next scheduled fight — scan _scheduled_fights for this
        # fighter, return earliest by week. Surfaces above fight
        # history so the upcoming bout is visible on the profile.
        next_fight = None
        try:
            _candidates = [
                sf for sf in (bridge._scheduled_fights or [])
                if sf.get('fighter1_id') == fighter.fighter_id
                or sf.get('fighter2_id') == fighter.fighter_id
            ]
            if _candidates:
                _candidates.sort(
                    key=lambda f: f.get('week', 9999))
                _nf = _candidates[0]
                # Resolve opponent perspective
                _is_f1 = _nf.get('fighter1_id') == fighter.fighter_id
                next_fight = {
                    'fight_id':      _nf.get('fight_id', ''),
                    'opponent_id':   (_nf.get('fighter2_id')
                                      if _is_f1
                                      else _nf.get('fighter1_id')),
                    'opponent_name': (_nf.get('fighter2_name')
                                      if _is_f1
                                      else _nf.get('fighter1_name')),
                    'event_name':    _nf.get('event_name', ''),
                    'week':          _nf.get('week', 0),
                    'is_title_fight': _nf.get('is_title_fight', False),
                    'card_slot':     _nf.get('card_slot', ''),
                }
        except Exception:
            next_fight = None

        # Ship HOF2: HOF badge on fighter profile
        is_hof = False
        try:
            if bridge.game_started and hasattr(bridge, 'get_record_book'):
                rb = bridge.get_record_book() or {}
                hof_ids = {h.get('fighter_id') for h in
                           (rb.get('hof_inductees') or [])}
                is_hof = fighter.fighter_id in hof_ids
        except Exception:
            is_hof = False

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
            contract_ask=contract_ask,
            amateur_record=amateur_record,
            contract_options=contract_options,
            player_ids=player_ids,
            fighter_sponsors=fighter_sponsors,
            next_fight=next_fight,
            is_free_agent=is_free_agent,
            can_sign=can_sign,
            is_hof=is_hof,
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
    # SPONSOR OFFERS — Ship S2
    # =========================================================================

    @app.route('/sponsor-offers')
    def sponsor_offers():
        """Pending sponsor approaches awaiting accept/decline."""
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('new_game'))
        offers = bridge.get_pending_sponsor_offers()
        return render_template('sponsor_offers.html',
            offers=offers,
            week=bridge.week_number,
            balance=bridge._camp_balance,
        )

    @app.route('/sponsor-offers/accept/<offer_id>', methods=['POST'])
    def accept_sponsor_offer(offer_id):
        bridge = get_bridge()
        result = bridge.accept_sponsor_offer(offer_id)
        if result.get('success'):
            flash(result.get('message', 'Sponsor signed!'), 'success')
        else:
            flash(result.get('error', 'Could not accept offer'), 'error')
        return redirect(url_for('sponsor_offers'))

    @app.route('/sponsor-offers/decline/<offer_id>', methods=['POST'])
    def decline_sponsor_offer(offer_id):
        bridge = get_bridge()
        result = bridge.decline_sponsor_offer(offer_id)
        if result.get('success'):
            flash('Offer declined.', 'info')
        else:
            flash(result.get('error', 'Could not decline offer'), 'error')
        return redirect(url_for('sponsor_offers'))

    # =========================================================================
    # TRAINING
    # =========================================================================
    
    @app.route('/training')
    def training():
        """Training management view."""
        bridge = get_bridge()
        fighters = bridge.get_player_fighters()
        camp = bridge.get_player_camp()
        
        # Two-stage focus model: pick GROUP, then EMPHASIS within group.
        # Hidden input submits as "GROUP:emphasis" (e.g. "STRIKING:boxing").
        # Bridge resolves both new format and legacy flat keys via
        # _FOCUS_LEGACY_MAP, so old saves still work.
        training_groups = [
            ('STRIKING',     '🥊', 'Hands, kicks, clinch, defense',
             [('boxing','Boxing'),('kicks','Kicks'),
              ('clinch','Clinch'),('clinch_control','Clinch Ctrl'),
              ('defense','Strike Def')]),
            ('GRAPPLING',    '🤼', 'Takedowns, control, subs, guard',
             [('takedowns','Takedowns'),('takedown_defense','TD Defense'),
              ('top_control','Top Control'),('submissions','Submissions'),
              ('guard','Guard')]),
            ('CONDITIONING', '💪', 'Cardio, strength, toughness',
             [('cardio','Cardio'),('strength','Strength'),
              ('toughness','Toughness')]),
            ('MENTAL',       '🧠', 'Fight IQ, composure',
             [('fight_iq','Fight IQ'),('composure','Composure')]),
            ('SPARRING',     '🎯', 'Balanced all-round light work',
             [('sparring','Sparring')]),
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

        # Ship MC1b: non-head coaches for the "Staff also developing" line
        staff = bridge.get_coach_contract_status().get('staff_list', [])
        staff_developing = [
            ((c.get('specialty') or 'Coach').title(),
             c.get('archetype', 'mma_head'),
             c.get('name', 'Coach'))
            for c in staff
            if not c.get('is_head')
        ]

        # Training plans per fighter
        training_plans = {}
        # Unified-grid: precompute per-stat targets from the saved queue
        # so the template doesn't need Jinja namespace gymnastics. Targets
        # map: {stat_key: target_value}. Zero/missing == no active goal.
        stat_targets = {}
        for f in fighters:
            plan = bridge.get_training_plan(f.fighter_id)
            training_plans[f.fighter_id] = plan
            _t = {}
            for _g in (plan.get('queue', []) or []):
                _focus = (_g.get('focus') or '').strip()
                _tgt   = int(_g.get('target', 0) or 0)
                if _focus and _focus != 'maintain' and _tgt > 0:
                    _t[_focus] = _tgt
            stat_targets[f.fighter_id] = _t

        # Decay risk per fighter — surfaces on training page
        decay_risks = {}
        try:
            if (hasattr(bridge, '_maintenance_system') and
                bridge._maintenance_system and
                hasattr(bridge._maintenance_system, 'get_fighter_decay_risk')):
                for f in fighters:
                    risks = bridge._maintenance_system.get_fighter_decay_risk(
                        f.fighter_id, bridge.week_number
                    )
                    # Only surface non-safe stats to keep the UI clean
                    at_risk = {
                        stat: info for stat, info in risks.items()
                        if info.get('risk_level') not in ('Safe',)
                    }
                    decay_risks[f.fighter_id] = at_risk
        except Exception:
            decay_risks = {}

        # Auto-rest hysteresis — fighters currently locked into
        # REST until fatigue drops to 40. Drives the UI indicator.
        recovering_fighters = {
            f.fighter_id for f in fighters
            if getattr(bridge, f'_auto_resting_{f.fighter_id}', False)
        }

        # Ship: next-fight per fighter (for fight camp banner).
        # Scan _scheduled_fights for earliest match, expose weeks_until +
        # opponent name. Keyed by fighter_id for template lookup.
        next_fights = {}
        try:
            sched = list(bridge._scheduled_fights or [])
            for f in fighters:
                fid = f.fighter_id
                cands = [
                    sf for sf in sched
                    if sf.get('fighter1_id') == fid
                    or sf.get('fighter2_id') == fid
                ]
                if not cands:
                    continue
                cands.sort(key=lambda sf: sf.get('week', 9999))
                nf = cands[0]
                weeks = max(0, nf.get('week', 0) - bridge.week_number)
                is_f1 = nf.get('fighter1_id') == fid
                next_fights[fid] = {
                    'weeks_until':  weeks,
                    'opponent':     (nf.get('fighter2_name')
                                     if is_f1 else nf.get('fighter1_name')),
                    'event_name':   nf.get('event_name', ''),
                    'is_title':     nf.get('is_title_fight', False),
                }
        except Exception:
            next_fights = {}

        # Ship: 4-week OVR momentum per fighter from training_history.
        # Sum of (ovr_after - ovr_before) across the last 4 weekly entries.
        # Empty/missing history → 0.0 delta.
        ovr_deltas = {}
        try:
            history = bridge.get_training_history() or {}
            for f in fighters:
                entries = history.get(f.fighter_id, [])[-4:]
                if not entries:
                    ovr_deltas[f.fighter_id] = 0.0
                    continue
                total = sum(
                    float(e.get('ovr_after', 0)) - float(e.get('ovr_before', 0))
                    for e in entries if isinstance(e, dict)
                )
                ovr_deltas[f.fighter_id] = total
        except Exception:
            ovr_deltas = {}

        return render_template('training.html',
            fighters=fighters,
            camp=camp,
            coach=coach,
            staff_developing=staff_developing,
            training_plans=training_plans,
            stat_targets=stat_targets,
            training_groups=training_groups,
            intensity_options=intensity_options,
            decay_risks=decay_risks,
            recovering_fighters=recovering_fighters,
            next_fights=next_fights,
            ovr_deltas=ovr_deltas,
            week=bridge.week_number,
        )
    
    @app.route('/training/set_floors/<fighter_id>', methods=['POST'])
    def set_stat_floors(fighter_id):
        """Save per-stat decay floors for a fighter."""
        bridge = get_bridge()
        if not bridge.game_started:
            return jsonify({"error": "No game loaded"}), 400
        floors = {}
        for stat in [
            'boxing','kicks','clinch_striking','clinch_control','striking_defense',
            'takedowns','takedown_defense','top_control','submissions',
            'guard','strength','speed','cardio','chin','recovery',
            'fight_iq','composure','heart',
        ]:
            val = request.form.get(f'floor_{stat}', '0').strip()
            try:
                floors[stat] = int(val) if val else 0
            except ValueError:
                floors[stat] = 0
        bridge.set_stat_floors(fighter_id, floors)
        # Silent mode: invoked from the queue-form-submit hook in
        # training.html so floors save quietly alongside the queue start.
        # Skip the flash (would otherwise stack with the queue flash) and
        # return 204 so the fetch caller doesn't have to follow a redirect.
        if request.form.get('silent') == '1':
            return ('', 204)
        flash(f"Stat floors saved.", "success")
        return redirect(url_for('training'))

    @app.route('/training/set_queue/<fighter_id>', methods=['POST'])
    def set_training_queue(fighter_id):
        """Save a training goal queue for a fighter."""
        bridge = get_bridge()
        if not bridge.game_started:
            return jsonify({"error": "No game loaded"}), 400

        intensity = request.form.get('queue_intensity', 'MODERATE').upper()

        queue = []
        i = 0
        while True:
            focus = request.form.get(f'queue_focus_{i}', '').strip()
            if not focus:
                break
            target_str = request.form.get(f'queue_target_{i}', '0').strip()
            try:
                target = int(target_str) if target_str else 0
            except ValueError:
                target = 0
            if focus == 'maintain':
                queue.append({"focus": "maintain", "target": 0})
                break
            if focus and target > 0:
                queue.append({"focus": focus, "target": target})
            i += 1
            if i > 10:
                break

        if queue:
            bridge.set_training_queue(fighter_id, queue, intensity)
            flash("Training queue saved — goals will advance automatically.", "success")
        else:
            flash("No valid goals — queue not saved.", "error")

        return redirect(url_for('training'))

    @app.route('/training/clear_queue/<fighter_id>', methods=['POST'])
    def clear_training_queue(fighter_id):
        """Clear training queue and return to manual mode."""
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('training'))
        bridge.clear_training_queue(fighter_id)
        flash("Training queue cleared — back to manual mode.", "success")
        return redirect(url_for('training'))

    @app.route('/training/set_unified/<fighter_id>', methods=['POST'])
    def set_unified_training(fighter_id):
        """Unified stat-grid submit — single POST carries all 18 floor_
        and target_ fields plus intensity. Builds the training queue
        from non-zero targets (preserving the grid order) and saves
        floors alongside. The existing queue advancement + auto-maintain
        hook in _apply_weekly_training does the rest."""
        bridge = get_bridge()
        if not bridge.game_started:
            return jsonify({"error": "No game loaded"}), 400

        all_stats = [
            'boxing','kicks','clinch_striking','clinch_control','striking_defense',
            'takedowns','takedown_defense','top_control','submissions','guard',
            'strength','speed','cardio','chin','recovery',
            'heart','fight_iq','composure',
        ]

        # Floors — clamp 50-95, step 5 enforced server-side too.
        floors = {}
        for stat in all_stats:
            raw = request.form.get(f'floor_{stat}', '50').strip()
            try:
                val = int(raw) if raw else 50
            except ValueError:
                val = 50
            val = max(50, min(95, (val // 5) * 5))
            floors[stat] = val
        bridge.set_stat_floors(fighter_id, floors)

        # Targets — build queue in stat-grid order. Skip targets that
        # are at or below current stat value (already maintained).
        fighter = bridge.get_fighter(fighter_id)
        queue = []
        for stat in all_stats:
            raw = request.form.get(f'target_{stat}', '0').strip()
            try:
                tgt = int(raw) if raw else 0
            except ValueError:
                tgt = 0
            if tgt <= 0:
                continue
            tgt = max(0, min(99, (tgt // 5) * 5))
            cur = int(getattr(fighter, stat, 0)) if fighter else 0
            if tgt > cur:
                queue.append({"focus": stat, "target": tgt})

        intensity = request.form.get('intensity', 'MODERATE').upper()
        if intensity not in ('REST','LIGHT','MODERATE','INTENSE','EXTREME'):
            intensity = 'MODERATE'

        if queue:
            bridge.set_training_queue(fighter_id, queue, intensity)
            flash(f"Training plan saved — {len(queue)} stat"
                  f"{'s' if len(queue) != 1 else ''} targeted. "
                  f"Floors locked in.", "success")
        else:
            # No active targets — clear queue, keep floors (maintain only).
            bridge.clear_training_queue(fighter_id)
            flash("Maintenance mode — floors locked in, no active goals.", "success")

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
        
        def _p4p_score(f):
            # OVR is the foundation
            score = f.overall_rating * 2.0
            # Win volume — diminishing above 20
            score += min(getattr(f, 'wins', 0), 20) * 3.0
            # Finish rate — dominance indicator
            total = (getattr(f, 'wins', 0)
                     + getattr(f, 'losses', 0))
            if total >= 5:
                finishes = (getattr(f, 'ko_wins', 0)
                            + getattr(f, 'sub_wins', 0))
                score += (finishes / total) * 25
            # Division rank bonus — #1 worth more than #10
            rank = getattr(f, 'ranking', None)
            if rank and rank > 0:
                score += max(0, 16 - rank) * 4
            # Champion bonus — meaningful but not dominant.
            # A weak champ shouldn't auto-beat a great non-champ.
            if getattr(f, 'is_champion', False):
                score += 20
                defenses = getattr(
                    f, 'title_defenses', 0) or 0
                score += defenses * 8
            score -= getattr(f, 'losses', 0) * 2.0
            return score

        p4p_fighters = sorted(
            [f for f in unique_fighters
             if f.is_active
             and (getattr(f, 'wins', 0)
                  + getattr(f, 'losses', 0)) >= 3],
            key=_p4p_score,
            reverse=True
        )[:15]

        # GOAT rankings
        def _goat_score(f):
            wins   = getattr(f, 'wins', 0)
            losses = getattr(f, 'losses', 0)
            ko_w   = getattr(f, 'ko_wins', 0)
            sub_w  = getattr(f, 'sub_wins', 0)
            total  = wins + losses
            # Win volume (primary)
            score = wins * 10
            # Finish quality bonus
            score += ko_w * 6
            score += sub_w * 5
            # Decision wins still count, less
            score += max(0, wins - ko_w - sub_w) * 3
            # Loss penalty — steeper for GOAT
            score -= losses * 4
            # Championship credit — sustained excellence
            if getattr(f, 'is_champion', False):
                score += 25
            defenses = getattr(
                f, 'title_defenses', 0) or 0
            score += defenses * 12
            # Longevity bonus
            if total >= 20:
                score += 15
            elif total >= 15:
                score += 8
            # OVR modifier — quality matters
            ovr = getattr(f, 'overall_rating', 60)
            score += max(0, ovr - 70) * 2
            return score

        goat_fighters = sorted(
            [f for f in unique_fighters
             if (getattr(f, 'wins', 0)
                 + getattr(f, 'losses', 0)) >= 5],
            key=_goat_score,
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
            camp_equipment=bridge._camp_equipment.get(camp_id, {}),
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
        """Upcoming events view — pro cards + amateur tournaments."""
        bridge = get_bridge()
        events = list(bridge.get_upcoming_events() or [])

        # Ship Amateur-Events: surface upcoming amateur tournaments
        # alongside pro cards. Tournament dicts carry event_type='amateur'
        # so the template can render them with distinct styling.
        try:
            am_sys = bridge._get_amateur_system() if hasattr(
                bridge, '_get_amateur_system') else None
            if am_sys and bridge._game_state:
                cur_wk = bridge._game_state.week_number
                for t in am_sys.get_upcoming_tournaments(cur_wk, weeks_ahead=8):
                    events.append({
                        'event_type':       'amateur',
                        'event_name':       getattr(t, 'name', 'Amateur Tournament'),
                        'event_city':       getattr(t, 'region', ''),
                        'week':             getattr(t, 'week', cur_wk),
                        'weight_class':     getattr(t, 'weight_class', ''),
                        'bracket_size':     getattr(t, 'bracket_size', 0),
                        'fighter_count':    len(getattr(t, 'fighters', []) or []),
                        'tournament_id':    getattr(t, 'tournament_id', ''),
                        'fights':           [],  # bracket, not slot-based
                        'player_has_fight': False,
                    })
                # Sort combined list by week ascending (soonest first)
                events.sort(key=lambda e: e.get('week', 99))
        except Exception:
            pass  # defensive — never block the events page

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
            # Ship K5: async challenge — pending response, no neg yet
            if result.get("pending"):
                flash(result.get("message", "Challenge sent."), "info")
                return redirect(url_for('dashboard'))
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

        # ── Stale offer check ──────────────────────────────
        # Offerer (ai_fighter) might have been booked, injured,
        # or retired between offer creation and player opening
        # the negotiation page. Redirect away if unavailable.
        try:
            unavailable_reason = None
            if bridge._game_state and opponent:
                gs = bridge._game_state
                if any(sf.get("fighter1_id") == ai_fighter_id
                       or sf.get("fighter2_id") == ai_fighter_id
                       for sf in (bridge._scheduled_fights or [])):
                    unavailable_reason = "booked for another fight"
                elif (hasattr(bridge, '_injury_system')
                        and bridge._injury_system
                        and not bridge._injury_system.is_cleared_to_fight(ai_fighter_id)):
                    unavailable_reason = "injured"
                elif not getattr(opponent, 'is_active', True):
                    unavailable_reason = "no longer active"

            if unavailable_reason:
                # Clean up any matching offer
                opp_name = getattr(opponent, 'name', neg.get('ai_fighter_name', 'Opponent'))
                bridge._fight_offers = [
                    o for o in (bridge._fight_offers or [])
                    if o.get("opponent_id") != ai_fighter_id
                       or o.get("fighter_id") != player_fighter_id
                ]
                flash(f"⚠️ {opp_name} is {unavailable_reason} — offer withdrawn.",
                      "warning")
                return redirect(url_for('fight_offers'))
        except Exception:
            pass

        # ── Opponent intel — style pill data + top 3 stats + scout lines ──
        top_stats = []
        scout_lines = []
        if opponent:
            _stat_keys = [
                ('Boxing', 'boxing'), ('Kicks', 'kicks'),
                ('Clinch', 'clinch_striking'),
                ('Clinch Ctrl', 'clinch_control'),
                ('Striking D', 'striking_defense'),
                ('Takedowns', 'takedowns'),
                ('TD Defense', 'takedown_defense'),
                ('Top Control', 'top_control'),
                ('Submissions', 'submissions'),
                ('Guard', 'guard'),
                ('Strength', 'strength'), ('Speed', 'speed'),
                ('Cardio', 'cardio'), ('Chin', 'chin'),
                ('Fight IQ', 'fight_iq'),
                ('Composure', 'composure'),
                ('Heart', 'heart'),
            ]
            _stat_vals = [
                (label, getattr(opponent, key, 0))
                for label, key in _stat_keys
            ]
            _stat_vals.sort(key=lambda x: -(x[1] or 0))
            top_stats = _stat_vals[:3]
            try:
                scout_lines = bridge._generate_opponent_tendencies(opponent)
            except Exception:
                scout_lines = []

        return render_template('negotiation.html',
            neg=neg,
            player_fighter=player_fighter,
            opponent=opponent,
            top_stats=top_stats,
            scout_lines=scout_lines,
            week=bridge.week_number,
        )

    @app.route('/champion-injury/<fighter_id>', methods=['GET'])
    def champion_injury_decision(fighter_id):
        """Slice 3 — player decides vacate or hold for an injured champion."""
        bridge = get_bridge()

        pending = bridge._pending_injury_decisions
        decision = next((d for d in pending if d.get("fighter_id") == fighter_id), None)
        if not decision:
            flash("No pending decision for that fighter.", "info")
            return redirect(url_for('dashboard'))

        fighter = bridge.get_fighter(fighter_id)
        if not fighter:
            flash("Fighter not found.", "error")
            return redirect(url_for('dashboard'))

        vacate_preview = bridge._preview_vacant_title_contenders(
            decision["weight_class"],
            exclude_fighter_ids={fighter_id},
        )

        pending_count = len(pending)
        pending_index = next(
            (i + 1 for i, d in enumerate(pending) if d.get("fighter_id") == fighter_id),
            1,
        )

        return render_template('champion_injury_decision.html',
            fighter=fighter,
            decision=decision,
            vacate_preview=vacate_preview,
            pending_count=pending_count,
            pending_index=pending_index,
            week=bridge.week_number,
        )

    @app.route('/champion-injury/<fighter_id>/vacate', methods=['POST'])
    def champion_injury_vacate(fighter_id):
        """Slice 3 vacate handler."""
        bridge = get_bridge()
        result = bridge.resolve_champion_injury_decision(fighter_id, "vacate")
        if result.get("success"):
            flash(f"{result.get('fighter_name', 'Champion')} vacated the title.", "info")
        else:
            flash(result.get("error", "Could not process decision"), "error")
        if bridge._pending_injury_decisions:
            return redirect(url_for('champion_injury_decision',
                                    fighter_id=bridge._pending_injury_decisions[0]["fighter_id"]))
        return redirect(url_for('dashboard'))

    @app.route('/champion-injury/<fighter_id>/hold', methods=['POST'])
    def champion_injury_hold(fighter_id):
        """Slice 3 hold handler."""
        bridge = get_bridge()
        result = bridge.resolve_champion_injury_decision(fighter_id, "hold")
        if result.get("success"):
            flash(f"{result.get('fighter_name', 'Champion')} holds the belt during recovery.", "success")
        else:
            flash(result.get("error", "Could not process decision"), "error")
        if bridge._pending_injury_decisions:
            return redirect(url_for('champion_injury_decision',
                                    fighter_id=bridge._pending_injury_decisions[0]["fighter_id"]))
        return redirect(url_for('dashboard'))

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
        _rec_focus_raw = cs.get('focus', 'boxing')
        # Convert legacy flat key (e.g. "boxing") → "STRIKING:boxing"
        # for template comparison against new fkey format.
        if ":" in str(_rec_focus_raw):
            rec_focus = _rec_focus_raw
        else:
            _g, _e = bridge._FOCUS_LEGACY_MAP.get(
                str(_rec_focus_raw).lower(), ("SPARRING", "sparring"))
            rec_focus = f"{_g}:{_e}"
        rec_intensity = cs.get('intensity',  'MODERATE')

        # Also normalize any persisted existing_focus to GROUP:emphasis
        # so the "currently selected" badge renders against legacy saves.
        _existing_raw = data.get('existing_focus')
        if _existing_raw and ":" not in str(_existing_raw):
            _g, _e = bridge._FOCUS_LEGACY_MAP.get(
                str(_existing_raw).lower(), ("SPARRING", "sparring"))
            data['existing_focus'] = f"{_g}:{_e}"

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

        # Grouped focus options — fkey is now "GROUP:emphasis".
        # Resolved by bridge via _TRAINING_GROUPS.
        focus_groups = [
            {
                "label": "⚔️ Striking",
                "color": "var(--blood-red)",
                "options": [
                    ("STRIKING:boxing",   "Boxing",    "🥊", "Punching technique, combos, distance"),
                    ("STRIKING:kicks",    "Kicking",   "🦵", "Leg, body, and head kicks"),
                    ("STRIKING:clinch",   "Clinch",    "👊", "Knees, elbows, dirty boxing"),
                    ("STRIKING:clinch_control", "Clinch Ctrl", "🤼", "Grip dominance, cage control, clinch entries"),
                    ("STRIKING:defense",  "Defense",   "🛡", "Head movement, blocking, footwork"),
                ],
            },
            {
                "label": "🥋 Grappling",
                "color": "var(--info)",
                "options": [
                    ("GRAPPLING:takedowns",        "Wrestling",   "🤼", "Takedowns and cage control"),
                    ("GRAPPLING:takedown_defense", "TD Defense",  "🦅", "Sprawl and takedown prevention"),
                    ("GRAPPLING:top_control",      "Top Control", "⬇️", "GnP position and pressure"),
                    ("GRAPPLING:submissions",      "Submissions", "🔒", "Chokes and joint locks"),
                    ("GRAPPLING:guard",            "Guard Work",  "🛡", "Sweeps, guard retention, getups"),
                ],
            },
            {
                "label": "💪 Conditioning",
                "color": "var(--neon-green)",
                "options": [
                    ("CONDITIONING:cardio",    "Cardio",    "❤️", "Gas tank and stamina"),
                    ("CONDITIONING:strength",  "Strength",  "⚡", "Power and clinch strength"),
                    ("CONDITIONING:toughness", "Toughness", "🦴", "Chin, heart, durability"),
                ],
            },
            {
                "label": "🧠 Mental",
                "color": "var(--gold)",
                "options": [
                    ("MENTAL:fight_iq",  "Fight IQ",  "🧠", "Ring generalship, adjustments"),
                    ("MENTAL:composure", "Composure", "🧘", "Stay sharp under pressure"),
                ],
            },
        ]

        # Fight camp intensity — REST recovers fatigue (stat/age-modified)
        intensity_options = [
            ("REST",     "Rest",     "Recovery only", "No training gains. Fighter recovers fatigue.", "var(--info)"),
            ("LIGHT",    "Light",    "50% gains",     "+2 fatigue, no injury risk",                   "blue"),
            ("MODERATE", "Moderate", "100% gains",    "+5 fatigue, 1% injury risk",                   "yellow"),
            ("INTENSE",  "Intense",  "150% gains",    "+10 fatigue, 3% injury risk",                  "orange"),
            ("EXTREME",  "Extreme",  "200% gains",    "+18 fatigue, 8% injury risk",                  "red"),
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

    @app.route('/amateur-circuit')
    def amateur_circuit():
        """Amateur circuit — scout prospects, rankings, graduates."""
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('new_game'))
        try:
            data = bridge.get_amateur_data()
        except Exception:
            data = {"available": False}

        # Tab + filter + sort from URL params
        active_tab   = request.args.get('tab', 'scout')
        wc_filter    = request.args.get('wc', '')
        style_filter = request.args.get('style', '')
        sort_by      = request.args.get('sort', 'potential')

        # Source: prefer data['all_prospects'] if present, else flatten
        # from data['eligible'] (weight-class-grouped dict) so the filter
        # surface always has something to work with.
        prospects = []
        if isinstance(data, dict):
            prospects = list(data.get('all_prospects') or [])
            if not prospects:
                for _wc, _ff in (data.get('eligible') or {}).items():
                    for _f in _ff:
                        prospects.append({**_f, 'wc': _wc})

        # Apply filters
        if wc_filter:
            prospects = [f for f in prospects
                         if (f.get('wc') == wc_filter
                             or f.get('weight_class') == wc_filter)]
        if style_filter:
            prospects = [f for f in prospects
                         if (f.get('style') or '') == style_filter]

        # Apply sort
        if sort_by == 'ovr':
            prospects = sorted(prospects, key=lambda x: -(
                x.get('overall') or x.get('overall_rating', 0)))
        elif sort_by == 'record':
            prospects = sorted(prospects, key=lambda x: (
                -(x.get('wins', 0) + x.get('losses', 0)),
                -x.get('wins', 0)
            ))
        elif sort_by == 'age':
            prospects = sorted(prospects, key=lambda x: x.get('age', 99))
        elif sort_by == 'time':
            prospects = sorted(prospects, key=lambda x: -x.get('weeks_in_amateur', 0))
        else:  # potential (default)
            _grade_order = {'Elite': 0, 'High': 1, 'Average': 2, 'Limited': 3}
            prospects = sorted(prospects, key=lambda x: (
                _grade_order.get(x.get('potential', 'Average'), 2),
                -(x.get('overall') or x.get('overall_rating', 0))
            ))
        if isinstance(data, dict):
            data['all_prospects'] = prospects

        # Build filter option lists from the current prospect pool
        # (so the dropdown reflects what's actually available).
        styles = sorted(set(
            f.get('style', '') for f in prospects
            if f.get('style')))

        # Build graduates list from authoritative registry
        graduates = []
        try:
            for g in bridge.get_amateur_graduates():
                fid = g.get('fighter_id', '')
                fdata = {}
                fighter = None
                if bridge._game_state:
                    fighter = bridge._game_state.get_fighter(fid)
                    fdata = bridge._game_state._fighter_data.get(fid, {})
                graduates.append({
                    'name':           g.get('fighter_name', ''),
                    'fighter_id':     fid,
                    'record':         f"{g.get('pro_wins',0)}-{g.get('pro_losses',0)}",
                    'overall':        getattr(fighter, 'overall_rating', 0) if fighter else 0,
                    'ovr_at_signing': int(fdata.get('ovr_at_signing', 0)),
                    'weight_class':   g.get('weight_class', ''),
                    'style':          fdata.get('style', ''),
                    'wins':           g.get('pro_wins', 0),
                    'losses':         g.get('pro_losses', 0),
                })
        except Exception:
            graduates = []

        # Weight classes for filter pills
        weight_classes = [
            'Strawweight','Flyweight','Bantamweight','Featherweight',
            'Lightweight','Welterweight','Middleweight',
            'Light Heavyweight','Heavyweight'
        ]

        return render_template('amateur.html',
            week=bridge.week_number,
            amateur=data,
            active_tab=active_tab,
            wc_filter=wc_filter,
            style_filter=style_filter,
            sort_by=sort_by,
            graduates=graduates,
            weight_classes=weight_classes,
            styles=styles,
            all_prospects=prospects,
        )

    @app.route('/sign-fighter/<fighter_id>', methods=['POST'])
    def sign_fighter_from_profile(fighter_id):
        """Sign a free-agent fighter directly from their profile."""
        bridge = get_bridge()
        from flask import flash
        try:
            contract_fights = int(
                request.form.get('contract_fights', 3))
        except (TypeError, ValueError):
            contract_fights = 3
        result = bridge.sign_free_agent(
            fighter_id, contract_fights)
        if result.get('success'):
            flash(result.get('message', 'Fighter signed!'),
                  'success')
        else:
            flash(result.get('error',
                'Could not sign fighter.'), 'error')
        return redirect(url_for('fighter_profile',
            fighter_id=fighter_id))

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

    @app.route('/fighter/<fighter_id>/move-class', methods=['POST'])
    def move_weight_class(fighter_id):
        """Move a player fighter up or down one weight class."""
        bridge = get_bridge()
        new_class = request.form.get('new_class', '').strip()
        if not new_class:
            flash("No weight class selected.", "error")
            return redirect(url_for('fighter_profile',
                                    fighter_id=fighter_id))
        result = bridge.move_weight_class(fighter_id, new_class)
        if result.get('success'):
            flash(result['message'], 'success')
        else:
            flash(result.get('error', 'Could not move weight class.'),
                  'error')
        return redirect(url_for('fighter_profile',
                                fighter_id=fighter_id))

    # Personality-typed reaction appended to the morale outcome flash
    # on successful re-sign. Combines with the existing 4-tier morale
    # message to produce "{morale-outcome} {personality-reaction}".
    # Gender-neutral by default — no `gender` field on fighters today.
    # CONTENDER line was reworded to drop the implied "guaranteed title
    # shot" commitment, which no system enforces (would auto-create
    # player obligation without a decision point).
    _RESIGN_OUTCOMES = {
        'WARRIOR':    "They just want the next fight.",
        'HUNGRY':     "They're grateful. They'll prove it in the cage.",
        'ELITE':      "They signed but expect to be treated like the headliner they are.",
        'PROSPECT':   "They're all-in on the camp's vision.",
        'JOURNEYMAN': "They say it's the longest contract they've had — they appreciate the stability.",
        'SHOWMAN':    "They want to know when their next main event is.",
        'CALCULATED': "They reviewed the terms thoroughly. The math worked.",
        'CONTENDER':  "They want a real climb up the rankings — book quality opposition.",
    }

    @app.route('/fighter/<fighter_id>/resign', methods=['POST'])
    def resign_fighter(fighter_id):
        """Re-sign a player fighter to a new contract."""
        bridge = get_bridge()
        contract_fights = int(request.form.get('contract_fights', 3))
        result = bridge.resign_fighter(fighter_id, contract_fights)
        from flask import flash
        if result.get('success'):
            # Morale-flavored outcome — read the post-resign morale
            # (resign_fighter bumps morale +15, so 80 is reachable)
            contract = bridge.get_contract_status(fighter_id)
            morale = contract.get('morale', 75) if contract else 75
            if morale >= 80:
                morale_msg = "They're fired up about the new deal."
            elif morale >= 60:
                morale_msg = "They accepted — a fair deal for both sides."
            elif morale >= 40:
                morale_msg = "They signed, but they want to see results."
            else:
                morale_msg = "They stayed — but they'll need to see improvement."
            # Personality reaction — typed flavor by archetype
            personality = bridge._contracts.get(
                fighter_id, {}).get('personality', 'HUNGRY')
            personality_msg = _RESIGN_OUTCOMES.get(personality, '')
            combined = f"{morale_msg} {personality_msg}".strip()
            flash(f"✅ Contract extended! {combined}", "success")
        else:
            flash(result.get('error', 'Could not re-sign.'), 'error')
        return redirect(url_for('fighter_profile', fighter_id=fighter_id))

    @app.route('/fighter/<fighter_id>/retirement-decision',
               methods=['POST'])
    def retirement_decision(fighter_id):
        """Resolve a queued player-fighter retirement prompt. The
        player picks 'retire' (process retirement now, free the roster
        slot, file the news headline) or 'continue' (clear the prompt,
        +15 morale bump for the convince-to-fight moment). The prompt
        is popped either way."""
        bridge = get_bridge()
        decision = request.form.get('decision', 'retire')
        prompt = bridge._pending_retirement_prompts.pop(fighter_id, None)
        if not prompt:
            return redirect(url_for('dashboard'))

        from flask import flash
        fighter = bridge.get_fighter(fighter_id)
        name = prompt.get('fighter_name', 'Fighter')

        if decision == 'retire':
            if fighter:
                fighter.is_active = False
                camp = bridge._game_state.camps.get(
                    getattr(fighter, 'camp_id', None))
                if camp and hasattr(camp, 'fighter_ids'):
                    if fighter_id in camp.fighter_ids:
                        camp.fighter_ids.remove(fighter_id)
                        if hasattr(camp, 'fighter_count'):
                            camp.fighter_count = len(
                                camp.fighter_ids)
                if fighter_id in bridge._game_state._fighter_data:
                    bridge._game_state._fighter_data[
                        fighter_id]['is_active'] = False
                bridge._news_items.insert(0, {
                    'headline': (
                        f"🥊 {name} ({prompt['record']}) "
                        f"retires at age {prompt['age']}"),
                    'category':     'retirement',
                    'week':         bridge.week_number,
                    'fighter_id':   fighter_id,
                    'fighter_name': name,
                })
            flash(f"{name} has retired. A legend.", "info")
        else:
            # Continue — convince-to-stay morale bump.
            if fighter:
                contract = bridge._contracts.get(fighter_id) or {}
                cur_morale = int(contract.get('morale', 70))
                contract['morale'] = min(100, cur_morale + 15)
                bridge._contracts[fighter_id] = contract
            bridge._news_items.insert(0, {
                'headline': (
                    f"💪 {name} decides to continue fighting "
                    f"— one more run!"),
                'category':     'roster',
                'week':         bridge.week_number,
                'fighter_id':   fighter_id,
                'fighter_name': name,
            })
            flash(f"{name} is staying. Let's get them one more fight.",
                  "success")

        return redirect(url_for('dashboard'))

    # =========================================================================
    # RECORD BOOK, COMPARE, FACILITY, SAVES
    # =========================================================================

    @app.route('/record-book')
    def record_book():
        """Cage Dynasty record book — all-time stats and records."""
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

    @app.route('/hall-of-fame')
    def hall_of_fame():
        """Standalone Hall of Fame — museum-feel surface for HOF1 data."""
        bridge = get_bridge()
        inductees = []
        if bridge.game_started:
            try:
                rb = bridge.get_record_book() if hasattr(
                    bridge, 'get_record_book') else {}
                inductees = rb.get('hof_inductees', []) or []
            except Exception:
                inductees = []
        return render_template('hall_of_fame.html',
            inductees=inductees,
            week=bridge.week_number if bridge.game_started else 0,
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

    @app.route('/facility/equipment/buy', methods=['POST'])
    def buy_equipment():
        """Purchase or upgrade a piece of equipment."""
        bridge = get_bridge()
        eq_type = request.form.get('eq_type', '')
        eq_tier = request.form.get('eq_tier', '')
        result = bridge.buy_equipment(eq_type, eq_tier)
        if result.get('success'):
            flash(result.get('message', 'Equipment purchased!'), 'success')
        else:
            flash(result.get('error', 'Could not purchase equipment.'), 'error')
        return redirect(url_for('facility'))

    @app.route('/facility')
    def facility():
        """Camp facility upgrades."""
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('new_game'))
        try:
            fdata = bridge.get_facility_info() if hasattr(bridge, 'get_facility_info') else {}
        except Exception:
            fdata = {}
        coach_status = bridge.get_coach_contract_status()
        if coach_status.get('has_coach'):
            coach_status['trait_display'] = [
                _TRAIT_DISPLAY.get(t, (t.replace('_', ' ').title(), 'personality'))
                for t in coach_status.get('traits', [])
            ]
        # Ship MC1b: surface tier slot limit so the staff grid can show usage
        from game_bridge import COACH_TIER_STAFF_SLOTS, MEDICAL_STAFF_OPTIONS, OVERSEAS_CAMPS
        coach_status['max_slots'] = COACH_TIER_STAFF_SLOTS.get(
            bridge._get_camp_tier(), 1)

        # Ship EC1 C+D — surface medical + overseas state
        player_fighters = bridge.get_player_fighters()
        medical_by_fid = {s['fighter_id']: s
                          for s in bridge.get_medical_staff()}
        overseas_by_fid = {t['fighter_id']: t
                           for t in (bridge._overseas_trips or [])}
        fighter_intel = []
        for f in player_fighters:
            fighter_intel.append({
                'fighter':       f,
                'medical_staff': medical_by_fid.get(f.fighter_id),
                'overseas_trip': overseas_by_fid.get(f.fighter_id),
                'overseas_opts': bridge.get_overseas_options(f.fighter_id),
            })

        # Ship Coach-1: surface player fighter styles so the facility
        # template can render the "✓ Style Match" indicator on each
        # coach card without making it look up fighters itself.
        player_fighter_styles = {
            getattr(f, 'fighting_style', '') for f in player_fighters
            if getattr(f, 'fighting_style', None)
        }

        return render_template('facility.html',
            week=bridge.week_number,
            facility=fdata,
            coach_status=coach_status,
            medical_options=MEDICAL_STAFF_OPTIONS,
            overseas_camps=OVERSEAS_CAMPS,
            fighter_intel=fighter_intel,
            player_fighter_styles=player_fighter_styles,
        )

    @app.route('/medical/hire/<fighter_id>', methods=['POST'])
    def hire_medical_staff(fighter_id):
        """Hire medical staff for a player fighter."""
        bridge = get_bridge()
        staff_key = request.form.get('staff_key', '')
        result = bridge.hire_medical_staff(fighter_id, staff_key)
        if result.get('success'):
            flash(result.get('message', 'Medical staff hired'), 'success')
        else:
            flash(result.get('error', 'Could not hire medical staff'), 'error')
        return redirect(url_for('facility'))

    @app.route('/medical/fire/<fighter_id>', methods=['POST'])
    def fire_medical_staff(fighter_id):
        """Release a fighter's medical staff."""
        bridge = get_bridge()
        result = bridge.fire_medical_staff(fighter_id)
        if result.get('success'):
            flash(result.get('message', 'Medical staff released'), 'success')
        else:
            flash(result.get('error', 'Could not release medical staff'), 'error')
        return redirect(url_for('facility'))

    @app.route('/free-agents')
    def free_agents_market():
        """Free agent market — browse, sort, filter all available FAs."""
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('new_game'))
        if not bridge._game_state:
            return redirect(url_for('new_game'))

        sort_by   = request.args.get('sort', 'ovr')
        wc_filter = request.args.get('wc', '')

        free_agent_ids = bridge._game_state.free_agents or set()
        free_agents = []
        for fid in free_agent_ids:
            f = bridge._game_state.get_fighter(fid)
            if not f or not f.is_active:
                continue
            # Skip if currently in a fighter camp (defensive)
            if f.camp_id:
                continue
            # Optional weight class filter
            wc = getattr(f, 'weight_class', '') or ''
            if wc_filter and wc != wc_filter:
                continue
            war = bridge._fa_bidding_wars.get(fid)
            potential = 0
            try:
                potential = int(bridge._game_state._fighter_data.get(
                    fid, {}).get('potential', 0) or 0)
            except Exception:
                pass
            free_agents.append({
                'fighter_id':    fid,
                'name':          f.name,
                'weight_class':  wc,
                'style':         getattr(f, 'fighting_style', '') or 'Balanced',
                'overall':       int(getattr(f, 'overall_rating', 0) or 0),
                'potential':     potential,
                'wins':          int(getattr(f, 'wins', 0) or 0),
                'losses':        int(getattr(f, 'losses', 0) or 0),
                'age':           int(getattr(f, 'age', 0) or 0),
                'ranking':       bridge._get_fighter_rank(f),
                'is_injured':    bool(
                    bridge._injury_system.has_injuries(fid)
                    if bridge._injury_system else False),
                'personality':   bridge._get_ai_neg_personality(f),
                'has_war':       war is not None,
                'war_weeks_left': (max(0, war.get('deadline_week', 0) - bridge.week_number)
                                   if war else 0),
                'war_offer_count': (len(war.get('offers', []))
                                    if war else 0),
                'war_top_purse': (max((int(o.get('purse', 0))
                                       for o in (war.get('offers', []) if war else [])
                                       if not o.get('is_player')),
                                      default=0)
                                  if war else 0),
            })

        # Sort
        if sort_by == 'age':
            free_agents.sort(key=lambda x: x['age'])
        elif sort_by == 'wins':
            free_agents.sort(key=lambda x: -x['wins'])
        elif sort_by == 'potential':
            free_agents.sort(key=lambda x: -x['potential'])
        else:  # ovr
            free_agents.sort(key=lambda x: -x['overall'])

        weight_classes = [
            'Strawweight','Flyweight','Bantamweight','Featherweight',
            'Lightweight','Welterweight','Middleweight',
            'Light Heavyweight','Heavyweight'
        ]

        return render_template('free_agents.html',
            free_agents=free_agents,
            sort_by=sort_by,
            wc_filter=wc_filter,
            weight_classes=weight_classes,
            balance=bridge._camp_balance,
            week=bridge.week_number,
        )

    @app.route('/free-agents/offer/<fighter_id>', methods=['POST'])
    def submit_fa_offer(fighter_id):
        """Player submits an offer into an active bidding war."""
        bridge = get_bridge()
        try:
            purse           = int(request.form.get('purse', 0))
            contract_fights = int(request.form.get('contract_fights', 3))
            signing_bonus   = int(request.form.get('signing_bonus', 0))
        except (TypeError, ValueError):
            flash("Invalid offer values", "error")
            return redirect(url_for('free_agents_market'))
        result = bridge.submit_player_fa_offer(
            fighter_id, purse, contract_fights, signing_bonus)
        if result.get('success'):
            flash(result.get('message', 'Offer submitted'), 'success')
        else:
            flash(result.get('error', 'Could not submit offer'), 'error')
        return redirect(url_for('free_agents_market'))

    @app.route('/overseas/send/<fighter_id>', methods=['POST'])
    def send_overseas(fighter_id):
        """Send a player fighter on an overseas training camp."""
        bridge = get_bridge()
        camp_tier = request.form.get('camp_tier', '')
        result = bridge.send_overseas(fighter_id, camp_tier)
        if result.get('success'):
            flash(result.get('message', 'Fighter sent abroad'), 'success')
        else:
            flash(result.get('error', 'Could not send fighter'), 'error')
        return redirect(url_for('facility'))

    @app.route('/coach/fire', methods=['POST'])
    def fire_coach():
        """Release a coach. Ship MC1b: accepts optional coach_id POST field
        to target a specific staff member; falls back to head coach."""
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('new_game'))
        coach_id = request.form.get('coach_id') or None
        result = bridge.fire_coach(coach_id=coach_id)
        if result.get('success'):
            flash(result.get('message', 'Coach released.'), 'success')
        else:
            flash(result.get('error', 'Could not release coach.'), 'error')
        return redirect(url_for('facility'))

    @app.route('/coach/designate/<coach_id>', methods=['POST'])
    def designate_head_coach(coach_id):
        """Promote a staff coach to head. Ship MC1b."""
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('new_game'))
        result = bridge.set_head_coach(coach_id)
        if not result.get('success'):
            flash(result.get('error', 'Could not designate head coach.'), 'error')
        return redirect(url_for('facility'))

    @app.route('/coach/hire', methods=['GET', 'POST'])
    def hire_coach_page():
        """Mid-game coach hiring. Ship MC1b: bridge-side persistent market,
        tier slot limits, multi-coach staff."""
        bridge = get_bridge()
        if not bridge.game_started:
            return redirect(url_for('new_game'))

        camp = bridge.get_player_camp()
        tier = camp.tier.upper() if camp and getattr(camp, 'tier', None) else 'GARAGE'
        contract_options = bridge.get_coach_contract_options()
        from game_bridge import COACH_TIER_STAFF_SLOTS
        max_slots = COACH_TIER_STAFF_SLOTS.get(tier, 1)
        slots_used = len(bridge._coaching_staff)

        # Block if staff is already full
        if slots_used >= max_slots:
            flash(f"Staff already full — {tier} tier allows {max_slots} coach{'es' if max_slots != 1 else ''}.", 'error')
            return redirect(url_for('facility'))

        if request.method == 'POST':
            coach_id = request.form.get('coach_id')
            try:
                contract_weeks = int(request.form.get('contract_weeks', contract_options[0]))
            except (TypeError, ValueError):
                contract_weeks = contract_options[0]
            coaches = [_enrich_market_entry(c) for c in bridge.get_coach_market()]
            selected = next((c for c in coaches if c['id'] == coach_id), None)
            if selected:
                result = bridge.hire_coach(selected, contract_weeks)
                if result.get('success'):
                    bridge.remove_from_coach_market(selected['coach_id'])
                    flash(result.get('message', 'Coach signed.'), 'success')
                    return redirect(url_for('facility'))
                else:
                    flash(result.get('error', 'Could not hire coach.'), 'error')
            return redirect(url_for('hire_coach_page'))

        coaches = [_enrich_market_entry(c) for c in bridge.get_coach_market()]
        slot_context = (f"Hiring coach {slots_used + 1} of {max_slots} — "
                        f"{tier} tier")
        return render_template('hire_coach.html',
            coaches=coaches,
            contract_options=contract_options,
            tier=tier,
            slot_context=slot_context,
        )

    @app.route('/manual')
    def manual():
        """Game manual — how to play."""
        return render_template('manual.html')

    @app.route('/saves')
    def saves_menu():
        """Save / load game."""
        bridge = get_bridge()
        saves = bridge.get_web_saves()
        return render_template('saves.html',
            week=bridge.week_number if bridge.game_started else 0,
            saves=saves,
        )

    @app.route('/export/universe')
    def export_universe():
        """Download universe snapshot JSON for external analysis."""
        bridge = get_bridge()
        if not bridge.game_started:
            flash("No game loaded.", "error")
            return redirect(url_for('saves_menu'))
        import json
        data = bridge.get_universe_export()
        from flask import Response
        json_str = json.dumps(data, indent=2, default=str)
        return Response(
            json_str,
            mimetype='application/json',
            headers={
                'Content-Disposition':
                    f'attachment; filename=cage_dynasty_week{bridge._game_state.week_number}.json'
            }
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
            blocking = result.get('blocking_decisions', [])
            if blocking:
                flash(err, "warning")
                return redirect(url_for('champion_injury_decision',
                                        fighter_id=blocking[0]["fighter_id"]))
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
                'ai_fights':      [{
                    'fight_id':      f.get('fight_id',''),
                    'fighter1_name': f.get('fighter1_name',''),
                    'fighter2_name': f.get('fighter2_name',''),
                    'fighter1_id':   f.get('fighter1_id',''),
                    'fighter2_id':   f.get('fighter2_id',''),
                    'winner_name':   f.get('winner_name',''),
                    'loser_name':    f.get('loser_name',''),
                    'method':        f.get('method',''),
                    'weight_class':  f.get('weight_class',''),
                    'card_slot':     f.get('card_slot','').lower() if f.get('card_slot') else '',
                    'is_title_fight':f.get('is_title_fight', False),
                    'is_fotn':       f.get('is_fotn', False),
                } for f in ai_fights],
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

        # Ship K5b: surface challenge resolution news + open negotiations
        # prominently so the player doesn't miss accepted challenges.
        challenge_responses = [
            n for n in bridge.get_news_feed(limit=50)
            if n.category == "signing"
            and n.week >= bridge.week_number
            and any(marker in (n.headline or '')
                    for marker in ['✅', '❌', '⏳'])
        ]
        pending_negotiations = bridge.get_pending_negotiations()

        # Detect if player fight was FOTN
        fotn_player_fight = None
        for fight in recap.get('player_fights', []):
            if fight.get('is_fotn'):
                fotn_player_fight = fight
                break

        fotn_ai_fight = None
        if not fotn_player_fight:
            # Only show AI FOTN banner if player fight wasn't FOTN
            for fight in recap.get('ai_fights', []):
                if fight.get('is_fotn'):
                    fotn_ai_fight = fight
                    break

        # Ship YS1: year-end summary (fires every 52-week boundary)
        year_summary = None
        if bridge.week_number % 52 == 0 and bridge.week_number > 0:
            _ya = bridge.get_yearly_awards() if hasattr(bridge, 'get_yearly_awards') else []
            year_summary = _ya[-1] if _ya else None

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
            fotn_ai_fight=fotn_ai_fight,
            training_report=recap.get('training_report', {}),
            year_summary=year_summary,
            finances={
                'balance':       recap.get('balance', 0),
                'overhead':      recap.get('overhead', 0),
                'weeks_runway':  int(recap.get('balance', 0) / max(recap.get('overhead', 1), 1)),
                'purses_earned': recap.get('purses_earned', 0),
            },
            challenge_responses=challenge_responses,
            pending_negotiations=pending_negotiations,
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

        # Find the fight result + containing event in completed events
        fight_result = None
        fight_event  = None
        for ev in bridge.get_completed_events():
            for f in ev.get('fights', []):
                if f.get('fight_id') == fight_id:
                    fight_result = f
                    fight_event  = ev
                    break
            if fight_result:
                break

        if not fight_result:
            flash("Fight not found.", "error")
            return redirect(url_for('dashboard'))

        # Get commentary lines
        commentary = bridge.get_fight_commentary(fight_id)

        # ── Commentary deduplication ─────────────────────
        # The commentary module can fire the same template
        # multiple times per round (e.g. "Back control for X!
        # This is DANGEROUS!" appearing 6-8 times).
        # Strategy: within a round block, cap any identical
        # line to max 2 appearances. Exception: finish lines
        # and round headers are never suppressed.
        _FINISH_KEYWORDS = {
            'TAP', 'STOP THE FIGHT', 'LIGHTS OUT', 'KO!',
            'KNOCKED DOWN', "AND THAT'S THE ONE",
            'THE FINAL BLOW', 'KILL SHOT', 'WOBBLES',
            'IS IN TROUBLE', 'HERE COMES THE FINISH',
            'POURING IT ON', 'UNLOADS', 'ALL OVER',
            'FINISH', 'stoppage', 'Excellent stoppage',
        }
        _MAX_REPEAT = 2

        def _dedup_commentary(lines):
            """Cap identical lines at _MAX_REPEAT within each
            round block. Round headers reset counts. Finish
            lines never suppressed."""
            result = []
            counts = {}
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    result.append(line)
                    continue
                if (stripped.startswith('===')
                        or stripped.lower().startswith('round ')
                        or stripped.startswith('[Round')):
                    counts = {}
                    result.append(line)
                    continue
                is_key = any(kw in stripped
                             for kw in _FINISH_KEYWORDS)
                if is_key:
                    result.append(line)
                    continue
                count = counts.get(stripped, 0)
                if count < _MAX_REPEAT:
                    result.append(line)
                    counts[stripped] = count + 1
            return result

        commentary = _dedup_commentary(commentary)

        # ── Position-cluster collapse ────────────────────
        # Same dominant-position info often fires from two
        # templates back-to-back. Drop the second.
        _POSITION_KEYWORDS = [
            'BACK MOUNT', 'Back control', 'TRUCK POSITION',
            'truck position', 'full mount', 'MOUNT',
            'takes the back', 'Hooks are in',
        ]
        def _collapse_position_clusters(lines):
            result = []
            prev_pos = None
            for line in lines:
                line_pos = next(
                    (kw for kw in _POSITION_KEYWORDS if kw in line),
                    None
                )
                if line_pos and line_pos == prev_pos:
                    continue
                prev_pos = line_pos if line_pos else None
                result.append(line)
            return result

        commentary = _collapse_position_clusters(commentary)

        # ── Semantic similarity filter ───────────────────
        # Lines describing the same action with different
        # wording still feel repetitive. Group into action
        # signatures, cap each at _MAX_SIG per round.
        _ACTION_CLUSTERS = [
            {
                'keys': ['digs in punches while controlling',
                         'punishes', 'from behind',
                         'short punches to the side',
                         'short shots connect from',
                         'lands short punches to the side',
                         'punishing from back'],
                'sig': 'back_control_strikes',
            },
            {
                'keys': ['protects the head well',
                         'maintains position excellently',
                         'Solid defensive work',
                         'defends the punches while fighting',
                         'controls the wrists',
                         'does an excellent job of tying up'],
                'sig': 'defensive_survival',
            },
            {
                'keys': ['defends the back take attempt',
                         'turns into', 'prevent the back take',
                         'stops the back take',
                         'good awareness from',
                         'Good awareness from'],
                'sig': 'back_take_defense',
            },
            {
                'keys': ['sprawls perfectly',
                         'shows great balance, stuffing',
                         'stuffs the shot',
                         'wrestling defense is on point',
                         'Excellent takedown defense',
                         'stuffing the shot'],
                'sig': 'takedown_defense',
            },
            {
                'keys': ['passes the guard',
                         'guard pass',
                         'slices through the guard',
                         'Excellent guard passing',
                         'SMOOTH transition past the guard',
                         'BEAUTIFUL guard pass'],
                'sig': 'guard_pass',
            },
            {
                'keys': ['secures the clinch',
                         "They're clinched up",
                         'Into the clinch',
                         'ties up with',
                         'Good clinch work',
                         'clinched up'],
                'sig': 'clinch',
            },
            {
                'keys': ['Good ground punches from',
                         'A clean punch gets through',
                         'connects with short punches on the ground',
                         'lands a solid punch from the top',
                         'Ground strikes land',
                         'Short strikes connect from',
                         'finds the mark from the top',
                         'lands from side control',
                         'finds the mark with an elbow from side control',
                         'A sharp elbow connects from side control',
                         'Short strikes connect from'],
                'sig': 'ground_strikes',
            },
            {
                'keys': ['advances to a better position',
                         'improves position beautifully',
                         'SMOOTH transition to a more dominant',
                         'Great positional awareness',
                         'Excellent positional grappling'],
                'sig': 'position_improve',
            },
            {
                'keys': ['frames against the neck',
                         'frames effectively',
                         'frames well to limit',
                         'using the underhook to disrupt',
                         'Good defensive work from',
                         'tucks the chin'],
                'sig': 'defensive_frames',
            },
            {
                'keys': ['circles away beautifully',
                         'uses excellent footwork',
                         'Smart movement from',
                         'keeps the fight at range',
                         'angles out nicely'],
                'sig': 'footwork',
            },
        ]
        _MAX_SIG = 2

        def _semantic_dedup(lines):
            result = []
            sig_counts = {}

            def _get_sig(line):
                for cluster in _ACTION_CLUSTERS:
                    if any(k in line for k in cluster['keys']):
                        return cluster['sig']
                return None

            for line in lines:
                stripped = line.strip()
                if (stripped.startswith('===')
                        or stripped.lower().startswith('round ')
                        or stripped.startswith('[Round')):
                    sig_counts = {}
                    result.append(line)
                    continue
                is_key = any(kw in stripped
                             for kw in _FINISH_KEYWORDS)
                if is_key:
                    result.append(line)
                    continue
                sig = _get_sig(stripped)
                if sig:
                    count = sig_counts.get(sig, 0)
                    if count < _MAX_SIG:
                        result.append(line)
                        sig_counts[sig] = count + 1
                else:
                    result.append(line)
            return result

        commentary = _semantic_dedup(commentary)

        # Parse commentary into rounds. Ship K1: use the engine's
        # `[Round N: <summary>]` bracketed end-of-round line as the
        # round boundary — round-start lines from the engine are
        # inconsistent (sometimes "Round N", sometimes mid-round prose,
        # sometimes missing). Corner advice between `=== CORNER ===`
        # and `=== /CORNER ===` markers attaches to the round that
        # just closed.
        import re
        ROUND_END_PATTERN = re.compile(r"^\[Round (\d+):", re.IGNORECASE)
        rounds = []
        buffer_lines = []
        in_corner = False
        for line in commentary:
            line = line.strip()
            if not line:
                continue
            if line.startswith('=== CORNER ==='):
                in_corner = True
                continue  # marker not displayed
            if line.startswith('=== /CORNER ==='):
                in_corner = False
                continue  # marker not displayed
            if in_corner:
                if rounds:
                    rounds[-1].setdefault('corner', []).append(line)
                continue
            buffer_lines.append(line)
            m = ROUND_END_PATTERN.match(line)
            if m:
                rounds.append({
                    'num':   int(m.group(1)),
                    'lines': buffer_lines,
                })
                buffer_lines = []

        # Trailing post-final-round content (result line, scorecard
        # hint) attaches to the last round's card.
        if buffer_lines and rounds:
            rounds[-1]['lines'].extend(buffer_lines)
        elif buffer_lines:
            # No `[Round N:` markers detected — fall back to single
            # block so the watch page still renders something.
            rounds = [{'num': 0, 'lines': buffer_lines}]

        # Final safety net for the truly-empty-commentary case
        if not rounds and commentary:
            rounds = [{'num': 0, 'lines': commentary}]

        # Get scorecard if available
        scorecard = fight_result.get('scorecard')

        return render_template('watch_fight.html',
            fight=fight_result,
            event=fight_event,
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

    @app.route('/api/git-pull', methods=['GET'])
    def api_git_pull():
        """Deployment webhook — runs git pull on the PA server.
        Gated by a query-param token. Called by deploy.sh after pushing
        to GitHub so the new code lands on disk before the webapp reload."""
        DEPLOY_TOKEN = "cd_deploy_2026"
        PA_REPO_DIR  = "/home/vandopegaming/cage_dynasty/cage_dynasty_web"

        if request.args.get('token', '') != DEPLOY_TOKEN:
            return jsonify({"status": "error", "message": "invalid token"}), 403

        try:
            result = subprocess.run(
                ['git', 'pull'],
                cwd=PA_REPO_DIR,
                capture_output=True,
                timeout=25,
            )
            stdout = result.stdout.decode('utf-8', errors='replace')
            stderr = result.stderr.decode('utf-8', errors='replace')
            if result.returncode != 0:
                return jsonify({
                    "status": "error",
                    "message": f"git pull exit {result.returncode}: {stderr}",
                    "output": stdout,
                }), 500
            return jsonify({"status": "ok", "output": stdout + stderr})
        except subprocess.TimeoutExpired:
            return jsonify({"status": "error", "message": "git pull timed out after 25s"}), 504
        except Exception as e:
            return jsonify({"status": "error", "message": f"{type(e).__name__}: {e}"}), 500
