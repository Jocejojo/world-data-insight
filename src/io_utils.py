"""
io_utils.py
I/O Utilities for CSV loading.

This module provides:
    detect_csv_params(path) 
        Automatically detects file encoding and delimiter.

    standardise_columns(df)
        Standardises column names (lowercase, underscores) and removes “Unnamed” columns.
    
    load_raw_world_data(path, ...)
        Reads a CSV file, cleans whitespace, and returns a DataFrame.
"""

import csv
import re
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

# --- Constants ---
REQUIRED_COLUMNS = {
    "iso_a2",
    "name_long",
    "continent",
    "region_un",
    "subregion",
    "type",
    "area_km2",
    "pop",
    "lifeExp",
    "gdpPercap",
}

COLUMN_ALIASES: Dict[str, str] = {}

# --- Helper ---
# Remove BOM and surrounding spaces from a string.
def _strip_bom_and_space(text: str) -> str:
    return str(text).lstrip("\ufeff").strip()

# Handles duplicated 'iso_a2' columns that appear in the CSV file.
def _coalesce_iso_a2(df: pd.DataFrame) -> pd.DataFrame:
    cols = list(df.columns)

    # Match 'iso_a2' or 'iso_a2.<number>'
    pattern = re.compile(r"^iso_a2(?:\.\d+)?$")
    iso_cols = [c for c in cols if pattern.fullmatch(str(c))]

    if not iso_cols:
        return df

    # Basic cleanup for single 'iso_a2' column
    if len(iso_cols) == 1:
        df["iso_a2"] = (
            df["iso_a2"]
            .astype(str)
            .map(_strip_bom_and_space)
            .replace({"": pd.NA, "nan": pd.NA, "NaN": pd.NA})
        )
        return df

    # Take the first non-null value per row for multiple 'iso_a2' variants
    def pick_first_non_null(row):
        for c in iso_cols:
            val = row.get(c)
            if val is None:
                continue
            s = _strip_bom_and_space(str(val))
            if s == "" or s.lower() == "nan":
                continue
            return s
        return pd.NA

    df["iso_a2"] = df.apply(pick_first_non_null, axis=1)

    # Drop other 'iso_a2' columns except the main one
    to_drop = [c for c in iso_cols if c != "iso_a2"]
    df = df.drop(columns=to_drop, errors="ignore")

    return df

# --- Public API ---
# Detect CSV encoding & delimiter by sampling.
def detect_csv_params(path: str | Path) -> Dict[str, str]:
    path = Path(path)
    encodings_to_try = ["utf-8-sig", "utf-8", "latin-1"]

    sample = None
    encoding_used = None
    for enc in encodings_to_try:
        try:
            with path.open("r", encoding=enc, errors="strict") as f:
                sample = f.read(4096)
                encoding_used = enc
                break
        except Exception:
            continue

    if sample is None:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            sample = f.read(4096)
        encoding_used = "utf-8"

    try:
        dialect = csv.Sniffer().sniff(sample)
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ","

    return {"encoding": encoding_used, "delimiter": delimiter}

# Perform only the necessary normalisation for this dataset
def standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    unnamed = [c for c in df.columns if str(c).startswith("Unnamed:")]
    if unnamed:
        df = df.drop(columns=unnamed)

    df = _coalesce_iso_a2(df)

    df.columns = [_strip_bom_and_space(c) for c in df.columns]

    return df

# Load the raw CSV robustly and return a DataFrame with minimal normalisation.
def load_raw_world_data(
    path: str | Path,
    encoding: Optional[str] = None,
    delimiter: Optional[str] = None,
) -> pd.DataFrame:

    path = Path(path)

    if encoding is None or delimiter is None:
        params = detect_csv_params(path)
        encoding = params["encoding"]
        delimiter = params["delimiter"]

    df = pd.read_csv(path, encoding=encoding, sep=delimiter)

    df = standardise_columns(df)

    obj_cols = df.select_dtypes(include=["object"]).columns
    for c in obj_cols:
        df[c] = (
            df[c]
            .astype(str)
            .map(_strip_bom_and_space)
            .replace({"": pd.NA, "nan": pd.NA, "NaN": pd.NA})
        )

    return df



