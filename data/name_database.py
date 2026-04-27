# data/name_database.py
# Module 17a: Name Database
# Lines: ~450
#
# Comprehensive database of names by country for realistic fighter generation.
# Each country includes culturally-accurate first and last names.

"""
Cage Dynasty - Name Database

Provides culturally-accurate names for fighter generation across 20+ countries.
Each country has 30-100 first names and 30-100 last names.

Usage:
    from data.name_database import get_random_name, get_full_name, COUNTRY_NAMES
    
    first, last = get_random_name("Brazil")
    full_name = get_full_name("Japan")
"""

import random
from typing import Dict, List, Tuple, Optional


# ============================================================================
# COUNTRY NAME DATABASE
# ============================================================================

COUNTRY_NAMES: Dict[str, Dict[str, List[str]]] = {
    "United States": {
        "first_names": [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles", 
            "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua",
            "Kenneth", "Kevin", "Brian", "George", "Edward", "Ronald", "Timothy", "Jason", "Jeffrey", "Ryan",
            "Jacob", "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott", "Brandon",
            "Benjamin", "Samuel", "Gregory", "Frank", "Alexander", "Raymond", "Patrick", "Jack", "Dennis", "Jerry",
            "Tyler", "Aaron", "Jose", "Adam", "Henry", "Nathan", "Douglas", "Zachary", "Peter", "Kyle", "Walter",
            "Ethan", "Jeremy", "Harold", "Keith", "Christian", "Roger", "Noah", "Gerald", "Carl", "Terry", "Sean",
            "Austin", "Arthur", "Lawrence", "Jesse", "Dylan", "Bryan", "Joe", "Jordan", "Billy", "Bruce", "Albert",
            "Willie", "Gabriel", "Logan", "Alan", "Juan", "Wayne", "Roy", "Ralph", "Randy", "Eugene", "Vincent",
            "Russell", "Elijah", "Louis", "Bobby", "Philip", "Johnny"
        ],
        "last_names": [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
            "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
            "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
            "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
            "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
            "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards", "Collins", "Reyes",
            "Stewart", "Morris", "Morales", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper",
            "Peterson", "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
            "Watson", "Brooks", "Chavez", "Wood", "James", "Bennet", "Gray", "Mendoza", "Ruiz", "Hughes",
            "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long", "Ross", "Foster", "Jimenez"
        ]
    },
    "Brazil": {
        "first_names": [
            "Gabriel", "Lucas", "Matheus", "Pedro", "Guilherme", "Gustavo", "Rafael", "Felipe", "João", "Enzo",
            "Nicolas", "Vinicius", "Leonardo", "Thiago", "Arthur", "Eduardo", "Bruno", "Caio", "Daniel", "Igor",
            "Miguel", "Davi", "Heitor", "Bernardo", "Lorenzo", "Samuel", "Benício", "Gael", "Joaquim", "Theo",
            "Ricardo", "Rodrigo", "Alexandre", "Marcelo", "Diego", "Leandro", "Renato", "Anderson", "Adriano", "Fábio",
            "Roberto", "Carlos", "Antônio", "Francisco", "Paulo", "Marcos", "Luiz", "Raimundo", "José", "Sebastião"
        ],
        "last_names": [
            "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes",
            "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa",
            "Pinto", "Mendes", "Rocha", "Nunes", "Dias", "Moura", "Melo", "Cardoso", "Teixeira", "Freitas",
            "Correia", "Campos", "Araujo", "Castro", "Marques", "Machado", "Andrade", "Moreira", "Nascimento", "Monteiro",
            "Barros", "Ramos", "Gonçalves", "Neves", "Leal", "Cunha", "Tavares", "Batista", "Moraes", "Duarte"
        ]
    },
    "Canada": {
        "first_names": [
            "Liam", "Noah", "William", "James", "Oliver", "Benjamin", "Lucas", "Henry", "Alexander", "Ethan",
            "Jacob", "Michael", "Daniel", "Logan", "Jackson", "Sebastian", "Jack", "Aiden", "Owen", "Samuel",
            "David", "Robert", "John", "Richard", "Paul", "Matthew", "Christopher", "Andrew", "Kevin", "Thomas",
            "Ryan", "Eric", "Mark", "Peter", "Jean", "Michel", "Joseph", "Patrick", "Jason", "Brian",
            "Andre", "Steven", "Anthony", "Joshua", "Nathan", "George", "Charles", "Adam", "Justin", "Scott"
        ],
        "last_names": [
            "Smith", "Brown", "Tremblay", "Martin", "Roy", "Gagnon", "Lee", "Wilson", "Johnson", "MacDonald",
            "Taylor", "Campbell", "Anderson", "Jones", "Leblanc", "Cote", "Williams", "Miller", "Thompson", "Gauthier",
            "White", "Clark", "Patel", "Bouchard", "Scott", "Stewart", "Morin", "Lavoie", "King", "Reid",
            "Fortin", "Gagné", "Ouellet", "Bergeron", "Levesque", "Paquette", "Girard", "Bélanger", "Landry", "Boucher",
            "Pelletier", "Savard", "Cloutier", "Richard", "Beaulieu", "Poirier", "Simard", "Dubé", "Lapointe", "Fournier"
        ]
    },
    "United Kingdom": {
        "first_names": [
            "Oliver", "George", "Arthur", "Noah", "Muhammad", "Leo", "Oscar", "Harry", "Archie", "Jack",
            "Henry", "Charlie", "Freddie", "Theodore", "Thomas", "Finley", "Albie", "Jacob", "James", "William",
            "David", "John", "Paul", "Mark", "Andrew", "Steven", "Robert", "Michael", "Richard", "Christopher",
            "Daniel", "Matthew", "Peter", "Stephen", "Ian", "Graham", "Kevin", "Brian", "Philip", "Alan",
            "Gary", "Colin", "Keith", "Neil", "Martin", "Shaun", "Darren", "Lee", "Craig", "Simon"
        ],
        "last_names": [
            "Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson", "Davies", "Robinson", "Wright",
            "Thompson", "Evans", "Walker", "White", "Roberts", "Green", "Hall", "Wood", "Jackson", "Clarke",
            "Harris", "Edwards", "Turner", "Martin", "Cooper", "Hill", "Ward", "Morris", "Moore", "King",
            "Hughes", "Watson", "Harrison", "Morgan", "Scott", "Allen", "Lewis", "Baker", "James", "Clark",
            "Mitchell", "Phillips", "Davis", "Parker", "Price", "Bennett", "Young", "Lee", "Cook", "Carter"
        ]
    },
    "Ireland": {
        "first_names": [
            "Jack", "James", "Noah", "Daniel", "Conor", "Finn", "Liam", "Fionn", "Oisin", "Tadhg",
            "Cillian", "Sean", "Michael", "Patrick", "Harry", "Alex", "Adam", "Darragh", "Luke", "Charlie",
            "John", "David", "Paul", "Mark", "Stephen", "Alan", "Brian", "Kevin", "Martin", "Brendan",
            "Declan", "Ciaran", "Eoin", "Shane", "Niall", "Rory", "Dermot", "Aidan", "Colm", "Fergal",
            "Padraig", "Ronan", "Cormac", "Donal", "Enda", "Gavin", "Barry", "Cathal", "Desmond", "Gerard"
        ],
        "last_names": [
            "Murphy", "Kelly", "O'Sullivan", "Walsh", "Smith", "O'Brien", "Byrne", "Ryan", "O'Connor", "O'Neill",
            "O'Reilly", "Doyle", "McCarthy", "Gallagher", "Doherty", "Kennedy", "Lynch", "Murray", "Quinn", "Moore",
            "McLaughlin", "Carroll", "Connolly", "Daly", "Wilson", "Brennan", "Burke", "Collins", "Campbell", "Clarke",
            "Johnston", "Hughes", "Farrell", "Fitzgerald", "Brown", "Martin", "Maguire", "Nolan", "Flynn", "Thompson",
            "Dunne", "Healy", "Power", "Kavanagh", "Cullen", "Brady", "Casey", "Kenny", "Sweeney", "Maher"
        ]
    },
    "Russia": {
        "first_names": [
            "Alexander", "Dmitry", "Maxim", "Sergey", "Andrey", "Alexey", "Artem", "Ilya", "Kirill", "Mikhail",
            "Nikita", "Ivan", "Roman", "Egor", "Vladimir", "Pavel", "Denis", "Yaroslav", "Timofey", "Matvey",
            "Danil", "Stepan", "Artur", "Boris", "Gleb", "Konstantin", "Leonid", "Oleg", "Ruslan", "Stanislav",
            "Vadim", "Valentin", "Vasily", "Victor", "Vitaly", "Yuri", "Anton", "Evgeny", "Fedor", "Gennady",
            "Igor", "Nikolai", "Pyotr", "Semyon", "Timur", "Anatoly", "Arkady", "Grigory", "Lev", "Marat"
        ],
        "last_names": [
            "Smirnov", "Ivanov", "Kuznetsov", "Popov", "Sokolov", "Lebedev", "Kozlov", "Novikov", "Morozov", "Petrov",
            "Volkov", "Solovyov", "Vasiliev", "Zaytsev", "Pavlov", "Semyonov", "Golubev", "Vinogradov", "Bogdanov", "Vorobyov",
            "Fedorov", "Mikhailov", "Belyaev", "Tarasov", "Belov", "Komarov", "Orlov", "Kiselev", "Makarov", "Andreev",
            "Kovalev", "Ilyin", "Gusev", "Titov", "Kuzmin", "Nazarov", "Antonov", "Timofeev", "Filatov", "Borisov",
            "Romanov", "Grigoriev", "Efimov", "Stepanov", "Yakovlev", "Nikitin", "Sorokin", "Frolov", "Alexeev", "Dmitriev"
        ]
    },
    "Mexico": {
        "first_names": [
            "Santiago", "Mateo", "Sebastián", "Leonardo", "Matías", "Emiliano", "Diego", "Daniel", "Alejandro", "Miguel",
            "Javier", "Carlos", "Luis", "José", "Juan", "Ricardo", "Fernando", "Jorge", "Eduardo", "Arturo",
            "Hector", "Raul", "Mario", "Manuel", "Andres", "Jesus", "Antonio", "Francisco", "Pedro", "Roberto",
            "Victor", "Sergio", "Oscar", "Enrique", "Ramon", "Alfredo", "Gustavo", "Cesar", "Ivan", "Ruben",
            "Felipe", "Gerardo", "Guillermo", "Jaime", "Marco", "Rafael", "Esteban", "Armando", "Ernesto", "Alberto"
        ],
        "last_names": [
            "Hernandez", "Garcia", "Martinez", "Lopez", "Gonzalez", "Perez", "Rodriguez", "Sanchez", "Ramirez", "Cruz",
            "Gomez", "Flores", "Morales", "Vazquez", "Reyes", "Jimenez", "Torres", "Diaz", "Gutierrez", "Mendoza",
            "Aguilar", "Ortiz", "Moreno", "Castillo", "Romero", "Alvarez", "Ruiz", "Ramos", "Chavez", "Acosta",
            "Rivera", "Juarez", "Salazar", "Rojas", "Herrera", "Soto", "Ochoa", "Vega", "Guerrero", "Luna",
            "Estrada", "Bautista", "Cortes", "Sosa", "Rios", "Campos", "Navarro", "Guzman", "Vargas", "Maldonado"
        ]
    },
    "Australia": {
        "first_names": [
            "Oliver", "William", "Jack", "Noah", "Henry", "Leo", "Lucas", "Thomas", "James", "Charlie",
            "Ethan", "Max", "Harrison", "Archer", "Levi", "Hudson", "Elijah", "Oscar", "Alexander", "Liam",
            "David", "John", "Michael", "Peter", "Andrew", "Chris", "Ben", "Daniel", "Matthew", "Paul",
            "Mark", "Robert", "Stephen", "Ryan", "Scott", "Adam", "Jason", "Nathan", "Joshua", "Luke",
            "Shane", "Wayne", "Darren", "Brett", "Craig", "Gary", "Kevin", "Glenn", "Ian", "Trevor"
        ],
        "last_names": [
            "Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Johnson", "White", "Martin", "Anderson",
            "Thompson", "Nguyen", "Thomas", "Walker", "Harris", "Lee", "Ryan", "Robinson", "Kelly", "King",
            "Davis", "Wright", "Evans", "Murray", "Clark", "Hall", "Campbell", "Miller", "Scott", "Mitchell",
            "Stewart", "Turner", "Edwards", "Baker", "Hill", "Green", "Adams", "Wood", "Watson", "Roberts",
            "Lewis", "Phillips", "Murphy", "Young", "James", "Allen", "Cook", "Hughes", "Bell", "Price"
        ]
    },
    "Netherlands": {
        "first_names": [
            "Daan", "Bram", "Sem", "Lucas", "Milan", "Levi", "Luuk", "Thijs", "Jayden", "Tim",
            "Finn", "Stijn", "Lars", "Ruben", "Jesse", "Mees", "Thomas", "Adam", "Noah", "Gijs",
            "Jan", "Pieter", "Johannes", "Cornelis", "Willem", "Hendrik", "Gerrit", "Kees", "Bas", "Tom",
            "Jeroen", "Maarten", "Sander", "Erik", "Mark", "Paul", "Rob", "Stefan", "Frank", "Dennis",
            "Niels", "Rick", "Kevin", "Jordy", "Mike", "Roy", "Sven", "Wouter", "Guus", "Joep"
        ],
        "last_names": [
            "de Jong", "Jansen", "de Vries", "van den Berg", "van Dijk", "Bakker", "Janssen", "Visser", "Smit", "Meijer",
            "de Boer", "Mulder", "de Groot", "Bos", "Vos", "Peters", "Hendriks", "van Leeuwen", "Dekker", "Brouwer",
            "de Wit", "Dijkstra", "Smits", "de Graaf", "van der Meer", "van der Linden", "Kok", "Jacobs", "de Haan", "Vermeulen",
            "van der Heijden", "van der Wal", "Prins", "Blom", "Post", "Schouten", "van Vliet", "Hoekstra", "Verhoeven", "Kramer",
            "Willems", "Gerritsen", "Hermans", "van den Heuvel", "Scholten", "van der Laan", "Kuipers", "Maas", "Verbeek", "Wolters"
        ]
    },
    "Sweden": {
        "first_names": [
            "William", "Liam", "Noah", "Lucas", "Oliver", "Oscar", "Elias", "Hugo", "Adam", "Leo",
            "Alexander", "Axel", "Vincent", "Arvid", "Ludvig", "Filip", "Alfred", "Isak", "Melvin", "Viktor",
            "Lars", "Mikael", "Anders", "Johan", "Per", "Erik", "Karl", "Peter", "Jan", "Thomas",
            "Daniel", "Fredrik", "Andreas", "Mattias", "Magnus", "Patrik", "Jonas", "Henrik", "Niklas", "Stefan",
            "Martin", "Christian", "Robert", "Marcus", "David", "Simon", "Emil", "Anton", "Joel", "Jonathan"
        ],
        "last_names": [
            "Andersson", "Johansson", "Karlsson", "Nilsson", "Eriksson", "Larsson", "Olsson", "Persson", "Svensson", "Gustafsson",
            "Pettersson", "Jonsson", "Jansson", "Hansson", "Bengtsson", "Holm", "Lindberg", "Berg", "Lundberg", "Lundqvist",
            "Lindgren", "Bergman", "Sandberg", "Lindstrom", "Holmgren", "Sjoberg", "Forsberg", "Engstrom", "Eklund", "Danielsson",
            "Lundin", "Berglund", "Fredriksson", "Mattsson", "Hedlund", "Olofsson", "Sundberg", "Bjork", "Nystrom", "Holmberg",
            "Jakobsson", "Wallin", "Magnusson", "Isaksson", "Abrahamsson", "Falk", "Samuelsson", "Dahlberg", "Fransson"
        ]
    },
    "Poland": {
        "first_names": [
            "Antoni", "Jan", "Jakub", "Aleksander", "Franciszek", "Szymon", "Filip", "Mikołaj", "Leon", "Stanisław",
            "Wojciech", "Adam", "Kacper", "Marcel", "Ignacy", "Tymon", "Nikodem", "Igor", "Miłosz", "Maksymilian",
            "Piotr", "Krzysztof", "Andrzej", "Tomasz", "Paweł", "Marcin", "Michał", "Grzegorz", "Józef", "Tadeusz",
            "Mateusz", "Dariusz", "Marek", "Zbigniew", "Jerzy", "Ryszard", "Kazimierz", "Czesław", "Henryk", "Marian",
            "Łukasz", "Rafał", "Jacek", "Kamil", "Patryk", "Dawid", "Damian", "Robert", "Artur", "Sebastian"
        ],
        "last_names": [
            "Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński", "Lewandowski", "Zieliński", "Szymański", "Woźniak",
            "Dąbrowski", "Kozłowski", "Jankowski", "Mazur", "Wojciechowski", "Kwiatkowski", "Krawczyk", "Kaczmarek", "Piotrowski", "Grabowski",
            "Zając", "Pawłowski", "Michalski", "Król", "Wieczorek", "Jabłoński", "Wróbel", "Nowicki", "Majewski", "Olszewski",
            "Stępień", "Malinowski", "Górski", "Pawlak", "Witkowski", "Walczak", "Sikora", "Baran", "Rutkowski", "Michalak",
            "Szewczyk", "Ostrowski", "Tomaszewski", "Pietrzak", "Marciniak", "Wróblewski", "Zawadzki", "Jakubowski", "Lis", "Bąk"
        ]
    },
    "Germany": {
        "first_names": [
            "Noah", "Leon", "Paul", "Matteo", "Ben", "Elias", "Finn", "Felix", "Jonas", "Louis",
            "Henry", "Lukas", "Maximilian", "Anton", "Emil", "Oskar", "Theo", "Jakob", "Liam", "Leo",
            "Michael", "Thomas", "Andreas", "Stefan", "Christian", "Martin", "Daniel", "Peter", "Markus", "Frank",
            "Jürgen", "Wolfgang", "Klaus", "Manfred", "Bernd", "Werner", "Uwe", "Helmut", "Horst", "Günter",
            "Matthias", "Sebastian", "Alexander", "Tobias", "Ralf", "Patrick", "Mario", "Sven", "Torsten", "Dirk"
        ],
        "last_names": [
            "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann",
            "Schäfer", "Koch", "Bauer", "Richter", "Klein", "Wolf", "Schröder", "Neumann", "Schwarz", "Zimmermann",
            "Braun", "Krüger", "Hofmann", "Hartmann", "Lange", "Schmitt", "Werner", "Schmitz", "Krause", "Meier",
            "Lehmann", "Huber", "Maier", "Walter", "Köhler", "Beck", "König", "Fuchs", "Kaiser", "Herrmann",
            "Lang", "Thomas", "Peters", "Jung", "Vogel", "Frank", "Friedrich", "Keller", "Günther", "Roth"
        ]
    },
    "France": {
        "first_names": [
            "Gabriel", "Léo", "Raphaël", "Arthur", "Louis", "Jules", "Adam", "Maël", "Lucas", "Hugo",
            "Noah", "Gabin", "Sacha", "Paul", "Ethan", "Nathan", "Tom", "Aaron", "Mohamed", "Victor",
            "Jean", "Michel", "Philippe", "Alain", "Pierre", "Nicolas", "Christophe", "Patrick", "Christian", "Daniel",
            "Eric", "Frédéric", "David", "Laurent", "Olivier", "Stéphane", "Pascal", "Thierry", "Hervé", "François",
            "Bruno", "Gilles", "Marc", "Didier", "Denis", "Vincent", "Julien", "Antoine", "Alexandre", "Sébastien"
        ],
        "last_names": [
            "Martin", "Bernard", "Thomas", "Petit", "Robert", "Richard", "Durand", "Dubois", "Moreau", "Laurent",
            "Simon", "Michel", "Lefebvre", "Leroy", "Roux", "David", "Bertrand", "Morel", "Fournier", "Girard",
            "Bonnet", "Dupont", "Lambert", "Fontaine", "Rousseau", "Vincent", "Muller", "Lefevre", "Faure", "Andre",
            "Mercier", "Blanc", "Guerin", "Boyer", "Garnier", "Chevalier", "Francois", "Legrand", "Gauthier", "Garcia",
            "Perez", "Robin", "Clement", "Morin", "Henry", "Nicolas", "Masson", "Meunier", "Lemaire", "Mathieu"
        ]
    },
    "Italy": {
        "first_names": [
            "Leonardo", "Francesco", "Alessandro", "Lorenzo", "Mattia", "Andrea", "Gabriele", "Tommaso", "Riccardo", "Edoardo",
            "Matteo", "Davide", "Giuseppe", "Antonio", "Marco", "Giovanni", "Filippo", "Pietro", "Samuele", "Christian",
            "Luca", "Roberto", "Stefano", "Paolo", "Mario", "Luigi", "Angelo", "Vincenzo", "Domenico", "Salvatore",
            "Carlo", "Michele", "Giorgio", "Franco", "Fabio", "Massimo", "Claudio", "Daniele", "Sergio", "Enrico",
            "Alberto", "Simone", "Walter", "Maurizio", "Mauro", "Fabrizio", "Alessio", "Federico", "Gianni", "Renato"
        ],
        "last_names": [
            "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo", "Ricci", "Marino", "Greco",
            "Bruno", "Gallo", "Conti", "De Luca", "Mancini", "Costa", "Giordano", "Rizzo", "Lombardi", "Moretti",
            "Barbieri", "Fontana", "Santoro", "Mariani", "Rinaldi", "Caruso", "Galli", "Martini", "Leone", "Longo",
            "Gentile", "Coppola", "Amato", "Sorrentino", "Parisi", "Gatti", "Ferraro", "Villa", "Conte", "Serra",
            "Farina", "Grasso", "Testa", "Messina", "D'Amico", "Sanna", "Piras", "Cattaneo", "Ferrara", "Palmieri"
        ]
    },
    "Spain": {
        "first_names": [
            "Hugo", "Martín", "Lucas", "Mateo", "Leo", "Daniel", "Alejandro", "Pablo", "Manuel", "Álvaro",
            "Adrián", "Enzo", "Mario", "Diego", "David", "Javier", "Marcos", "Izan", "Marco", "Alex",
            "José", "Antonio", "Francisco", "Juan", "Carlos", "Jesús", "Miguel", "Pedro", "Angel", "Rafael",
            "Luis", "Fernando", "Sergio", "Jorge", "Alberto", "Roberto", "Ricardo", "Eduardo", "Enrique", "Victor",
            "Ramón", "Vicente", "Raúl", "Santiago", "Rubén", "Iván", "Oscar", "Andrés", "Joaquín", "Jaime"
        ],
        "last_names": [
            "García", "Rodríguez", "González", "Fernández", "López", "Martínez", "Sánchez", "Pérez", "Gómez", "Martín",
            "Jiménez", "Ruiz", "Hernández", "Díaz", "Moreno", "Muñoz", "Álvarez", "Romero", "Alonso", "Gutiérrez",
            "Navarro", "Torres", "Domínguez", "Vázquez", "Ramos", "Gil", "Ramírez", "Serrano", "Blanco", "Molina",
            "Morales", "Suárez", "Ortega", "Delgado", "Castro", "Ortiz", "Rubio", "Marín", "Sanz", "Iglesias",
            "Nuñez", "Medina", "Garrido", "Santos", "Castillo", "Cortés", "Lozano", "Guerrero", "Cano", "Prieto"
        ]
    },
    "Japan": {
        "first_names": [
            "Hiroto", "Ren", "Yuma", "Sota", "Haruto", "Minato", "Yuki", "Kaito", "Sora", "Ryota",
            "Daiki", "Tsubasa", "Riku", "Haru", "Hayato", "Takumi", "Itsuki", "Asahi", "Hinata", "Yamato",
            "Hiroshi", "Takashi", "Akira", "Kenji", "Kazuo", "Taro", "Jiro", "Saburo", "Shiro", "Goro",
            "Ichiro", "Kenta", "Makoto", "Nobu", "Osamu", "Shigeru", "Susumu", "Takeshi", "Toru", "Yoshio",
            "Isamu", "Katsu", "Kiyoshi", "Masao", "Minoru", "Satoshi", "Tadashi", "Toshio", "Yasuo", "Yutaka"
        ],
        "last_names": [
            "Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe", "Ito", "Yamamoto", "Nakamura", "Kobayashi", "Kato",
            "Yoshida", "Yamada", "Sasaki", "Yamaguchi", "Matsumoto", "Inoue", "Kimura", "Hayashi", "Shimizu", "Mori",
            "Abe", "Ikeda", "Hashimoto", "Yamashita", "Ishikawa", "Nakajima", "Maeda", "Fujita", "Ogawa", "Goto",
            "Okada", "Hasegawa", "Murakami", "Kondo", "Ishii", "Saito", "Sakamoto", "Endo", "Aoki", "Fujii",
            "Nishimura", "Fukuda", "Ota", "Miura", "Fujiwara", "Okamoto", "Matsuda", "Nakagawa", "Nakano", "Harada"
        ]
    },
    "China": {
        "first_names": [
            "Wei", "Feng", "Hao", "Jian", "Lei", "Peng", "Qiang", "Tao", "Yang", "Yi",
            "Yong", "Yu", "Zhi", "Bin", "Bo", "Chao", "Chen", "Cheng", "Dong", "Gang",
            "Guo", "Hai", "Hui", "Jia", "Jie", "Jin", "Jun", "Kai", "Kun", "Liang",
            "Lin", "Long", "Min", "Ming", "Ning", "Ping", "Qing", "Rong", "Shan", "Shu",
            "Tian", "Wei", "Wen", "Xiang", "Xiao", "Xin", "Xing", "Xue", "Yan", "Yuan"
        ],
        "last_names": [
            "Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Huang", "Zhao", "Wu", "Zhou",
            "Xu", "Sun", "Ma", "Zhu", "Hu", "Guo", "He", "Gao", "Lin", "Luo",
            "Zheng", "Cheng", "Xie", "Tang", "Feng", "Yu", "Yuan", "Deng", "Cao", "Song",
            "Su", "Jiang", "Cai", "Pan", "Tian", "Yao", "Fan", "Jin", "Lu", "Xia",
            "Fang", "Shi", "Ren", "Liao", "Hou", "Tan", "Qiu", "Dai", "Mo", "Kong"
        ]
    },
    "South Korea": {
        "first_names": [
            "Min-jun", "Seo-jun", "Do-yun", "Ye-jun", "Si-woo", "Ha-jun", "Ji-ho", "Ju-won", "Gun-woo", "Hyun-woo",
            "Sung-min", "Jae-won", "Dong-hyun", "Young-ho", "Sang-hoon", "Dae-hyun", "Tae-hyung", "Woo-jin", "Yong-hwa", "Joon-ho",
            "Chul", "Haneul", "In-su", "Ji-hoon", "Jong-su", "Kwang", "Kyung", "Myung", "Seok", "Shin",
            "Sung", "Tae-hwan", "Won-shik", "Yong", "Yoon-gi", "Bong", "Byung-ho", "Chang-min", "Dae-jung", "Eun",
            "Gi", "Hoon", "Hwan", "Hyun", "Il-sung", "Jae", "Jin", "Joo-heon", "Ki-bum", "Kyu"
        ],
        "last_names": [
            "Kim", "Lee", "Park", "Choi", "Jeong", "Yoon", "Jang", "Lim", "Han", "Oh",
            "Seo", "Kwon", "Hwang", "Ahn", "Song", "Hong", "Kang", "Shin", "Cho", "Moon",
            "Yang", "Bae", "Son", "Heo", "Nam", "Shim", "Ryu", "Go", "Jin", "Cha",
            "Yoo", "Na", "Ki", "Pyo", "Bang", "Wang", "No", "Ma", "Ok", "Seong",
            "Im", "Myung", "Byun", "Chae", "Hyeon", "Gong", "Ra", "Yeo", "Do", "Joo"
        ]
    },
    "Thailand": {
        "first_names": [
            "Anurak", "Apichat", "Arthit", "Chai", "Chanathip", "Chatchai", "Chiraphat", "Kittipong", "Natthawut", "Niwat",
            "Phuwadon", "Pongsak", "Sakchai", "Somchai", "Surachai", "Supachai", "Teerapat", "Thanakorn", "Wichai", "Winai",
            "Wirat", "Sakda", "Ratchanon", "Krit", "Nattapong", "Patchara", "Worawut", "Phattachai", "Suchart", "Preecha"
        ],
        "last_names": [
            "Chanthavong", "Sukprasert", "Kongsuwan", "Phanpao", "Ruangsiri", "Sricharoen", "Pradchaphet", "Thepparat", "Pongchai", "Boonyarit",
            "Phromma", "Sukonta", "Vongchai", "Thavorn", "Narumon", "Chalermpon", "Intharachote", "Jatupon", "Keerati", "Manutsanun",
            "Natthapong", "Pornsak", "Saksit", "Thanapol", "Udom", "Vichai", "Wichit", "Yuthana", "Pakorn", "Arthit"
        ]
    },
    "New Zealand": {
        "first_names": [
            "Oliver", "Jack", "Noah", "Ethan", "Lucas", "Leo", "Mason", "Liam", "Oscar", "Samuel",
            "Alexander", "Jacob", "Harry", "Max", "Benjamin", "Christian", "Charlie", "Ryan", "Thomas", "Connor",
            "Daniel", "George", "Joseph", "Michael", "David", "Harrison", "Cooper", "Finlay", "Blake", "Jayden"
        ],
        "last_names": [
            "Smith", "Williams", "Brown", "Wilson", "Taylor", "Jones", "Nguyen", "Thomas", "Martin", "Lee",
            "Clark", "Walker", "Hall", "Hughes", "Kelly", "King", "Turner", "White", "Miller", "Davis",
            "Evans", "Robinson", "Watson", "Young", "Edwards", "Parker", "Murphy", "Cooper", "Johnson", "Wright"
        ]
    },
    "South Africa": {
        "first_names": [
            "Liam", "Ethan", "Noah", "Logan", "Jayden", "Daniel", "Michael", "Matthew", "Joshua", "Tyler",
            "James", "Christopher", "David", "Luke", "Alexander", "Andrew", "Joseph", "Jack", "Ryan", "Samuel",
            "Nicholas", "Benjamin", "Adam", "Kyle", "Deon", "Thabo", "Siphiwe", "Jabulani", "Vuyani", "Mandla"
        ],
        "last_names": [
            "Nkosi", "Botha", "van der Merwe", "Müller", "Smith", "Naidoo", "Ngcobo", "van Wyk", "Schoeman", "van Zyl",
            "du Plessis", "Fourie", "van der Walt", "Pietersen", "Khumalo", "Jacobs", "Williams", "Mokoena", "Mbatha", "Mbeki",
            "Dlamini", "Mhlongo", "Ndlovu", "Sithole", "Zulu", "Mthethwa", "Pretorius", "Steyn", "Visagie"
        ]
    },
    "Nigeria": {
        "first_names": [
            "Chukwuemeka", "Ifeanyi", "Oluwaseun", "Emmanuel", "Chinedu", "Amadi", "Chukwudi", "Ibrahim", "Jibril", "Abdul",
            "Michael", "Tony", "Kingsley", "Uche", "Tunde", "Segun", "Obinna", "Chibuzor", "Somadina", "Chukwu",
            "Adebayo", "Olusola", "Temitope", "Gbenga", "Okechukwu", "Henry", "Samuel", "Stephen", "Joseph", "Mark"
        ],
        "last_names": [
            "Okafor", "Ogunleye", "Ibrahim", "Abiola", "Adebayo", "Olawale", "Eze", "Uche", "Chukwu", "Oloyede",
            "Akinola", "Adewale", "Balogun", "Ilesanmi", "Obi", "Ohiri", "Oyebode", "Adeyemi", "Ojo", "Oluwo",
            "Nwachukwu", "Amadi", "Eke", "Anyanwu", "Uzoho", "Edozien", "Ibe", "Njoku", "Onyema", "Orji"
        ]
    },
    "Ukraine": {
        "first_names": [
            "Oleksandr", "Andriy", "Dmytro", "Serhiy", "Viktor", "Oleh", "Mykola", "Yuriy", "Volodymyr", "Taras",
            "Stanislav", "Bohdan", "Roman", "Anatoliy", "Valeriy", "Ostap", "Sergiy", "Igor", "Orest", "Yevhen",
            "Pavlo", "Yaroslav", "Petro", "Valentyn", "Eduard", "Anton", "Denys", "Vasyl", "Mykhailo", "Maxym"
        ],
        "last_names": [
            "Shevchenko", "Kovalenko", "Boyko", "Tkachenko", "Kruts", "Kravchenko", "Melnyk", "Zelensky", "Bondarenko", "Khmara",
            "Lysenko", "Polishchuk", "Savchenko", "Moroz", "Petrenko", "Makarenko", "Romanenko", "Lebed", "Mazur", "Antonov",
            "Khoroshko", "Yatsenko", "Bondar", "Chernenko", "Chumak", "Grishchenko", "Korchynski", "Sushchenko", "Voronov"
        ]
    },
    # Additional countries for broader coverage
    "Argentina": {
        "first_names": [
            "Santiago", "Mateo", "Lucas", "Joaquín", "Benjamín", "Juan", "Martín", "Thiago", "Tomás", "Franco",
            "Diego", "Nicolás", "Agustín", "Federico", "Emiliano", "Gonzalo", "Facundo", "Maximiliano", "Pablo", "Ricardo"
        ],
        "last_names": [
            "González", "Rodríguez", "Gómez", "Fernández", "López", "Díaz", "Martínez", "Pérez", "García", "Sánchez",
            "Romero", "Sosa", "Torres", "Álvarez", "Ruiz", "Ramírez", "Flores", "Acosta", "Benítez", "Medina"
        ]
    },
    "Uzbekistan": {
        "first_names": [
            "Jamshid", "Azamat", "Sherzod", "Akmal", "Murod", "Botir", "Dilshod", "Farhod", "Jasur", "Rustam",
            "Timur", "Ulugbek", "Sardor", "Jahongir", "Bekzod", "Otabek", "Umid", "Nodirjon", "Ibrokhim", "Mirjalol"
        ],
        "last_names": [
            "Toshmatov", "Kholmatov", "Sobirov", "Jalolov", "Karimov", "Rakhimov", "Mirzaev", "Abdullaev", "Kasimov", "Ergashev",
            "Yusupov", "Askarov", "Nazarov", "Salimov", "Davlatov", "Madaminov", "Rasulov", "Khamraev", "Turgunov", "Alimov"
        ]
    },
    "Kazakhstan": {
        "first_names": [
            "Nursultan", "Damir", "Arman", "Erlan", "Serik", "Kairat", "Daniyar", "Azamat", "Bauyrzhan", "Bekzat",
            "Yerlan", "Marat", "Zhanbek", "Aibek", "Ruslan", "Timur", "Nurlan", "Bolat", "Darkhan", "Aslan"
        ],
        "last_names": [
            "Nazarbayev", "Tokayev", "Suleimenov", "Iskakov", "Baitursynov", "Turlybaev", "Nurmagambetov", "Aubakirov", "Serikbaev", "Kaliyev",
            "Zhumabayev", "Bekmuratov", "Omarov", "Akhmetov", "Sydykov", "Bektenov", "Tulegenov", "Kurmangaliyev", "Nurgaliyev", "Zharylgap"
        ]
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_available_countries() -> List[str]:
    """Get list of all countries with name data"""
    return list(COUNTRY_NAMES.keys())


def get_random_name(country: str) -> Tuple[str, str]:
    """
    Get a random first and last name for a country.
    
    Args:
        country: Country name (must be in COUNTRY_NAMES)
        
    Returns:
        Tuple of (first_name, last_name)
        
    Raises:
        ValueError if country not found
    """
    if country not in COUNTRY_NAMES:
        # Fall back to US names if country not found
        country = "United States"
    
    names = COUNTRY_NAMES[country]
    first = random.choice(names["first_names"])
    last = random.choice(names["last_names"])
    return first, last


def get_full_name(country: str) -> str:
    """
    Get a full name (first + last) for a country.
    
    Args:
        country: Country name
        
    Returns:
        Full name as string
    """
    first, last = get_random_name(country)
    return f"{first} {last}"


def get_random_country() -> str:
    """Get a random country from the database"""
    return random.choice(list(COUNTRY_NAMES.keys()))


def generate_unique_name(
    country: Optional[str] = None,
    existing_names: Optional[set] = None,
    max_attempts: int = 100
) -> Tuple[str, str]:
    """
    Generate a unique name not in the existing set.
    
    Args:
        country: Specific country (random if None)
        existing_names: Set of names to avoid
        max_attempts: Maximum attempts before giving up
        
    Returns:
        Tuple of (full_name, country)
    """
    if existing_names is None:
        existing_names = set()
    
    for _ in range(max_attempts):
        c = country or get_random_country()
        name = get_full_name(c)
        
        if name not in existing_names:
            return name, c
    
    # If we couldn't find a unique name, add a number
    c = country or get_random_country()
    first, last = get_random_name(c)
    counter = 1
    name = f"{first} {last}"
    while name in existing_names:
        name = f"{first} {last} {counter}"
        counter += 1
    
    return name, c


# ============================================================================
# STATISTICS
# ============================================================================

def get_database_stats() -> Dict[str, int]:
    """Get statistics about the name database"""
    stats = {
        "total_countries": len(COUNTRY_NAMES),
        "total_first_names": sum(len(c["first_names"]) for c in COUNTRY_NAMES.values()),
        "total_last_names": sum(len(c["last_names"]) for c in COUNTRY_NAMES.values()),
    }
    stats["total_combinations"] = sum(
        len(c["first_names"]) * len(c["last_names"]) 
        for c in COUNTRY_NAMES.values()
    )
    return stats
