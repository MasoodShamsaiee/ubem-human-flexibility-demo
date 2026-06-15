from __future__ import annotations

import random

import pandas as pd


def infer_schedule_type(row: pd.Series) -> str:
    """Infer a conference-friendly schedule label from supported synthetic-pop fields."""
    labour = str(row.get("labour_force_status", "")).lower()
    commute = str(row.get("commute_duration", "")).lower()
    mode = str(row.get("commute_mode", "")).lower()

    if "worked at home" in mode or "not applicable" in commute:
        return "Home-flexible / low commute"
    if "full-time" in labour and ("45" in commute or "60" in commute):
        return "Structured workday / long commute"
    if "part-time" in labour:
        return "Part-time or variable schedule"
    if "not in labour force" in labour or "unemployed" in labour:
        return "More daytime presence likely"
    return "Mixed schedule"


def with_inferred_fields(population: pd.DataFrame) -> pd.DataFrame:
    out = population.copy()
    out["inferred_schedule_type"] = out.apply(infer_schedule_type, axis=1)
    out["display_name"] = (
        out["resident_id"].astype(str)
        + " | "
        + out["age_group"].astype(str)
        + " | "
        + out["household_type"].astype(str)
        + " | "
        + out["tenure"].astype(str)
    )
    return out


def random_resident_index(population: pd.DataFrame) -> int:
    return random.randrange(len(population))


def resident_summary(row: pd.Series) -> dict[str, str]:
    fields = [field for field in [
        "age_group",
        "sex",
        "household_size",
        "household_type",
        "labour_force_status",
        "household_income",
        "education_level",
        "family_status",
        "inferred_schedule_type",
    ] if field in row.index]
    return {field: str(row.get(field, "")) for field in fields}
