"""
tests/conftest.py
Shared pytest configuration and reusable fixtures.

"""
from pathlib import Path
import sys
import pandas as pd
import pytest

# Make "src/" importable
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Small, tidy dataset for testing analysis functions (deterministic answers).
@pytest.fixture
def sample_df() -> pd.DataFrame:
    rows = [
        # iso_a2, name_long, continent, region_un, subregion, type, area_km2, pop, lifeExp, gdpPercap
        ("AA", "Alfa",   "Europe", "Europe", "Western Europe", "Country", 1000, 1_000_000, 80.0, 50_000),
        ("BB", "Bravo",  "Asia",   "Asia",   "Eastern Asia",   "Country", 2000, 2_000_000, 76.0, 30_000),
        ("CC", "Charlie","Africa", "Africa", "Eastern Africa", "Country", 3000, 3_000_000, 60.0,  2_000),
        ("DD", "Delta",  "Africa", "Africa", "Western Africa", "Country", 4000,   500_000, 62.0,  1_800),
    ]
    return pd.DataFrame(rows, columns=[
        "iso_a2","name_long","continent","region_un","subregion","type",
        "area_km2","pop","lifeExp","gdpPercap"
    ])


#Messy input to exercise the cleaning pipeline:
# - duplicate iso_a2
# - invalid nonpositive values
# - extreme lifeExp
# - some NaNs 
@pytest.fixture
def raw_df_for_cleaning() -> pd.DataFrame:
    rows = [
        # duplicate AA (second row has better completeness to test "keep more non-nulls")
        ("AA", "Alfa",   "Europe", "Europe", "Western Europe", "Country", 1000,  1_000_000,  80.0,  50_000),
        ("AA", "Alfa",   "Europe", "Europe", "Western Europe", "Country", 1000,  1_000_000,  None,  50_000),
        # invalids to be dropped/fixed
        ("BB", "Bravo",  "Asia",   "Asia",   "Eastern Asia",   "Country",    0,  2_000_000,  76.0,  30_000),  # area=0 (drop)
        ("CC", "Charlie","Africa", "Africa", "Eastern Africa", "Country", 3000,         -10,  60.0,   2_000),  # pop<=0 (drop)
        ("DD", "Delta",  "Africa", "Africa", "Western Africa", "Country", 4000,    500_000, 140.0,   1_800),  # lifeExp out of range
        ("EE", None,     "Oceania","Oceania","Australia and New Zealand","Country", 7700, 25_000_000,  83.0,  45_000),  # missing name_long (drop)
        (None,"Foxtrot", "Americas","Americas","South America","Country", 8000, 44_000_000,  75.0,  12_000),  # missing iso_a2 (drop)
    ]
    return pd.DataFrame(rows, columns=[
        "iso_a2","name_long","continent","region_un","subregion","type",
        "area_km2","pop","lifeExp","gdpPercap"
    ])
