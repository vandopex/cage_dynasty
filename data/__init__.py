# data/__init__.py
"""
Cage Dynasty - Data Module

Static data and databases for fighter generation.
"""

from data.name_database import (
    COUNTRY_NAMES,
    get_available_countries,
    get_random_name,
    get_full_name,
    get_random_country,
    generate_unique_name,
    get_database_stats,
)

__all__ = [
    "COUNTRY_NAMES",
    "get_available_countries",
    "get_random_name",
    "get_full_name",
    "get_random_country",
    "generate_unique_name",
    "get_database_stats",
]
