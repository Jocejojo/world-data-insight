"""
analysis.py
Answer the four required questions on the cleaned dataset.

This module provides:
    most_countries_by_continent(df) -> (continent, count)
        Returns the continent with the largest number of countries.

    region_with_largest_area(df) -> (region_un, sum_area)
        Returns the UN region with the largest total area (km²).

    country_highest_life_expectancy(df) -> (name_long, lifeExp)
        Returns the country with the highest life expectancy.

    subregion_gdp_extremes(df) -> (subregion_min, gdp_min, subregion_max, gdp_max)
        Returns the subregions with the lowest and highest average GDP per capita.

    write_summary_txt(out_path, answers: dict) -> None
        Writes a human-readable summary.txt.

"""

from __future__ import annotations
from pathlib import Path
from typing import Tuple, Dict

import pandas as pd


# Returns the continent with the largest number of countries and its count.
def most_countries_by_continent(df: pd.DataFrame) -> Tuple[str, int]:
    vc = df["continent"].value_counts(dropna=False)
    continent = vc[vc == vc.max()].index[0]
    return str(continent), int(vc.max())

# Returns the region with the largest combined area in sq. km.
def region_with_largest_area(df: pd.DataFrame) -> Tuple[str, float]:
    group = df.groupby("region_un", dropna=False)["area_km2"].sum(numeric_only=True)
    region = group.idxmax()
    return str(region), float(group.loc[region])

# Returns the country has the highest life expectancy.
def country_highest_life_expectancy(df: pd.DataFrame) -> Tuple[str, float]:
    idx = df["lifeExp"].idxmax()
    row = df.loc[idx]
    return str(row["name_long"]), float(row["lifeExp"])

# Returns subregion has the lowest / highest average GDP per capita.
def subregion_gdp_extremes(df: pd.DataFrame) -> Tuple[str, float, str, float]:
    means = df.groupby("subregion", dropna=False)["gdpPercap"].mean(numeric_only=True)
    means = means[means.index.notna()]
    sub_min = means.idxmin()
    sub_max = means.idxmax()
    return str(sub_min), float(means.loc[sub_min]), str(sub_max), float(means.loc[sub_max])

# Write a readable summary file.
def write_summary_txt(out_path: str | Path, answers: Dict[str, object]) -> None:
    out_path = Path(out_path)
    lines = []
    lines.append(f"Continent with the largest number of countries: {answers['continent']} ({answers['continent_count']})")
    lines.append(f"Region with largest combined area in sq. km: {answers['region_un']} ({answers['region_area_km2']:.2f} km2)")
    lines.append(f"Country with highest life expectancy: {answers['country']} ({answers['lifeExp']:.2f} years)")
    lines.append(
        "Subregion with lowest average GDP per capita: "
        f"{answers['subregion_min']} ({answers['gdp_min']:.2f})"
    )
    lines.append(
        "Subregion with highest average GDP per capita: "
        f"{answers['subregion_max']} ({answers['gdp_max']:.2f})"
    )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")