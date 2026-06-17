from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


MPL_BLUE = "#1f77b4"
MPL_LIGHT_BLUE = "#aec7e8"
MPL_ORANGE = "#ff7f0e"
MPL_LIGHT_ORANGE = "#ffbb78"

COLOR_SEQUENCE = [MPL_BLUE, MPL_ORANGE, "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
AREA_COLOR = MPL_BLUE
SELECTED_COLOR = MPL_ORANGE
COMPONENT_COLORS = {
    "Demand relevance": MPL_BLUE,
    "Temporal flexibility": MPL_ORANGE,
    "Demand elasticity": "#d95f02",
    "Technical eligibility": MPL_LIGHT_ORANGE,
    "Control authority": "#e6550d",
    "Curtailment tolerance": "#fd8d3c",
    "Structural demand": MPL_BLUE,
    "Adoption capacity": MPL_ORANGE,
    "Persistence capacity": "#d95f02",
    "System relevance": MPL_BLUE,
    "Energy vulnerability": MPL_ORANGE,
    "Household resemblance": "#d62728",
}
ALIGNMENT_CLASS_COLORS = {
    "Ideal target": MPL_BLUE,
    "Policy gap": MPL_ORANGE,
    "Low priority": "#9467bd",
    "Minimal impact": "#d62728",
}
DEMAND_COLOR = MPL_BLUE
CAPACITY_COLOR = MPL_ORANGE
REST_COLOR = MPL_LIGHT_BLUE


def selected_vs_rest_bar(
    frame: pd.DataFrame,
    selected_key: str,
    key_col: str,
    metrics: list[tuple[str, str]],
    title: str,
    xaxis_title: str = "Normalized index",
    fixed_unit_range: bool = True,
    normalize_per_metric: bool = False,
) -> go.Figure:
    selected = frame.loc[frame[key_col].eq(selected_key)]
    labels = [label for _, label in metrics]
    rest = frame.loc[~frame[key_col].eq(selected_key)]
    selected_values = []
    rest_values = []
    for column, _ in metrics:
        all_values = pd.to_numeric(frame[column], errors="coerce")
        selected_value = (
            float(pd.to_numeric(pd.Series([selected.iloc[0][column]]), errors="coerce").iloc[0])
            if not selected.empty
            else 0.0
        )
        rest_value = float(pd.to_numeric(rest[column], errors="coerce").mean()) if not rest.empty else 0.0
        if normalize_per_metric:
            min_value = float(all_values.min()) if not all_values.dropna().empty else 0.0
            max_value = float(all_values.max()) if not all_values.dropna().empty else 1.0
            span = max(max_value - min_value, 1e-9)
            selected_value = (selected_value - min_value) / span
            rest_value = (rest_value - min_value) / span
        selected_values.append(0.0 if pd.isna(selected_value) else selected_value)
        rest_values.append(0.0 if pd.isna(rest_value) else rest_value)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=labels,
            x=rest_values,
            name="Other FSAs avg.",
            orientation="h",
            marker_color=REST_COLOR,
            hovertemplate="<b>%{y}</b><br>Other FSAs avg.: %{x:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            y=labels,
            x=selected_values,
            name=selected_key,
            orientation="h",
            marker_color=SELECTED_COLOR,
            hovertemplate="<b>%{y}</b><br>" + selected_key + ": %{x:.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        barmode="group",
        height=max(280, 46 * len(labels) + 110),
        margin=dict(l=8, r=16, t=48, b=38),
        legend=dict(orientation="h", y=-0.15, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    max_value = max(selected_values + rest_values + [0.01])
    x_range = [0, 1] if fixed_unit_range else [0, max_value * 1.18]
    fig.update_xaxes(title=xaxis_title, range=x_range)
    fig.update_yaxes(title="", autorange="reversed")
    return fig


def selected_distribution_bar(
    population: pd.DataFrame,
    selected_fsa: str,
    column: str,
    title: str,
) -> go.Figure:
    data = population.copy()
    data["Group"] = data["fsa_context"].eq(selected_fsa).map({True: selected_fsa, False: "Other FSAs"})
    counts = data.groupby(["Group", column]).size().reset_index(name="count")
    totals = counts.groupby("Group")["count"].transform("sum").replace(0, 1)
    counts["share"] = counts["count"] / totals
    fig = px.bar(
        counts,
        x=column,
        y="share",
        color="Group",
        barmode="group",
        color_discrete_map={selected_fsa: SELECTED_COLOR, "Other FSAs": REST_COLOR},
        title=title,
        text=counts["share"].map(lambda value: f"{value:.0%}"),
    )
    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=50, b=86),
        legend=dict(orientation="h", y=-0.26, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(title="", tickangle=-25)
    fig.update_yaxes(title="Resident-option share", tickformat=".0%")
    return fig


def energy_percentile_strip(
    frame: pd.DataFrame,
    selected_fsa: str,
    metrics: list[tuple[str, str]],
    title: str,
) -> go.Figure:
    rows = []
    for column, label in metrics:
        values = pd.to_numeric(frame[column], errors="coerce")
        ranks = values.rank(pct=True, method="average") * 100
        for fsa, value, percentile in zip(frame["fsa_context"], values, ranks, strict=False):
            if pd.isna(value) or pd.isna(percentile):
                continue
            rows.append(
                {
                    "fsa_context": fsa,
                    "Metric": label,
                    "Percentile": float(percentile),
                    "Raw value": float(value),
                    "Selected": fsa == selected_fsa,
                }
            )
    data = pd.DataFrame(rows)
    fig = go.Figure()
    if data.empty:
        fig.update_layout(title=title, height=320)
        return fig
    metric_order = [label for _, label in metrics]
    for metric in metric_order:
        part = data.loc[data["Metric"].eq(metric) & ~data["Selected"]]
        fig.add_trace(
            go.Scatter(
                x=part["Percentile"],
                y=part["Metric"],
                mode="markers",
                name="Other FSAs",
                marker=dict(size=8, color=REST_COLOR, opacity=0.48),
                customdata=part[["fsa_context", "Raw value"]],
                hovertemplate="<b>%{customdata[0]}</b><br>%{y}<br>Percentile: %{x:.0f}<br>Raw value: %{customdata[1]:.4g}<extra></extra>",
                showlegend=metric == metric_order[0],
            )
        )
    selected = data.loc[data["Selected"]]
    fig.add_trace(
        go.Scatter(
            x=selected["Percentile"],
            y=selected["Metric"],
            mode="markers+text",
            name=selected_fsa,
            marker=dict(size=16, color=SELECTED_COLOR, symbol="diamond"),
            text=selected["Percentile"].map(lambda value: f"{value:.0f}"),
            textposition="middle right",
            customdata=selected[["Raw value"]],
            hovertemplate="<b>" + selected_fsa + "</b><br>%{y}<br>Percentile: %{x:.0f}<br>Raw value: %{customdata[0]:.4g}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        height=max(300, 42 * len(metric_order) + 100),
        margin=dict(l=6, r=14, t=44, b=40),
        legend=dict(orientation="h", y=-0.14, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(title="Percentile among Montreal FSAs", range=[0, 103], ticksuffix="%")
    fig.update_yaxes(title="", categoryorder="array", categoryarray=metric_order[::-1])
    return fig


def energy_relationship_scatter(
    frame: pd.DataFrame,
    selected_fsa: str,
    x_col: str,
    y_col: str,
    title: str,
    x_label: str,
    y_label: str,
    color_col: str | None = None,
    color_label: str | None = None,
    size_col: str | None = None,
    size_label: str | None = None,
) -> go.Figure:
    data = frame.copy()
    data[x_col] = pd.to_numeric(data[x_col], errors="coerce")
    data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
    color_values = pd.to_numeric(data[color_col], errors="coerce") if color_col else None
    if size_col:
        size_values = pd.to_numeric(data[size_col], errors="coerce")
        span = max(float(size_values.max() - size_values.min()), 1e-9)
        data["_marker_size"] = 9 + 17 * ((size_values - size_values.min()) / span).fillna(0)
    else:
        data["_marker_size"] = 11
    data["_is_selected"] = data["fsa_context"].eq(selected_fsa)
    other = data.loc[~data["_is_selected"]]
    selected = data.loc[data["_is_selected"]]
    fig = go.Figure()
    marker = dict(size=other["_marker_size"], color=REST_COLOR, opacity=0.62)
    if color_col and color_values is not None:
        marker = dict(
            size=other["_marker_size"],
            color=pd.to_numeric(other[color_col], errors="coerce"),
            colorscale=[[0, "#deebf7"], [0.5, MPL_LIGHT_BLUE], [1, MPL_BLUE]],
            colorbar=dict(title=color_label or color_col, thickness=12),
            opacity=0.74,
        )
    custom_cols = ["fsa_context"]
    if color_col:
        custom_cols.append(color_col)
    if size_col:
        custom_cols.append(size_col)
    hover = f"<b>%{{customdata[0]}}</b><br>{x_label}: %{{x:.4g}}<br>{y_label}: %{{y:.4g}}"
    custom_index = 1
    if color_col:
        hover += f"<br>{color_label or color_col}: %{{customdata[{custom_index}]:.4g}}"
        custom_index += 1
    if size_col:
        hover += f"<br>{size_label or size_col}: %{{customdata[{custom_index}]:.4g}}"
    hover += "<extra></extra>"
    fig.add_trace(
        go.Scatter(
            x=other[x_col],
            y=other[y_col],
            mode="markers",
            name="Other FSAs",
            marker=marker,
            customdata=other[custom_cols],
            hovertemplate=hover,
        )
    )
    if not selected.empty:
        fig.add_trace(
            go.Scatter(
                x=selected[x_col],
                y=selected[y_col],
                mode="markers+text",
                name=selected_fsa,
                marker=dict(size=22, color=SELECTED_COLOR, symbol="star", line=dict(width=1.5, color="#FFFFFF")),
                text=selected["fsa_context"],
                textposition="top center",
                customdata=selected[custom_cols],
                hovertemplate=hover,
            )
        )
    fig.update_layout(
        title=title,
        height=340,
        margin=dict(l=6, r=8, t=44, b=42),
        legend=dict(orientation="h", y=-0.15, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(title=x_label, zeroline=False)
    fig.update_yaxes(title=y_label, zeroline=False)
    return fig


def program_axis_stacked_bar(program_axes: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=program_axes["Program"],
            y=program_axes["Demand-related"],
            name="Demand-related",
            marker_color=DEMAND_COLOR,
            customdata=program_axes[["Demand label", "Demand-related"]],
            hovertemplate="<b>%{x}</b><br>%{customdata[0]}: %{customdata[1]:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=program_axes["Program"],
            y=program_axes["Capacity-related"],
            name="Capacity-related",
            marker_color=CAPACITY_COLOR,
            customdata=program_axes[["Capacity label", "Capacity-related"]],
            hovertemplate="<b>%{x}</b><br>%{customdata[0]}: %{customdata[1]:.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        barmode="group",
        height=330,
        margin=dict(l=6, r=8, t=44, b=74),
        legend=dict(orientation="h", y=-0.24, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Axis value", range=[0, 1])
    return fig


def program_component_axis_scatter(breakdown: pd.DataFrame, title: str) -> go.Figure:
    data = breakdown.copy()
    data["axis"] = data.get("axis", "Component")
    data["label"] = data["program"] + " | " + data["component"]
    data["marker_size"] = 14 + 34 * pd.to_numeric(data["weight"], errors="coerce").fillna(0)
    axis_colors = {"Demand-related": DEMAND_COLOR, "Capacity-related": CAPACITY_COLOR}
    label_order = data["label"].tolist()[::-1]
    fig = go.Figure()
    for axis in ["Demand-related", "Capacity-related"]:
        part = data.loc[data["axis"].eq(axis)]
        if part.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=part["source_value"],
                y=part["label"],
                mode="markers",
                name=axis,
                marker=dict(
                    size=part["marker_size"],
                    color=axis_colors[axis],
                    opacity=0.88,
                    line=dict(width=1.5, color="#FFFFFF"),
                ),
                customdata=part[["weight", "contribution", "description"]],
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Source index: %{x:.2f}<br>"
                    "Weight: %{customdata[0]:.2f}<br>"
                    "Weighted contribution: %{customdata[1]:.3f}<br>"
                    "%{customdata[2]}<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        title=title,
        height=max(390, 30 * len(label_order) + 105),
        margin=dict(l=6, r=12, t=46, b=44),
        legend=dict(orientation="h", y=-0.13, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(title="Source index value", range=[0, 1], zeroline=False)
    fig.update_yaxes(title="", categoryorder="array", categoryarray=label_order)
    return fig


def _iter_coordinate_pairs(coordinates):
    if not coordinates:
        return
    first = coordinates[0]
    if isinstance(first, (int, float)) and len(coordinates) >= 2:
        yield float(coordinates[0]), float(coordinates[1])
        return
    for item in coordinates:
        yield from _iter_coordinate_pairs(item)


def _fsa_label_points(fsa_geojson: dict) -> pd.DataFrame:
    rows = []
    for feature in fsa_geojson.get("features", []):
        fsa = feature.get("properties", {}).get("CFSAUID")
        pairs = list(_iter_coordinate_pairs(feature.get("geometry", {}).get("coordinates", [])))
        if not fsa or not pairs:
            continue
        lon = sum(pair[0] for pair in pairs) / len(pairs)
        lat = sum(pair[1] for pair in pairs) / len(pairs)
        rows.append({"fsa": fsa, "lon": lon, "lat": lat})
    return pd.DataFrame(rows)


def alignment_bar(scores: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        scores,
        x="alignment_score",
        y="program",
        color="program",
        orientation="h",
        range_x=[0, 1],
        color_discrete_sequence=COLOR_SEQUENCE,
        text=scores["alignment_score"].map(lambda x: f"{x:.2f}"),
    )
    fig.update_layout(showlegend=False, height=310, margin=dict(l=8, r=8, t=20, b=8))
    fig.update_yaxes(categoryorder="total ascending", title="")
    fig.update_xaxes(title="Illustrative alignment score")
    return fig


def comparison_bar(compare_scores: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        compare_scores,
        x="program",
        y="alignment_score",
        color="resident_label",
        barmode="group",
        range_y=[0, 1],
        color_discrete_sequence=["#2F6B63", "#D08C60"],
        text=compare_scores["alignment_score"].map(lambda x: f"{x:.2f}"),
    )
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=70), legend_title_text="")
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Illustrative alignment score")
    return fig


def comparison_radar_chart(compare_scores: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for resident_label, color in [("Resident A", "#2F6B63"), ("Resident B", "#D08C60")]:
        rows = compare_scores.loc[compare_scores["resident_label"].eq(resident_label)].sort_values("program")
        theta = rows["program"].tolist()
        values = rows["alignment_score"].tolist()
        if theta:
            theta = theta + [theta[0]]
            values = values + [values[0]]
        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=theta,
                fill="toself",
                name=resident_label,
                line_color=color,
                opacity=0.82,
                hovertemplate="<b>%{fullData.name}</b><br>%{theta}: %{r:.2f}<extra></extra>",
            )
        )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1], tickformat=".1f")),
        showlegend=True,
        height=390,
        margin=dict(l=25, r=25, t=25, b=25),
        legend=dict(orientation="h", y=-0.08, x=0, title_text=""),
    )
    return fig


def comparison_dumbbell_chart(compare_scores: pd.DataFrame) -> go.Figure:
    score_wide = compare_scores.pivot(index="program", columns="resident_label", values="alignment_score").fillna(0)
    score_wide["gap"] = (score_wide["Resident A"] - score_wide["Resident B"]).abs()
    score_wide = score_wide.sort_values("gap", ascending=True)
    fig = go.Figure()
    for program, row in score_wide.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row["Resident A"], row["Resident B"]],
                y=[program, program],
                mode="lines",
                line=dict(color="#B9C4C0", width=4),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    for resident_label, color in [("Resident A", "#2F6B63"), ("Resident B", "#D08C60")]:
        fig.add_trace(
            go.Scatter(
                x=score_wide[resident_label],
                y=score_wide.index,
                mode="markers+text",
                name=resident_label,
                marker=dict(size=14, color=color, line=dict(width=1, color="#FFFFFF")),
                text=score_wide[resident_label].map(lambda value: f"{value:.2f}"),
                textposition="middle right" if resident_label == "Resident A" else "middle left",
                customdata=score_wide["gap"],
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    f"{resident_label}: " + "%{x:.2f}<br>"
                    "Absolute gap: %{customdata:.3f}<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        height=330,
        margin=dict(l=8, r=35, t=20, b=35),
        legend=dict(orientation="h", y=-0.18, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(title="Illustrative alignment score", range=[0, 1])
    fig.update_yaxes(title="")
    return fig


def relevance_capacity_matrix(
    frame: pd.DataFrame,
    selected_fsa: str,
    relevance_col: str,
    capacity_col: str,
    class_col: str,
    title: str,
    relevance_label: str = "Demand relevance",
    capacity_label: str = "Participation capacity",
) -> go.Figure:
    data = frame.copy()
    cap_threshold = float(data[capacity_col].median())
    rel_threshold = float(data[relevance_col].median())
    data["alignment_label"] = data[class_col].map(
        {
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
    ).fillna(data[class_col])
    data["is_selected"] = data["fsa"].eq(selected_fsa)

    fig = go.Figure()
    quadrant_shapes = [
        (0, cap_threshold, 0, rel_threshold, "Minimal impact", "#F7BABA"),
        (cap_threshold, 1, 0, rel_threshold, "Low priority", "#DCD8FA"),
        (0, cap_threshold, rel_threshold, 1, "Policy gap", "#F4D0A0"),
        (cap_threshold, 1, rel_threshold, 1, "Ideal target", "#B8EFCF"),
    ]
    for x0, x1, y0, y1, label, color in quadrant_shapes:
        fig.add_shape(
            type="rect",
            x0=x0,
            x1=x1,
            y0=y0,
            y1=y1,
            fillcolor=color,
            opacity=0.34,
            layer="below",
            line_width=0,
        )
        fig.add_annotation(
            x=(x0 + x1) / 2,
            y=(y0 + y1) / 2,
            text=label,
            showarrow=False,
            font=dict(size=13, color="#263332"),
            opacity=0.88,
        )

    for label in ["Minimal impact", "Low priority", "Policy gap", "Ideal target"]:
        part = data.loc[data["alignment_label"].eq(label)]
        if part.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=part[capacity_col],
                y=part[relevance_col],
                mode="markers",
                name=label,
                marker=dict(
                    size=12,
                    color=ALIGNMENT_CLASS_COLORS.get(label, "#6B5B95"),
                    opacity=0.82,
                    line=dict(width=1, color="#FFFFFF"),
                ),
                customdata=part[["fsa", "alignment_label"]],
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                + f"{capacity_label}: "
                + "%{x:.2f}<br>"
                + f"{relevance_label}: "
                + "%{y:.2f}<extra></extra>",
            )
        )

    selected = data.loc[data["fsa"].eq(selected_fsa)]
    if not selected.empty:
        row = selected.iloc[0]
        fig.add_trace(
            go.Scatter(
                x=[row[capacity_col]],
                y=[row[relevance_col]],
                mode="markers+text",
                name=f"Selected FSA {selected_fsa}",
                marker=dict(size=18, color="#1F2A2A", symbol="star", line=dict(width=2, color="#FFFFFF")),
                text=[selected_fsa],
                textposition="top center",
                hovertemplate="<b>%{text}</b><br>"
                + f"{capacity_label}: "
                + "%{x:.2f}<br>"
                + f"{relevance_label}: "
                + "%{y:.2f}<extra></extra>",
            )
        )

    fig.add_vline(x=cap_threshold, line_dash="dash", line_color="#2F6B63", opacity=0.75)
    fig.add_hline(y=rel_threshold, line_dash="dash", line_color="#2F6B63", opacity=0.75)
    fig.update_layout(
        title=title,
        height=390,
        margin=dict(l=8, r=8, t=42, b=58),
        legend=dict(orientation="h", y=-0.18, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        clickmode="event+select",
        dragmode=False,
    )
    fig.update_xaxes(title=capacity_label, range=[0, 1], zeroline=False)
    fig.update_yaxes(title=relevance_label, range=[0, 1], zeroline=False)
    return fig


def alignment_breakdown_bar(breakdown: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    programs = breakdown["program"].drop_duplicates().tolist()
    for component in breakdown["component"].drop_duplicates():
        part = breakdown.loc[breakdown["component"].eq(component)].set_index("program")
        values = [part.loc[program, "contribution"] if program in part.index else 0.0 for program in programs]
        source_values = [part.loc[program, "source_value"] if program in part.index else 0.0 for program in programs]
        weights = [part.loc[program, "weight"] if program in part.index else 0.0 for program in programs]
        descriptions = [part.loc[program, "description"] if program in part.index else "" for program in programs]
        fig.add_trace(
            go.Bar(
                x=values,
                y=programs,
                name=component,
                orientation="h",
                marker_color=COMPONENT_COLORS.get(component, "#6B5B95"),
                customdata=list(zip(source_values, weights, descriptions, strict=False)),
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "%{y}<br>"
                    "Contribution: %{x:.3f}<br>"
                    "Source subindex: %{customdata[0]:.2f}<br>"
                    "Weight in final score: %{customdata[1]:.3f}<br>"
                    "%{customdata[2]}<extra></extra>"
                ),
            )
        )
    totals = breakdown.groupby("program", sort=False)["contribution"].sum()
    for program, total in totals.items():
        fig.add_annotation(
            x=min(float(total) + 0.02, 0.98),
            y=program,
            text=f"{float(total):.2f}",
            showarrow=False,
            xanchor="left",
            font=dict(size=12, color="#1F2A2A"),
        )
    fig.update_layout(
        barmode="stack",
        height=380,
        margin=dict(l=8, r=8, t=16, b=46),
        legend=dict(orientation="h", y=-0.16, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(title="Illustrative alignment score", range=[0, 1])
    fig.update_yaxes(title="", categoryorder="array", categoryarray=programs[::-1])
    return fig


def comparison_alignment_breakdown_bar(breakdown: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    breakdown = breakdown.copy()
    breakdown["axis_label"] = breakdown["program"] + "<br>" + breakdown["resident_label"].replace({"Resident A": "A", "Resident B": "B"})
    axis_order = []
    for program in breakdown["program"].drop_duplicates():
        axis_order.extend([f"{program}<br>A", f"{program}<br>B"])
    components = breakdown["component"].drop_duplicates().tolist()
    for component in components:
        part = breakdown.loc[breakdown["component"].eq(component)].set_index("axis_label")
        values = [part.loc[label, "contribution"] if label in part.index else 0.0 for label in axis_order]
        source_values = [part.loc[label, "source_value"] if label in part.index else 0.0 for label in axis_order]
        weights = [part.loc[label, "weight"] if label in part.index else 0.0 for label in axis_order]
        descriptions = [part.loc[label, "description"] if label in part.index else "" for label in axis_order]
        fig.add_trace(
            go.Bar(
                x=axis_order,
                y=values,
                name=component,
                marker_color=COMPONENT_COLORS.get(component, "#6B5B95"),
                customdata=list(zip(source_values, weights, descriptions, strict=False)),
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "%{x}<br>"
                    "Contribution: %{y:.3f}<br>"
                    "Source subindex: %{customdata[0]:.2f}<br>"
                    "Weight in final score: %{customdata[1]:.3f}<br>"
                    "%{customdata[2]}<extra></extra>"
                ),
            )
        )
    totals = breakdown.groupby("axis_label", sort=False)["contribution"].sum()
    for label in axis_order:
        total = float(totals.get(label, 0.0))
        fig.add_annotation(
            x=label,
            y=min(total + 0.03, 0.98),
            text=f"{total:.2f}",
            showarrow=False,
            yanchor="bottom",
            font=dict(size=11, color="#1F2A2A"),
        )
    fig.update_layout(
        barmode="stack",
        height=410,
        margin=dict(l=10, r=10, t=30, b=95),
        legend=dict(orientation="h", y=-0.28, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Illustrative alignment score", range=[0, 1])
    return fig


def stacked_breakdown_bar(breakdown: pd.DataFrame, program: str) -> go.Figure:
    fig = go.Figure()
    colors = ["#2F6B63", "#D08C60", "#6E7FA8", "#7C9A5B", "#B85C5C"]
    for i, row in breakdown.reset_index(drop=True).iterrows():
        fig.add_trace(
            go.Bar(
                x=[row["contribution"]],
                y=[program],
                name=row["component"],
                orientation="h",
                marker_color=colors[i % len(colors)],
                customdata=[[row["source_value"], row["weight"], row["description"]]],
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Contribution: %{x:.3f}<br>"
                    "Source subindex: %{customdata[0]:.2f}<br>"
                    "Weight in final score: %{customdata[1]:.3f}<br>"
                    "%{customdata[2]}<extra></extra>"
                ),
            )
        )
    total = breakdown["contribution"].sum()
    fig.add_annotation(
        x=min(total + 0.02, 0.98),
        y=program,
        text=f"{total:.2f}",
        showarrow=False,
        xanchor="left",
        font=dict(size=13, color="#1F2A2A"),
    )
    fig.update_layout(
        barmode="stack",
        height=150,
        margin=dict(l=8, r=8, t=10, b=35),
        legend=dict(orientation="h", y=-0.25, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(title="Contribution to final alignment score", range=[0, 1])
    fig.update_yaxes(title="", showticklabels=False)
    return fig


def comparison_breakdown_bar(breakdown: pd.DataFrame, program: str) -> go.Figure:
    fig = go.Figure()
    resident_order = ["Resident A", "Resident B"]
    component_order = breakdown["component"].drop_duplicates().tolist()
    colors = {"Resident A": "#2F6B63", "Resident B": "#D08C60"}
    for resident_label in resident_order:
        part = breakdown.loc[breakdown["resident_label"].eq(resident_label)].set_index("component")
        values = [part.loc[component, "contribution"] if component in part.index else 0.0 for component in component_order]
        source_values = [part.loc[component, "source_value"] if component in part.index else 0.0 for component in component_order]
        weights = [part.loc[component, "weight"] if component in part.index else 0.0 for component in component_order]
        descriptions = [part.loc[component, "description"] if component in part.index else "" for component in component_order]
        fig.add_trace(
            go.Bar(
                x=values,
                y=component_order,
                name=resident_label,
                orientation="h",
                marker_color=colors[resident_label],
                customdata=list(zip(source_values, weights, descriptions, strict=False)),
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "%{y}<br>"
                    "Contribution: %{x:.3f}<br>"
                    "Source subindex: %{customdata[0]:.2f}<br>"
                    "Weight in final score: %{customdata[1]:.3f}<br>"
                    "%{customdata[2]}<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        title=program,
        barmode="group",
        height=max(260, 58 * len(component_order) + 95),
        margin=dict(l=8, r=8, t=35, b=35),
        legend=dict(orientation="h", y=-0.18, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    max_value = max(float(breakdown["contribution"].max()), 0.05)
    fig.update_xaxes(title="Contribution to final alignment score", range=[0, min(max_value * 1.25, 1)])
    fig.update_yaxes(title="")
    return fig


def comparison_component_radar_chart(breakdown: pd.DataFrame, program: str) -> go.Figure:
    fig = go.Figure()
    component_order = breakdown["component"].drop_duplicates().tolist()
    max_value = max(float(breakdown["contribution"].max()), 0.05)
    for resident_label, color in [("Resident A", "#2F6B63"), ("Resident B", "#D08C60")]:
        part = breakdown.loc[breakdown["resident_label"].eq(resident_label)].set_index("component")
        values = [part.loc[component, "contribution"] if component in part.index else 0.0 for component in component_order]
        theta = component_order.copy()
        if theta:
            theta = theta + [theta[0]]
            values = values + [values[0]]
        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=theta,
                fill="toself",
                name=resident_label,
                line_color=color,
                opacity=0.82,
                hovertemplate="<b>%{fullData.name}</b><br>%{theta}: %{r:.3f}<extra></extra>",
            )
        )
    fig.update_layout(
        title=program,
        polar=dict(radialaxis=dict(visible=True, range=[0, min(max_value * 1.3, 1)], tickformat=".2f")),
        showlegend=True,
        height=max(330, 42 * len(component_order) + 150),
        margin=dict(l=25, r=25, t=45, b=35),
        legend=dict(orientation="h", y=-0.1, x=0, title_text=""),
    )
    return fig


def comparison_component_dumbbell_chart(breakdown: pd.DataFrame, program: str) -> go.Figure:
    wide = breakdown.pivot(index="component", columns="resident_label", values="contribution").fillna(0)
    wide["gap"] = (wide["Resident A"] - wide["Resident B"]).abs()
    wide = wide.sort_values("gap", ascending=True)
    max_value = max(float(wide[["Resident A", "Resident B"]].max().max()), 0.05)
    fig = go.Figure()
    for component, row in wide.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row["Resident A"], row["Resident B"]],
                y=[component, component],
                mode="lines",
                line=dict(color="#B9C4C0", width=4),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    for resident_label, color in [("Resident A", "#2F6B63"), ("Resident B", "#D08C60")]:
        fig.add_trace(
            go.Scatter(
                x=wide[resident_label],
                y=wide.index,
                mode="markers+text",
                name=resident_label,
                marker=dict(size=13, color=color, line=dict(width=1, color="#FFFFFF")),
                text=wide[resident_label].map(lambda value: f"{value:.3f}"),
                textposition="middle right" if resident_label == "Resident A" else "middle left",
                customdata=wide["gap"],
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    f"{resident_label}: " + "%{x:.3f}<br>"
                    "Absolute gap: %{customdata:.3f}<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        title=program,
        height=max(280, 54 * len(wide) + 100),
        margin=dict(l=8, r=35, t=40, b=35),
        legend=dict(orientation="h", y=-0.16, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(title="Absolute component contribution", range=[0, min(max_value * 1.25, 1)])
    fig.update_yaxes(title="")
    return fig


def area_context_map(
    dsm_profiles: pd.DataFrame,
    area_locations: pd.DataFrame,
    selected_area: str | None = None,
    title: str = "Demo area context map",
) -> go.Figure:
    df = area_locations.merge(
        dsm_profiles[["area", "area_label", "fsa_context", "winter_peak_intensity", "owner_pct", "renter_pct"]],
        on="area",
        how="left",
    )
    df["is_selected"] = df["area"].eq(selected_area)
    marker_size = df["is_selected"].map({True: 22, False: 13})
    marker_color = df["is_selected"].map({True: SELECTED_COLOR, False: AREA_COLOR})

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["x"],
            y=df["y"],
            mode="markers+text",
            text=df["area"],
            textposition="top center",
            marker=dict(size=marker_size, color=marker_color, line=dict(width=1.5, color="#FFFFFF")),
            customdata=df[["area_label", "fsa_context", "winter_peak_intensity", "owner_pct", "renter_pct", "map_zone"]],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "%{customdata[0]}<br>"
                "Energy/DSM area context: %{customdata[1]}<br>"
                "Winter peak intensity: %{customdata[2]:.2f}<br>"
                "Area tenure mix: %{customdata[3]:.0f}% owner / %{customdata[4]:.0f}% renter<br>"
                "Map zone: %{customdata[5]}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=title,
        height=360,
        margin=dict(l=10, r=10, t=45, b=10),
        plot_bgcolor="#F5F7F4",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    fig.update_xaxes(visible=False, range=[0.4, 5.7], fixedrange=True)
    fig.update_yaxes(visible=False, range=[1.0, 5.2], fixedrange=True, scaleanchor="x", scaleratio=1)
    fig.add_annotation(
        x=0.45,
        y=1.05,
        xref="x",
        yref="y",
        text="Offline schematic map: positions are for demo orientation, not geographic coordinates.",
        showarrow=False,
        font=dict(size=11, color="#586765"),
        align="left",
    )
    return fig


def fsa_context_map(
    dsm_profiles: pd.DataFrame,
    area_scores: pd.DataFrame,
    fsa_geojson: dict,
    area_locations: pd.DataFrame | None = None,
    selected_area: str | None = None,
    selected_fsa: str | None = None,
    title: str = "FSA-level energy/DSM context map",
) -> go.Figure:
    if not fsa_geojson:
        if area_locations is None:
            raise ValueError("area_locations is required when fsa_geojson is unavailable.")
        return area_context_map(dsm_profiles, area_locations, selected_area=selected_area, title=title)

    if "area" in area_scores.columns:
        df = dsm_profiles[["area", "area_label", "fsa_context"]].merge(
            area_scores.drop(columns=["fsa_context"], errors="ignore"),
            on="area",
            how="left",
        )
    else:
        df = area_scores.copy()
        df["area"] = ""
        df["area_label"] = "DSM report FSA"
    all_fsas = pd.DataFrame(
        {
            "fsa": [
                feature.get("properties", {}).get("CFSAUID")
                for feature in fsa_geojson.get("features", [])
            ]
        }
    ).dropna()
    if selected_fsa is None and selected_area is not None:
        match = df.loc[df["area"].eq(selected_area), "fsa_context"]
        if not match.empty:
            selected_fsa = match.iloc[0]

    fig = go.Figure()
    fig.add_trace(
        go.Choroplethmapbox(
            geojson=fsa_geojson,
            locations=all_fsas["fsa"],
            z=[1] * len(all_fsas),
            featureidkey="properties.CFSAUID",
            colorscale=[[0, "rgba(203,212,208,0.06)"], [1, "rgba(203,212,208,0.06)"]],
            showscale=False,
            marker_line_color="rgba(127,141,137,0.35)",
            marker_line_width=0.45,
            hovertemplate="<b>FSA %{location}</b><br>No demo DSM score shown<extra></extra>",
        )
    )
    fig.add_trace(
        go.Choroplethmapbox(
            geojson=fsa_geojson,
            locations=df["fsa_context"],
            z=df["demand_relevance"],
            featureidkey="properties.CFSAUID",
            colorscale=[
                [0, "rgba(231,237,233,0.12)"],
                [0.5, "rgba(143,174,167,0.18)"],
                [1, "rgba(47,107,99,0.24)"],
            ],
            marker_line_color="rgba(255,255,255,0.62)",
            marker_line_width=0.55,
            colorbar=dict(title="Demand<br>relevance", thickness=12),
            customdata=df[["area", "area_label", "Flex D", "Hilo", "LogisVert", "Low-income assistance"]],
            hovertemplate=(
                "<b>FSA %{location}</b><br>"
                "Matched demo area: %{customdata[0]}<br>"
                "%{customdata[1]}<br>"
                "Flex D: %{customdata[2]:.2f}<br>"
                "Hilo: %{customdata[3]:.2f}<br>"
                "LogisVert: %{customdata[4]:.2f}<br>"
                "Low-income assistance: %{customdata[5]:.2f}<extra></extra>"
            ),
        )
    )

    if selected_fsa is not None:
        fig.add_trace(
            go.Choroplethmapbox(
                geojson=fsa_geojson,
                locations=[selected_fsa],
                z=[1],
                featureidkey="properties.CFSAUID",
                colorscale=[[0, "rgba(255,127,14,0.03)"], [1, "rgba(255,127,14,0.03)"]],
                showscale=False,
                marker_line_color=SELECTED_COLOR,
                marker_line_width=3,
                hovertemplate=f"<b>Selected context</b><br>FSA {selected_fsa}<extra></extra>",
            )
        )

    fsa_points = _fsa_label_points(fsa_geojson)
    if not fsa_points.empty:
        fsa_points["is_selected"] = fsa_points["fsa"].eq(selected_fsa)
        fig.add_trace(
            go.Scattermapbox(
                lon=fsa_points["lon"],
                lat=fsa_points["lat"],
                mode="markers",
                text=fsa_points["fsa"],
                customdata=fsa_points[["fsa"]],
                marker=dict(
                    size=fsa_points["is_selected"].map({True: 18, False: 13}),
                    color=fsa_points["is_selected"].map({True: SELECTED_COLOR, False: "#263332"}),
                    opacity=fsa_points["is_selected"].map({True: 0.94, False: 0.34}),
                ),
                hovertemplate="<b>FSA %{text}</b><br>Click to choose residents<extra></extra>",
                name="Selectable FSA",
                showlegend=False,
            )
        )

    fig.update_layout(
        title=title,
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=45.56, lon=-73.67),
            zoom=8.9,
        ),
        height=430,
        margin=dict(l=0, r=0, t=38, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        clickmode="event+select",
        dragmode="pan",
    )
    fig.add_annotation(
        x=0,
        y=0,
        xref="paper",
        yref="paper",
        text="All Montreal FSAs are colored by DSM demand relevance from the report; basemap tiles load from OpenStreetMap.",
        showarrow=False,
        font=dict(size=11, color="#586765"),
        align="left",
    )
    return fig


def comparison_context_map(
    dsm_profiles: pd.DataFrame,
    area_locations: pd.DataFrame,
    area_a: str,
    area_b: str,
) -> go.Figure:
    fig = area_context_map(dsm_profiles, area_locations, selected_area=None, title="Matched area contexts")
    df = area_locations.set_index("area")
    overlays = [(area_a, "Resident A", "#2F6B63"), (area_b, "Resident B", "#D08C60")]
    for area, label, color in overlays:
        if area not in df.index:
            continue
        row = df.loc[area]
        fig.add_trace(
            go.Scatter(
                x=[row["x"]],
                y=[row["y"]],
                mode="markers+text",
                text=[label],
                textposition="bottom center",
                marker=dict(size=25, color=color, symbol="circle-open", line=dict(width=4)),
                hovertemplate=f"<b>{label}</b><br>{area}<extra></extra>",
                showlegend=False,
            )
        )
    return fig


def radar_chart(scores: pd.DataFrame) -> go.Figure:
    ordered = scores.sort_values("program")
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=ordered["alignment_score"],
            theta=ordered["program"],
            fill="toself",
            name="Selected resident",
            line_color="#2F6B63",
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False,
        height=330,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig


def distribution_bar(population: pd.DataFrame, column: str, title: str) -> go.Figure:
    counts = population[column].value_counts().rename_axis(column).reset_index(name="count")
    fig = px.bar(counts, x=column, y="count", color=column, color_discrete_sequence=COLOR_SEQUENCE, title=title)
    fig.update_layout(showlegend=False, height=330, margin=dict(l=10, r=10, t=50, b=80))
    fig.update_xaxes(title="", tickangle=-25)
    fig.update_yaxes(title="Demo residents")
    return fig


def average_vs_heterogeneous(population: pd.DataFrame, dsm_scores: pd.DataFrame) -> go.Figure:
    program_cols = ["Flex D", "Hilo", "LogisVert", "Low-income assistance"]
    long = dsm_scores.melt(id_vars=["area"], value_vars=program_cols, var_name="program", value_name="area_score")
    avg = long.groupby("program", as_index=False)["area_score"].mean()
    avg["case"] = "Average area"

    resident_counts = population["area"].value_counts().rename_axis("area").reset_index(name="n")
    weighted = long.merge(resident_counts, on="area", how="left")
    weighted["n"] = weighted["n"].fillna(0)
    hetero = weighted.loc[weighted.index.repeat(weighted["n"].astype(int))]
    fig = px.box(
        hetero,
        x="program",
        y="area_score",
        color="program",
        points="all",
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    fig.add_trace(
        go.Scatter(
            x=avg["program"],
            y=avg["area_score"],
            mode="markers",
            marker=dict(color="black", size=11, symbol="diamond"),
            name="Average area",
        )
    )
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=70), showlegend=True)
    fig.update_yaxes(title="Area-level alignment score", range=[0, 1])
    fig.update_xaxes(title="")
    return fig
