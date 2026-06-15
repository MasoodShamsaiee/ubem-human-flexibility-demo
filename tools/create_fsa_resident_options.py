from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SYNPOP_PATH = ROOT.parents[1] / "urban-energy-data" / "data" / "processed" / "synthetic_population" / "syn_inds_with_hh_montreal_p24_seed42_all.parquet"
FSA_PATH = ROOT / "data" / "demo_real_dsm_alignment.csv"
BRIDGE_PATH = ROOT / "data" / "demo_da_to_fsa_bridge.csv"
OUT_PATH = ROOT / "data" / "demo_fsa_resident_options.csv"


def label_age(value: int) -> str:
    labels = {
        0: "0-4 years",
        1: "5-14 years",
        2: "15-24 years",
        3: "25-34 years",
        4: "35-39 years",
        5: "40-44 years",
        6: "45-49 years",
        7: "50-54 years",
        8: "55-59 years",
        9: "60-64 years",
        10: "65-69 years",
        11: "70-74 years",
        12: "75-79 years",
        13: "80-84 years",
        14: "85+ years",
    }
    return labels.get(int(value), f"Age group {int(value)}")


def label_sex(value: int) -> str:
    return {0: "Female", 1: "Male"}.get(int(value), f"Sex code {value}")


def label_work(value: int) -> str:
    return {
        1867: "Employed",
        1868: "Unemployed",
        1869: "Not in labour force",
        0: "Employed",
        1: "Unemployed",
        2: "Not in labour force",
    }.get(int(value), f"Work status group {value}")


def label_income(value: int) -> str:
    return {
        0: "< $20,000",
        1: "$20,000-$59,999",
        2: "$60,000-$99,999",
        3: "$100,000+",
    }.get(int(value), f"Income group {int(value)}")


def label_education(value: int) -> str:
    return {
        0: "No certificate / high school or less",
        1: "Trades or college credential",
        2: "University credential",
    }.get(int(value), f"Education code {value}")


def label_family(value: int) -> str:
    return {
        0: "Couple family context",
        1: "Couple family context",
        2: "Lone-parent or child context",
        3: "Non-family household context",
        4: "One-person household context",
    }.get(int(value), f"Family status code {value}")


def label_household_type(value: int) -> str:
    return {
        0: "Couple without children",
        1: "Couple with children",
        2: "One-parent household",
        3: "One-person household",
        4: "Other household",
    }.get(int(value), f"Household type code {value}")


def schedule(row: pd.Series) -> str:
    work = int(row.get("lfact", -1))
    household_size = int(row.get("hhsize", 1))
    age_group = int(row.get("agegrp", -1))
    employed = work in {0, 1867}
    unemployed = work in {1, 1868}
    not_in_labour = work in {2, 1869}
    if employed and household_size <= 2:
        return "Structured workday / smaller household"
    if employed and household_size >= 4:
        return "Structured workday / family household"
    if not_in_labour:
        return "More daytime presence likely"
    if unemployed:
        return "Variable schedule / employment transition"
    return "Mixed schedule"


def main() -> None:
    synpop = pd.read_parquet(SYNPOP_PATH)
    bridge = pd.read_csv(BRIDGE_PATH, dtype={"area": str, "fsa": str}).dropna()
    synpop["area"] = synpop["area"].astype(str)
    synpop = synpop.merge(bridge, on="area", how="inner")
    fsas = pd.read_csv(FSA_PATH)["fsa"].sort_values().tolist()
    rows: list[dict[str, object]] = []

    for fsa_index, fsa in enumerate(fsas):
        pool = synpop.loc[synpop["fsa"] == fsa].sample(frac=1, random_state=42 + fsa_index).reset_index(drop=True)
        sample = pool.head(5)
        if len(sample) < 5:
            sample = synpop.sample(5, random_state=100 + fsa_index)
        for person_index, (_, row) in enumerate(sample.iterrows(), start=1):
            rows.append(
                {
                    "resident_id": f"{fsa}-P{person_index}",
                    "fsa_context": fsa,
                    "source_da": str(row["area"]),
                    "area": str(row["area"]),
                    "HID": row.get("HID", ""),
                    "person_uid": f"{fsa}-P{person_index}",
                    "sex": label_sex(row["sex"]),
                    "age_group": label_age(row["agegrp"]),
                    "education_level": label_education(row["hdgree"]),
                    "labour_force_status": label_work(row["lfact"]),
                    "household_income": label_income(row["totinc"]),
                    "family_status": label_family(row["cfstat"]),
                    "household_size": {0: "1", 1: "2", 2: "3", 3: "4", 4: "5+"}.get(int(row["hhsize"]), str(int(row["hhsize"]))),
                    "household_type": label_household_type(row["hhtype"]),
                    "inferred_schedule_type": schedule(row),
                    "code_agegrp": int(row["agegrp"]),
                    "code_lfact": int(row["lfact"]),
                    "code_totinc": int(row["totinc"]),
                    "code_hhtype": int(row["hhtype"]),
                    "source_synpop_file": SYNPOP_PATH.name,
                }
            )

    out = pd.DataFrame(rows)
    out.to_csv(OUT_PATH, index=False)
    print(f"Wrote {OUT_PATH} with {len(out)} rows for {len(fsas)} FSAs.")


if __name__ == "__main__":
    main()
