"""
cleaning.py
Data cleaning pipeline for worldData.csv

This module provides:
    clean_world_data(df_raw) -> (df_clean, report: dict) 
        Cleans and prepares the raw dataset: converts types, removes invalid values, imputes missing data, deduplicates by iso_a2, and adds population density.
    
    save_cleaning_report(report, path)
        Saves a human-readable cleaning summary detailing dropped rows, imputations, and key column completeness.

"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


NUMERIC_COLS = ["area_km2", "pop", "lifeExp", "gdpPercap"]
IDENTIFIER_COLS = ["iso_a2", "name_long"]
GROUP_COLS = ["continent", "subregion"]


# --- Helpers ---
# Convert strings like '1,234 ' or ' 5 678' to numeric safely.
def _to_numeric_safe(s: pd.Series) -> pd.Series:
    if s.dtype.kind in "biufc":
        return s
    
    cleaned = (
        s.astype(str)
        .str.replace("\u00a0", " ", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    cleaned = cleaned.replace({"": np.nan, "nan": np.nan, "Nan": np.nan})
    return pd.to_numeric(cleaned, errors="coerce")


# Group-wise median imputation with fallbacks.
def _imputation_groupwise_median(
        df: pd.DataFrame, col: str, groups_priority: List[str]
) -> Tuple[pd.Series, Dict[str, int]]:
    filled = df[col].copy()
    report = {"by_subregion": 0, "by_continent": 0, "by_global": 0}

    missing_idx = filled.isna()
    if not missing_idx.any():
        return filled, report
    
    # subregion
    if "subregion" in groups_priority:
        med_sub = df.groupby("subregion")[col].median(numeric_only=True)
        idx = missing_idx & df["subregion"].notna() & df["subregion"].isin(med_sub.index)
        filled.loc[idx] = df.loc[idx, "subregion"].map(med_sub)
        report["by_subregion"] = int(idx.sum())
        missing_idx = filled.isna()

    # continent
    if "continent" in groups_priority and missing_idx.any():
        med_cont = df.groupby("continent")[col].median(numeric_only=True)
        idx = missing_idx & df["continent"].notna() & df["continent"].isin(med_cont.index)
        filled.loc[idx] = df.loc[idx, "continent"].map(med_cont)
        report["by_continent"] = int(idx.sum())
        missing_idx = filled.isna()

    # global
    if missing_idx.any():
        global_med = df[col].median(numeric_only=True)
        filled.loc[missing_idx] = global_med
        report["by_global"] = int(missing_idx.sum())

    return filled, report


# Given duplicated rows, keep the one with more non null values.
def _choose_row_with_more_non_nulls(rows: pd.DataFrame, important_cols: List[str]) -> pd.Series:
    counts = rows[important_cols].notna().sum(axis=1)
    best_idx = counts.idxmax()
    return rows.loc[best_idx]


# ----- Main cleaning -----

def clean_world_data(df_raw: pd.DataFrame, generate_report: bool = True) -> tuple[pd.DataFrame, dict]:
    report: Dict[str, any] = {"steps": []}

    df = df_raw.copy()

    # Step A: drop rows with missing identifiers
    before = len(df)
    df = df.dropna(subset=IDENTIFIER_COLS, how="any")
    report["dropped_missing_identifiers"] = int(before - len(df))
    report["steps"].append(f"Drop missing identifiers: {report['dropped_missing_identifiers']}")

    # Step B: numeric conversion
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = _to_numeric_safe(df[col])
    report["steps"].append("Converted numeric columns safely")

    # Step C: invalid-value filtering
    # Drop: pop <= 0 / area_km2 <= 0 / gdpPercap <= 0
    # NaN: lifeExp out of (0,120)
    before = len(df)
    invalid_mask = (
        (df["pop"] <= 0) |
        (df["area_km2"] <= 0) |
        (df["gdpPercap"] <= 0)
    )
    invalid_mask = invalid_mask.fillna(False)
    df = df.loc[~invalid_mask].copy()
    report["dropped_invalid_nonpositive"] = int(before - len(df))

    out_of_range = (df["lifeExp"] <= 0) | (df["lifeExp"] >= 120)
    out_of_range = out_of_range.fillna(False)
    if out_of_range.any():
        df.loc[out_of_range, "lifeExp"] = np.nan
        report["lifeExp_out_of_range_set_nan"] = int(out_of_range.sum())
    report["steps"].append("Filtered invalid values and bounded life expectancy")

    # Step D: imputation for lifeExp & gdpPercap
    for col in ["lifeExp", "gdpPercap"]:
        if col in df.columns:
            df[col], counts = _imputation_groupwise_median(df, col, groups_priority=["subregion", "continent"])
            report[f"impute_{col}"] = counts
    report["steps"].append("Imputed lifeExp & gdpPercap via group-wise median with fallbacks")

    # Step E: drop rows still missing critical numeric columns area_km2/pop
    before = len(df)
    df = df.dropna(subset=["area_km2", "pop"])
    report["dropped_missing_area_or_pop"] = int(before - len(df))
    report["steps"].append("Drop rows still missing area_km2 or pop")

    # Step F: deduplicate by iso_a2, keep the one with more non nulls
    before = len(df)
    if df["iso_a2"].duplicated().any():
        kept_rows = []
        for _, group in df.groupby("iso_a2", dropna=False):
            if len(group) == 1:
                kept_rows.append(group.iloc[0])
            else:
                kept_rows.append(_choose_row_with_more_non_nulls(group, important_cols=NUMERIC_COLS))
        df = pd.DataFrame(kept_rows).reset_index(drop=True)
    report["deduplicated_rows"] = int(before - len(df))
    report["steps"].append("Deduplicated by iso_a2 keeping rows with more non-nulls on key metrics")

    # Step G: derive pop_density
    df["pop_density"] = df["pop"] / df["area_km2"]

    # Step H: summary stats report
    if generate_report:
        non_null_ratio = {c: float(df[c].notna().mean()) for c in df.columns}
        stats = df[["area_km2", "pop", "lifeExp", "gdpPercap", "pop_density"]].describe(include="all").to_dict()
        report["non_null_ratio"] = non_null_ratio
        report["stats"] = stats
        report["row_count"] = int(len(df))

    return df, report


#  Save a human-readable cleaning report to path (txt).
def save_cleaning_report(report: dict, path: str | Path) -> None:
    path = Path(path)
    lines: list[str] = []
    lines.append("== Cleaning Report ==")
    lines.append(f"Rows after cleaning: {report.get('row_count', 'N/A')}")
    lines.append("Steps:")
    for s in report.get("steps", []):
        lines.append(f"- {s}")

    # counts
    for k in [
        "dropped_missing_identifiers",
        "dropped_invalid_nonpositive",
        "lifeExp_out_of_range_set_nan",
        "dropped_missing_area_or_pop",
        "deduplicated_rows",
    ]:
        if k in report:
            lines.append(f"{k}: {report[k]}")

    # imputation summary
    for col in ["lifeExp", "gdpPercap"]:
        key = f"impute_{col}"
        if key in report:
            c = report[key]
            lines.append(f"Imputation counts for {col}: subregion={c['by_subregion']}, continent={c['by_continent']}, global={c['by_global']}")

    # simple non-null ratios
    lines.append("\nNon-null ratios:")
    for c, r in report.get("non_null_ratio", {}).items():
        lines.append(f"  {c}: {r:.2%}")

    path.write_text("\n".join(lines), encoding="utf-8")