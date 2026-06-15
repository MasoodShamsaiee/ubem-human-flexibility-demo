from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def load_metadata() -> dict:
    with (DATA_DIR / "metadata.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def read_demo_population() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "demo_synthetic_population.csv")


def read_fsa_resident_options() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "demo_fsa_resident_options.csv", dtype={"area": str, "source_da": str})


def read_dsm_profiles() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "demo_dsm_profiles.csv")


def read_real_dsm_alignment() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "demo_real_dsm_alignment.csv")


def read_area_locations() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "demo_area_locations.csv")


def read_fsa_geojson() -> dict:
    path = DATA_DIR / "demo_montreal_fsa_context.geojson"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def score_label(score: float) -> str:
    if score >= 0.67:
        return "High"
    if score >= 0.40:
        return "Medium"
    return "Low"


def pct(value: float) -> str:
    return f"{100 * float(value):.0f}%"
