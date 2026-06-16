# UBEM Human Flexibility Demo

An audience-facing Streamlit demo that connects two research codebases:

- `dsm-alignment`: area-level DSM suitability/alignment scoring for programs such as Flex D, Hilo, LogisVert, and low-income assistance.
- `synthetic-population-qc`: bundle-first synthetic population generation with supported people and household output schemas.

Core idea: build a city resident, match them to a synthetic population profile and local area context, then estimate illustrative DSM alignment. The demo is intentionally careful: it communicates heterogeneity and targeting logic without claiming validated individual prediction.

> This is a research communication demo using simplified/demo-safe data. It illustrates the workflow and findings, not an operational DSM recommendation tool.

## Conference Demo Paths

The first control in the app lets participants choose one of three paths:

- **BuildSys synthetic population**: focuses on census-consistent people/household records, attribute support, and why some fields should be treated as stable while mobility and housing-quality fields remain exploratory.
- **eSim DSM alignment**: focuses on FSA-level relevance-capacity alignment for Tarif Flex D, Hilo, LogisVert, and low-income assistance.
- **Integrated demo**: connects both papers by selecting an FSA, choosing one of five synthetic residents sampled from that area, and showing how household heterogeneity changes illustrative DSM suitability.

The two paper-specific paths are intentionally narrower than the integrated path, so a conference visitor can understand each paper on its own before seeing the combined workflow.

## Source Repo Review

### DSM / Demand-Side Management Repo

Reviewed repositories:

- `../dsm-alignment`
- legacy/source context in `../DSM and SD`
- dependency context in `../urban-energy-core`

Structure and reusable pieces:

- `src/dsm_alignment/common.py`: percentile-rank normalization, weighted composites, quadrant classification, keyword column matching.
- `src/dsm_alignment/flexd.py`: Flex D temporal flexibility, demand elasticity, participation capacity, and demand relevance.
- `src/dsm_alignment/hilo.py`: technical eligibility, control/authority, curtailment tolerance, and demand relevance.
- `src/dsm_alignment/logisvert.py`: structural demand relevance, adoption capacity, persistence capacity.
- `src/dsm_alignment/low_income.py`: energy vulnerability and system relevance.
- `docs/data_contracts.md`: unit-indexed feature-table contract with PRISM, short-term load, and census-style proxy columns.
- `../DSM and SD/reports/.../tables/*.csv`: existing report outputs such as alignment scores, program summaries, PRISM summaries, and short-term summaries.

Important interpretation:

- The DSM code evaluates spatial units such as FSA/DA/building-ready units, not individual people.
- The demo therefore uses terms such as `illustrative alignment`, `profile resemblance`, and `high/medium/low suitability`.

### Synthetic Population / UBEM Repo

Reviewed repository:

- `../synthetic-population-qc`

Structure and reusable pieces:

- `src/synthetic_population_qc/energy_workflow.py`: neutral end-to-end workflow.
- `src/synthetic_population_qc/runs/`: standardized run bundle models and loaders.
- `src/synthetic_population_qc/context_tables.py`: labeled DA-scale census context loaders.
- `src/synthetic_population_qc/reporting.py`: compact fit summaries.
- `docs/data_contracts.md`: public synthesis output contract.
- `examples/sample_plateau_30das/`: small example bundles and exploration artifacts.

Supported public people fields include `area`, `HID`, `sex`, `age_group`, `education_level`, `labour_force_status`, `household_income`, `family_status`, `household_size`, `household_type`, `person_uid`, `citizenship_status`, `immigrant_status`, `commute_mode`, and `commute_duration`.

Supported public household fields include `area`, `household_id`, `household_size`, `household_type`, `dwelling_type`, `tenure`, `bedrooms`, `period_built`, `dwelling_condition`, and `core_housing_need`.

## Demo Data Model

`data/demo_synthetic_population.csv` combines supported person and household columns into one small resident table for easy conference interaction.

`data/demo_dsm_profiles.csv` contains compact FSA-level area-context features derived from the processed Montreal DSM tables:

- energy features for the 94 Montreal FSAs in the alignment extract: `winter_peak_share`, `heating_slope_per_hdd`, `heating_change_point_temp_c`, `baseload_intercept`, `cooling_slope_per_cdd`, `winter_peak_intensity`, `peak_load`, `p90_top10_mean`, `mean_load`, `am_pm_peak_ratio`, and `ramp_up_rate`
- census-style proxies: `owner_pct`, `renter_pct`, `single_detached_house_pct`, `apartment_pct`, `average_household_size`, `children_0_14_pct`, `older_65_plus_pct`, `full_year_full_time_pct`, `not_in_labour_force_pct`, `one_parent_family_pct`, `commute_60_min_plus_pct`, `persons_per_room_high_pct`, `non_movers_1yr_pct`, `median_income`, `low_income_pct`

All values are illustrative and non-sensitive.

`data/demo_real_dsm_alignment.csv` contains a small copied excerpt from the local DSM report tables under `../DSM and SD/reports/dsm_alignment_montreal_distributional_weighted_20260219_131042/tables/`. These are already-normalized FSA-level research outputs. The app uses them as the matched FSA energy baseline and maps each demo DA to one `fsa_context`.

`data/demo_montreal_fsa_context.geojson` contains the lightweight Montreal FSA boundary file copied from `../urban-energy-data/data/raw/geometry/Montreal.geojson`. It is used for the app maps. The much larger DA geometry is intentionally not copied.

## Feedback Collection

The app includes a sidebar feedback form for conference participants. The submitted results are not shown in the public app.

For Streamlit Community deployment, feedback can be appended directly to a Google Sheet. Create a Google Cloud service account, share the target Sheet with the service-account `client_email`, then add the values from `.streamlit/secrets.example.toml` to the app's Streamlit Secrets. The expected secrets are:

```toml
[feedback]
google_sheet_id = "..."
worksheet_name = "feedback"

[google_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

If Google Sheets secrets are not configured, submissions fall back to local development storage at:

```text
data/feedback/user_feedback.csv
```

Each row includes timestamp, demo path, section, clarity rating, comment, optional role/affiliation, selected FSA, selected resident, source DA, and the current top DSM program/score. The `data/feedback/` folder and real `.streamlit/secrets.toml` file are git-ignored by default.

## Scoring Logic

The app adapts the DSM repo's rank-based weighted composite idea:

1. Use the real FSA-level DSM report excerpt as the area-context baseline when available.
2. Read the selected resident's synthetic-population attributes.
3. Add a small household-context resemblance modifier for conference explanation.
4. Report high/medium/low suitability bands and program-specific explanations.

If the real DSM excerpt is removed, the app falls back to computing demo proxy scores from `data/demo_dsm_profiles.csv`.

Assumptions are documented in code comments in `src/dsm_scoring.py`. The important one: the source DSM model is area-level, so resident-level scores are communication aids only.

## Run Locally

```bash
cd ubem-human-flexibility-demo
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

On macOS/Linux, activate with `source .venv/bin/activate`.

For the current Windows/conda demo environment, restart Streamlit with verbose health-check output:

```powershell
.\tools\restart_streamlit_verbose.cmd
```

The script stops any process on port `8501`, clears local Python caches, starts Streamlit in the `urban-energy-core` conda environment, and prints `READY: HTTP 200` plus the fresh app URL when it is serving.

For fully attached diagnostic output, run Streamlit in the foreground:

```powershell
.\tools\restart_streamlit.ps1 -Foreground
```

Foreground mode is intentionally not detached; stop it with `Ctrl+C`.

## Deploy

Streamlit Community Cloud:

1. Push this folder as a GitHub repo.
2. In Streamlit Community Cloud, choose **New app** and connect that repo.
3. Set the main file path to `app/streamlit_app.py`.
4. Leave the dependency file as `requirements.txt`; the app also includes `runtime.txt` to request Python 3.11.
5. No secrets are required for the demo-safe version.

Recommended repository name:

```text
ubem-human-flexibility-demo
```

Self-hosted or Cloudflare Tunnel:

```bash
streamlit run app/streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

Docker:

```bash
docker build -t ubem-human-flexibility-demo .
docker run --rm -p 8501:8501 ubem-human-flexibility-demo
```

## Screenshots

Add conference-ready screenshots after first run:

- `assets/demo_screenshot.png`
- `assets/qr_code_placeholder.png`

## Limitations

- This is not an operational DSM recommendation tool.
- Demo data are toy values that preserve schema and qualitative relationships.
- The DSM source logic is spatial/unit-level; household modifiers are simplified communication scaffolding.
- No external API is required.

## Citation Placeholders

- DSM alignment paper/repo: add final citation here.
- Synthetic population / UBEM paper/repo: add final citation here.
