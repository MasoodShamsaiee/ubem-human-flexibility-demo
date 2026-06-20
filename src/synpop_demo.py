from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
BLUE = "#1f77b4"
ORANGE = "#ff7f0e"
FIT_COLORS = {
    "Strong": "#2ca02c",
    "Good": BLUE,
    "Moderate": ORANGE,
    "Weak": "#d62728",
    "Not assessed": "#7f7f7f",
}

PERSON_ATTRIBUTES = [
    "sex",
    "age_group",
    "education_level",
    "labour_force_status",
    "household_income",
    "family_status",
    "citizenship_status",
    "immigrant_status",
    "commute_mode",
    "commute_duration",
]

HOUSEHOLD_ATTRIBUTES = [
    "household_size",
    "household_type",
    "dwelling_type",
    "tenure",
    "bedrooms",
    "period_built",
    "dwelling_condition",
    "core_housing_need",
]


def display_text(value: object) -> str:
    if pd.isna(value):
        return "Not available"
    return str(value).replace("_", " ").replace("plus", "+").title()


def display_label(column: str) -> str:
    labels = {
        "age_group": "Age group",
        "education_level": "Education",
        "labour_force_status": "Labour-force status",
        "household_income": "Household income",
        "family_status": "Family status",
        "citizenship_status": "Citizenship",
        "immigrant_status": "Immigrant status",
        "commute_mode": "Commute mode",
        "commute_duration": "Commute duration",
        "household_size": "Household size",
        "household_type": "Household type",
        "dwelling_type": "Dwelling type",
        "tenure": "Tenure",
        "bedrooms": "Bedrooms",
        "period_built": "Period built",
        "dwelling_condition": "Dwelling condition",
        "core_housing_need": "Core housing need",
    }
    return labels.get(column, column.replace("_", " ").title())


def read_h2j_population() -> pd.DataFrame:
    return pd.read_csv(
        DATA_DIR / "synpop_h2j_people_households.csv.gz",
        dtype={"area": str, "HID": str, "household_id": str},
    )


def read_validation_summary() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "synpop_validation_summary.csv")


def read_support_summary() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "synpop_support_summary.csv")


def read_population_totals() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "synpop_population_totals_audit.csv", dtype={"area": str})


def read_bundle_metadata() -> dict:
    return json.loads((DATA_DIR / "synpop_bundle_metadata.json").read_text(encoding="utf-8"))


def distribution_figure(frame: pd.DataFrame, column: str, title: str) -> go.Figure:
    values = frame[column].map(display_text).fillna("Not available")
    counts = values.value_counts(dropna=False).rename_axis("Category").reset_index(name="Count")
    counts["Share"] = counts["Count"] / max(int(counts["Count"].sum()), 1)
    fig = px.bar(
        counts.sort_values("Share"),
        x="Share",
        y="Category",
        orientation="h",
        color_discrete_sequence=[BLUE],
        title=title,
        custom_data=["Count"],
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Share: %{x:.1%}<br>Records: %{customdata[0]:,}<extra></extra>"
    )
    fig.update_layout(
        height=max(300, 38 * len(counts) + 105),
        margin=dict(l=8, r=12, t=46, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    fig.update_xaxes(title="Share", tickformat=".0%", range=[0, max(float(counts["Share"].max()) * 1.12, 0.05)])
    fig.update_yaxes(title="")
    return fig


def validation_fit_figure(summary: pd.DataFrame) -> go.Figure:
    data = summary.copy()
    data["Attribute"] = data["attribute"].map(display_label)
    data["Unit"] = data["unit"].map({"person": "Person", "household": "Household"}).fillna(data["unit"])
    data["Fit rating"] = data["fit_rating"].fillna("Not assessed")
    data = data.sort_values("mean_tvd", ascending=False)
    fig = px.scatter(
        data,
        x="mean_tvd",
        y="Attribute",
        color="Fit rating",
        symbol="Unit",
        size="n_areas",
        color_discrete_map=FIT_COLORS,
        category_orders={"Fit rating": ["Strong", "Good", "Moderate", "Weak", "Not assessed"]},
        custom_data=["Unit", "n_areas", "median_tvd", "p90_tvd", "mean_max_abs_pp"],
        title="Attribute fit across the 30-DA validation bundle",
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>Unit: %{customdata[0]}<br>Mean TVD: %{x:.3f}<br>"
            "DAs: %{customdata[1]}<br>Median TVD: %{customdata[2]:.3f}<br>"
            "90th percentile TVD: %{customdata[3]:.3f}<br>Mean max error: %{customdata[4]:.1f} pp<extra></extra>"
        )
    )
    fig.add_vline(x=0.02, line_dash="dot", line_color="#2ca02c")
    fig.add_vline(x=0.10, line_dash="dot", line_color=ORANGE)
    fig.add_vline(x=0.25, line_dash="dot", line_color="#d62728")
    fig.update_layout(
        height=max(430, 30 * len(data) + 120),
        margin=dict(l=8, r=12, t=48, b=44),
        legend=dict(orientation="h", y=-0.14, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(title="Mean total variation distance (lower is better)", rangemode="tozero")
    fig.update_yaxes(title="")
    return fig


def profile_fields(row: pd.Series, columns: list[str]) -> dict[str, str]:
    return {
        display_label(column): display_text(row.get(column))
        for column in columns
        if column in row.index
    }


def resident_option_label(row: pd.Series) -> str:
    return " | ".join(
        [
            str(row.get("resident_id", "Resident")),
            display_text(row.get("age_group")),
            display_text(row.get("household_type")),
            display_text(row.get("tenure")),
        ]
    )


def inferred_schedule(row: pd.Series) -> str:
    labour = str(row.get("labour_force_status", "")).lower()
    commute = str(row.get("commute_duration", "")).lower()
    household_size = str(row.get("household_size", "1")).lower()
    if "employed" in labour and ("45" in commute or "60" in commute):
        return "Structured workday / long commute"
    if "employed" in labour and household_size in {"1", "2"}:
        return "Structured workday / smaller household"
    if "employed" in labour:
        return "Structured workday / family household"
    if "not in labour" in labour:
        return "More daytime presence likely"
    if "unemployed" in labour:
        return "Variable schedule / employment transition"
    return "Mixed schedule"


def household_overlay_figure(scores: pd.DataFrame) -> go.Figure:
    data = scores[["program", "area_context_score", "alignment_score"]].copy()
    long = data.melt(
        id_vars="program",
        value_vars=["area_context_score", "alignment_score"],
        var_name="View",
        value_name="Score",
    )
    long["View"] = long["View"].map(
        {
            "area_context_score": "FSA baseline",
            "alignment_score": "Illustrative household lens",
        }
    )
    fig = px.bar(
        long,
        x="program",
        y="Score",
        color="View",
        barmode="group",
        color_discrete_map={"FSA baseline": BLUE, "Illustrative household lens": ORANGE},
        title="How the selected household context changes the program view",
    )
    fig.update_layout(
        height=340,
        margin=dict(l=8, r=10, t=48, b=72),
        legend=dict(orientation="h", y=-0.24, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(title="", tickangle=-15)
    fig.update_yaxes(title="Illustrative score", range=[0, 1])
    return fig
