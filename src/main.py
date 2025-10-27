"""
main.py
CLI entry point for the worldData analysis project.

This script provides:
    - Command-line interface for cleaning, analysis, and optional filtering.
    - Generates cleaned data (CSV), cleaning report (TXT), and analytical summaries.
    - Supports interactive filtering and summary statistics display via CLI.
"""

from pathlib import Path
import argparse
import pandas as pd
from tabulate import tabulate
from datetime import datetime

from io_utils import load_raw_world_data
from cleaning import clean_world_data, save_cleaning_report
from analysis import (
    most_countries_by_continent,
    region_with_largest_area,
    country_highest_life_expectancy,
    subregion_gdp_extremes,
    write_summary_txt,
)
from visualisation import (
    plot_population_density_by_region,
    plot_average_gdp_by_continent,
    plot_gdp_vs_life_expectancy,
)


# --- CLI argument parsing ---
def _parse_args():
    """Parse command-line options for cleaning and filtering."""
    parser = argparse.ArgumentParser(
        description="WOrld Data CLI — data cleaning, analysis, and interactive filtering."
    )
    parser.add_argument(
        "--save-subset",
        action="store_true",
        help="Save filtered subset to outputs/filtered_subset.csv",
    )
    parser.add_argument(
        "--fresh-clean",
        action="store_true",
        help="Force re-run of cleaning pipeline (otherwise reuse standard process).",
    )
    return parser.parse_args()

def _slug(s: str | None) -> str:
    """Helper: make a safe, short version of a filter value for filenames."""
    if not s:
        return "all"
    return (
        str(s)
        .strip()
        .replace(" ", "_")
        .replace("/", "-")
        .replace("\\", "-")
    )

# --- CLI input helpers and validation ---
# Return a few sorted unique options for a given column.
def _list_options(df: pd.DataFrame, col: str, limit: int = 15) -> list[str]:
    if col not in df.columns:
        return []
    opts = sorted(df[col].dropna().astype(str).unique())
    return opts[:limit] + (["..."] if len(opts) > limit else [])

#Prompt user for one filter value (press Enter to skip)
# Case-insensitive; if invalid, show valid examples and retry.
def _prompt_one_filter(df: pd.DataFrame, col: str, display_name: str) -> str | None:
    options = sorted(df[col].dropna().astype(str).unique())
    options_lower = {o.lower(): o for o in options}

    while True:
        val = input(f"Enter {display_name} (or press Enter for all): ").strip()
        if val == "":
            return None
        key = val.lower()
        if key in options_lower:
            return options_lower[key]
        sample = _list_options(df, col)
        print(f"[!] '{val}' is not a valid {display_name}. Available examples: {', '.join(sample)}")

# Apply equality-based filters. None means skip that column.
def apply_filters(df: pd.DataFrame, filters: dict[str, str | None]) -> pd.DataFrame:
    out = df.copy()
    for col, v in filters.items():
        if v is None:
            continue
        out = out[out[col].astype(str) == str(v)]
    return out

# Compute basic summary statistics: count, sum, mean, median, min, max, std.
def compute_summary(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    agg_map = {
        "count": "count",
        "sum": "sum",
        "mean": "mean",
        "median": "median",
        "min": "min",
        "max": "max",
        "std": "std",
    }
    res = df[cols].agg(agg_map.values())
    res.index = agg_map.keys()
    return res.T  # rows = column names, columns = statistic types



# --- Main pipeline ---

def main(args=None):
    root = Path(__file__).resolve().parents[1]
    csv_path = root / "data" / "worldData.csv"
    out_dir = root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load raw data
    df_raw = load_raw_world_data(csv_path)

    # Clean dataset 
    df_clean, report = clean_world_data(df_raw, generate_report=True)

    # Export cleaned CSV and report
    clean_csv = out_dir / "worldData_clean.csv"
    df_clean.to_csv(clean_csv, index=False, encoding="utf-8")
    print(f"[OK] Saved cleaned CSV -> {clean_csv}")

    report_txt = out_dir / "cleaning_report.txt"
    save_cleaning_report(report, report_txt)
    print(f"[OK] Saved cleaning report -> {report_txt}")

    # Analysis 
    continent, continent_count = most_countries_by_continent(df_clean)
    region, region_area = region_with_largest_area(df_clean)
    country, lifeexp = country_highest_life_expectancy(df_clean)
    sub_min, gdp_min, sub_max, gdp_max = subregion_gdp_extremes(df_clean)

    answers = {
        "continent": continent,
        "continent_count": continent_count,
        "region_un": region,
        "region_area_km2": region_area,
        "country": country,
        "lifeExp": lifeexp,
        "subregion_min": sub_min,
        "gdp_min": gdp_min,
        "subregion_max": sub_max,
        "gdp_max": gdp_max,
    }

    # Write analysis results to summary file
    summary_path = out_dir / "summary.txt"
    write_summary_txt(summary_path, answers)
    print(f"[OK] Wrote analysis summary -> {summary_path}")

    # --- Bonus Visualisations ---
    plot_average_gdp_by_continent(df_clean, out_dir / "avg_gdp_by_continent.png")
    plot_gdp_vs_life_expectancy(df_clean, out_dir / "gdp_vs_lifeExp.png")
    plot_population_density_by_region(df_clean, out_dir / "population_density_by_region.png")

    # --- Interactive filtering (CLI) ---
    # User can filter by continent, region, subregion, or type.
    df_clean = pd.read_csv(clean_csv, encoding="utf-8")  # Reload cleaned data to avoid recomputation

    print("\n=== Interactive Filter ===")
    print("You can filter by any of the following (press Enter to skip each):")
    print(" - continent")
    print(" - region_un")
    print(" - subregion")
    print(" - type\n")

    f_cont = _prompt_one_filter(df_clean, "continent", "continent")
    f_regu = _prompt_one_filter(df_clean, "region_un", "region_un")
    f_subr = _prompt_one_filter(df_clean, "subregion", "subregion")
    f_type = _prompt_one_filter(df_clean, "type", "type")

    filters = {
        "continent": f_cont,
        "region_un": f_regu,
        "subregion": f_subr,
        "type": f_type,
    }
    df_sub = apply_filters(df_clean, filters)

    print(f"\n[Info] Rows after filtering: {len(df_sub)}")
    if "name_long" in df_sub.columns:
        country_list = df_sub["name_long"].dropna().unique().tolist()
        print(f"Filtered countries ({len(country_list)}):")
        print(", ".join(country_list[:15]) + ("..." if len(country_list) > 15 else ""))

    numeric_cols = ["area_km2", "pop", "lifeExp", "gdpPercap"]
    if len(df_sub) == 0:
        print("[Warn] No rows match your filters.")
    else:
        summary_tbl = compute_summary(df_sub, numeric_cols)
        print("\nSummary statistics (per column):")
        print(tabulate(summary_tbl, headers="keys", tablefmt="github", floatfmt=".2f"))

        if args and getattr(args, "save_subset", False) and len(df_sub) > 0:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            fname = f"filtered_{_slug(f_cont)}_{_slug(f_regu)}_{_slug(f_subr)}_{_slug(f_type)}_{ts}.csv"
            subset_path = out_dir / fname
            df_sub.to_csv(subset_path, index=False, encoding="utf-8")
            print(f"[OK] Saved filtered subset -> {subset_path}")


if __name__ == "__main__":
    args = _parse_args()
    main(args)
