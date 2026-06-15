import pandas as pd

from src.dsm_scoring import compute_report_alignment, program_breakdown, score_resident
from src.utils import read_area_locations, read_dsm_profiles, read_fsa_geojson, read_fsa_resident_options, read_real_dsm_alignment
from src.visualization import alignment_breakdown_bar, comparison_alignment_breakdown_bar, comparison_breakdown_bar, comparison_component_dumbbell_chart, comparison_component_radar_chart, comparison_dumbbell_chart, comparison_radar_chart


def test_demo_data_and_scores_load():
    population = read_fsa_resident_options()
    dsm_profiles = read_dsm_profiles()
    real_alignment = read_real_dsm_alignment()
    area_locations = read_area_locations()
    fsa_geojson = read_fsa_geojson()

    resident = population.iloc[0]
    scores, explanations = score_resident(resident, dsm_profiles, real_alignment, fsa_context=resident["fsa_context"])

    assert len(population) >= 470
    assert population.groupby("fsa_context").size().min() == 5
    assert population["source_synpop_file"].eq("syn_inds_with_hh_montreal_p24_seed42_all.parquet").all()
    assert len(dsm_profiles) == 10
    assert len(real_alignment) >= 90
    assert len(area_locations) == 10
    assert len(fsa_geojson.get("features", [])) >= 90
    assert set(scores["program"]) == {"Flex D", "Hilo", "LogisVert", "Low-income assistance"}
    assert scores["alignment_score"].between(0, 1).all()
    assert "Flex D" in explanations


def test_real_report_alignment_path_is_used():
    population = read_fsa_resident_options()
    dsm_profiles = read_dsm_profiles()
    real_alignment = read_real_dsm_alignment()

    area_scores = compute_report_alignment(dsm_profiles, real_alignment)
    resident = population.iloc[0]
    scores, _ = score_resident(resident, dsm_profiles, real_alignment, fsa_context=resident["fsa_context"])
    breakdown = program_breakdown("Flex D", resident, dsm_profiles, real_alignment, fsa_context=resident["fsa_context"])
    flex_score = scores.set_index("program").loc["Flex D", "alignment_score"]

    assert area_scores["source"].eq("real_dsm_report_excerpt").all()
    assert scores["source"].eq("real_dsm_report_all_montreal_fsas").all()
    assert "Household resemblance" in set(breakdown["component"])
    assert abs(breakdown["contribution"].sum() - flex_score) < 1e-9
    assert breakdown["description"].notna().all()


def test_comparison_breakdown_chart_builds():
    population = read_fsa_resident_options()
    dsm_profiles = read_dsm_profiles()
    real_alignment = read_real_dsm_alignment()
    fsa = population.iloc[0]["fsa_context"]
    residents = population.loc[population["fsa_context"] == fsa].head(2)

    breakdown = pd.concat(
        [
            program_breakdown("Hilo", residents.iloc[0], dsm_profiles, real_alignment, fsa_context=fsa).assign(resident_label="Resident A"),
            program_breakdown("Hilo", residents.iloc[1], dsm_profiles, real_alignment, fsa_context=fsa).assign(resident_label="Resident B"),
        ],
        ignore_index=True,
    )
    fig = comparison_breakdown_bar(breakdown, "Hilo")
    radar = comparison_component_radar_chart(breakdown, "Hilo")
    dumbbell = comparison_component_dumbbell_chart(breakdown, "Hilo")

    assert len(fig.data) >= 2
    assert len(radar.data) == 2
    assert len(dumbbell.data) >= 4
    assert set(breakdown["resident_label"]) == {"Resident A", "Resident B"}


def test_headline_breakdown_charts_build():
    population = read_fsa_resident_options()
    dsm_profiles = read_dsm_profiles()
    real_alignment = read_real_dsm_alignment()
    fsa = population.iloc[0]["fsa_context"]
    residents = population.loc[population["fsa_context"] == fsa].head(2)
    scores, _ = score_resident(residents.iloc[0], dsm_profiles, real_alignment, fsa_context=fsa)

    selected_breakdown = pd.concat(
        [
            program_breakdown(program, residents.iloc[0], dsm_profiles, real_alignment, fsa_context=fsa).assign(program=program)
            for program in scores["program"]
        ],
        ignore_index=True,
    )
    comparison_breakdown = pd.concat(
        [
            selected_breakdown.assign(resident_label="Resident A"),
            pd.concat(
                [
                    program_breakdown(program, residents.iloc[1], dsm_profiles, real_alignment, fsa_context=fsa).assign(program=program)
                    for program in scores["program"]
                ],
                ignore_index=True,
            ).assign(resident_label="Resident B"),
        ],
        ignore_index=True,
    )

    individual_fig = alignment_breakdown_bar(selected_breakdown)
    comparison_fig = comparison_alignment_breakdown_bar(comparison_breakdown)
    radar_fig = comparison_radar_chart(
        pd.concat(
            [
                score_resident(residents.iloc[0], dsm_profiles, real_alignment, fsa_context=fsa)[0].assign(resident_label="Resident A"),
                score_resident(residents.iloc[1], dsm_profiles, real_alignment, fsa_context=fsa)[0].assign(resident_label="Resident B"),
            ],
            ignore_index=True,
        )
    )
    dumbbell_fig = comparison_dumbbell_chart(
        pd.concat(
            [
                score_resident(residents.iloc[0], dsm_profiles, real_alignment, fsa_context=fsa)[0].assign(resident_label="Resident A"),
                score_resident(residents.iloc[1], dsm_profiles, real_alignment, fsa_context=fsa)[0].assign(resident_label="Resident B"),
            ],
            ignore_index=True,
        )
    )

    assert individual_fig.layout.barmode == "stack"
    assert comparison_fig.layout.barmode == "stack"
    assert len(comparison_fig.data) >= 2
    assert len(radar_fig.data) == 2
    assert len(dumbbell_fig.data) >= 4
