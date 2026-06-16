from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
FEEDBACK_DIR = ROOT / "data" / "feedback"
FEEDBACK_PATH = FEEDBACK_DIR / "user_feedback.csv"
ESIM_MATRIX_IMAGE = ROOT / "assets" / "esim_evaluation_matrix.jpg"

DEMO_MODES = {
    "eSim DSM alignment": "Inspect FSA-level DSM relevance-capacity patterns.",
    "Integrated demo": "Connect synthetic residents to FSA-level DSM alignment.",
    "BuildSys synthetic population": "Explore support-aware resident and household attributes.",
}
DEMO_PATH_META = {
    "eSim DSM alignment": {
        "logo": "eSim",
        "logo_class": "path-logo-esim",
        "title": "eSim paper path",
        "description": "FSA-level DSM alignment, relevance-capacity classes, and program diagnostics.",
    },
    "Integrated demo": {
        "logo": "UBEM",
        "logo_class": "path-logo-integrated",
        "title": "Integrated workflow",
        "description": "Synthetic residents linked to the selected FSA so household heterogeneity can be discussed with DSM context.",
    },
    "BuildSys synthetic population": {
        "logo": "BuildSys",
        "logo_class": "path-logo-buildsys",
        "title": "BuildSys path",
        "description": "Support-aware synthetic population attributes for occupant-sensitive urban energy research.",
    },
}

BUILDSYS_ATTRIBUTE_SUPPORT = pd.DataFrame(
    [
        ("Age group", "Stable", 0.0014, "Core person synthesis"),
        ("Labour force status", "Stable", 0.0021, "Core person synthesis"),
        ("Household type", "Stable", 0.0024, "Core generation proxy"),
        ("Household income", "Stable", 0.0030, "Household synthesis"),
        ("Tenure", "Stable", 0.0045, "Household synthesis"),
        ("Bedrooms", "Stable", 0.0038, "Household synthesis"),
        ("Dwelling type", "Moderate", 0.0098, "Sparse handling"),
        ("Core housing need", "Moderate", 0.0109, "Sparse handling"),
        ("Commute duration", "Moderate", 0.0117, "Exploratory timing proxy"),
        ("Commute mode", "Moderate", 0.0131, "Exploratory timing proxy"),
        ("Dwelling condition", "Moderate", 0.0136, "Sparse handling"),
    ],
    columns=["Attribute", "Support", "TVD", "Interpretation"],
)

ESIM_PROGRAM_CONTEXT = pd.DataFrame(
    [
        (
            "Tarif Flex D",
            "Behavioral peak-period response",
            "Participation capacity",
            "Temporal flexibility and demand elasticity",
            "26 ideal FSAs; 14 policy-gap FSAs",
        ),
        (
            "Hilo",
            "Automated demand response",
            "Hilo suitability",
            "Technical eligibility, control authority, curtailment tolerance",
            "29 ideal FSAs; 11 policy-gap FSAs",
        ),
        (
            "LogisVert",
            "Structural efficiency and electrification",
            "Overall retrofit capacity",
            "Structural demand, adoption capacity, persistence",
            "30 ideal FSAs; 10 policy-gap FSAs",
        ),
        (
            "Low-income assistance",
            "Affordability and protection",
            "Energy vulnerability",
            "System relevance and vulnerability concentration",
            "12 ideal FSAs; 28 policy-gap FSAs",
        ),
    ],
    columns=["Program", "Pathway", "Capacity or targeting axis", "Main alignment constraint", "Paper result"],
)

ESIM_PROGRAM_AXES = {
    "Tarif Flex D": {
        "relevance_col": "demand_relevance",
        "capacity_col": "participation_capacity",
        "class_col": "flexd_alignment_class",
        "relevance_label": "Demand relevance",
        "capacity_label": "Participation capacity",
        "program_column": "Flex D",
    },
    "Hilo": {
        "relevance_col": "demand_relevance",
        "capacity_col": "hilo_suitability",
        "class_col": "hilo_alignment_class",
        "relevance_label": "Demand relevance",
        "capacity_label": "Hilo suitability",
        "program_column": "Hilo",
    },
    "LogisVert": {
        "relevance_col": "structural_demand_relevance",
        "capacity_col": "overall_capacity",
        "class_col": "logisvert_alignment_class",
        "relevance_label": "Structural demand relevance",
        "capacity_label": "Overall retrofit capacity",
        "program_column": "LogisVert",
    },
    "Low-income assistance": {
        "relevance_col": "system_relevance",
        "capacity_col": "energy_vulnerability",
        "class_col": "low_income_alignment_class",
        "relevance_label": "System relevance",
        "capacity_label": "Energy vulnerability",
        "program_column": "Low-income assistance",
    },
}

ESIM_CLASS_LABELS = {
    "high_demand_high_capacity": "Ideal target",
    "high_demand_low_capacity": "Policy gap",
    "low_demand_high_capacity": "Low priority",
    "low_demand_low_capacity": "Minimal impact",
    "high_demand_high_hilo_suitability": "Ideal target",
    "high_demand_low_hilo_suitability": "Policy gap",
    "low_demand_high_hilo_suitability": "Low priority",
    "low_demand_low_hilo_suitability": "Minimal impact",
    "high_structural_relevance_high_capacity": "Ideal target",
    "high_structural_relevance_low_capacity": "Policy gap",
    "low_structural_relevance_high_capacity": "Low priority",
    "low_structural_relevance_low_capacity": "Minimal impact",
    "high_system_relevance_high_vulnerability": "Ideal target",
    "high_system_relevance_low_vulnerability": "Policy gap",
    "low_system_relevance_high_vulnerability": "Low priority",
    "low_system_relevance_low_vulnerability": "Minimal impact",
}

ESIM_PAPER_CLASS_DISTRIBUTION = pd.DataFrame(
    [
        ("Tarif Flex D", "Ideal target", "26 (32.9%)"),
        ("Tarif Flex D", "Policy gap", "14 (17.7%)"),
        ("Tarif Flex D", "Low priority", "14 (17.7%)"),
        ("Tarif Flex D", "Minimal impact", "25 (31.6%)"),
        ("Hilo", "Ideal target", "29 (36.7%)"),
        ("Hilo", "Policy gap", "11 (13.9%)"),
        ("Hilo", "Low priority", "11 (13.9%)"),
        ("Hilo", "Minimal impact", "28 (35.4%)"),
        ("LogisVert", "Ideal target", "30 (38.0%)"),
        ("LogisVert", "Policy gap", "10 (12.7%)"),
        ("LogisVert", "Low priority", "10 (12.7%)"),
        ("LogisVert", "Minimal impact", "29 (36.7%)"),
        ("Low-income assistance", "Ideal target", "12 (15.2%)"),
        ("Low-income assistance", "Policy gap", "28 (35.4%)"),
        ("Low-income assistance", "Low priority", "28 (35.4%)"),
        ("Low-income assistance", "Minimal impact", "11 (13.9%)"),
    ],
    columns=["Program", "Class", "Paper-reported FSAs"],
)

ESIM_COMPONENT_DESCRIPTIONS = {
    "Demand relevance": "FSA-level winter/system demand signal used for peak-oriented programs.",
    "Temporal flexibility": "FSA-level proxy for whether routines and load shapes allow peak-period shifting.",
    "Demand elasticity": "FSA-level proxy for likely response to price or peak-event signals.",
    "Technical eligibility": "FSA-level Hilo proxy for controllable electric heating or compatible equipment.",
    "Control authority": "FSA-level proxy for tenure and ability to install or authorize controls.",
    "Curtailment tolerance": "FSA-level proxy for tolerance of short automated adjustments.",
    "Structural demand": "FSA-level relevance of retrofit or equipment upgrades for winter demand.",
    "Adoption capacity": "FSA-level proxy for financial and institutional capacity to adopt upgrades.",
    "Persistence capacity": "FSA-level proxy for whether benefits persist in the same population and territory.",
    "System relevance": "FSA-level system-facing relevance for protection-oriented programs.",
    "Energy vulnerability": "FSA-level affordability and energy-hardship exposure.",
}

from src.dsm_scoring import all_fsa_report_alignment, compute_report_alignment, program_breakdown, score_resident
from src.synthetic_population import resident_summary
from src.utils import load_metadata, read_area_locations, read_dsm_profiles, read_fsa_geojson, read_fsa_resident_options, read_real_dsm_alignment, score_label
from src.visualization import (
    alignment_bar,
    average_vs_heterogeneous,
    comparison_bar,
    distribution_bar,
    energy_percentile_strip,
    energy_relationship_scatter,
    fsa_context_map,
    program_axis_stacked_bar,
    radar_chart,
    relevance_capacity_matrix,
    selected_distribution_bar,
    selected_vs_rest_bar,
)
try:
    from src.visualization import stacked_breakdown_bar
except ImportError:
    stacked_breakdown_bar = None
try:
    from src.visualization import alignment_breakdown_bar
except ImportError:
    alignment_breakdown_bar = None
try:
    from src.visualization import comparison_alignment_breakdown_bar
except ImportError:
    comparison_alignment_breakdown_bar = None
try:
    from src.visualization import comparison_radar_chart
except ImportError:
    comparison_radar_chart = None
try:
    from src.visualization import comparison_dumbbell_chart
except ImportError:
    comparison_dumbbell_chart = None
try:
    from src.visualization import comparison_breakdown_bar
except ImportError:
    comparison_breakdown_bar = None
try:
    from src.visualization import comparison_component_radar_chart
except ImportError:
    comparison_component_radar_chart = None
try:
    from src.visualization import comparison_component_dumbbell_chart
except ImportError:
    comparison_component_dumbbell_chart = None


st.set_page_config(page_title="UBEM Human Flexibility Demo", page_icon=":zap:", layout="wide")

st.markdown(
    """
    <style>
    .resident-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
        gap: 0.65rem;
    }
    .resident-card {
        background: #EEF2EF;
        border: 1px solid #D8E0DB;
        border-radius: 8px;
        padding: 0.72rem 0.78rem;
        min-height: 82px;
    }
    .resident-label {
        color: #586765;
        font-size: 0.76rem;
        line-height: 1.15;
        text-transform: uppercase;
        letter-spacing: 0;
        margin-bottom: 0.35rem;
        overflow-wrap: anywhere;
        display: flex;
        align-items: center;
        gap: 0.35rem;
    }
    .resident-value {
        color: #1F2A2A;
        font-size: 0.96rem;
        line-height: 1.22;
        font-weight: 650;
        overflow-wrap: anywhere;
        word-break: normal;
    }
    .context-note {
        border-left: 4px solid #2F6B63;
        padding: 0.75rem 0.9rem;
        background: #F5F7F4;
        border-radius: 0 8px 8px 0;
        color: #263332;
    }
    .help-dot {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1rem;
        height: 1rem;
        border-radius: 50%;
        background: #D8E0DB;
        color: #2F3A39;
        font-size: 0.68rem;
        font-weight: 700;
        cursor: help;
        flex: 0 0 auto;
    }
    .resident-option {
        border-radius: 8px;
        border: 1px solid #D8E0DB;
        background: #FFFFFF;
        padding: 0.72rem 0.78rem;
        min-height: 176px;
    }
    .resident-option-selected {
        border: 2px solid #2F6B63;
        background: #F3F8F6;
    }
    .resident-option-title {
        font-weight: 700;
        color: #1F2A2A;
        margin-bottom: 0.35rem;
    }
    .resident-option-line {
        color: #586765;
        font-size: 0.83rem;
        line-height: 1.25;
        margin: 0.12rem 0;
    }
    .path-card {
        border: 1px solid #D8E0DB;
        background: #FFFFFF;
        border-radius: 8px;
        padding: 0.82rem;
        min-height: 154px;
        margin-bottom: 0.45rem;
    }
    .path-card-selected {
        border: 2px solid #2F6B63;
        background: #F3F8F6;
    }
    .path-logo {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 78px;
        height: 42px;
        border-radius: 7px;
        color: #FFFFFF;
        font-weight: 800;
        letter-spacing: 0;
        margin-bottom: 0.62rem;
    }
    .path-logo-esim {
        background: #2F6B63;
    }
    .path-logo-integrated {
        background: #6E7FA8;
    }
    .path-logo-buildsys {
        background: #B85C5C;
    }
    .path-title {
        font-weight: 760;
        color: #1F2A2A;
        line-height: 1.15;
        margin-bottom: 0.35rem;
    }
    .path-description {
        color: #586765;
        font-size: 0.86rem;
        line-height: 1.28;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

FIELD_LABELS = {
    "age_group": "Age Group",
    "household_size": "Household Size",
    "household_type": "Household Structure",
    "tenure": "Housing Tenure",
    "dwelling_type": "Dwelling Type",
    "labour_force_status": "Work Status",
    "household_income": "Household Income Group",
    "fsa_context": "Selected FSA",
    "source_da": "Source Synthetic DA",
    "source_synpop_file": "Synthetic Population Source File",
    "resident_id": "Resident Option ID",
    "HID": "Household Donor ID",
    "person_uid": "Demo Person ID",
    "code_agegrp": "Raw Age Code",
    "code_lfact": "Raw Work Code",
    "code_totinc": "Raw Income Code",
    "code_hhtype": "Raw Household Type Code",
    "commute_mode": "Main Commute Mode",
    "commute_duration": "Commute Duration",
    "inferred_schedule_type": "Inferred Schedule Pattern",
    "core_housing_need": "Core Housing Need",
    "Demo area": "Demo Synthetic Area",
    "Energy/DSM area context": "Matched FSA Energy Baseline",
    "Winter peak intensity": "Winter Peak Intensity",
    "Area tenure mix": "Area Tenure Mix",
    "Area median income proxy": "Area Median Income Proxy",
    "DSM area context": "Matched FSA Energy Baseline",
    "Age group": "Age Group",
    "Household type": "Household Structure",
    "Household size": "Household Size",
    "Dwelling type": "Dwelling Type",
    "Labour status": "Work Status",
    "Income group": "Household Income Group",
    "Schedule type": "Inferred Schedule Pattern",
}

FIELD_HELP = {
    "age_group": "Synthetic-population age category for the selected person.",
    "household_size": "Number of people in the selected synthetic household.",
    "household_type": "Household composition category from the synthetic-population output.",
    "tenure": "Whether the selected household is owner-occupied or rented.",
    "dwelling_type": "Dwelling form from the household record, such as apartment or single-detached house.",
    "labour_force_status": "Work or labour-force category for the selected person.",
    "household_income": "Grouped household-income bracket from the synthetic-population workflow: < $20k, $20k-$59,999, $60k-$99,999, or $100k+.",
    "fsa_context": "Montreal FSA selected by the user. DSM report scores are evaluated at this area level.",
    "source_da": "The DA code from the latest synthetic-population run that supplied this resident option.",
    "source_synpop_file": "The local processed synthetic-population artifact used to sample resident options.",
    "resident_id": "App-level ID for this sampled resident option.",
    "HID": "Household donor identifier from the synthetic-population output. Shown for traceability only.",
    "person_uid": "Demo person identifier used inside this app.",
    "code_agegrp": "Internal age-group code from the source synthetic-population artifact.",
    "code_lfact": "Internal labour-force code from the source synthetic-population artifact.",
    "code_totinc": "Internal income-code index from the source synthetic-population artifact.",
    "code_hhtype": "Internal household-type code from the source synthetic-population artifact.",
    "commute_mode": "Main commute mode category from the synthetic-population output.",
    "commute_duration": "Commute-duration category. Not applicable may indicate no regular commute or work from home.",
    "inferred_schedule_type": "A simple demo inference from work status, commute mode, and commute duration. It is not a directly observed survey variable.",
    "core_housing_need": "Housing-need indicator carried from the household-side synthetic-population schema.",
    "Demo area": "Small demo DA-like area assigned to the synthetic resident.",
    "Energy/DSM area context": "The FSA-level energy and DSM score row linked to the resident's demo area. This is not an individual attribute.",
    "Winter peak intensity": "Area-level winter peak proxy used to represent demand relevance.",
    "Area tenure mix": "Owner/renter share for the matched area context, not the selected household.",
    "Area median income proxy": "Area-level income proxy for the matched context, not the selected household income.",
    "DSM area context": "Demo area and matched FSA-level energy baseline used for energy interpretation.",
    "Age group": "Synthetic-population age category for this selected person.",
    "Household type": "Household composition category for this selected household.",
    "Household size": "Number of people in this selected synthetic household.",
    "Dwelling type": "Dwelling form for this selected household.",
    "Labour status": "Work or labour-force category for this selected person.",
    "Income group": "Grouped household income category for this selected household.",
    "Schedule type": "Demo inference from work and commute fields. It is not an original source variable.",
}


def display_label(key: str) -> str:
    return FIELD_LABELS.get(key, key.replace("_", " ").title())


def display_help(key: str) -> str:
    return FIELD_HELP.get(key, "")


def render_field_cards(fields: dict[str, str]) -> None:
    cards = ['<div class="resident-grid">']
    for key, value in fields.items():
        label = escape(display_label(key))
        help_text = escape(display_help(key), quote=True)
        display_value = escape(str(value))
        help_badge = f'<span class="help-dot" title="{help_text}">?</span>' if help_text else ""
        cards.append(
            f'<div class="resident-card"><div class="resident-label">{label}{help_badge}</div>'
            f'<div class="resident-value">{display_value}</div></div>'
        )
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)


def save_feedback(entry: dict[str, str]) -> None:
    row = {
        "feedback_id": str(uuid.uuid4()),
        "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
        **entry,
    }
    if save_feedback_to_google_sheet(row):
        return
    save_feedback_to_csv(row)


def save_feedback_to_csv(row: dict[str, str]) -> None:
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([row])
    frame.to_csv(FEEDBACK_PATH, mode="a", header=not FEEDBACK_PATH.exists(), index=False, encoding="utf-8")


def secret_section(name: str) -> dict:
    try:
        return dict(st.secrets.get(name, {}))
    except Exception:
        return {}


def save_feedback_to_google_sheet(row: dict[str, str]) -> bool:
    feedback_config = secret_section("feedback")
    service_account_info = secret_section("google_service_account")
    sheet_id = feedback_config.get("google_sheet_id") or feedback_config.get("sheet_id")
    worksheet_name = feedback_config.get("worksheet_name", "feedback")
    if not sheet_id or not service_account_info:
        return False
    try:
        import gspread

        client = gspread.service_account_from_dict(service_account_info)
        spreadsheet = client.open_by_key(sheet_id)
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=max(20, len(row)))
        columns = list(row)
        existing_header = worksheet.row_values(1)
        if not existing_header:
            worksheet.append_row(columns, value_input_option="USER_ENTERED")
            existing_header = columns
        for column in columns:
            if column not in existing_header:
                existing_header.append(column)
        if existing_header != worksheet.row_values(1):
            worksheet.update("A1", [existing_header])
        worksheet.append_row([row.get(column, "") for column in existing_header], value_input_option="USER_ENTERED")
        return True
    except Exception:
        return False


def read_feedback() -> pd.DataFrame:
    if not FEEDBACK_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(FEEDBACK_PATH)


def render_intro(metadata: dict) -> None:
    st.markdown(
        """
        This demo connects two research threads into one visitor-facing workflow. First, it maps Montreal Forward
        Sortation Areas (FSAs) through a demand-side-management alignment framework: PRISM heating sensitivity,
        short-term winter demand indicators, and socio-demographic capacity proxies are used to diagnose whether
        each program is structurally well matched to local demand. Second, it links those FSA contexts to synthetic
        resident options so the audience can see why average-area targeting can hide household-level constraints.
        """
    )
    with st.expander("Workflow and matrix summary", expanded=True):
        left, right = st.columns([1, 1])
        with left:
            st.markdown(
                """
                **Workflow**

                1. Select a Montreal FSA from the map.
                2. Review the selected FSA against PRISM, short-term demand, and socio-demographic indicators.
                3. Inspect program-level DSM alignment, keeping demand-related and capacity-related dimensions separate.
                4. Use synthetic residents when the demo path needs household-level interpretation.
                """
            )
        with right:
            st.markdown(
                """
                **Relevance-capacity matrix**

                The matrix compares where system demand is high with where a program has enough participation
                capacity, technical suitability, adoption capacity, or vulnerability concentration. The four classes
                are ideal targets, policy gaps, low-priority areas, and minimal-impact areas.
                """
            )
    st.caption(metadata["disclaimer"])


def render_path_selector(current_mode: str) -> str:
    st.subheader("Demo path")
    st.caption("Choose the conference-facing path. The map remains the primary FSA selector for all paths.")
    columns = st.columns(len(DEMO_PATH_META))
    selected_mode = current_mode
    for column, (mode, meta) in zip(columns, DEMO_PATH_META.items(), strict=False):
        with column:
            selected = mode == current_mode
            card_class = "path-card path-card-selected" if selected else "path-card"
            st.markdown(
                f"""
                <div class="{card_class}">
                    <div class="path-logo {meta['logo_class']}">{escape(meta['logo'])}</div>
                    <div class="path-title">{escape(meta['title'])}</div>
                    <div class="path-description">{escape(meta['description'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "Active" if selected else "Select path",
                key=f"path_select_{mode}",
                type="primary" if selected else "secondary",
                width="stretch",
            ):
                selected_mode = mode
    return selected_mode


def selected_fsa_from_plotly_event(event: object, valid_fsas: set[str]) -> str | None:
    if event is None:
        return None
    selection = event.get("selection", {}) if isinstance(event, dict) else getattr(event, "selection", {})
    points = selection.get("points", []) if isinstance(selection, dict) else getattr(selection, "points", [])
    if not points:
        return None
    point = points[0]
    if isinstance(point, dict):
        candidates = [point.get("location"), point.get("text")]
        customdata = point.get("customdata")
        if isinstance(customdata, (list, tuple)):
            candidates.extend(customdata)
        elif customdata is not None:
            candidates.append(customdata)
    else:
        candidates = [getattr(point, "location", None), getattr(point, "text", None)]
        customdata = getattr(point, "customdata", None)
        if isinstance(customdata, (list, tuple)):
            candidates.extend(customdata)
        elif customdata is not None:
            candidates.append(customdata)
    for candidate in candidates:
        if candidate in valid_fsas:
            return str(candidate)
    return None


def request_fsa_change(fsa: str) -> None:
    st.session_state.pending_fsa_context = fsa


def render_pending_fsa_change(population: pd.DataFrame) -> None:
    pending_fsa = st.session_state.get("pending_fsa_context")
    if not pending_fsa or pending_fsa == st.session_state.selected_fsa_context:
        return
    st.warning(f"Change selected FSA from {st.session_state.selected_fsa_context} to {pending_fsa}?")
    yes, no = st.columns([0.18, 0.82])
    with yes:
        if st.button("Yes, update", type="primary", key="confirm_fsa_change"):
            set_selected_fsa(pending_fsa, population)
            st.session_state.pending_fsa_context = None
            st.rerun()
    with no:
        if st.button("Cancel", key="cancel_fsa_change"):
            st.session_state.pending_fsa_context = None
            st.rerun()


def set_selected_fsa(fsa: str, population: pd.DataFrame) -> None:
    st.session_state.selected_fsa_context = fsa
    residents = population.loc[population["fsa_context"] == fsa]
    if not residents.empty:
        st.session_state.selected_resident_id = residents.iloc[0]["resident_id"]


def render_resident_option_card(resident_row: pd.Series, selected: bool = False) -> None:
    css_class = "resident-option resident-option-selected" if selected else "resident-option"
    lines = [
        f"<div class='{css_class}'>",
        f"<div class='resident-option-title'>{escape(str(resident_row['resident_id']))}</div>",
        f"<div class='resident-option-line'><b>Age:</b> {escape(str(resident_row['age_group']))}</div>",
        f"<div class='resident-option-line'><b>Household:</b> {escape(str(resident_row['household_type']))}</div>",
        f"<div class='resident-option-line'><b>Size:</b> {escape(str(resident_row['household_size']))}</div>",
        f"<div class='resident-option-line'><b>Work:</b> {escape(str(resident_row['labour_force_status']))}</div>",
        f"<div class='resident-option-line'><b>Income:</b> {escape(str(resident_row['household_income']))}</div>",
        "</div>",
    ]
    st.markdown("".join(lines), unsafe_allow_html=True)


def render_buildsys_path(population: pd.DataFrame, residents_in_fsa: pd.DataFrame, resident: pd.Series) -> None:
    tab_profile, tab_support, tab_population = st.tabs(["Resident Sample", "Attribute Support", "Population Context"])
    with tab_profile:
        st.subheader("Support-aware synthetic residents")
        st.write(
            "This path mirrors the BuildSys paper: the resident is not a real person, but a census-consistent synthetic household/person record assembled from public-data marginals and microdata support."
        )
        left, right = st.columns([1.2, 1])
        with left:
            render_field_cards(resident_summary(resident))
        with right:
            st.markdown("#### Interpretation boundary")
            st.info(
                "Stable household/person attributes can support central interpretation. Mobility and some housing-quality fields are useful exploratory proxies, not direct occupancy schedules or causal explanations."
            )
            st.dataframe(
                residents_in_fsa[["resident_id", "age_group", "household_type", "household_income", "labour_force_status"]],
                width="stretch",
                hide_index=True,
            )
    with tab_support:
        st.subheader("Attribute validation framing")
        st.write(
            "The BuildSys contribution is not only adding more variables; it is making clear which variables are strongly supported and which should be used cautiously downstream."
        )
        st.dataframe(BUILDSYS_ATTRIBUTE_SUPPORT, width="stretch", hide_index=True)
        stable_share = BUILDSYS_ATTRIBUTE_SUPPORT["Support"].eq("Stable").mean()
        c1, c2, c3 = st.columns(3)
        c1.metric("Attributes shown", len(BUILDSYS_ATTRIBUTE_SUPPORT))
        c2.metric("Stable share", f"{stable_share:.0%}")
        c3.metric("Lowest TVD", f"{BUILDSYS_ATTRIBUTE_SUPPORT['TVD'].min():.4f}")
        st.caption("TVD values are paper-reported Plateau-Mont-Royal validation results; the demo resident sample uses the latest Montreal synthetic-population artifact.")
    with tab_population:
        st.subheader("Why heterogeneity matters for UBEM")
        a, b = st.columns(2)
        with a:
            st.plotly_chart(distribution_bar(population, "household_type", "Household structure"), width="stretch")
        with b:
            st.plotly_chart(distribution_bar(population, "household_income", "Household income group"), width="stretch")
        c, d = st.columns(2)
        with c:
            st.plotly_chart(distribution_bar(population, "labour_force_status", "Work status"), width="stretch")
        with d:
            st.plotly_chart(distribution_bar(population, "inferred_schedule_type", "Inferred schedule proxy"), width="stretch")


def esim_class_label(raw_class: str) -> str:
    return ESIM_CLASS_LABELS.get(raw_class, raw_class.replace("_", " ").title())


def esim_program_score_rows(selected_scores: pd.Series) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "program": ["Flex D", "Hilo", "LogisVert", "Low-income assistance"],
            "alignment_score": [
                selected_scores["Flex D"],
                selected_scores["Hilo"],
                selected_scores["LogisVert"],
                selected_scores["Low-income assistance"],
            ],
        }
    ).sort_values("alignment_score", ascending=False)


def esim_demo_class_distribution(real_alignment: pd.DataFrame, program: str) -> pd.DataFrame:
    class_col = ESIM_PROGRAM_AXES[program]["class_col"]
    out = (
        real_alignment[class_col]
        .map(esim_class_label)
        .value_counts()
        .rename_axis("Class")
        .reset_index(name="Current demo FSAs")
    )
    order = ["Ideal target", "Policy gap", "Low priority", "Minimal impact"]
    out["Class"] = pd.Categorical(out["Class"], order, ordered=True)
    return out.sort_values("Class").reset_index(drop=True)


def esim_component_breakdown(report_row: pd.Series) -> pd.DataFrame:
    rows = [
        ("Flex D", "Demand relevance", "demand_relevance", 0.55),
        ("Flex D", "Temporal flexibility", "temporal_flexibility", 0.45 * 0.50),
        ("Flex D", "Demand elasticity", "demand_elasticity", 0.45 * 0.50),
        ("Hilo", "Demand relevance", "demand_relevance", 0.50),
        ("Hilo", "Technical eligibility", "technical_eligibility", 0.50 / 3),
        ("Hilo", "Control authority", "control_authority", 0.50 / 3),
        ("Hilo", "Curtailment tolerance", "curtailment_tolerance", 0.50 / 3),
        ("LogisVert", "Structural demand", "structural_demand_relevance", 0.50),
        ("LogisVert", "Adoption capacity", "adoption_capacity", 0.25),
        ("LogisVert", "Persistence capacity", "persistence_capacity", 0.25),
        ("Low-income assistance", "System relevance", "system_relevance", 0.50),
        ("Low-income assistance", "Energy vulnerability", "energy_vulnerability", 0.50),
    ]
    return pd.DataFrame(
        [
            {
                "program": program,
                "component": component,
                "source_value": float(report_row[source_col]),
                "weight": weight,
                "contribution": float(report_row[source_col]) * weight,
                "value": float(report_row[source_col]) * weight,
                "description": ESIM_COMPONENT_DESCRIPTIONS[component],
            }
            for program, component, source_col, weight in rows
        ]
    )


def esim_program_axis_rows(report_row: pd.Series) -> pd.DataFrame:
    rows = [
        {
            "Program": "Flex D",
            "Demand-related": float(report_row["demand_relevance"]),
            "Capacity-related": float(report_row["participation_capacity"]),
            "Demand label": "Demand relevance",
            "Capacity label": "Participation capacity",
        },
        {
            "Program": "Hilo",
            "Demand-related": float(report_row["demand_relevance"]),
            "Capacity-related": float(report_row["hilo_suitability"]),
            "Demand label": "Demand relevance",
            "Capacity label": "Hilo suitability",
        },
        {
            "Program": "LogisVert",
            "Demand-related": float(report_row["structural_demand_relevance"]),
            "Capacity-related": float(report_row["overall_capacity"]),
            "Demand label": "Structural demand relevance",
            "Capacity label": "Overall retrofit capacity",
        },
        {
            "Program": "Low-income assistance",
            "Demand-related": float(report_row["system_relevance"]),
            "Capacity-related": float(report_row["energy_vulnerability"]),
            "Demand label": "System relevance",
            "Capacity label": "Energy vulnerability",
        },
    ]
    return pd.DataFrame(rows)


def selected_area_profile(dsm_profiles: pd.DataFrame, selected_fsa_context: str) -> pd.Series | None:
    matches = dsm_profiles.loc[dsm_profiles["fsa_context"].eq(selected_fsa_context)]
    if matches.empty:
        return None
    return matches.iloc[0]


def energy_feature_cards(area_profile: pd.Series) -> dict[str, str]:
    fields = {
        "Winter peak share": f"{float(area_profile['winter_peak_share']):.3f}",
        "Heating slope per HDD": f"{float(area_profile['heating_slope_per_hdd']):.2f}",
        "Heating change point": f"{float(area_profile['heating_change_point_temp_c']):.1f} C",
        "Baseload intercept": f"{float(area_profile['baseload_intercept']):.2f}",
        "Cooling slope per CDD": f"{float(area_profile['cooling_slope_per_cdd']):.3f}",
        "Winter peak intensity": f"{float(area_profile['winter_peak_intensity']):.2f}",
        "Daily peak load": f"{float(area_profile['peak_load']):.2f}",
        "Top 10% load mean": f"{float(area_profile['p90_top10_mean']):.2f}",
        "Mean load": f"{float(area_profile['mean_load']):.2f}",
        "Morning/evening peak ratio": f"{float(area_profile['am_pm_peak_ratio']):.2f}",
        "Ramp-up rate": f"{float(area_profile['ramp_up_rate']):.3f}",
    }
    cluster = area_profile.get("dtw_cluster_label")
    if pd.notna(cluster):
        fields["DTW cluster label"] = str(cluster)
    return fields


def available_energy_fsa_text(dsm_profiles: pd.DataFrame) -> str:
    fsas = dsm_profiles["fsa_context"].dropna().drop_duplicates().sort_values().tolist()
    return ", ".join(fsas)


def render_esim_path(
    selected_fsa_context: str,
    real_alignment: pd.DataFrame,
    all_fsa_scores: pd.DataFrame,
    population: pd.DataFrame,
    valid_fsas: set[str],
) -> None:
    tab_results, tab_programs, tab_info = st.tabs(["FSA Results", "Program Analysis", "Info"])
    selected_scores = all_fsa_scores.loc[all_fsa_scores["fsa_context"] == selected_fsa_context]
    if selected_scores.empty:
        st.warning("No DSM alignment row found for the selected FSA.")
        return
    selected_scores = selected_scores.iloc[0]
    score_rows = esim_program_score_rows(selected_scores)
    report_row = real_alignment.loc[real_alignment["fsa"] == selected_fsa_context].iloc[0]
    esim_breakdown = esim_component_breakdown(report_row)
    area_profile = selected_area_profile(dsm_profiles, selected_fsa_context)
    program_axes = esim_program_axis_rows(report_row)

    with tab_results:
        st.subheader(f"Analysis results for FSA {selected_fsa_context}")
        st.write(
            "This view compares the selected FSA with the rest of the Montreal FSA set. The values are normalized FSA-level indicators, so they show structural position in the study area rather than individual household predictions."
        )
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Best program score", score_rows.iloc[0]["program"])
        with m2:
            st.metric("Score", f"{float(score_rows.iloc[0]['alignment_score']):.2f}")
        with m3:
            st.metric("Demand relevance", f"{float(report_row['demand_relevance']):.2f}")
        with m4:
            st.metric("Energy vulnerability", f"{float(report_row['energy_vulnerability']):.2f}")

        st.subheader("Energy-demand features")
        st.caption(f"Raw energy-profile data are available for {dsm_profiles['fsa_context'].nunique()} FSAs: {available_energy_fsa_text(dsm_profiles)}.")
        if area_profile is None:
            st.info(
                "Raw PRISM/load feature rows are not included for this FSA in the current demo extract. "
                "The FSA-wide alignment indices above are still available, but the paper's raw energy-feature diagnostics "
                "should be added for full manuscript fidelity."
            )
        else:
            st.caption(
                "Available energy features from the processed Montreal FSA DSM tables. These align with the paper's PRISM and short-term winter-load feature layer; hourly average daily profiles and usable DTW cluster labels are still not included in this compact deploy artifact."
            )
            long_term_energy_metrics = [
                ("heating_slope_per_hdd", "Heating slope per HDD"),
                ("heating_change_point_temp_c", "Heating change point"),
                ("baseload_intercept", "Baseload intercept"),
                ("cooling_slope_per_cdd", "Cooling slope per CDD"),
                ("winter_peak_share", "Winter peak share"),
                ("winter_peak_intensity", "Winter peak intensity"),
            ]
            short_term_energy_metrics = [
                ("peak_load", "Daily peak load"),
                ("p90_top10_mean", "Top 10% load mean"),
                ("mean_load", "Mean load"),
                ("am_pm_peak_ratio", "Morning/evening peak ratio"),
                ("ramp_up_rate", "Ramp-up rate"),
            ]
            long_scatter, short_scatter = st.columns(2)
            with long_scatter:
                st.plotly_chart(
                    energy_relationship_scatter(
                        dsm_profiles,
                        selected_fsa_context,
                        x_col="heating_change_point_temp_c",
                        y_col="heating_slope_per_hdd",
                        title="Long-term PRISM signature",
                        x_label="Heating change point (C)",
                        y_label="Heating slope per HDD",
                        color_col="baseload_intercept",
                        color_label="Baseload intercept",
                        size_col="winter_peak_intensity",
                        size_label="Winter peak intensity",
                    ),
                    width="stretch",
                )
            with short_scatter:
                st.plotly_chart(
                    energy_relationship_scatter(
                        dsm_profiles,
                        selected_fsa_context,
                        x_col="peak_load",
                        y_col="ramp_up_rate",
                        title="Short-term winter load signature",
                        x_label="Daily peak load",
                        y_label="Ramp-up rate",
                        color_col="am_pm_peak_ratio",
                        color_label="Morning/evening peak ratio",
                        size_col="p90_top10_mean",
                        size_label="Top 10% load mean",
                    ),
                    width="stretch",
                )

            render_field_cards(energy_feature_cards(area_profile))

            with st.expander("Energy metric percentiles", expanded=False):
                p_left, p_right = st.columns(2)
                with p_left:
                    st.plotly_chart(
                        energy_percentile_strip(
                            dsm_profiles,
                            selected_fsa_context,
                            long_term_energy_metrics,
                            "Long-term energy feature percentiles",
                        ),
                        width="stretch",
                    )
                with p_right:
                    st.plotly_chart(
                        energy_percentile_strip(
                            dsm_profiles,
                            selected_fsa_context,
                            short_term_energy_metrics,
                            "Short-term load feature percentiles",
                        ),
                        width="stretch",
                    )

        derived_demand_metrics = [
            ("structural_demand_relevance", "Structural demand"),
            ("technical_eligibility", "Technical eligibility"),
            ("demand_relevance", "Demand relevance"),
        ]
        short_term_metrics = [
            ("temporal_flexibility", "Temporal flexibility"),
            ("demand_elasticity", "Demand elasticity"),
            ("curtailment_tolerance", "Curtailment tolerance"),
        ]
        st.subheader("Derived alignment indicators")
        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                selected_vs_rest_bar(real_alignment, selected_fsa_context, "fsa", derived_demand_metrics, "Demand and technical indices"),
                width="stretch",
            )
        with right:
            st.plotly_chart(
                selected_vs_rest_bar(real_alignment, selected_fsa_context, "fsa", short_term_metrics, "Short-term flexibility indices"),
                width="stretch",
            )

        st.subheader("Socio-demographic context")
        if area_profile is None:
            st.info("The current demo extract does not include socio-demographic profile rows for this FSA.")
        else:
            socio_metrics = [
                ("owner_pct", "Owner share"),
                ("renter_pct", "Renter share"),
                ("single_detached_house_pct", "Single-detached share"),
                ("apartment_pct", "Apartment share"),
                ("low_income_pct", "Low-income share"),
                ("older_65_plus_pct", "Older-adult share"),
                ("children_0_14_pct", "Children share"),
                ("commute_60_min_plus_pct", "Long commute share"),
            ]
            profile = dsm_profiles.copy()
            socio_left, socio_right = st.columns(2)
            with socio_left:
                st.plotly_chart(
                    energy_percentile_strip(
                        profile,
                        selected_fsa_context,
                        socio_metrics,
                        "Socio-demographic indicator percentiles",
                    ),
                    width="stretch",
                )
            with socio_right:
                st.plotly_chart(
                    energy_relationship_scatter(
                        profile,
                        selected_fsa_context,
                        x_col="owner_pct",
                        y_col="low_income_pct",
                        title="Housing tenure and income context",
                        x_label="Owner share (%)",
                        y_label="Low-income share (%)",
                        color_col="apartment_pct",
                        color_label="Apartment share (%)",
                        size_col="median_income",
                        size_label="Median income",
                    ),
                    width="stretch",
                )

        st.subheader("Resident-option distributions")
        d1, d2 = st.columns(2)
        with d1:
            st.plotly_chart(selected_distribution_bar(population, selected_fsa_context, "household_income", "Household income distribution"), width="stretch")
        with d2:
            st.plotly_chart(selected_distribution_bar(population, selected_fsa_context, "household_type", "Household-structure distribution"), width="stretch")

    with tab_programs:
        st.subheader("Program analysis")
        st.write(
            "Overall program scores are shown with demand-related and capacity-related dimensions kept separate. The matrix below is secondary: click a dot when you want to move the whole app to a different FSA."
        )
        st.plotly_chart(program_axis_stacked_bar(program_axes, "Separated demand and capacity axes by program"), width="stretch")
        st.caption(
            "The annotation above each stacked bar is the two-axis average used for the FSA-level program score. The stacked height is not interpreted as a combined program value."
        )

        program = st.radio("Matrix program", list(ESIM_PROGRAM_AXES), horizontal=True, key="esim_results_matrix_program")
        config = ESIM_PROGRAM_AXES[program]
        selected_class = esim_class_label(str(report_row[config["class_col"]]))
        selected_score = float(selected_scores[config["program_column"]])
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Selected FSA", selected_fsa_context)
        with c2:
            st.metric("Matrix class", selected_class)
        with c3:
            st.metric(config["relevance_label"], f"{report_row[config['relevance_col']]:.2f}")
        with c4:
            st.metric(config["capacity_label"], f"{report_row[config['capacity_col']]:.2f}")
        matrix_event = st.plotly_chart(
            relevance_capacity_matrix(
                real_alignment,
                selected_fsa_context,
                relevance_col=config["relevance_col"],
                capacity_col=config["capacity_col"],
                class_col=config["class_col"],
                title=f"{program}: relevance-capacity matrix",
                relevance_label=config["relevance_label"],
                capacity_label=config["capacity_label"],
            ),
            width="stretch",
            key=f"esim_matrix_{program}",
            on_select="rerun",
            selection_mode=["points"],
        )
        matrix_fsa = selected_fsa_from_plotly_event(matrix_event, valid_fsas)
        if matrix_fsa and matrix_fsa != selected_fsa_context:
            request_fsa_change(matrix_fsa)
        render_pending_fsa_change(population)
        st.caption(
            f"Selected FSA {selected_fsa_context} has a composite {program} alignment score of {selected_score:.2f}. "
            "The dashed thresholds use the current demo extract's quantile split; the paper table below reports the submitted-paper class counts."
        )
        demo_counts = esim_demo_class_distribution(real_alignment, program)
        paper_counts = ESIM_PAPER_CLASS_DISTRIBUTION.loc[
            ESIM_PAPER_CLASS_DISTRIBUTION["Program"].eq(program)
        ].reset_index(drop=True)
        count_table = paper_counts.merge(demo_counts, on="Class", how="left").fillna({"Current demo FSAs": 0})
        st.dataframe(count_table, width="stretch", hide_index=True)

        st.subheader("Detailed program components")
        left, right = st.columns([0.9, 1.2])
        with left:
            if alignment_breakdown_bar is None:
                st.plotly_chart(alignment_bar(score_rows), width="stretch")
            else:
                st.plotly_chart(alignment_breakdown_bar(esim_breakdown), width="stretch")
            st.caption("Each total score is decomposed into the paper subindices used for that program.")
        with right:
            index_rows = pd.DataFrame(
                [
                    ("Demand relevance", report_row["demand_relevance"], "System need for peak-oriented programs"),
                    ("Participation capacity", report_row["participation_capacity"], "Flex D behavioral readiness"),
                    ("Temporal flexibility", report_row["temporal_flexibility"], "Ability to shift peak-period routines"),
                    ("Demand elasticity", report_row["demand_elasticity"], "Likelihood of price response"),
                    ("Hilo suitability", report_row["hilo_suitability"], "Automated response readiness"),
                    ("Technical eligibility", report_row["technical_eligibility"], "Controllable electric-heating proxy"),
                    ("Control authority", report_row["control_authority"], "Tenure and installation authority proxy"),
                    ("Curtailment tolerance", report_row["curtailment_tolerance"], "Capacity to tolerate short automated adjustments"),
                    ("Structural demand relevance", report_row["structural_demand_relevance"], "Retrofit/equipment-upgrade relevance"),
                    ("Overall retrofit capacity", report_row["overall_capacity"], "Ability to adopt structural upgrades"),
                    ("System relevance", report_row["system_relevance"], "Peak-system relevance for protection programs"),
                    ("Energy vulnerability", report_row["energy_vulnerability"], "Affordability and hardship exposure"),
                ],
                columns=["Index", "Value", "Paper interpretation"],
            )
            st.dataframe(index_rows, width="stretch", hide_index=True)
        st.info(
            "These are FSA-level normalized indices from the DSM report workflow. They describe local structural fit, not a resident-level recommendation."
        )

    with tab_info:
        st.subheader("Workflow notes and references")
        st.write(
            "This workflow evaluates structural alignment rather than realized program impacts. It asks whether each DSM program's assumptions are co-located with FSA-level demand pressures and socio-demographic conditions."
        )
        st.markdown(
            "- **Paper workflow**: PRISM-derived heating sensitivity, winter peak/load-shape indicators, DML-informed socio-demographic associations, and program-specific relevance-capacity classes.\n"
            "- **Program pathways**: Tarif Flex D, Hilo, LogisVert, and low-income assistance are evaluated as different demand and capacity mechanisms.\n"
            "- **Interpretation**: high-demand FSAs are not automatically high-flexibility, high-eligibility, high-capacity, or high-vulnerability FSAs.\n"
            "- **Current demo data boundary**: raw PRISM and short-term aggregate features are now present for the 94 Montreal FSAs in the alignment extract; usable DTW cluster labels, hourly average daily profiles, and full DML feature-importance tables are still not included in this compact deploy artifact.\n"
            "- **Author links**: [Google Scholar](https://scholar.google.com/citations?hl=en&user=7BeRoW4AAAAJ) | [LinkedIn](https://ca.linkedin.com/in/masoodshamsaiee).\n"
            "- **Related paper links**: [BuildSys 2026 program](https://buildsys.acm.org/2026/program/) | [Energy & Buildings article record](https://ui.adsabs.harvard.edu/abs/2026EneBu.35216793S/abstract) | [SSRN preprint](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5381520).\n"
            "- **Contact**: Masood Shamsaiee, Next-Generation Cities Institute, Concordia University."
        )
        st.subheader("Program-specific assumptions used in the paper")
        st.dataframe(ESIM_PROGRAM_CONTEXT, width="stretch", hide_index=True)
        if ESIM_MATRIX_IMAGE.exists():
            st.image(str(ESIM_MATRIX_IMAGE), caption="Relevance-capacity matrix used in the eSim paper.")


@st.cache_data
def load_data():
    population = read_fsa_resident_options()
    population["display_name"] = (
        population["resident_id"].astype(str)
        + " | DA "
        + population["source_da"].astype(str)
        + " | "
        + population["age_group"].astype(str)
        + " | "
        + population["household_type"].astype(str)
    )
    dsm_profiles = read_dsm_profiles()
    real_alignment = read_real_dsm_alignment()
    area_locations = read_area_locations()
    fsa_geojson = read_fsa_geojson()
    metadata = load_metadata()
    return population, dsm_profiles, real_alignment, area_locations, fsa_geojson, metadata


population, dsm_profiles, real_alignment, area_locations, fsa_geojson, metadata = load_data()
area_scores = compute_report_alignment(dsm_profiles, real_alignment)
all_fsa_scores = all_fsa_report_alignment(real_alignment)

st.title("UBEM Human Flexibility Demo")
render_intro(metadata)
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = "eSim DSM alignment"
demo_mode = render_path_selector(st.session_state.demo_mode)
if demo_mode != st.session_state.demo_mode:
    st.session_state.demo_mode = demo_mode
    st.rerun()

fsa_options = real_alignment["fsa"].sort_values().tolist()
valid_fsas = set(fsa_options)
if "selected_fsa_context" not in st.session_state:
    st.session_state.selected_fsa_context = fsa_options[0]
if "selected_resident_id" not in st.session_state:
    first_resident = population.loc[population["fsa_context"] == st.session_state.selected_fsa_context].iloc[0]
    st.session_state.selected_resident_id = first_resident["resident_id"]

st.subheader("1. Choose a Montreal FSA from the map")
st.caption("Click a dot to propose a new FSA. The app asks for confirmation before changing the active analysis context.")
map_event = st.plotly_chart(
    fsa_context_map(
        dsm_profiles,
        all_fsa_scores,
        fsa_geojson,
        area_locations,
        selected_fsa=st.session_state.selected_fsa_context,
        title="Primary FSA selector",
    ),
    width="stretch",
    key="primary_fsa_map",
    on_select="rerun",
    selection_mode=["points"],
)
clicked_fsa = selected_fsa_from_plotly_event(map_event, valid_fsas)
if clicked_fsa and clicked_fsa != st.session_state.selected_fsa_context:
    request_fsa_change(clicked_fsa)
render_pending_fsa_change(population)

selection_a, selection_b = st.columns(2)
with selection_a:
    st.metric("Selected FSA", st.session_state.selected_fsa_context)
with selection_b:
    if demo_mode == "eSim DSM alignment":
        selected_demand = all_fsa_scores.loc[all_fsa_scores["fsa_context"] == st.session_state.selected_fsa_context, "demand_relevance"]
        st.metric("Demand relevance", f"{selected_demand.iloc[0]:.2f}" if not selected_demand.empty else "n/a")
    else:
        st.metric("Resident", st.session_state.selected_resident_id)

if demo_mode != "eSim DSM alignment":
    st.subheader("2. Choose a resident card")
    resident_cards = population.loc[population["fsa_context"] == st.session_state.selected_fsa_context].reset_index(drop=True)
    card_columns = st.columns(len(resident_cards))
    for card_index, (_, option) in enumerate(resident_cards.iterrows()):
        with card_columns[card_index]:
            is_selected = option["resident_id"] == st.session_state.selected_resident_id
            render_resident_option_card(option, selected=is_selected)
            if st.button(
                "Selected" if is_selected else "Select",
                key=f"select_resident_{option['resident_id']}",
                type="primary" if is_selected else "secondary",
                width="stretch",
            ):
                st.session_state.selected_resident_id = option["resident_id"]
                st.rerun()

with st.sidebar:
    st.header("Current selection")
    st.metric("FSA", st.session_state.selected_fsa_context)
    if demo_mode != "eSim DSM alignment":
        st.caption(f"Resident: {st.session_state.selected_resident_id}")
        st.caption("Use the map and resident cards as the primary selector.")
    else:
        st.caption("Use the map as the primary selector.")
    with st.expander("Manual selection fallback", expanded=False):
        manual_fsa = st.selectbox(
            "Montreal FSA",
            fsa_options,
            index=fsa_options.index(st.session_state.selected_fsa_context),
            help="Fallback selector if map selection is inconvenient.",
        )
        if manual_fsa != st.session_state.selected_fsa_context:
            set_selected_fsa(manual_fsa, population)
            st.rerun()

selected_fsa_context = st.session_state.selected_fsa_context
residents_in_fsa = population.loc[population["fsa_context"] == selected_fsa_context].reset_index(drop=True)
if st.session_state.selected_resident_id not in set(residents_in_fsa["resident_id"]):
    st.session_state.selected_resident_id = residents_in_fsa.iloc[0]["resident_id"]
resident = residents_in_fsa.loc[residents_in_fsa["resident_id"] == st.session_state.selected_resident_id].iloc[0]

scores, explanations = score_resident(resident, dsm_profiles, real_alignment, fsa_context=selected_fsa_context)
selected_breakdown = pd.concat(
    [
        program_breakdown(
            program,
            resident,
            dsm_profiles,
            real_alignment,
            fsa_context=selected_fsa_context,
        ).assign(program=program)
        for program in scores["program"]
    ],
    ignore_index=True,
)
top = scores.iloc[0]

with st.sidebar:
    with st.expander("Send feedback", expanded=False):
        st.caption("Share what worked, what was confusing, or what should be improved.")
        with st.form("feedback_form", clear_on_submit=True):
            feedback_section = st.selectbox(
                "What are you reacting to?",
                [
                    "Overall demo",
                    "BuildSys synthetic population path",
                    "eSim DSM alignment path",
                    "Integrated demo path",
                    "Map/FSA selection",
                    "Resident profile",
                    "DSM suitability",
                    "Resident comparison",
                    "Scientific interpretation",
                ],
            )
            feedback_rating = st.radio(
                "How clear was it?",
                ["Very clear", "Mostly clear", "Unclear", "Confusing"],
                horizontal=False,
            )
            feedback_comment = st.text_area(
                "Feedback",
                placeholder="What worked, what was confusing, or what should be improved?",
                height=120,
            )
            feedback_role = st.text_input("Role or affiliation", placeholder="Optional")
            submitted = st.form_submit_button("Submit feedback", type="primary", width="stretch")
        if submitted:
            if not feedback_comment.strip():
                st.warning("Please add a short comment before submitting.")
            else:
                save_feedback(
                    {
                        "demo_mode": demo_mode,
                        "section": feedback_section,
                        "clarity_rating": feedback_rating,
                        "comment": feedback_comment.strip(),
                        "role_or_affiliation": feedback_role.strip(),
                        "selected_fsa": str(selected_fsa_context),
                        "selected_resident_id": str(resident["resident_id"]),
                        "source_da": str(resident["source_da"]),
                        "top_program": str(top["program"]),
                        "top_alignment_score": f"{float(top['alignment_score']):.4f}",
                    }
                )
                st.success("Thanks. Feedback submitted.")

if demo_mode == "BuildSys synthetic population":
    render_buildsys_path(population, residents_in_fsa, resident)
elif demo_mode == "eSim DSM alignment":
    render_esim_path(selected_fsa_context, real_alignment, all_fsa_scores, population, valid_fsas)
else:
    tab_resident, tab_dsm, tab_compare, tab_why = st.tabs(
        ["Resident Profile", "DSM Fit", "Compare People", "Population Context"]
    )

    with tab_resident:
        st.subheader("Meet a synthetic resident")
        left, right = st.columns([1.2, 1])
        with left:
            summary = resident_summary(resident)
            individual_fields = {
                key: value
                for key, value in summary.items()
                if key
                not in {
                    "area",
                }
            }
            render_field_cards(individual_fields)
            with st.expander("Data provenance", expanded=False):
                provenance_fields = {
                    "resident_id": resident["resident_id"],
                    "person_uid": resident["person_uid"],
                    "HID": resident["HID"],
                    "source_da": resident["source_da"],
                    "fsa_context": resident["fsa_context"],
                    "source_synpop_file": resident["source_synpop_file"],
                    "code_agegrp": resident["code_agegrp"],
                    "code_lfact": resident["code_lfact"],
                    "code_totinc": resident["code_totinc"],
                    "code_hhtype": resident["code_hhtype"],
                }
                render_field_cards(provenance_fields)
        with right:
            st.subheader("Matched FSA Energy Baseline")
            context_fields = {
                "Energy/DSM area context": selected_fsa_context,
            }
            render_field_cards(context_fields)
            st.caption(
                f"Workflow: selected FSA {selected_fsa_context} -> five residents sampled from latest synthetic-pop DAs mapped to that FSA -> selected resident {resident['resident_id']}."
            )

    with tab_dsm:
        st.subheader("DSM suitability is not one-size-fits-all")
        st.write(
            "Scores below are illustrative alignments. The DSM source repo evaluates spatial units using rank-based proxies; this demo combines the selected resident's matched area context with a small household-context resemblance modifier."
        )
        c1, c2, c3 = st.columns([0.9, 1.25, 1])
        with c1:
            st.metric("Best-fit illustrative strategy", top["program"])
            st.metric("Suitability band", score_label(float(top["alignment_score"])))
            st.metric("Alignment score", f"{top['alignment_score']:.2f}")
            st.caption(f"Area baseline: {top['source']} | FSA context: {top['fsa_context']}")
        with c2:
            if alignment_breakdown_bar is None:
                st.plotly_chart(alignment_bar(scores), width="stretch")
            else:
                st.plotly_chart(alignment_breakdown_bar(selected_breakdown), width="stretch")
        with c3:
            st.plotly_chart(radar_chart(scores), width="stretch")

        st.divider()
        st.subheader("Why this profile aligns")
        for _, row in scores.iterrows():
            with st.expander(f"{row['program']} | {score_label(float(row['alignment_score']))} suitability"):
                st.write(row["description"])
                st.write(explanations[row["program"]])
                breakdown = program_breakdown(
                    row["program"],
                    resident,
                    dsm_profiles,
                    real_alignment,
                    fsa_context=selected_fsa_context,
                )
                if stacked_breakdown_bar is None:
                    st.bar_chart(
                        breakdown.set_index("component")[["contribution"]],
                        horizontal=True,
                        height=190,
                    )
                else:
                    st.plotly_chart(stacked_breakdown_bar(breakdown, row["program"]), width="stretch")
                for _, component in breakdown.iterrows():
                    st.markdown(
                        f"**{component['component']}**: {component['description']} "
                        f"Source subindex `{component['source_value']:.2f}` x weight `{component['weight']:.3f}` "
                        f"= contribution `{component['contribution']:.3f}`."
                    )
                st.progress(float(row["alignment_score"]))
                st.caption(
                    f"Area context: {row['area_context_score']:.2f}; household context: {row['household_context_score']:.2f}."
                )

    with tab_compare:
        st.subheader("Compare two synthetic residents")
        st.write(
            "Use this view to show why similar average demand contexts can still imply different DSM pathways once household heterogeneity is visible."
        )
        valid_compare_ids = residents_in_fsa["resident_id"].tolist()
        if st.session_state.get("compare_fsa_context") != selected_fsa_context:
            st.session_state.compare_fsa_context = selected_fsa_context
            st.session_state.compare_a_id = valid_compare_ids[0]
            st.session_state.compare_b_id = valid_compare_ids[1] if len(valid_compare_ids) > 1 else valid_compare_ids[0]
        if st.session_state.get("compare_a_id") not in valid_compare_ids:
            st.session_state.compare_a_id = valid_compare_ids[0]
        if st.session_state.get("compare_b_id") not in valid_compare_ids:
            st.session_state.compare_b_id = valid_compare_ids[1] if len(valid_compare_ids) > 1 else valid_compare_ids[0]

        st.caption("Assign two cards as Resident A and Resident B.")
        compare_columns = st.columns(len(residents_in_fsa))
        for card_index, (_, option) in enumerate(residents_in_fsa.iterrows()):
            with compare_columns[card_index]:
                assigned = option["resident_id"] in {st.session_state.compare_a_id, st.session_state.compare_b_id}
                render_resident_option_card(option, selected=assigned)
                a_type = "primary" if option["resident_id"] == st.session_state.compare_a_id else "secondary"
                b_type = "primary" if option["resident_id"] == st.session_state.compare_b_id else "secondary"
                if st.button("Set A", key=f"compare_set_a_{option['resident_id']}", type=a_type, width="stretch"):
                    st.session_state.compare_a_id = option["resident_id"]
                    st.rerun()
                if st.button("Set B", key=f"compare_set_b_{option['resident_id']}", type=b_type, width="stretch"):
                    st.session_state.compare_b_id = option["resident_id"]
                    st.rerun()

        resident_a = residents_in_fsa.loc[residents_in_fsa["resident_id"] == st.session_state.compare_a_id].iloc[0]
        resident_b = residents_in_fsa.loc[residents_in_fsa["resident_id"] == st.session_state.compare_b_id].iloc[0]
        fsa_a = resident_a["fsa_context"]
        fsa_b = resident_b["fsa_context"]
        scores_a, _ = score_resident(resident_a, dsm_profiles, real_alignment, fsa_context=fsa_a)
        scores_b, _ = score_resident(resident_b, dsm_profiles, real_alignment, fsa_context=fsa_b)

        profile_a, profile_b = st.columns(2)
        with profile_a:
            st.markdown("#### Resident A")
            render_field_cards(
                {
                    "Age group": resident_a["age_group"],
                    "Household type": resident_a["household_type"],
                    "Household size": resident_a["household_size"],
                    "Labour status": resident_a["labour_force_status"],
                    "Income group": resident_a["household_income"],
                    "Education": resident_a["education_level"],
                    "Schedule type": resident_a["inferred_schedule_type"],
                    "DSM area context": f"DA {resident_a['source_da']} -> {resident_a['fsa_context']}",
                }
            )
        with profile_b:
            st.markdown("#### Resident B")
            render_field_cards(
                {
                    "Age group": resident_b["age_group"],
                    "Household type": resident_b["household_type"],
                    "Household size": resident_b["household_size"],
                    "Labour status": resident_b["labour_force_status"],
                    "Income group": resident_b["household_income"],
                    "Education": resident_b["education_level"],
                    "Schedule type": resident_b["inferred_schedule_type"],
                    "DSM area context": f"DA {resident_b['source_da']} -> {resident_b['fsa_context']}",
                }
            )

        compare_scores = pd.concat(
            [
                scores_a.assign(resident_label="Resident A"),
                scores_b.assign(resident_label="Resident B"),
            ],
            ignore_index=True,
        )
        comparison_score_breakdown = pd.concat(
            [
                program_breakdown(program, resident_a, dsm_profiles, real_alignment, fsa_context=fsa_a).assign(program=program, resident_label="Resident A")
                for program in scores_a["program"]
            ]
            + [
                program_breakdown(program, resident_b, dsm_profiles, real_alignment, fsa_context=fsa_b).assign(program=program, resident_label="Resident B")
                for program in scores_b["program"]
            ],
            ignore_index=True,
        )
        comparison_view = st.radio(
            "Comparison visual",
            ["Paired dots", "Grouped bars", "Radar"],
            horizontal=True,
            help="Paired dots keep absolute scores on the same scale and use a connector to make small gaps visible.",
        )
        if comparison_view == "Paired dots" and comparison_dumbbell_chart is not None:
            st.plotly_chart(comparison_dumbbell_chart(compare_scores), width="stretch")
        elif comparison_view == "Grouped bars" and comparison_alignment_breakdown_bar is not None:
            st.plotly_chart(comparison_alignment_breakdown_bar(comparison_score_breakdown), width="stretch")
        elif comparison_radar_chart is None:
            if comparison_alignment_breakdown_bar is None:
                st.plotly_chart(comparison_bar(compare_scores), width="stretch")
            else:
                st.plotly_chart(comparison_alignment_breakdown_bar(comparison_score_breakdown), width="stretch")
        else:
            st.plotly_chart(comparison_radar_chart(compare_scores), width="stretch")

        st.subheader("Why the residents differ")
        for program in compare_scores["program"].drop_duplicates():
            compare_breakdown = comparison_score_breakdown.loc[
                comparison_score_breakdown["program"].eq(program)
            ].reset_index(drop=True)
            component_gap = (
                compare_breakdown.pivot(index="component", columns="resident_label", values="contribution")
                .fillna(0)
                .assign(absolute_gap=lambda df: (df["Resident A"] - df["Resident B"]).abs())
                .sort_values("absolute_gap", ascending=False)
            )
            gap_component = component_gap.index[0]
            with st.expander(f"{program} component breakdown"):
                if comparison_view == "Paired dots" and comparison_component_dumbbell_chart is not None:
                    st.plotly_chart(comparison_component_dumbbell_chart(compare_breakdown, program), width="stretch")
                elif comparison_view == "Grouped bars" and comparison_breakdown_bar is not None:
                    st.plotly_chart(comparison_breakdown_bar(compare_breakdown, program), width="stretch")
                elif comparison_component_radar_chart is None:
                    st.bar_chart(
                        compare_breakdown.pivot(index="component", columns="resident_label", values="contribution").fillna(0),
                        horizontal=True,
                        height=260,
                    )
                else:
                    st.plotly_chart(comparison_component_radar_chart(compare_breakdown, program), width="stretch")
                st.caption(
                    f"Largest component gap: {gap_component}. "
                    f"Resident A contribution {component_gap.loc[gap_component, 'Resident A']:.3f}; "
                    f"Resident B contribution {component_gap.loc[gap_component, 'Resident B']:.3f}."
                )
                for component_name, component_row in compare_breakdown.drop_duplicates("component").set_index("component").iterrows():
                    st.markdown(f"**{component_name}**: {component_row['description']}")

        score_wide = compare_scores.pivot(index="program", columns="resident_label", values="alignment_score")
        score_wide["absolute_gap"] = (score_wide["Resident A"] - score_wide["Resident B"]).abs()
        biggest_gap = score_wide.sort_values("absolute_gap", ascending=False).iloc[0]
        biggest_program = score_wide.sort_values("absolute_gap", ascending=False).index[0]
        st.info(
            f"Largest difference: {biggest_program}. Resident A scores {biggest_gap['Resident A']:.2f}; "
            f"Resident B scores {biggest_gap['Resident B']:.2f}."
        )

    with tab_why:
        st.subheader("Average households hide flexibility-relevant diversity")
        st.write(
            "The synthetic-population workflow keeps residents heterogeneous across age group, household structure, work status, income group, and source DA. This matters because DSM proxies do not move together for every household."
        )
        a, b = st.columns(2)
        with a:
            st.plotly_chart(distribution_bar(population, "labour_force_status", "Work status in sampled resident options"), width="stretch")
        with b:
            st.plotly_chart(distribution_bar(population, "household_type", "Household structure in sampled resident options"), width="stretch")

        c, d = st.columns(2)
        with c:
            st.plotly_chart(distribution_bar(population, "household_income", "Household income group"), width="stretch")
        with d:
            st.plotly_chart(distribution_bar(population, "inferred_schedule_type", "Inferred schedule type"), width="stretch")

        st.plotly_chart(average_vs_heterogeneous(population, area_scores), width="stretch")
        st.plotly_chart(
            fsa_context_map(
                dsm_profiles,
                all_fsa_scores,
                fsa_geojson,
                area_locations,
                title="FSA contexts used by the demo residents",
            ),
            width="stretch",
        )
        st.caption(
            "Black diamonds mark the average area score. The spread shows how a single average can miss renter-heavy, repair-sensitive, owner-occupied, family, older-adult, and long-commute contexts."
        )

