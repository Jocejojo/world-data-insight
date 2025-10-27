""" 
tests/test_cleaning.py
Unit tests for the data-cleaning pipeline

These tests verify that the cleaning function:
    Returns a valid DataFrame and report dictionary
    Produces the expected columns
    Removes duplicates, invalids, and missing identifiers
    Enforces numeric validity and life expectancy bounds
    Correctly computes population density
"""
import math
import pandas as pd
from cleaning import clean_world_data

REQUIRED = {
    "iso_a2","name_long","continent","region_un","subregion","type",
    "area_km2","pop","lifeExp","gdpPercap","pop_density"
}

def test_clean_world_data_core_invariants(raw_df_for_cleaning: pd.DataFrame):
    df_clean, report = clean_world_data(raw_df_for_cleaning, generate_report=True)

    # basic shape and columns
    assert isinstance(df_clean, pd.DataFrame)
    assert REQUIRED.issubset(df_clean.columns)
    assert isinstance(report, dict)

    # no duplicate iso_a2
    assert df_clean["iso_a2"].isna().sum() == 0
    assert df_clean.groupby("iso_a2").size().max() == 1

    # numeric positivity
    assert (df_clean["area_km2"] > 0).all()
    assert (df_clean["pop"] > 0).all()
    assert (df_clean["gdpPercap"] > 0).all()

    # reasonable life expectancy
    assert ((df_clean["lifeExp"] > 0) & (df_clean["lifeExp"] < 120)).all()

    # derived density correct (within floating tolerance)
    dens = (df_clean["pop"] / df_clean["area_km2"]).fillna(math.nan)
    assert (abs(df_clean["pop_density"] - dens) < 1e-9).all()
