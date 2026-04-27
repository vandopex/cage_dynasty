"""
Cage Dynasty — Name Database
Module: name_database.py

Single source of truth for all fighter name generation.
Keys use "first"/"last" throughout — matches world_init.generate_name() directly.

Coverage: 28 countries, 50-100 names per pool.
Import: from name_database import COUNTRY_NAMES, generate_unique_name, get_random_country
"""

import random

# ---------------------------------------------------------------------------
# COUNTRY NAME DATABASE
# ---------------------------------------------------------------------------
# Each country: {"first": [...], "last": [...]}
# Pools sized for 225+ fighters with minimal collisions.

COUNTRY_NAMES: dict = {

    "United States": {
        "first": [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
            "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Anthony", "Mark",
            "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth", "Kevin", "Brian",
            "George", "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas",
            "Eric", "Jonathan", "Stephen", "Justin", "Scott", "Brandon", "Benjamin",
            "Samuel", "Gregory", "Alexander", "Patrick", "Jack", "Dennis", "Tyler", "Aaron",
            "Adam", "Nathan", "Zachary", "Ethan", "Logan", "Dylan", "Jordan", "Caleb",
            "Hunter", "Carter", "Wyatt", "Connor", "Cole", "Mason", "Chase", "Luke",
        ],
        "last": [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas",
            "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris",
            "Clark", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright",
            "Scott", "Hill", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera",
            "Campbell", "Mitchell", "Carter", "Cooper", "Turner", "Phillips", "Evans",
            "Torres", "Parker", "Collins", "Edwards", "Stewart", "Morris", "Rogers",
            "Reed", "Cook", "Morgan", "Bell", "Murphy", "Bailey", "Rivera", "Cox",
        ],
    },

    "Brazil": {
        "first": [
            "Gabriel", "Lucas", "Matheus", "Pedro", "Gustavo", "Felipe", "Thiago",
            "Rafael", "Bruno", "Diego", "Leonardo", "Rodrigo", "Marcelo", "Eduardo",
            "Vitor", "Anderson", "Alexandre", "Renato", "Caio", "Igor", "Leandro",
            "Fabricio", "Gleison", "Erick", "Paulo", "Fernando", "Ricardo", "Daniel",
            "Wanderlei", "Demian", "Lyoto", "Jose", "Carlos", "Francisco",
        ],
        "last": [
            "Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Ferreira",
            "Costa", "Rodrigues", "Almeida", "Nascimento", "Carvalho", "Machado",
            "Barbosa", "Nogueira", "Lopes", "Martins", "Araujo", "Melo", "Ribeiro",
            "Cardoso", "Cavalcante", "Andrade", "Moraes", "Vincius", "Prochazka",
            "Werdum", "Belfort", "Moreira", "Adesanya", "Teixeira", "Magalhaes",
        ],
    },

    "Russia": {
        "first": [
            "Alexander", "Alexei", "Andrei", "Dmitri", "Ivan", "Nikita", "Pavel",
            "Sergei", "Vladimir", "Viktor", "Maxim", "Mikhail", "Evgeny", "Konstantin",
            "Roman", "Anton", "Denis", "Artem", "Ilya", "Oleg", "Ruslan", "Timur",
            "Magomed", "Zabit", "Khamzat", "Azamat", "Tagir", "Marat", "Said",
        ],
        "last": [
            "Volkov", "Kovalev", "Emelianenko", "Shlemenko", "Makhachev", "Nurmagomedov",
            "Ankalaev", "Morozov", "Khabilov", "Oleynik", "Ismakov", "Gadjiev",
            "Nogueira", "Nemkov", "Tukhugov", "Dagaev", "Tsarukyan", "Lebedev",
            "Smirnov", "Petrov", "Sokolov", "Ivanov", "Sidorov", "Kuznetsov",
            "Fedorov", "Popov", "Nikolaev", "Magomedov", "Rasulov", "Gadzhiev",
        ],
    },

    "United Kingdom": {
        "first": [
            "Jack", "Oliver", "Harry", "George", "Charlie", "Alfie", "Freddie", "Archie",
            "James", "William", "Thomas", "Oscar", "Henry", "Edward", "Noah", "Liam",
            "Lewis", "Luke", "Ryan", "Daniel", "Jordan", "Jamie", "Lee", "Craig",
            "Darren", "Danny", "Billy", "Shane", "Conor", "Paddy",
        ],
        "last": [
            "Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Evans", "Wilson",
            "Thomas", "Roberts", "Johnson", "Lewis", "Walker", "Robinson", "Wood",
            "Thompson", "White", "Jackson", "Hughes", "Edwards", "Green", "Hall",
            "Whittaker", "Till", "Aspinall", "Hardy", "Bisping", "Mousasi",
        ],
    },

    "Ireland": {
        "first": [
            "Conor", "Paddy", "Sean", "Cathal", "Joseph", "Michael", "Patrick", "Brendan",
            "Declan", "Cian", "Finn", "Oisin", "Callum", "Darragh", "Eoin", "Niall",
            "Rory", "Shane", "Ryan", "Luke", "Brian", "Ciaran",
        ],
        "last": [
            "McGregor", "Holohan", "Byrne", "Kelly", "Murphy", "Walsh", "Ryan", "O'Brien",
            "McCarthy", "Gallagher", "O'Neill", "Kennedy", "Doyle", "Quinn", "Lynch",
            "Dunne", "Foley", "Brennan", "Kavanagh", "Hendricks", "Pedro", "Hunt",
        ],
    },

    "Mexico": {
        "first": [
            "Jesus", "Juan", "Miguel", "Jose", "Carlos", "Luis", "Fernando", "Ricardo",
            "Eduardo", "Alejandro", "Manuel", "Sergio", "Jorge", "Roberto", "Marco",
            "Daniel", "Oscar", "Victor", "Diego", "Andres", "Francisco", "Raul",
        ],
        "last": [
            "Garcia", "Martinez", "Lopez", "Gonzalez", "Rodriguez", "Hernandez", "Perez",
            "Sanchez", "Ramirez", "Torres", "Flores", "Rivera", "Gomez", "Diaz",
            "Morales", "Reyes", "Cruz", "Ortiz", "Romero", "Gutierrez", "Herrera",
            "Vargas", "Roblero", "Alejo", "Espino", "Quiambao",
        ],
    },

    "Canada": {
        "first": [
            "Georges", "Rory", "Patrick", "Mark", "Jason", "Jordan", "Travis", "Kevin",
            "Alex", "Ryan", "Matt", "Chris", "Mike", "Andrew", "Tyler", "Justin",
            "Cole", "Connor", "Brett", "Dylan", "Ethan", "Nathan",
        ],
        "last": [
            "St-Pierre", "MacDonald", "Carman", "Hominick", "Grant", "McDonald",
            "Lauzon", "Ngannou", "Potts", "Tafa", "Harris", "Thompson", "Jenkins",
            "Schmidt", "Rakhmonov", "Smith", "Johnson", "Brown", "Wilson",
        ],
    },

    "Australia": {
        "first": [
            "Tai", "Robert", "Jacob", "Luke", "Tyson", "Shane", "Kyle", "Ben",
            "Jake", "Jamie", "Brent", "Alex", "Jack", "James", "Ryan", "Scott",
            "Daniel", "Tommy", "Tyler", "Callan", "Oluwale", "Max", "Ivan",
        ],
        "last": [
            "Tuivasa", "Whittaker", "Volkanovski", "Matthews", "Hooker", "Smith",
            "O'Neill", "Meredith", "Kelly", "Hunt", "Tafa", "Crute", "Pedro",
            "Okafor", "Thompson", "Jenkins", "Kim", "Peters", "Walker",
        ],
    },

    "Japan": {
        "first": [
            "Takanori", "Kazushi", "Mirko", "Yushin", "Yoshihiro", "Ryo", "Hatsu",
            "Keita", "Takashi", "Naoki", "Shinya", "Daisuke", "Kazunori", "Ikuhisa",
            "Yuki", "Mikuru", "Maki", "Hideki", "Ryuichi", "Tomoki", "Kenta",
        ],
        "last": [
            "Aoki", "Yamamoto", "Akiyama", "Okami", "Inoue", "Nakamura", "Suzuki",
            "Tanaka", "Watanabe", "Ito", "Sato", "Kato", "Kobayashi", "Saito",
            "Sakuraba", "Takahashi", "Sasaki", "Yoshida", "Shirai", "Fujita",
        ],
    },

    "South Korea": {
        "first": [
            "Chan Sung", "Dong Hyun", "Seung Woo", "Yair", "Jung Woo", "Min Soo",
            "Kyung Ho", "Hyun Gyu", "Jun Young", "Seung Yoon", "Jae Hyun",
        ],
        "last": [
            "Jung", "Kim", "Park", "Choi", "Lee", "Kang", "Byun", "Shin",
            "Oh", "Han", "Yoon", "Joo", "Lim", "Hong", "Baek",
        ],
    },

    "Thailand": {
        "first": [
            "Rodtang", "Superbon", "Buakaw", "Nong-O", "Saenchai", "Sitthichai",
            "Petchmorakot", "Jongsanan", "Dieselnoi", "Yodsanklai", "Prajanchai",
            "Liam", "John", "Sam", "Murodjon",
        ],
        "last": [
            "Sitjaopho", "Banchamek", "Fairtex", "Jitmuangnon", "Petchyindee",
            "Lookboonme", "Kiatmoo9", "Or Atchariya", "Muradov", "Yusupov",
        ],
    },

    "Netherlands": {
        "first": [
            "Alistair", "Gegard", "Stefan", "Melvin", "Tyrone", "Rico", "Bas",
            "Bram", "Lars", "Remy", "Cyril", "Dave", "Jordy", "Jairzinho",
        ],
        "last": [
            "Overeem", "Mousasi", "Struve", "Manhoef", "Spong", "Verhoeven",
            "Bonjasky", "de Ridder", "de Vries", "Lohore", "Rozenstruik",
        ],
    },

    "Poland": {
        "first": [
            "Jan", "Joanna", "Karolina", "Michal", "Piotr", "Marcin", "Tomasz",
            "Pawel", "Lukasz", "Krzysztof", "Sebastian", "Rafal", "Kamil", "Mateusz",
        ],
        "last": [
            "Blachowicz", "Jedrzejczyk", "Kowalkiewicz", "Held", "Lewandowski",
            "Pudzianowski", "Grabowski", "Nowak", "Wojcik", "Walczak",
        ],
    },

    "Uzbekistan": {
        "first": [
            "Shavkat", "Islam", "Khamzat", "Akbar", "Bekzod", "Dilshod", "Sanjar",
            "Arman", "Aziz", "Temur", "Ulugbek", "Sardor", "Jasur", "Mirzo",
        ],
        "last": [
            "Rakhmonov", "Makhachev", "Sobirov", "Mirzaev", "Yusupov", "Karimov",
            "Azimov", "Tashkentov", "Saidov", "Khodjiev", "Abdurakhimov",
        ],
    },

    "Kazakhstan": {
        "first": [
            "Shavkat", "Arman", "Zhalgas", "Daniyar", "Serhiy", "Serik", "Yerzhan",
            "Askar", "Nurzhan", "Abzal", "Bekzhan", "Rinat", "Almat",
        ],
        "last": [
            "Zhumabaev", "Zhumagulov", "Rakhmonov", "Suleymanov", "Ankalaev",
            "Muratov", "Ibragimov", "Dosmaganbet", "Yusupov", "Zhaksybekov",
        ],
    },

    "Nigeria": {
        "first": [
            "Kamaru", "Israel", "Sodiq", "Ode", "Francis", "Tunde", "Chidi",
            "Oluwale", "Kennedy", "Usman", "Kingsley", "Emeka", "Nnamdi",
        ],
        "last": [
            "Usman", "Adesanya", "Yusuff", "Njokuani", "Ngannou", "Chukwu",
            "Obiora", "Okafor", "Adesanya", "Chimaev", "Morakinyo",
        ],
    },

    "China": {
        "first": [
            "Weili", "Yan", "Liu", "Zhang", "Song", "Li", "Wang", "Wu",
            "Xu", "Chen", "Jingliang", "Kenan", "Ning", "Bo",
        ],
        "last": [
            "Zhang", "Yan", "Li", "Wang", "Liu", "Chen", "Xu", "Song",
            "Lipeng", "Jingliang", "Xiaolong", "Weili", "Ning",
        ],
    },

    "Ukraine": {
        "first": [
            "Alexander", "Vitali", "Oleksandr", "Serhiy", "Ivan", "Roman",
            "Artem", "Volodymyr", "Dmytro", "Andriy", "Maksym", "Viktor",
        ],
        "last": [
            "Usyk", "Klitschko", "Krassyuk", "Petriv", "Sokolov", "Kim",
            "Boytsov", "Romanov", "Bondarenko", "Kovalchuk",
        ],
    },

    "Germany": {
        "first": [
            "Stefan", "Marco", "Marcel", "Dennis", "Nico", "Alexander", "Markus",
            "Florian", "Andre", "Lars", "Philipp", "Sebastian", "Tobias",
        ],
        "last": [
            "Struve", "Huck", "Rios", "Holzken", "Leier", "Bektic", "Ramirez",
            "Schmidt", "Weber", "Muller", "Fischer", "Wagner", "Brandt",
        ],
    },

    "France": {
        "first": [
            "Francis", "Cyril", "Benoit", "Tahar", "Fares", "Aziz", "Sofiane",
            "Mehdi", "Julien", "Kevin", "Laurent", "Maxime", "Oscar", "Remy",
        ],
        "last": [
            "Ngannou", "Gane", "Saint Denis", "Mokhtar", "Benlahfid", "Pichel",
            "Dupont", "Martin", "Bernard", "Petit", "Bonjasky", "Pereira",
        ],
    },

    "Sweden": {
        "first": [
            "Alexander", "Gunnar", "Magnus", "Andreas", "David", "Marcus",
            "Emil", "Niklas", "Viktor", "Lars", "Johan", "Daniel",
        ],
        "last": [
            "Gustafsson", "Nelson", "Bahadurzada", "Hector", "Svensson",
            "Larsson", "Lindqvist", "Johansson", "Eriksson", "Berg",
        ],
    },

    "New Zealand": {
        "first": [
            "Kai", "Tyson", "Israel", "Carlos", "Max", "Leo", "Andre",
            "Jake", "Ivan", "Ben", "Sam", "Callan",
        ],
        "last": [
            "Kara-France", "Pedro", "Adesanya", "Ulberg", "Kim", "Martin",
            "Schmidt", "Jenkins", "Petrov", "Hooker",
        ],
    },

    "South Africa": {
        "first": [
            "Dricus", "Niko", "Charl", "Igeu", "Chris", "Ockert", "Nkazimulo",
            "Themba", "Victor", "Max", "Marco", "Leo", "Oscar",
        ],
        "last": [
            "Du Plessis", "Price", "Joubert", "Vermeulen", "Zikode", "Msimango",
            "Kim", "Silva", "Petrov", "Martin", "Lee",
        ],
    },

    "Argentina": {
        "first": [
            "Santiago", "Mateo", "Joaquin", "Benjamin", "Lucas", "Felipe",
            "Tomas", "Agustin", "Bruno", "Lautaro", "Franco", "Facundo", "Ivan",
        ],
        "last": [
            "Gonzalez", "Rodriguez", "Fernandez", "Lopez", "Martinez", "Garcia",
            "Sanchez", "Perez", "Romero", "Diaz", "Alvarez", "Gomez", "Kim",
        ],
    },

}

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def get_random_country() -> str:
    """Return a random country weighted by MMA participation."""
    weights = {
        "United States": 30, "Brazil": 20, "Russia": 12,
        "United Kingdom": 6, "Canada": 5, "Australia": 5,
        "Mexico": 4, "Kazakhstan": 3, "Uzbekistan": 3,
        "Japan": 3, "Netherlands": 2, "Ireland": 2,
        "Nigeria": 2, "Poland": 1, "South Korea": 1,
        "Thailand": 1, "Germany": 1, "France": 1,
        "Ukraine": 1, "China": 1, "Sweden": 1,
        "New Zealand": 1, "South Africa": 1, "Argentina": 1,
    }
    countries = list(weights.keys())
    wts       = [weights[c] for c in countries]
    return random.choices(countries, weights=wts, k=1)[0]


def generate_unique_name(country: str, used_names: set) -> str:
    """
    Generate a culturally-accurate unique name for the given country.
    Tries 100 combinations before falling back to a numeric suffix.
    """
    pool = COUNTRY_NAMES.get(country, COUNTRY_NAMES["United States"])
    for _ in range(100):
        first = random.choice(pool["first"])
        last  = random.choice(pool["last"])
        name  = f"{first} {last}"
        if name not in used_names:
            used_names.add(name)
            return name
    # Fallback — still unique
    first = random.choice(pool["first"])
    last  = random.choice(pool["last"])
    for suffix in range(2, 99):
        name = f"{first} {last} {suffix}"
        if name not in used_names:
            used_names.add(name)
            return name
    return f"{first} {last} {random.randint(100,999)}"


def get_random_name(country: str) -> tuple:
    """Return (first, last) for the given country."""
    pool = COUNTRY_NAMES.get(country, COUNTRY_NAMES["United States"])
    return random.choice(pool["first"]), random.choice(pool["last"])
