# systems/camp_generator.py
# Module: Camp Name & Location Generator
# Lines: ~650
#
# Generates realistic, diverse MMA camp names using actual cities
# and culturally-appropriate naming patterns.

"""
Cage Dynasty - Camp Name & Location Generator

Creates authentic-feeling MMA gym names using three templates:
1. Modern Brand: "Apex MMA", "Kinetic Systems", "Syndicate"
2. Team Identity: "Team Ronin", "Team Alpha", "Team Valor"
3. Regional Powerhouse: "Denver Top Team", "Miami Combat Club"

Also supports nationality-specific naming patterns:
- Brazilian: "Nova União", "Chute Boxe São Paulo"
- Thai: "Tiger Muay Thai", "Fairtex Pattaya"
- Russian: "Akhmat Fight Club", "Dagestan MMA"
- Japanese: "Shooto Gym", "Pancrase Yokohama"

USAGE:
    from systems.camp_generator import (
        generate_camp_name,
        generate_camp_with_location,
        get_random_city,
        CampLocation,
    )
    
    # Simple name
    name = generate_camp_name()  # "Apex Systems"
    
    # Name with location
    name, location = generate_camp_with_location(country="Brazil")
    # ("Chute Boxe Rio", CampLocation(city="Rio de Janeiro", country="Brazil", region="South America"))
    
    # Get random city
    city = get_random_city("USA")  # "Las Vegas"
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import random


# ============================================================================
# CITY DATABASE BY COUNTRY
# ============================================================================

CITIES_BY_COUNTRY: Dict[str, List[str]] = {
    # North America
    "USA": [
        "Las Vegas", "Los Angeles", "San Diego", "Sacramento", "San Jose",
        "Albuquerque", "Denver", "Phoenix", "Miami", "Orlando", "Tampa",
        "Atlanta", "Dallas", "Houston", "Austin", "Chicago", "Detroit",
        "New York", "Newark", "Boston", "Philadelphia", "Pittsburgh",
        "Seattle", "Portland", "Salt Lake City", "Minneapolis", "Milwaukee",
        "Kansas City", "St. Louis", "Nashville", "Charlotte", "Raleigh",
        "Long Island", "Brooklyn", "Queens", "The Bronx", "Jersey City",
        "Huntington Beach", "Costa Mesa", "Oceanside", "Fresno", "Stockton",
        "Tucson", "Colorado Springs", "Baltimore", "Jacksonville", "Memphis",
        "Louisville", "Indianapolis", "Columbus", "San Antonio", "El Paso",
    ],
    "Canada": [
        "Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton",
        "Ottawa", "Winnipeg", "Quebec City", "Halifax", "Victoria",
        "Mississauga", "Brampton", "Surrey", "Burnaby", "Richmond",
    ],
    "Mexico": [
        "Mexico City", "Guadalajara", "Tijuana", "Monterrey", "Cancun",
        "Cabo", "Leon", "Puebla", "Juarez", "Queretaro",
        "Hermosillo", "Chihuahua", "Culiacan", "Saltillo", "Merida",
    ],

    # Central America & Caribbean
    "Puerto Rico": [
        "San Juan", "Ponce", "Bayamón", "Carolina", "Caguas",
    ],
    "Cuba": [
        "Havana", "Santiago de Cuba", "Camagüey",
    ],
    "Jamaica": [
        "Kingston", "Montego Bay",
    ],
    "Panama": [
        "Panama City", "Colón",
    ],

    # South America
    "Brazil": [
        "Rio de Janeiro", "São Paulo", "Curitiba", "Belo Horizonte",
        "Salvador", "Fortaleza", "Brasília", "Manaus", "Porto Alegre",
        "Recife", "Florianópolis", "Natal", "Campinas", "Santos",
        "Belém", "Maceió", "Teresina", "Campo Grande", "João Pessoa",
        "Goiânia", "Uberlândia", "Sorocaba", "Ribeirão Preto",
    ],
    "Argentina": [
        "Buenos Aires", "Córdoba", "Rosario", "Mendoza", "La Plata",
        "Tucumán", "Mar del Plata", "Salta", "Santa Fe",
    ],
    "Colombia": [
        "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena",
        "Bucaramanga", "Pereira", "Manizales",
    ],
    "Peru": [
        "Lima", "Arequipa", "Cusco", "Trujillo", "Chiclayo",
    ],
    "Chile": [
        "Santiago", "Valparaíso", "Concepción", "Viña del Mar", "Antofagasta",
    ],
    "Venezuela": [
        "Caracas", "Maracaibo", "Valencia", "Barquisimeto",
    ],
    "Ecuador": [
        "Quito", "Guayaquil", "Cuenca",
    ],
    "Uruguay": [
        "Montevideo", "Punta del Este",
    ],
    "Bolivia": [
        "Santa Cruz", "La Paz", "Cochabamba",
    ],

    # Western Europe
    "UK": [
        "London", "Manchester", "Liverpool", "Birmingham", "Leeds",
        "Glasgow", "Edinburgh", "Belfast", "Cardiff", "Bristol",
        "Nottingham", "Sheffield", "Newcastle", "Brighton", "Oxford",
        "Coventry", "Leicester", "Derby", "Sunderland", "Middlesbrough",
    ],
    "Ireland": [
        "Dublin", "Cork", "Galway", "Limerick", "Waterford",
    ],
    "France": [
        "Paris", "Marseille", "Lyon", "Nice", "Toulouse", "Bordeaux",
        "Strasbourg", "Nantes", "Montpellier", "Lille",
        "Grenoble", "Rennes", "Rouen", "Saint-Etienne", "Toulon",
    ],
    "Germany": [
        "Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne",
        "Düsseldorf", "Stuttgart", "Dortmund", "Leipzig", "Dresden",
        "Hanover", "Nuremberg", "Bochum", "Wuppertal", "Bielefeld",
    ],
    "Netherlands": [
        "Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven",
        "Groningen", "Tilburg", "Almere", "Breda",
    ],
    "Belgium": [
        "Brussels", "Antwerp", "Ghent", "Liège", "Bruges",
    ],
    "Switzerland": [
        "Zurich", "Geneva", "Basel", "Bern", "Lausanne",
    ],
    "Austria": [
        "Vienna", "Graz", "Salzburg", "Innsbruck",
    ],
    "Sweden": [
        "Stockholm", "Gothenburg", "Malmö", "Uppsala", "Linköping",
    ],
    "Norway": [
        "Oslo", "Bergen", "Trondheim", "Stavanger",
    ],
    "Denmark": [
        "Copenhagen", "Aarhus", "Odense",
    ],
    "Finland": [
        "Helsinki", "Tampere", "Turku",
    ],
    "Italy": [
        "Rome", "Milan", "Naples", "Turin", "Florence", "Bologna",
        "Genoa", "Palermo", "Catania", "Bari", "Venice", "Verona",
    ],
    "Spain": [
        "Madrid", "Barcelona", "Valencia", "Seville", "Bilbao", "Malaga",
        "Zaragoza", "Murcia", "Las Palmas", "Alicante", "Córdoba",
    ],
    "Portugal": [
        "Lisbon", "Porto", "Faro", "Coimbra", "Braga",
    ],
    "Greece": [
        "Athens", "Thessaloniki", "Patras", "Heraklion",
    ],

    # Eastern Europe
    "Russia": [
        "Moscow", "St. Petersburg", "Krasnodar", "Yekaterinburg",
        "Novosibirsk", "Chelyabinsk", "Samara", "Kazan", "Rostov",
        "Grozny", "Makhachkala", "Sochi", "Volgograd",
        "Ufa", "Perm", "Omsk", "Krasnoyarsk", "Saratov",
        "Vladivostok", "Irkutsk", "Khabarovsk",
    ],
    "Ukraine": [
        "Kyiv", "Kharkiv", "Odesa", "Lviv", "Dnipro",
        "Donetsk", "Zaporizhzhia", "Mykolaiv", "Vinnytsia",
    ],
    "Poland": [
        "Warsaw", "Kraków", "Łódź", "Wrocław", "Poznań", "Gdańsk",
        "Szczecin", "Bydgoszcz", "Lublin", "Katowice",
    ],
    "Czech Republic": [
        "Prague", "Brno", "Ostrava", "Plzen",
    ],
    "Slovakia": [
        "Bratislava", "Košice", "Prešov",
    ],
    "Hungary": [
        "Budapest", "Debrecen", "Miskolc", "Pécs",
    ],
    "Romania": [
        "Bucharest", "Cluj-Napoca", "Timișoara", "Iași", "Constanța",
    ],
    "Bulgaria": [
        "Sofia", "Plovdiv", "Varna", "Burgas",
    ],
    "Serbia": [
        "Belgrade", "Novi Sad", "Niš", "Kragujevac",
    ],
    "Croatia": [
        "Zagreb", "Split", "Rijeka", "Osijek",
    ],
    "Bosnia": [
        "Sarajevo", "Banja Luka", "Mostar",
    ],
    "Georgia": [
        "Tbilisi", "Batumi", "Kutaisi", "Rustavi",
    ],
    "Armenia": [
        "Yerevan", "Gyumri", "Vanadzor",
    ],
    "Azerbaijan": [
        "Baku", "Ganja", "Sumqayit",
    ],
    "Belarus": [
        "Minsk", "Homel", "Vitebsk", "Grodno",
    ],
    "Moldova": [
        "Chișinău", "Tiraspol",
    ],

    # Caucasus / Central Asia
    "Kazakhstan": [
        "Almaty", "Nur-Sultan", "Shymkent", "Karaganda", "Aktobe",
    ],
    "Uzbekistan": [
        "Tashkent", "Samarkand", "Namangan", "Andijan", "Fergana",
    ],
    "Kyrgyzstan": [
        "Bishkek", "Osh",
    ],
    "Tajikistan": [
        "Dushanbe", "Khujand",
    ],
    "Turkmenistan": [
        "Ashgabat", "Turkmenabat",
    ],
    "Mongolia": [
        "Ulaanbaatar", "Erdenet",
    ],

    # Asia
    "Japan": [
        "Tokyo", "Osaka", "Nagoya", "Yokohama", "Sapporo", "Fukuoka",
        "Kobe", "Kyoto", "Sendai", "Hiroshima", "Okinawa",
        "Saitama", "Chiba", "Kawasaki", "Niigata",
    ],
    "South Korea": [
        "Seoul", "Busan", "Incheon", "Daegu", "Daejeon", "Gwangju",
        "Ulsan", "Suwon", "Changwon", "Goyang",
    ],
    "China": [
        "Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu",
        "Hong Kong", "Macau", "Xi'an", "Hangzhou", "Nanjing",
        "Wuhan", "Tianjin", "Chongqing", "Dongguan", "Shenyang",
        "Harbin", "Kunming", "Dalian", "Qingdao",
    ],
    "Thailand": [
        "Bangkok", "Phuket", "Pattaya", "Chiang Mai", "Koh Samui",
        "Hua Hin", "Krabi", "Hat Yai", "Nakhon Ratchasima",
    ],
    "Vietnam": [
        "Ho Chi Minh City", "Hanoi", "Da Nang", "Hai Phong", "Can Tho",
    ],
    "Philippines": [
        "Manila", "Cebu", "Davao", "Quezon City", "Makati",
        "Zamboanga", "Cagayan de Oro", "General Santos", "Bacolod",
    ],
    "Indonesia": [
        "Jakarta", "Bali", "Surabaya", "Bandung",
        "Medan", "Makassar", "Palembang", "Semarang",
    ],
    "Singapore": [
        "Singapore",
    ],
    "Malaysia": [
        "Kuala Lumpur", "Penang", "Johor Bahru", "Ipoh", "Kota Kinabalu",
    ],
    "Myanmar": [
        "Yangon", "Mandalay", "Naypyidaw",
    ],
    "Cambodia": [
        "Phnom Penh", "Siem Reap",
    ],
    "Laos": [
        "Vientiane", "Luang Prabang",
    ],
    "India": [
        "Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad",
        "Pune", "Ahmedabad", "Surat", "Jaipur", "Lucknow", "Chandigarh",
    ],
    "Pakistan": [
        "Karachi", "Lahore", "Islamabad", "Rawalpindi", "Peshawar",
    ],
    "Bangladesh": [
        "Dhaka", "Chittagong", "Khulna",
    ],
    "Sri Lanka": [
        "Colombo", "Kandy",
    ],
    "Nepal": [
        "Kathmandu", "Pokhara",
    ],

    # Middle East
    "UAE": [
        "Dubai", "Abu Dhabi", "Sharjah", "Al Ain",
    ],
    "Bahrain": [
        "Manama",
    ],
    "Saudi Arabia": [
        "Riyadh", "Jeddah", "Dammam", "Mecca", "Medina",
    ],
    "Kuwait": [
        "Kuwait City",
    ],
    "Qatar": [
        "Doha",
    ],
    "Jordan": [
        "Amman", "Zarqa", "Irbid",
    ],
    "Lebanon": [
        "Beirut", "Tripoli",
    ],
    "Israel": [
        "Tel Aviv", "Jerusalem", "Haifa", "Be'er Sheva",
    ],
    "Turkey": [
        "Istanbul", "Ankara", "Izmir", "Antalya", "Bursa",
        "Adana", "Gaziantep", "Konya", "Mersin",
    ],
    "Iran": [
        "Tehran", "Isfahan", "Shiraz", "Tabriz", "Mashhad", "Ahvaz",
    ],
    "Iraq": [
        "Baghdad", "Basra", "Mosul", "Erbil",
    ],

    # Africa
    "South Africa": [
        "Johannesburg", "Cape Town", "Durban", "Pretoria",
        "Port Elizabeth", "Bloemfontein", "East London",
    ],
    "Nigeria": [
        "Lagos", "Abuja", "Ibadan", "Kano", "Port Harcourt",
        "Benin City", "Kaduna", "Enugu",
    ],
    "Egypt": [
        "Cairo", "Alexandria", "Giza", "Sharm el-Sheikh", "Luxor",
    ],
    "Morocco": [
        "Casablanca", "Marrakech", "Rabat", "Fes", "Tangier", "Agadir",
    ],
    "Kenya": [
        "Nairobi", "Mombasa", "Kisumu", "Nakuru",
    ],
    "Cameroon": [
        "Douala", "Yaoundé", "Garoua",
    ],
    "Ghana": [
        "Accra", "Kumasi", "Takoradi",
    ],
    "Ethiopia": [
        "Addis Ababa", "Dire Dawa", "Gondar",
    ],
    "Tanzania": [
        "Dar es Salaam", "Dodoma", "Mwanza",
    ],
    "Uganda": [
        "Kampala", "Gulu",
    ],
    "Senegal": [
        "Dakar", "Thiès",
    ],
    "Ivory Coast": [
        "Abidjan", "Bouaké", "Daloa",
    ],
    "Angola": [
        "Luanda", "Huambo",
    ],
    "Mozambique": [
        "Maputo", "Beira",
    ],
    "Zambia": [
        "Lusaka", "Ndola",
    ],
    "Zimbabwe": [
        "Harare", "Bulawayo",
    ],
    "Tunisia": [
        "Tunis", "Sfax", "Sousse",
    ],
    "Algeria": [
        "Algiers", "Oran", "Constantine",
    ],

    # Oceania
    "Australia": [
        "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
        "Gold Coast", "Newcastle", "Canberra", "Darwin", "Hobart",
        "Wollongong", "Geelong", "Townsville", "Cairns",
    ],
    "New Zealand": [
        "Auckland", "Wellington", "Christchurch", "Hamilton",
        "Tauranga", "Dunedin", "Palmerston North",
    ],
    "Fiji": [
        "Suva", "Nadi",
    ],
    "Papua New Guinea": [
        "Port Moresby", "Lae",
    ],
    "Samoa": [
        "Apia",
    ],
    "Tonga": [
        "Nuku'alofa",
    ],
}

# Map countries to regions
COUNTRY_TO_REGION: Dict[str, str] = {
    # North America
    "USA": "North America", "Canada": "North America", "Mexico": "North America",
    "Puerto Rico": "North America", "Cuba": "North America",
    "Jamaica": "North America", "Panama": "Central America",
    # South America
    "Brazil": "South America", "Argentina": "South America", "Colombia": "South America",
    "Peru": "South America", "Chile": "South America", "Venezuela": "South America",
    "Ecuador": "South America", "Uruguay": "South America", "Bolivia": "South America",
    # Western Europe
    "UK": "Western Europe", "Ireland": "Western Europe", "France": "Western Europe",
    "Germany": "Western Europe", "Netherlands": "Western Europe", "Belgium": "Western Europe",
    "Switzerland": "Western Europe", "Austria": "Western Europe",
    "Italy": "Western Europe", "Spain": "Western Europe", "Portugal": "Western Europe",
    "Greece": "Western Europe",
    # Northern Europe
    "Sweden": "Northern Europe", "Norway": "Northern Europe",
    "Denmark": "Northern Europe", "Finland": "Northern Europe",
    # Eastern Europe
    "Russia": "Eastern Europe", "Ukraine": "Eastern Europe", "Poland": "Eastern Europe",
    "Czech Republic": "Eastern Europe", "Slovakia": "Eastern Europe",
    "Hungary": "Eastern Europe", "Romania": "Eastern Europe", "Bulgaria": "Eastern Europe",
    "Serbia": "Eastern Europe", "Croatia": "Eastern Europe", "Bosnia": "Eastern Europe",
    "Belarus": "Eastern Europe", "Moldova": "Eastern Europe",
    # Caucasus
    "Georgia": "Caucasus", "Armenia": "Caucasus", "Azerbaijan": "Caucasus",
    # Central Asia
    "Kazakhstan": "Central Asia", "Uzbekistan": "Central Asia",
    "Kyrgyzstan": "Central Asia", "Tajikistan": "Central Asia",
    "Turkmenistan": "Central Asia", "Mongolia": "Central Asia",
    # East Asia
    "Japan": "East Asia", "South Korea": "East Asia", "China": "East Asia",
    # Southeast Asia
    "Thailand": "Southeast Asia", "Vietnam": "Southeast Asia",
    "Philippines": "Southeast Asia", "Indonesia": "Southeast Asia",
    "Singapore": "Southeast Asia", "Malaysia": "Southeast Asia",
    "Myanmar": "Southeast Asia", "Cambodia": "Southeast Asia", "Laos": "Southeast Asia",
    # South Asia
    "India": "South Asia", "Pakistan": "South Asia", "Bangladesh": "South Asia",
    "Sri Lanka": "South Asia", "Nepal": "South Asia",
    # Middle East
    "UAE": "Middle East", "Bahrain": "Middle East", "Saudi Arabia": "Middle East",
    "Kuwait": "Middle East", "Qatar": "Middle East", "Jordan": "Middle East",
    "Lebanon": "Middle East", "Israel": "Middle East", "Turkey": "Middle East",
    "Iran": "Middle East", "Iraq": "Middle East",
    # Africa
    "South Africa": "Southern Africa", "Mozambique": "Southern Africa",
    "Zambia": "Southern Africa", "Zimbabwe": "Southern Africa", "Angola": "Southern Africa",
    "Nigeria": "West Africa", "Ghana": "West Africa", "Senegal": "West Africa",
    "Ivory Coast": "West Africa", "Cameroon": "West Africa",
    "Kenya": "East Africa", "Ethiopia": "East Africa", "Tanzania": "East Africa",
    "Uganda": "East Africa",
    "Egypt": "North Africa", "Morocco": "North Africa", "Tunisia": "North Africa",
    "Algeria": "North Africa",
    # Oceania
    "Australia": "Oceania", "New Zealand": "Oceania",
    "Fiji": "Pacific Islands", "Papua New Guinea": "Pacific Islands",
    "Samoa": "Pacific Islands", "Tonga": "Pacific Islands",
}


# ============================================================================
# CITY MMA CULTURE OVERRIDES
# ============================================================================
# Cities with a distinct fighting identity get style weight overrides.
# These stack on top of (and partially replace) the country-level defaults.
# Format: city → {style: weight, ...}
# Weights don't need to sum to 1 — they'll be normalised at call time.

CITY_MMA_CULTURE: Dict[str, Dict[str, float]] = {
    # ── Russia — Dagestan/Chechen wrestling belt ──────────────────
    "Makhachkala":  {"Wrestling": 0.55, "Sambo": 0.30, "MMA Hybrid": 0.15},
    "Grozny":       {"Wrestling": 0.45, "Sambo": 0.35, "MMA Hybrid": 0.20},
    "Khasavyurt":   {"Wrestling": 0.60, "Sambo": 0.30, "MMA Hybrid": 0.10},
    # ── Thailand — Muay Thai heartland ───────────────────────────
    "Phuket":       {"Muay Thai": 0.80, "MMA Hybrid": 0.15, "Kickboxing": 0.05},
    "Chiang Mai":   {"Muay Thai": 0.75, "MMA Hybrid": 0.20, "Kickboxing": 0.05},
    "Pattaya":      {"Muay Thai": 0.65, "MMA Hybrid": 0.25, "Kickboxing": 0.10},
    "Bangkok":      {"Muay Thai": 0.55, "MMA Hybrid": 0.30, "Kickboxing": 0.15},
    # ── Netherlands — Dutch kickboxing schools ────────────────────
    "Amsterdam":    {"Kickboxing": 0.50, "Muay Thai": 0.25, "MMA Hybrid": 0.20, "Boxing": 0.05},
    "Rotterdam":    {"Kickboxing": 0.55, "Muay Thai": 0.20, "MMA Hybrid": 0.20, "Boxing": 0.05},
    "Eindhoven":    {"Kickboxing": 0.50, "MMA Hybrid": 0.30, "Muay Thai": 0.20},
    # ── USA — Regional hotspots ───────────────────────────────────
    "Albuquerque":  {"Wrestling": 0.45, "MMA Hybrid": 0.30, "Boxing": 0.20, "BJJ": 0.05},
    "Las Vegas":    {"MMA Hybrid": 0.45, "Boxing": 0.30, "BJJ": 0.15, "Wrestling": 0.10},
    "San Diego":    {"BJJ": 0.35, "Wrestling": 0.30, "MMA Hybrid": 0.25, "Boxing": 0.10},
    "Los Angeles":  {"BJJ": 0.30, "Boxing": 0.30, "MMA Hybrid": 0.25, "Wrestling": 0.15},
    "New York":     {"Boxing": 0.40, "Wrestling": 0.25, "MMA Hybrid": 0.25, "BJJ": 0.10},
    "Chicago":      {"Wrestling": 0.35, "Boxing": 0.35, "MMA Hybrid": 0.20, "BJJ": 0.10},
    # ── Brazil — BJJ / MMA academies ─────────────────────────────
    "Rio de Janeiro": {"BJJ": 0.55, "MMA Hybrid": 0.30, "Muay Thai": 0.15},
    "São Paulo":    {"BJJ": 0.40, "MMA Hybrid": 0.35, "Muay Thai": 0.15, "Wrestling": 0.10},
    "Curitiba":     {"BJJ": 0.45, "MMA Hybrid": 0.35, "Muay Thai": 0.20},
    # ── Japan — Traditional martial arts + MMA ────────────────────
    "Tokyo":        {"Judo": 0.30, "MMA Hybrid": 0.35, "Karate": 0.20, "BJJ": 0.15},
    "Osaka":        {"Karate": 0.35, "MMA Hybrid": 0.35, "Judo": 0.20, "BJJ": 0.10},
    # ── South Korea ───────────────────────────────────────────────
    "Seoul":        {"Judo": 0.35, "MMA Hybrid": 0.35, "Karate": 0.20, "BJJ": 0.10},
    # ── Oceania ───────────────────────────────────────────────────
    "Auckland":     {"MMA Hybrid": 0.40, "Muay Thai": 0.30, "Wrestling": 0.20, "BJJ": 0.10},
    "Melbourne":    {"MMA Hybrid": 0.35, "Muay Thai": 0.30, "BJJ": 0.25, "Boxing": 0.10},
    # ── Middle East hubs ─────────────────────────────────────────
    "Dubai":        {"MMA Hybrid": 0.40, "Boxing": 0.25, "Wrestling": 0.20, "BJJ": 0.15},
    # ── UK ───────────────────────────────────────────────────────
    "London":       {"Boxing": 0.40, "MMA Hybrid": 0.35, "BJJ": 0.15, "Wrestling": 0.10},
    "Manchester":   {"Boxing": 0.45, "MMA Hybrid": 0.30, "BJJ": 0.15, "Kickboxing": 0.10},
    # ── Ireland ──────────────────────────────────────────────────
    "Dublin":       {"Boxing": 0.50, "MMA Hybrid": 0.35, "BJJ": 0.10, "Wrestling": 0.05},
    # ── Mexico ───────────────────────────────────────────────────
    "Monterrey":    {"Boxing": 0.60, "MMA Hybrid": 0.25, "Wrestling": 0.15},
    "Mexico City":  {"Boxing": 0.55, "Wrestling": 0.25, "MMA Hybrid": 0.20},
    "Tijuana":      {"Boxing": 0.55, "MMA Hybrid": 0.30, "Wrestling": 0.15},
    # ── Poland ───────────────────────────────────────────────────
    "Warsaw":       {"MMA Hybrid": 0.35, "Kickboxing": 0.30, "Wrestling": 0.25, "Boxing": 0.10},
    "Kraków":       {"MMA Hybrid": 0.35, "Kickboxing": 0.35, "Wrestling": 0.20, "Boxing": 0.10},
    # ── Nigeria / West Africa ─────────────────────────────────────
    "Lagos":        {"Boxing": 0.50, "Wrestling": 0.25, "MMA Hybrid": 0.25},
    # ── Georgia / Caucasus ────────────────────────────────────────
    "Tbilisi":      {"Wrestling": 0.45, "Sambo": 0.30, "MMA Hybrid": 0.25},
    # ── Kazakhstan / Central Asia ─────────────────────────────────
    "Almaty":       {"Wrestling": 0.50, "Boxing": 0.25, "Sambo": 0.15, "MMA Hybrid": 0.10},
    "Nur-Sultan":   {"Wrestling": 0.50, "Boxing": 0.25, "MMA Hybrid": 0.25},
}


# ============================================================================
# NEIGHBORING COUNTRY POOLS
# ============================================================================
# When a camp recruits fighters, they draw mostly from their own country,
# secondarily from regional neighbours, and occasionally from further afield.
# Format: country → [(neighbour_country, relative_weight), ...]
# The home country is always implicitly weighted at 1.0 — these are extras.

NEIGHBORING_COUNTRIES: Dict[str, List[Tuple[str, float]]] = {
    # North America
    "USA":          [("Canada", 0.30), ("Mexico", 0.25), ("Brazil", 0.10),
                     ("UK", 0.08), ("Puerto Rico", 0.08)],
    "Canada":       [("USA", 0.50), ("UK", 0.10), ("France", 0.08)],
    "Mexico":       [("USA", 0.35), ("Brazil", 0.15), ("Colombia", 0.10),
                     ("Puerto Rico", 0.10)],
    "Puerto Rico":  [("USA", 0.50), ("Mexico", 0.15), ("Cuba", 0.10),
                     ("Brazil", 0.10)],
    "Cuba":         [("Puerto Rico", 0.25), ("USA", 0.20), ("Mexico", 0.15)],
    # South America
    "Brazil":       [("Argentina", 0.20), ("Colombia", 0.15), ("USA", 0.10),
                     ("Uruguay", 0.08), ("Peru", 0.07)],
    "Argentina":    [("Brazil", 0.30), ("Uruguay", 0.20), ("Chile", 0.15),
                     ("Colombia", 0.10)],
    "Colombia":     [("Brazil", 0.20), ("Venezuela", 0.15), ("Ecuador", 0.12),
                     ("Argentina", 0.10), ("USA", 0.08)],
    "Chile":        [("Argentina", 0.30), ("Brazil", 0.15), ("Peru", 0.15)],
    "Peru":         [("Brazil", 0.20), ("Colombia", 0.18), ("Chile", 0.15),
                     ("Bolivia", 0.10)],
    "Venezuela":    [("Colombia", 0.25), ("Brazil", 0.20), ("USA", 0.10)],
    "Ecuador":      [("Colombia", 0.25), ("Peru", 0.20), ("Brazil", 0.15)],
    "Uruguay":      [("Argentina", 0.40), ("Brazil", 0.30)],
    "Bolivia":      [("Brazil", 0.25), ("Argentina", 0.20), ("Peru", 0.20)],
    # Western Europe
    "UK":           [("Ireland", 0.25), ("France", 0.15), ("Australia", 0.12),
                     ("Nigeria", 0.10), ("Jamaica", 0.08)],
    "Ireland":      [("UK", 0.45), ("USA", 0.15), ("Nigeria", 0.10)],
    "France":       [("Morocco", 0.20), ("Algeria", 0.15), ("Belgium", 0.12),
                     ("Senegal", 0.10), ("UK", 0.10), ("Tunisia", 0.10)],
    "Germany":      [("Netherlands", 0.15), ("Poland", 0.15), ("Austria", 0.10),
                     ("Czech Republic", 0.10), ("Turkey", 0.12)],
    "Netherlands":  [("Belgium", 0.20), ("Germany", 0.15), ("Suriname", 0.10),
                     ("Morocco", 0.12), ("Turkey", 0.10)],
    "Spain":        [("Morocco", 0.15), ("Colombia", 0.12), ("Argentina", 0.10),
                     ("Brazil", 0.10), ("Portugal", 0.12)],
    "Portugal":     [("Brazil", 0.35), ("Cape Verde", 0.12), ("Angola", 0.10),
                     ("Spain", 0.12)],
    "Italy":        [("Romania", 0.15), ("Morocco", 0.10), ("Albania", 0.10),
                     ("Brazil", 0.08)],
    "Sweden":       [("Norway", 0.20), ("Denmark", 0.18), ("Finland", 0.15)],
    "Norway":       [("Sweden", 0.30), ("Denmark", 0.20), ("Finland", 0.10)],
    "Denmark":      [("Sweden", 0.25), ("Norway", 0.20), ("Germany", 0.15)],
    "Finland":      [("Sweden", 0.30), ("Norway", 0.15), ("Russia", 0.10)],
    # Eastern Europe
    "Russia":       [("Kazakhstan", 0.20), ("Ukraine", 0.15), ("Georgia", 0.12),
                     ("Uzbekistan", 0.12), ("Belarus", 0.10)],
    "Ukraine":      [("Russia", 0.30), ("Poland", 0.15), ("Georgia", 0.10),
                     ("Moldova", 0.10)],
    "Poland":       [("Ukraine", 0.20), ("Russia", 0.15), ("Czech Republic", 0.12),
                     ("Germany", 0.10)],
    "Georgia":      [("Russia", 0.25), ("Armenia", 0.20), ("Azerbaijan", 0.15)],
    "Armenia":      [("Russia", 0.25), ("Georgia", 0.20), ("Azerbaijan", 0.15)],
    "Kazakhstan":   [("Russia", 0.30), ("Uzbekistan", 0.20), ("Kyrgyzstan", 0.12)],
    "Uzbekistan":   [("Tajikistan", 0.20), ("Kazakhstan", 0.20), ("Russia", 0.15),
                     ("Kyrgyzstan", 0.12)],
    # Asia
    "Japan":        [("South Korea", 0.20), ("Brazil", 0.15), ("USA", 0.12)],
    "South Korea":  [("Japan", 0.25), ("China", 0.15), ("USA", 0.10)],
    "China":        [("South Korea", 0.15), ("Japan", 0.12), ("Kazakhstan", 0.10),
                     ("Mongolia", 0.10)],
    "Thailand":     [("Myanmar", 0.12), ("Cambodia", 0.10), ("Vietnam", 0.10),
                     ("Laos", 0.08), ("Malaysia", 0.10)],
    "Philippines":  [("USA", 0.20), ("Japan", 0.12), ("South Korea", 0.10),
                     ("Indonesia", 0.10)],
    "Indonesia":    [("Malaysia", 0.15), ("Philippines", 0.12), ("Singapore", 0.10),
                     ("Australia", 0.10)],
    "Australia":    [("New Zealand", 0.25), ("UK", 0.15), ("Fiji", 0.08),
                     ("Papua New Guinea", 0.07), ("Samoa", 0.06), ("Tonga", 0.06)],
    "New Zealand":  [("Australia", 0.35), ("Samoa", 0.12), ("Tonga", 0.10),
                     ("Fiji", 0.08), ("UK", 0.08)],
    # Middle East
    "UAE":          [("Egypt", 0.15), ("Jordan", 0.12), ("Lebanon", 0.10),
                     ("Saudi Arabia", 0.12), ("Pakistan", 0.10)],
    "Turkey":       [("Georgia", 0.12), ("Azerbaijan", 0.12), ("Iran", 0.10),
                     ("Iraq", 0.08)],
    # Africa
    "Nigeria":      [("Ghana", 0.20), ("Cameroon", 0.15), ("UK", 0.12),
                     ("USA", 0.10)],
    "South Africa": [("Zimbabwe", 0.12), ("Mozambique", 0.10), ("Zambia", 0.10),
                     ("UK", 0.10), ("Australia", 0.08)],
    "Morocco":      [("France", 0.25), ("Algeria", 0.20), ("Spain", 0.12),
                     ("Tunisia", 0.10)],
    "Kenya":        [("Uganda", 0.15), ("Tanzania", 0.15), ("Ethiopia", 0.12),
                     ("UK", 0.10)],
    "Egypt":        [("Jordan", 0.15), ("Morocco", 0.12), ("Sudan", 0.10),
                     ("UAE", 0.10)],
}


def get_location_style_weights(city: str, country: str) -> Dict[str, float]:
    """
    Return style probability weights for a specific city/country.
    
    City-level overrides (CITY_MMA_CULTURE) take full precedence where defined.
    Otherwise falls back to country-level weights from COUNTRY_STYLE_MAP
    (imported at call time to avoid circular imports).
    """
    # City-level override first
    if city in CITY_MMA_CULTURE:
        return dict(CITY_MMA_CULTURE[city])

    # Country-level fallback — we replicate the core map here to avoid
    # importing generator.py (circular import risk)
    COUNTRY_DEFAULTS: Dict[str, Dict[str, float]] = {
        "Brazil":        {"BJJ": 0.50, "MMA Hybrid": 0.30, "Muay Thai": 0.15, "Boxing": 0.05},
        "Russia":        {"Sambo": 0.40, "Wrestling": 0.35, "MMA Hybrid": 0.20, "Boxing": 0.05},
        "USA":           {"Wrestling": 0.40, "MMA Hybrid": 0.30, "Boxing": 0.20, "BJJ": 0.10},
        "Netherlands":   {"Kickboxing": 0.45, "Muay Thai": 0.25, "MMA Hybrid": 0.20, "Boxing": 0.10},
        "Thailand":      {"Muay Thai": 0.70, "MMA Hybrid": 0.20, "Kickboxing": 0.10},
        "Japan":         {"Judo": 0.35, "Karate": 0.25, "MMA Hybrid": 0.25, "BJJ": 0.15},
        "Canada":        {"Wrestling": 0.35, "MMA Hybrid": 0.35, "BJJ": 0.20, "Kickboxing": 0.10},
        "Mexico":        {"Boxing": 0.55, "Wrestling": 0.25, "MMA Hybrid": 0.20},
        "UK":            {"Boxing": 0.40, "MMA Hybrid": 0.35, "BJJ": 0.15, "Wrestling": 0.10},
        "Ireland":       {"Boxing": 0.50, "Karate": 0.20, "MMA Hybrid": 0.30},
        "Sweden":        {"MMA Hybrid": 0.40, "Wrestling": 0.25, "Kickboxing": 0.20, "Boxing": 0.15},
        "Germany":       {"Kickboxing": 0.40, "MMA Hybrid": 0.35, "Wrestling": 0.15, "Boxing": 0.10},
        "France":        {"Judo": 0.30, "Kickboxing": 0.25, "MMA Hybrid": 0.30, "Boxing": 0.15},
        "Poland":        {"MMA Hybrid": 0.35, "Wrestling": 0.30, "Kickboxing": 0.25, "Boxing": 0.10},
        "South Korea":   {"Judo": 0.35, "Karate": 0.25, "MMA Hybrid": 0.30, "BJJ": 0.10},
        "China":         {"MMA Hybrid": 0.35, "Wrestling": 0.30, "Kickboxing": 0.25, "Judo": 0.10},
        "Australia":     {"MMA Hybrid": 0.35, "Muay Thai": 0.30, "BJJ": 0.20, "Boxing": 0.15},
        "New Zealand":   {"MMA Hybrid": 0.35, "Muay Thai": 0.30, "Wrestling": 0.20, "BJJ": 0.15},
        "Kazakhstan":    {"Wrestling": 0.50, "Boxing": 0.25, "MMA Hybrid": 0.15, "Sambo": 0.10},
        "Uzbekistan":    {"Wrestling": 0.45, "Boxing": 0.30, "Sambo": 0.15, "MMA Hybrid": 0.10},
        "Nigeria":       {"Boxing": 0.40, "Wrestling": 0.25, "MMA Hybrid": 0.25, "Kickboxing": 0.10},
        "South Africa":  {"MMA Hybrid": 0.40, "Wrestling": 0.25, "Kickboxing": 0.20, "Boxing": 0.15},
        "Georgia":       {"Wrestling": 0.45, "Sambo": 0.30, "MMA Hybrid": 0.25},
        "Armenia":       {"Wrestling": 0.40, "Boxing": 0.30, "Sambo": 0.20, "MMA Hybrid": 0.10},
        "Morocco":       {"Boxing": 0.45, "MMA Hybrid": 0.30, "Kickboxing": 0.25},
        "Ukraine":       {"Boxing": 0.40, "Sambo": 0.25, "Wrestling": 0.25, "MMA Hybrid": 0.10},
        "Philippines":   {"Boxing": 0.55, "MMA Hybrid": 0.25, "Wrestling": 0.12, "BJJ": 0.08},
        "Indonesia":     {"Muay Thai": 0.30, "MMA Hybrid": 0.35, "Pencak Silat": 0.20, "Wrestling": 0.15},
        "Vietnam":       {"Muay Thai": 0.35, "MMA Hybrid": 0.35, "Kickboxing": 0.20, "Wrestling": 0.10},
        "India":         {"Wrestling": 0.45, "MMA Hybrid": 0.30, "Boxing": 0.15, "BJJ": 0.10},
        "Pakistan":      {"Wrestling": 0.50, "Boxing": 0.25, "MMA Hybrid": 0.25},
        "Turkey":        {"Wrestling": 0.45, "Boxing": 0.25, "MMA Hybrid": 0.20, "Kickboxing": 0.10},
        "Cuba":          {"Boxing": 0.65, "Wrestling": 0.20, "MMA Hybrid": 0.15},
        "Puerto Rico":   {"Boxing": 0.55, "MMA Hybrid": 0.25, "Wrestling": 0.20},
        "Colombia":      {"Boxing": 0.35, "MMA Hybrid": 0.35, "BJJ": 0.20, "Wrestling": 0.10},
    }
    return COUNTRY_DEFAULTS.get(country, {"MMA Hybrid": 1.0})


def get_fighter_nationality_pool(
    location: "CampLocation",
    pool_size: int = 12,
) -> List[Tuple[str, float]]:
    """
    Build a weighted nationality pool for fighter recruitment at a given camp.

    A camp in São Paulo will draw:
      ~55% Brazilian fighters
      ~25% from neighbouring South American nations
      ~20% from the rest of the world

    Returns list of (country, weight) tuples, normalised so weights sum to 1.
    """
    home_country = location.country
    neighbours   = NEIGHBORING_COUNTRIES.get(home_country, [])

    # Build raw pool
    pool: Dict[str, float] = {home_country: 1.0}
    for country, weight in neighbours:
        if country in CITIES_BY_COUNTRY:
            pool[country] = pool.get(country, 0) + weight

    # Add a small global tail (any country in the database)
    # Keep this low so home + neighbours dominate
    global_weight = 0.015
    for country in CITIES_BY_COUNTRY:
        if country not in pool:
            pool[country] = global_weight

    # Normalise
    total = sum(pool.values())
    normalised = [(c, w / total) for c, w in pool.items()]
    normalised.sort(key=lambda x: x[1], reverse=True)
    return normalised


def get_random_nationality_for_camp(location: "CampLocation") -> str:
    """
    Pick a single nationality for a fighter being generated at this camp.
    Uses the weighted pool — home country most likely, neighbours secondary.
    """
    pool = get_fighter_nationality_pool(location)
    countries = [c for c, _ in pool]
    weights   = [w for _, w in pool]
    return random.choices(countries, weights=weights, k=1)[0]


# ============================================================================
# NAME COMPONENTS BY TEMPLATE
# ============================================================================

# Template 1: Modern Brand (Corporate/Elite feel)
MODERN_PREFIXES = [
    "Apex", "Zenith", "Fusion", "Catalyst", "Nexus", "Vertex",
    "Summit", "Pinnacle", "Evolve", "Ascend", "Core", "Hybrid",
    "Kinetic", "Syndicate", "Alliance", "Elevation", "Xtreme",
    "Prime", "Elite", "Vanguard", "Vector", "Titan", "Forge",
    "Origin", "Nova", "Primal", "Axis", "Onyx", "Obsidian",
    "Iron", "Steel", "Granite", "Cobalt", "Chrome", "Carbon",
]

MODERN_SUFFIXES = [
    "MMA", "Systems", "Labs", "Performance", "Institute",
    "Academy", "Athletics", "Combat", "Training", "Fitness",
    "Sports", "Center", "Gym", "Factory", "HQ",
]

# Template 2: Team Identity (Brotherhood feel)
TEAM_NOUNS = [
    "Quest", "Alpha", "Solara", "Titan", "Ronin", "Valor",
    "Chaos", "Renegade", "Phantom", "Savage", "Fury", "One",
    "Victory", "Omega", "Legion", "Viper", "Cobra", "Wolf",
    "Bear", "Hawk", "Eagle", "Shark", "Dragon", "Phoenix",
    "Thunder", "Storm", "Lightning", "Blaze", "Inferno",
    "Shadow", "Specter", "Ghost", "Warrior", "Gladiator",
    "Spartan", "Viking", "Samurai", "Ninja", "Predator",
]

# Template 3: Regional Powerhouse suffixes
REGIONAL_SUFFIXES = [
    "Top Team", "Combat Club", "Fight Team", "Fight Club",
    "Kickboxing", "Martial Arts", "MMA", "Combat Sports",
    "Fight Factory", "Training Center", "Fight Academy",
]

# ============================================================================
# NATIONALITY-SPECIFIC TEMPLATES
# ============================================================================

NATIONALITY_TEMPLATES: Dict[str, List[str]] = {
    "Brazil": [
        "{city} Top Team",
        "Nova União {city}",
        "Chute Boxe {city}",
        "{city} Jiu-Jitsu",
        "Brazilian {noun}",
        "Team {city}",
        "{city} Fight Team",
        "Fightzone {city}",
        "{city} Combat",
    ],
    "Thailand": [
        "Tiger {noun}",
        "{city} Muay Thai",
        "Fairtex {city}",
        "Petchyindee {city}",
        "Sitsongpeenong {city}",
        "Evolve {city}",
        "{city} Muay Thai Gym",
    ],
    "Russia": [
        "{city} Fight Club",
        "Akhmat {city}",
        "{city} MMA",
        "Eagles {city}",
        "Fedor Team {city}",
        "Berkut {city}",
        "{city} Sambo",
        "Red Devil {city}",
    ],
    "Japan": [
        "{city} Dojo",
        "Shooto {city}",
        "Pancrase {city}",
        "Krazy Bee {city}",
        "Reversal {city}",
        "Team {noun} {city}",
        "{city} Fight Gym",
        "Killer Bee {city}",
    ],
    "South Korea": [
        "Korean {noun}",
        "Team {city}",
        "{city} MMA",
        "Korea Top Team {city}",
        "Spirit {city}",
    ],
    "China": [
        "{city} Fight Club",
        "China {noun}",
        "Dragon {city}",
        "Tiger {city}",
        "{city} Kung Fu",
        "Wushu {city}",
    ],
    "UK": [
        "{city} Shootfighters",
        "Team {city}",
        "{city} MMA",
        "Next Generation {city}",
        "{city} Fight Academy",
        "GB {noun}",
    ],
    "Ireland": [
        "SBG {city}",
        "Team {city}",
        "{city} MMA",
        "Celtic {noun}",
        "{city} Fight Club",
    ],
    "Netherlands": [
        "{city} Kickboxing",
        "Golden Glory {city}",
        "Mike's Gym {city}",
        "Mejiro {city}",
        "{city} Combat",
    ],
    "Poland": [
        "{city} Fight Club",
        "Ankos {city}",
        "Berkut {city}",
        "{city} MMA",
        "Team {city}",
    ],
    "Mexico": [
        "Lobo {city}",
        "{city} Combat",
        "Bonebreakers {city}",
        "Entram {city}",
        "{city} Fight Team",
    ],
    "Australia": [
        "{city} Combat Club",
        "Team {city}",
        "{city} MMA",
        "{city} Top Team",
        "Aussie {noun}",
    ],
    "New Zealand": [
        "City Kickboxing {city}",
        "{city} MMA",
        "Team {city}",
        "Kiwi {noun}",
    ],
}

# Default template for countries not in the nationality list
DEFAULT_TEMPLATES = [
    "{city} Top Team",
    "{city} MMA",
    "{city} Fight Team",
    "{city} Combat Club",
    "Team {city}",
    "{city} Fight Academy",
    "{city} Martial Arts",
]


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CampLocation:
    """Location information for a camp."""
    city: str
    country: str
    region: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "city": self.city,
            "country": self.country,
            "region": self.region,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "CampLocation":
        return cls(
            city=data.get("city", "Unknown"),
            country=data.get("country", "Unknown"),
            region=data.get("region", "Unknown"),
        )
    
    def __str__(self) -> str:
        return f"{self.city}, {self.country}"


class CampStyle(Enum):
    """The 'flavor' of the camp name."""
    MODERN_BRAND = "modern_brand"      # "Apex Systems", "Kinetic Labs"
    TEAM_IDENTITY = "team_identity"    # "Team Ronin", "Team Alpha"
    REGIONAL = "regional"              # "Denver Top Team", "Miami Fight Club"
    NATIONALITY = "nationality"        # Culture-specific names


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_countries() -> List[str]:
    """Get list of all available countries."""
    return list(CITIES_BY_COUNTRY.keys())


def get_random_country() -> str:
    """Get a random country, weighted towards MMA-heavy nations."""
    weighted_countries = [
        # Tier 1 — MMA powerhouses
        "USA", "USA", "USA", "USA",
        "Brazil", "Brazil", "Brazil",
        "Russia", "Russia",
        # Tier 2 — strong MMA scenes
        "UK", "UK",
        "Japan", "Japan",
        "Canada",
        "Mexico",
        "Poland",
        "Netherlands",
        "Australia",
        "Ireland",
        "South Korea",
        "France",
        "Germany",
        "Kazakhstan",
        "Uzbekistan",
        "Thailand",
        "Georgia",
        # Tier 3 — growing MMA scenes
        "Ukraine",
        "Nigeria",
        "South Africa",
        "New Zealand",
        "Philippines",
        "Sweden",
        "Morocco",
        "Turkey",
        "Armenia",
        "Azerbaijan",
        "Colombia",
        "Argentina",
        "Cuba",
        "Puerto Rico",
        # Tier 4 — emerging / underdog nations
        "India",
        "Indonesia",
        "China",
        "Vietnam",
        "Romania",
        "Serbia",
        "Hungary",
        "Czech Republic",
        "Belgium",
        "Portugal",
        "Kenya",
        "Cameroon",
        "Israel",
        "Italy",
        "Fiji",
        "Samoa",
        "Tonga",
        "Mongolia",
        "Kyrgyzstan",
        "Ecuador",
        "Chile",
        "Jamaica",
        "Panama",
    ]
    return random.choice(weighted_countries)


def get_random_city(country: Optional[str] = None) -> Tuple[str, str]:
    """
    Get a random city.
    
    Args:
        country: Specific country, or None for random
        
    Returns:
        Tuple of (city_name, country_name)
    """
    if country and country in CITIES_BY_COUNTRY:
        city = random.choice(CITIES_BY_COUNTRY[country])
        return (city, country)
    
    # Random country
    country = get_random_country()
    city = random.choice(CITIES_BY_COUNTRY[country])
    return (city, country)


def get_region(country: str) -> str:
    """Get the region for a country."""
    return COUNTRY_TO_REGION.get(country, "Unknown")


def _shorten_city(city: str) -> str:
    """Shorten long city names for camp names."""
    # Map long names to shorter versions
    SHORT_NAMES = {
        "Rio de Janeiro": "Rio",
        "São Paulo": "São Paulo",
        "Belo Horizonte": "Belo",
        "Los Angeles": "LA",
        "New York": "NYC",
        "Las Vegas": "Vegas",
        "San Diego": "San Diego",
        "San Jose": "San Jose",
        "Salt Lake City": "Salt Lake",
        "Mexico City": "Mexico City",
        "St. Petersburg": "St. Pete",
        "Kuala Lumpur": "KL",
        "Hong Kong": "HK",
        "Quezon City": "QC",
    }
    return SHORT_NAMES.get(city, city)


# ============================================================================
# NAME GENERATION FUNCTIONS
# ============================================================================

def generate_modern_brand_name() -> str:
    """
    Generate a modern/corporate style camp name.
    
    Examples: "Apex Systems", "Kinetic Labs", "Syndicate"
    """
    prefix = random.choice(MODERN_PREFIXES)
    
    # 20% chance to be single word (like "Syndicate", "Alliance")
    if random.random() < 0.20:
        return prefix
    
    suffix = random.choice(MODERN_SUFFIXES)
    return f"{prefix} {suffix}"


def generate_team_name() -> str:
    """
    Generate a team identity style name.
    
    Examples: "Team Ronin", "Team Alpha", "Team Valor"
    """
    noun = random.choice(TEAM_NOUNS)
    return f"Team {noun}"


def generate_regional_name(city: str) -> str:
    """
    Generate a regional powerhouse style name.
    
    Examples: "Denver Top Team", "Miami Combat Club"
    """
    short_city = _shorten_city(city)
    suffix = random.choice(REGIONAL_SUFFIXES)
    return f"{short_city} {suffix}"


def generate_nationality_name(city: str, country: str) -> str:
    """
    Generate a culture-specific camp name.
    
    Uses templates appropriate for the country's MMA culture.
    """
    templates = NATIONALITY_TEMPLATES.get(country, DEFAULT_TEMPLATES)
    template = random.choice(templates)
    
    short_city = _shorten_city(city)
    noun = random.choice(TEAM_NOUNS)
    
    return template.format(city=short_city, noun=noun)


def generate_camp_name(
    city: Optional[str] = None,
    country: Optional[str] = None,
    style: Optional[CampStyle] = None,
) -> str:
    """
    Generate a camp name using one of several templates.
    
    Args:
        city: Specific city (for regional/nationality styles)
        country: Specific country (for nationality style)
        style: Force a specific style, or None for random
        
    Returns:
        Generated camp name string
    """
    # Determine style if not specified
    if style is None:
        roll = random.random()
        if city and roll > 0.50:
            # 50% regional/nationality if city provided
            style = CampStyle.NATIONALITY if country else CampStyle.REGIONAL
        elif roll > 0.65:
            style = CampStyle.TEAM_IDENTITY  # 35% team
        else:
            style = CampStyle.MODERN_BRAND  # 65% modern
    
    # Generate based on style
    if style == CampStyle.MODERN_BRAND:
        return generate_modern_brand_name()
    
    elif style == CampStyle.TEAM_IDENTITY:
        return generate_team_name()
    
    elif style == CampStyle.REGIONAL:
        if not city:
            city, _ = get_random_city()
        return generate_regional_name(city)
    
    elif style == CampStyle.NATIONALITY:
        if not city or not country:
            city, country = get_random_city(country)
        return generate_nationality_name(city, country)
    
    # Fallback
    return generate_modern_brand_name()


def generate_camp_with_location(
    country: Optional[str] = None,
    style: Optional[CampStyle] = None,
) -> Tuple[str, CampLocation]:
    """
    Generate a camp name along with its location data.
    
    Args:
        country: Specific country, or None for random
        style: Force a specific style, or None for random
        
    Returns:
        Tuple of (camp_name, CampLocation)
    """
    # Get city and country
    if country:
        city, country = get_random_city(country)
    else:
        city, country = get_random_city()
    
    region = get_region(country)
    location = CampLocation(city=city, country=country, region=region)
    
    # Generate name using location
    name = generate_camp_name(city=city, country=country, style=style)
    
    return (name, location)


def generate_unique_camp_names(
    count: int,
    countries: Optional[List[str]] = None,
) -> List[Tuple[str, CampLocation]]:
    """
    Generate multiple unique camp names with locations.
    
    Args:
        count: Number of camps to generate
        countries: List of countries to use, or None for random
        
    Returns:
        List of (name, CampLocation) tuples
    """
    camps = []
    used_names = set()
    
    attempts = 0
    max_attempts = count * 5  # Prevent infinite loop
    
    while len(camps) < count and attempts < max_attempts:
        attempts += 1
        
        # Pick country
        country = random.choice(countries) if countries else None
        
        # Generate
        name, location = generate_camp_with_location(country=country)
        
        # Check uniqueness
        if name.lower() not in used_names:
            used_names.add(name.lower())
            camps.append((name, location))
    
    return camps


# ============================================================================
# BATCH GENERATION FOR GAME INITIALIZATION
# ============================================================================

def generate_world_camps(
    num_camps: int = 20,
    include_famous_regions: bool = True,
) -> List[Tuple[str, CampLocation]]:
    """
    Generate camps for world initialization with good geographic spread.
    
    Args:
        num_camps: Total number of camps to generate
        include_famous_regions: Ensure representation from MMA hotspots
        
    Returns:
        List of (name, location) tuples
    """
    camps = []
    used_names = set()
    
    # Ensure representation from major MMA regions
    if include_famous_regions and num_camps >= 10:
        priority_countries = [
            "USA", "USA", "USA", "USA",  # Vegas, LA, etc.
            "Brazil", "Brazil",  # Rio, São Paulo
            "Russia",  # Dagestan region
            "Thailand",  # Phuket, Bangkok
            "UK",  # London
            "Japan",  # Tokyo
        ]
        
        for country in priority_countries[:min(len(priority_countries), num_camps // 2)]:
            name, location = generate_camp_with_location(country=country)
            if name.lower() not in used_names:
                used_names.add(name.lower())
                camps.append((name, location))
    
    # Fill remaining with random camps
    while len(camps) < num_camps:
        name, location = generate_camp_with_location()
        if name.lower() not in used_names:
            used_names.add(name.lower())
            camps.append((name, location))
    
    return camps


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Data classes
    "CampLocation",
    "CampStyle",
    
    # Main functions
    "generate_camp_name",
    "generate_camp_with_location",
    "generate_unique_camp_names",
    "generate_world_camps",
    
    # Helper functions
    "get_all_countries",
    "get_random_country",
    "get_random_city",
    "get_region",
    "get_location_style_weights",
    "get_fighter_nationality_pool",
    "get_random_nationality_for_camp",
    
    # Template-specific generators
    "generate_modern_brand_name",
    "generate_team_name",
    "generate_regional_name",
    "generate_nationality_name",
    
    # Data (for reference/customization)
    "CITIES_BY_COUNTRY",
    "COUNTRY_TO_REGION",
    "CITY_MMA_CULTURE",
    "NEIGHBORING_COUNTRIES",
    "MODERN_PREFIXES",
    "MODERN_SUFFIXES",
    "TEAM_NOUNS",
    "REGIONAL_SUFFIXES",
    "NATIONALITY_TEMPLATES",
]


# ============================================================================
# DEMO / TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CAMP NAME GENERATOR DEMO")
    print("=" * 60)
    print()
    
    print("MODERN BRAND STYLE:")
    for _ in range(5):
        print(f"  {generate_modern_brand_name()}")
    print()
    
    print("TEAM IDENTITY STYLE:")
    for _ in range(5):
        print(f"  {generate_team_name()}")
    print()
    
    print("REGIONAL STYLE (USA):")
    for _ in range(5):
        city, _ = get_random_city("USA")
        print(f"  {generate_regional_name(city)}")
    print()
    
    print("NATIONALITY STYLE (Brazil):")
    for _ in range(5):
        city, country = get_random_city("Brazil")
        print(f"  {generate_nationality_name(city, country)}")
    print()
    
    print("NATIONALITY STYLE (Japan):")
    for _ in range(5):
        city, country = get_random_city("Japan")
        print(f"  {generate_nationality_name(city, country)}")
    print()
    
    print("NATIONALITY STYLE (Russia):")
    for _ in range(5):
        city, country = get_random_city("Russia")
        print(f"  {generate_nationality_name(city, country)}")
    print()
    
    print("WORLD INITIALIZATION (20 camps):")
    world_camps = generate_world_camps(20)
    for name, loc in world_camps:
        print(f"  {name:35} ({loc})")
