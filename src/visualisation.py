"""
visualisation.py
Generates analytical charts to visualise global socio-economic patterns.

This script provides:
      
    plot_population_density_by_region(df, path):
    Generates a bar chart illustrating the average population density per UN region.

    plot_average_gdp_by_continent(df, path):
    Creates a bar chart showing the average GDP per capita for each continent.

    plot_gdp_vs_life_expectancy(df, path):
    Plots a scatter chart comparing average life expectancy and GDP per capita by subregion.
       
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns 

# Plot and save average population density by region.
def plot_population_density_by_region(df: pd.DataFrame, output_path: str | Path) -> None:
    required = {"region_un", "pop", "area_km2"}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required - set(df.columns)}")
    df = df.copy()
    df["pop_density"] = df["pop"] / df["area_km2"]
    df = df[df["pop_density"].notna() & (df["pop_density"] > 0)]

    grouped = df.groupby("region_un", dropna=False)["pop_density"].mean().sort_values(ascending=False)
    
    plt.figure(figsize=(10,6))
    grouped.plot(kind="bar", edgecolor="black", color="skyblue")
    plt.title("Average Population Density by Region (people per km²)", fontsize=13)
    plt.xlabel("Region (UN classification)")
    plt.ylabel("Average Population Density")
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[OK] Saved population density chart -> {output_path}")    


# Plot and save a bar chart of average GDP per capita by continent.
def plot_average_gdp_by_continent(df: pd.DataFrame, output_path: str | Path) -> None:
    required = {"continent", "gdpPercap"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # count the mean of each continent
    grouped = (
        df.dropna(subset=["continent", "gdpPercap"])
          .groupby("continent")["gdpPercap"]
          .mean(numeric_only=True)
          .sort_values(ascending=False)
    )

    plt.figure(figsize=(10, 6))
    grouped.plot(kind="bar", edgecolor="black", color="skyblue")
    plt.title("Average GDP per Capita by Continent", fontsize=13, pad=8)
    plt.xlabel("Continent")
    plt.ylabel("Average GDP per Capita")
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[OK] Saved chart -> {output_path}")


# Plot average GDP per capita vs life expectancy by subregion.
def plot_gdp_vs_life_expectancy(df: pd.DataFrame, output_path: str | Path) -> None:
    required = {"subregion", "gdpPercap", "lifeExp"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Summarise the average of gdpPercap and lifeExp of each subregion
    df_summary = (
        df.dropna(subset=["subregion", "gdpPercap", "lifeExp"])
          .groupby("subregion", as_index=False)[["gdpPercap", "lifeExp"]]
          .mean()
    )

    n_sub = len(df_summary)
    palette = sns.color_palette("tab20", n_sub)
    colour_map = {sr: palette[i % len(palette)] for i, sr in enumerate(df_summary["subregion"])}

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10.5, 6.5))
    ax = sns.scatterplot(
        data=df_summary,
        x="gdpPercap",
        y="lifeExp",
        hue="subregion",
        palette=colour_map,
        s=120,
        edgecolor="black",
        linewidth=0.5,
        legend=True,
    )

    ax.set_title("Average GDP per Capita vs Life Expectancy by Subregion", fontsize=13)
    ax.set_xlabel("Average GDP per Capita (USD)")
    ax.set_ylabel("Average Life Expectancy (years)")
    ax.grid(True, linestyle="--", alpha=0.6)

    ncol = 2 if n_sub > 12 else 1
    ax.legend(title="Subregion", loc="upper left", bbox_to_anchor=(1.02, 1),
              frameon=True, ncol=ncol, borderaxespad=0.0)

    plt.tight_layout()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[OK] Saved subregion-level GDP vs Life Expectancy chart -> {output_path}")