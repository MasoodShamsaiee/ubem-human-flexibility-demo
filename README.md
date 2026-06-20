# Urban Energy Research Explorer v2

A Streamlit research communication suite with two deliberately separate presentations:

- **Synthetic Population**, aligned with the BuildSys 2026 paper *A Census-Consistent Synthetic Population Pipeline for Urban Energy Systems Research*
- **DSM Alignment**, developed for the eSim 2026 conference demonstration

The eSim-only conference release is preserved by the Git tag `v1-demo`.

The app opens with a top-level presentation selector. **Synthetic Population** is currently the default and is presented independently from **DSM Alignment**; the two workflows are intentionally not merged in this release.

The DSM presentation lets visitors select a Montreal Forward Sortation Area (FSA) from a map and inspect how that FSA aligns with four program pathways:

- Tarif Flex D
- Hilo
- LogisVert
- Low-income assistance

The demo is intentionally spatial and program-oriented. It illustrates FSA-level relevance, capacity, and policy-gap diagnostics; it is not an operational program-enrolment or household-level recommendation tool.

## Synthetic Population Presentation

The BuildSys presentation follows the manuscript structure:

1. Research gap, contribution, and four-stage support-aware workflow
2. Energy-oriented person, household, dwelling, and mobility attributes
3. Interactive population and linked household exploration
4. Reported 133-DA manuscript validation and comparison with three baseline families
5. Explicit interpretation boundaries and future work

The manuscript case study covers 133 Plateau-Mont-Royal DAs. The interactive deployment uses a separate reproducible 30-DA H2J sample with 16,278 people linked to 8,685 households. The interface labels these scopes separately.

## DSM Workflow

1. Select a Montreal FSA from the map.
2. Review long-term energy features, short-term winter load features, and socio-demographic context for the selected FSA.
3. Compare program scores while keeping demand-related and capacity-related dimensions separate.
4. Use the relevance-capacity matrix to explore ideal targets, policy gaps, low-priority areas, and minimal-impact areas.
5. Open the info tab for interpretation boundaries and author links.

## Demo Data

`data/demo_dsm_profiles.csv` contains compact FSA-level features derived from processed Montreal DSM tables:

- long-term energy features: `winter_peak_share`, `heating_slope_per_hdd`, `heating_change_point_temp_c`, `baseload_intercept`, `cooling_slope_per_cdd`, and `winter_peak_intensity`
- short-term winter load features: `peak_load`, `p90_top10_mean`, `mean_load`, `am_pm_peak_ratio`, and `ramp_up_rate`
- socio-demographic proxies: tenure, dwelling type, household composition, labour force, commute, income, and low-income indicators

`data/demo_real_dsm_alignment.csv` contains normalized FSA-level alignment outputs copied from the local DSM report tables. The app uses these outputs for program scores, relevance-capacity classes, and matrix views.

`data/demo_montreal_fsa_context.geojson` contains the lightweight Montreal FSA boundary file used for the map.

Synthetic records represent plausible combinations constrained by public-data distributions; they are not identifiable residents.

The H2J bundle is packaged in compact CSV artifacts:

- `data/synpop_h2j_people_households.csv.gz`
- `data/synpop_validation_summary.csv`
- `data/synpop_support_summary.csv`
- `data/synpop_population_totals_audit.csv`
- `data/synpop_bundle_metadata.json`
- `data/buildsys_manuscript_validation.csv`
- `data/buildsys_method_comparison.csv`
- `data/buildsys_attribute_relevance.csv`

All outputs are research-demo data and should be interpreted as communication and diagnostic results, not final planning recommendations or household-level predictions.

## Feedback Collection

The app includes a sidebar feedback form. Submitted feedback is not shown in the public app.

For Streamlit Community deployment, feedback can be appended to a Google Sheet. Create a Google Cloud service account, share the target Sheet with the service-account `client_email`, then add the values from `.streamlit/secrets.example.toml` to the app's Streamlit Secrets.

If Google Sheets secrets are not configured, submissions fall back to local development storage at:

```text
data/feedback/user_feedback.csv
```

The `data/feedback/` folder and real `.streamlit/secrets.toml` file are git-ignored by default.

## Run Locally

```bash
cd ubem-human-flexibility-demo
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

On macOS/Linux, activate with `source .venv/bin/activate`.

For the current Windows demo environment:

```powershell
.\tools\restart_streamlit_verbose.cmd
```

## Deploy

Streamlit Community Cloud:

1. Push this folder to GitHub.
2. In Streamlit Community Cloud, choose **New app** and connect the repo.
3. Set the main file path to `app/streamlit_app.py`.
4. Add Google Sheets credentials in **Settings > Secrets** if feedback should be written to Google Sheets.
5. Reboot the app after saving secrets.

The public address is:

```text
https://demo.pishi.fyi
```

It is served by a Cloudflare Worker that records the configured GA4 access event and redirects directly to the Streamlit deployment. The older GitHub Pages tracking hop is no longer required.
