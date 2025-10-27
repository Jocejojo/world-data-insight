""" 
tests/test_analysis.py
Unit tests for analysis functions.
"""
import pandas as pd

from analysis import (
    most_countries_by_continent,
    region_with_largest_area,
    country_highest_life_expectancy,
    subregion_gdp_extremes,
)

# Verify that the function correctly identifies the continent with the highest number of countries.
def test_most_countries_by_continent(sample_df: pd.DataFrame):
    cont, n = most_countries_by_continent(sample_df)
    assert cont == "Africa"
    assert n == 2

# The function should return Africa as the region with the largest combined area (3000 + 4000 = 7000 km²).
def test_region_with_largest_area(sample_df: pd.DataFrame):
    region, total_area = region_with_largest_area(sample_df)
    assert region == "Africa"
    assert abs(total_area - 7000) < 1e-9

# Check that the country with the highest life expectancy is correctly identified.
def test_country_highest_life_expectancy(sample_df: pd.DataFrame):
    country, lifeexp = country_highest_life_expectancy(sample_df)
    assert country == "Alfa"
    assert abs(lifeexp - 80.0) < 1e-9

# Ensure the function returns the subregions with the lowest and highest average GDP per capita, along with their corresponding values.
def test_subregion_gdp_extremes(sample_df: pd.DataFrame):
    sub_min, gdp_min, sub_max, gdp_max = subregion_gdp_extremes(sample_df)
    assert sub_min == "Western Africa" and abs(gdp_min - 1800) < 1e-9
    assert sub_max == "Western Europe" and abs(gdp_max - 50000) < 1e-9
