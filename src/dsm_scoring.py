from __future__ import annotations

import numpy as np
import pandas as pd


PROGRAM_DESCRIPTIONS = {
    "Flex D": "Critical-peak or time-varying tariff alignment where temporal flexibility and winter peak relevance matter.",
    "Hilo": "Smart-control alignment where controllable electric heating, ownership/control, and curtailment tolerance matter.",
    "LogisVert": "Retrofit or equipment-upgrade alignment where structural demand, income, ownership, and residential stability matter.",
    "Low-income assistance": "Equity-oriented targeting where energy vulnerability and system relevance are considered together.",
}

COMPONENT_DESCRIPTIONS = {
    "Demand relevance": "FSA-level winter/system demand signal from the DSM report. Higher values mean the area is more relevant for peak or system-facing DSM action.",
    "Temporal flexibility": "FSA-level proxy for whether daily routines may allow shifting or curtailment, derived from synthetic-population and census-style scheduling indicators in the DSM workflow.",
    "Demand elasticity": "FSA-level proxy for how much the local load and household context may respond to price or peak signals.",
    "Technical eligibility": "FSA-level Hilo proxy for electrically heated or otherwise controllable homes.",
    "Control authority": "FSA-level Hilo proxy for whether households are likely to have enough control over equipment and dwelling decisions.",
    "Curtailment tolerance": "FSA-level proxy for whether residents may be able to tolerate short comfort or timing changes.",
    "Structural demand": "FSA-level retrofit/equipment-upgrade relevance, emphasizing heating and winter demand intensity.",
    "Adoption capacity": "FSA-level proxy for the ability to adopt an upgrade, using income, ownership, and dwelling-form indicators from the DSM workflow.",
    "Persistence capacity": "FSA-level proxy for whether an intervention is likely to remain useful over time, including residential stability and tenure-related indicators.",
    "System relevance": "FSA-level low-income-program system value, combining demand and grid-relevance indicators from the DSM report.",
    "Energy vulnerability": "FSA-level equity and affordability signal from the DSM report.",
    "Household resemblance": "Selected-resident modifier from the synthetic household: tenure, dwelling, income, work/commute schedule, household size, age, and core-housing-need fields where available.",
}


def _component_row(component: str, source_value: float, weight: float) -> dict[str, float | str]:
    return {
        "component": component,
        "source_value": float(source_value),
        "weight": float(weight),
        "contribution": float(source_value) * float(weight),
        "description": COMPONENT_DESCRIPTIONS[component],
    }


def _rank(series: pd.Series, invert: bool = False) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").astype(float)
    return numeric.rank(pct=True, ascending=not invert, method="average").fillna(0.5)


def _weighted(parts: dict[str, pd.Series], weights: dict[str, float]) -> pd.Series:
    total = sum(abs(v) for v in weights.values())
    out = pd.Series(0.0, index=next(iter(parts.values())).index)
    for key, weight in weights.items():
        out = out + parts[key] * weight
    return (out / total).clip(0, 1)


def compute_area_alignment(area_profiles: pd.DataFrame) -> pd.DataFrame:
    """Adapt the DSM repo's rank-composite construct logic to demo-safe area rows."""
    df = area_profiles.set_index("area").copy()

    heating = _rank(df["heating_slope_per_hdd"])
    winter_intensity = _rank(df["winter_peak_intensity"])
    winter_share = _rank(df["winter_peak_share"])
    owner = _rank(df["owner_pct"])
    renter = _rank(df["renter_pct"])
    single_detached = _rank(df["single_detached_house_pct"])
    apartment = _rank(df["apartment_pct"])
    household_size = _rank(df["average_household_size"])
    children = _rank(df["children_0_14_pct"], invert=True)
    older = _rank(df["older_65_plus_pct"], invert=True)
    full_time = _rank(df["full_year_full_time_pct"])
    not_labour = _rank(df["not_in_labour_force_pct"], invert=True)
    one_parent = _rank(df["one_parent_family_pct"], invert=True)
    commute = _rank(df["commute_60_min_plus_pct"], invert=True)
    crowding = _rank(df["persons_per_room_high_pct"], invert=True)
    stability = _rank(df["non_movers_1yr_pct"])
    income = _rank(df["median_income"])
    low_income = _rank(df["low_income_pct"])
    mean_load = _rank(df["mean_load"])

    demand_relevance = _weighted(
        {
            "winter_peak_share": winter_share,
            "heating": heating,
            "winter_intensity": winter_intensity,
        },
        {"winter_peak_share": 0.50, "heating": 0.30, "winter_intensity": 0.20},
    )

    flex_temporal = _weighted(
        {
            "full_time": full_time,
            "not_labour": not_labour,
            "children": children,
            "one_parent": one_parent,
            "commute": commute,
        },
        {"full_time": 0.25, "not_labour": 0.20, "children": 0.20, "one_parent": 0.20, "commute": 0.15},
    )
    flex_elasticity = _weighted(
        {
            "owner": owner,
            "household_size": household_size,
            "crowding": crowding,
            "winter_intensity": winter_intensity,
            "peak_to_mean": _rank(df["am_pm_peak_ratio"]),
            "heating": heating,
        },
        {"owner": 0.20, "household_size": 0.15, "crowding": 0.15, "winter_intensity": 0.20, "peak_to_mean": 0.10, "heating": 0.20},
    )

    hilo_technical = _weighted(
        {"heating": heating, "winter_intensity": winter_intensity, "single_detached": single_detached},
        {"heating": 0.50, "winter_intensity": 0.30, "single_detached": 0.20},
    )
    hilo_control = _weighted(
        {"owner": owner, "renter": _rank(df["renter_pct"], invert=True), "apartment": _rank(df["apartment_pct"], invert=True), "stability": stability},
        {"owner": 0.35, "renter": 0.25, "apartment": 0.20, "stability": 0.20},
    )
    hilo_tolerance = _weighted(
        {"household_size": household_size, "crowding": crowding, "children": children, "older": older},
        {"household_size": 0.25, "crowding": 0.20, "children": 0.25, "older": 0.30},
    )

    logis_structural = _weighted(
        {"heating": heating, "winter_intensity": winter_intensity, "mean_load": mean_load, "peak": winter_intensity},
        {"heating": 0.35, "winter_intensity": 0.30, "mean_load": 0.20, "peak": 0.15},
    )
    logis_adoption = _weighted(
        {"income": income, "owner": owner, "single_detached": single_detached, "stability": stability},
        {"income": 0.45, "owner": 0.25, "single_detached": 0.15, "stability": 0.15},
    )
    logis_persistence = _weighted(
        {"stability": stability, "renter": _rank(df["renter_pct"], invert=True), "owner": owner},
        {"stability": 0.40, "renter": 0.30, "owner": 0.30},
    )

    vulnerability = _weighted(
        {"low_income": low_income, "one_parent": _rank(df["one_parent_family_pct"]), "household_size": household_size, "crowding": _rank(df["persons_per_room_high_pct"]), "renter": renter},
        {"low_income": 0.35, "one_parent": 0.20, "household_size": 0.15, "crowding": 0.15, "renter": 0.15},
    )

    out = pd.DataFrame(index=df.index)
    out["Flex D"] = 0.45 * demand_relevance + 0.275 * flex_temporal + 0.275 * flex_elasticity
    out["Hilo"] = 0.35 * demand_relevance + 0.2167 * hilo_technical + 0.2167 * hilo_control + 0.2166 * hilo_tolerance
    out["LogisVert"] = 0.50 * logis_structural + 0.25 * logis_adoption + 0.25 * logis_persistence
    out["Low-income assistance"] = 0.45 * demand_relevance + 0.55 * vulnerability
    out["demand_relevance"] = demand_relevance
    out["energy_vulnerability"] = vulnerability
    return out.clip(0, 1).reset_index()


def household_modifiers(resident: pd.Series) -> dict[str, float]:
    """Illustrative household-context modifiers derived from supported synthetic-pop columns."""
    tenure = str(resident.get("tenure", "")).lower()
    dwelling = str(resident.get("dwelling_type", "")).lower()
    income = str(resident.get("household_income", "")).lower()
    labour = str(resident.get("labour_force_status", "")).lower()
    commute = str(resident.get("commute_duration", "")).lower()
    need = str(resident.get("core_housing_need", "")).lower()
    hsize_raw = str(resident.get("household_size", 1)).replace("+", "")
    hsize = float(hsize_raw) if hsize_raw else 1.0
    age = str(resident.get("age_group", "")).lower()

    owner = 1.0 if "owner" in tenure else 0.25
    renter = 1.0 if "renter" in tenure else 0.15
    detached = 1.0 if "single-detached" in dwelling else 0.45 if "semi" in dwelling or "row" in dwelling else 0.20
    high_income = 1.0 if "higher" in income or "group 4" in income else 0.75 if "upper" in income or "group 3" in income else 0.45 if "$60k" in income or "group 2" in income else 0.20
    low_income = 1.0 if "$20k" in income or "$40k" in income or "lower income" in income or "group 0" in income else 0.45 if "$60k" in income or "group 1" in income else 0.15
    stable_schedule = 0.85 if "full-time" in labour and "60" not in commute else 0.55
    flexibility_penalty = 0.25 if hsize >= 4 or "65 years" in age else 0.0
    vulnerability_boost = 0.35 if "yes" in need else 0.0

    return {
        "Flex D": np.clip(0.45 * stable_schedule + 0.30 * owner + 0.25 * (max(hsize, 1.0) / 5.0) - flexibility_penalty, 0, 1),
        "Hilo": np.clip(0.45 * owner + 0.35 * detached + 0.20 * (1.0 - flexibility_penalty), 0, 1),
        "LogisVert": np.clip(0.40 * high_income + 0.35 * owner + 0.25 * detached, 0, 1),
        "Low-income assistance": np.clip(0.55 * low_income + 0.30 * renter + vulnerability_boost, 0, 1),
    }


def compute_report_alignment(
    dsm_profiles: pd.DataFrame,
    report_alignment: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Use real DSM report scores when present, otherwise compute toy proxy scores."""
    if report_alignment is None or "fsa_context" not in dsm_profiles.columns:
        return compute_area_alignment(dsm_profiles)

    merged = dsm_profiles[["area", "fsa_context"]].merge(
        report_alignment,
        left_on="fsa_context",
        right_on="fsa",
        how="left",
    )
    if merged[["participation_capacity", "hilo_suitability", "overall_capacity", "energy_vulnerability"]].isna().any().any():
        return compute_area_alignment(dsm_profiles)

    out = pd.DataFrame(
        {
            "area": merged["area"],
            "fsa_context": merged["fsa_context"],
            "Flex D": 0.55 * merged["demand_relevance"] + 0.45 * merged["participation_capacity"],
            "Hilo": 0.50 * merged["demand_relevance"] + 0.50 * merged["hilo_suitability"],
            "LogisVert": 0.50 * merged["structural_demand_relevance"] + 0.50 * merged["overall_capacity"],
            "Low-income assistance": 0.50 * merged["system_relevance"] + 0.50 * merged["energy_vulnerability"],
            "demand_relevance": merged["demand_relevance"],
            "energy_vulnerability": merged["energy_vulnerability"],
            "source": "real_dsm_report_excerpt",
        }
    )
    numeric_cols = out.select_dtypes("number").columns
    out[numeric_cols] = out[numeric_cols].clip(0, 1)
    return out


def all_fsa_report_alignment(report_alignment: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "fsa_context": report_alignment["fsa"],
            "Flex D": 0.55 * report_alignment["demand_relevance"] + 0.45 * report_alignment["participation_capacity"],
            "Hilo": 0.50 * report_alignment["demand_relevance"] + 0.50 * report_alignment["hilo_suitability"],
            "LogisVert": 0.50 * report_alignment["structural_demand_relevance"] + 0.50 * report_alignment["overall_capacity"],
            "Low-income assistance": 0.50 * report_alignment["system_relevance"] + 0.50 * report_alignment["energy_vulnerability"],
            "demand_relevance": report_alignment["demand_relevance"],
            "energy_vulnerability": report_alignment["energy_vulnerability"],
            "source": "real_dsm_report_all_montreal_fsas",
        }
    )
    numeric_cols = out.select_dtypes("number").columns
    out[numeric_cols] = out[numeric_cols].clip(0, 1)
    return out


def program_breakdown(
    program: str,
    resident: pd.Series,
    dsm_profiles: pd.DataFrame,
    report_alignment: pd.DataFrame | None = None,
    fsa_context: str | None = None,
) -> pd.DataFrame:
    area_match = dsm_profiles.loc[dsm_profiles["area"] == resident["area"]]
    selected_fsa = fsa_context or resident.get("fsa_context")
    if selected_fsa is None and not area_match.empty:
        selected_fsa = area_match.iloc[0].get("fsa_context")
    if report_alignment is not None and selected_fsa is not None:
        report = report_alignment.loc[report_alignment["fsa"] == selected_fsa]
        if not report.empty:
            r = report.iloc[0]
            modifiers = household_modifiers(resident)
            components = {
                "Flex D": [
                    _component_row("Demand relevance", r["demand_relevance"], 0.70 * 0.55),
                    _component_row("Temporal flexibility", r["temporal_flexibility"], 0.70 * 0.45 * 0.50),
                    _component_row("Demand elasticity", r["demand_elasticity"], 0.70 * 0.45 * 0.50),
                    _component_row("Household resemblance", modifiers["Flex D"], 0.30),
                ],
                "Hilo": [
                    _component_row("Demand relevance", r["demand_relevance"], 0.70 * 0.50),
                    _component_row("Technical eligibility", r["technical_eligibility"], 0.70 * 0.50 / 3),
                    _component_row("Control authority", r["control_authority"], 0.70 * 0.50 / 3),
                    _component_row("Curtailment tolerance", r["curtailment_tolerance"], 0.70 * 0.50 / 3),
                    _component_row("Household resemblance", modifiers["Hilo"], 0.30),
                ],
                "LogisVert": [
                    _component_row("Structural demand", r["structural_demand_relevance"], 0.70 * 0.50),
                    _component_row("Adoption capacity", r["adoption_capacity"], 0.70 * 0.50 * 0.50),
                    _component_row("Persistence capacity", r["persistence_capacity"], 0.70 * 0.50 * 0.50),
                    _component_row("Household resemblance", modifiers["LogisVert"], 0.30),
                ],
                "Low-income assistance": [
                    _component_row("System relevance", r["system_relevance"], 0.70 * 0.50),
                    _component_row("Energy vulnerability", r["energy_vulnerability"], 0.70 * 0.50),
                    _component_row("Household resemblance", modifiers["Low-income assistance"], 0.30),
                ],
            }
            out = pd.DataFrame(components[program])
            out["value"] = out["contribution"]
            return out
    fallback_area = float(score_resident(resident, dsm_profiles)[0].set_index("program").loc[program, "area_context_score"])
    fallback_household = household_modifiers(resident)[program]
    return pd.DataFrame(
        [
            {
                "component": "Demand relevance",
                "source_value": fallback_area,
                "weight": 0.70,
                "contribution": 0.70 * fallback_area,
                "value": 0.70 * fallback_area,
                "description": COMPONENT_DESCRIPTIONS["Demand relevance"],
            },
            {
                "component": "Household resemblance",
                "source_value": fallback_household,
                "weight": 0.30,
                "contribution": 0.30 * fallback_household,
                "value": 0.30 * fallback_household,
                "description": COMPONENT_DESCRIPTIONS["Household resemblance"],
            },
        ]
    )


def score_resident(
    resident: pd.Series,
    dsm_profiles: pd.DataFrame,
    report_alignment: pd.DataFrame | None = None,
    fsa_context: str | None = None,
) -> tuple[pd.DataFrame, dict[str, str]]:
    area = resident["area"]
    if fsa_context and report_alignment is not None:
        all_scores = all_fsa_report_alignment(report_alignment)
        selected = all_scores.loc[all_scores["fsa_context"] == fsa_context].iloc[0].copy()
        selected["area"] = area
    else:
        area_scores = compute_report_alignment(dsm_profiles, report_alignment)
        selected = area_scores.loc[area_scores["area"] == area].iloc[0]
    modifiers = household_modifiers(resident)

    rows = []
    for program in PROGRAM_DESCRIPTIONS:
        area_score = float(selected[program])
        household_score = modifiers[program]
        score = 0.70 * area_score + 0.30 * household_score
        rows.append(
            {
                "program": program,
                "alignment_score": score,
                "area_context_score": area_score,
                "household_context_score": household_score,
                "description": PROGRAM_DESCRIPTIONS[program],
                "fsa_context": selected.get("fsa_context", ""),
                "source": selected.get("source", "demo_proxy_scores"),
            }
        )

    area_match = dsm_profiles.loc[dsm_profiles["area"] == area]
    if area_match.empty:
        area_profile = pd.Series(
            {
                "area": area,
                "area_label": f"Synthetic DA {area}",
                "fsa_context": fsa_context or selected.get("fsa_context", ""),
                "winter_peak_intensity": np.nan,
            }
        )
    else:
        area_profile = area_match.iloc[0]
    explanations = build_explanations(resident, area_profile, report_alignment, fsa_context=fsa_context)
    return pd.DataFrame(rows).sort_values("alignment_score", ascending=False), explanations


def build_explanations(
    resident: pd.Series,
    area_profile: pd.Series,
    report_alignment: pd.DataFrame | None = None,
    fsa_context: str | None = None,
) -> dict[str, str]:
    tenure = str(resident.get("tenure", "not available in this extract"))
    dwelling = str(resident.get("dwelling_type", "not available in this extract"))
    schedule = resident["inferred_schedule_type"]
    income = resident["household_income"]
    need = str(resident.get("core_housing_need", "not available in this extract"))
    fsa_text = ""
    selected_fsa = fsa_context or area_profile.get("fsa_context")
    if selected_fsa:
        fsa_text = f" It is linked to matched FSA energy baseline {selected_fsa} from the DSM report."
    return {
        "Flex D": f"The resident context is {schedule.lower()}.{fsa_text}",
        "Hilo": f"Hilo-style control is usually easier where ownership and controllable equipment are present. Tenure and dwelling type are {tenure.lower()} here, so this demo relies mainly on the selected FSA baseline and available household structure.",
        "LogisVert": f"Retrofit alignment is linked to structural heating relevance plus adoption capacity proxies. This resident option carries household income group {income}; tenure and dwelling type are {tenure.lower()} here.",
        "Low-income assistance": f"Equity alignment rises for renter, lower-income, repair-sensitive, or core-housing-need profiles; this profile records core housing need as {need}.",
    }
