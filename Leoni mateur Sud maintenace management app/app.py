"""Leoni Mateur Sud — Maintenance Defect Analysis Dashboard."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from analysis import (
    compute_kpis,
    cross_ref_defect,
    daily_trend,
    generate_insights,
    get_solutions,
    heatmap_data,
    load_report,
    location_hotspots,
    pareto_data,
    team_breakdown,
    weekly_trend,
)

DEFAULT_FILE = "defect_full_report_bol_702092.xlsx"

st.set_page_config(
    page_title="Leoni — Analyse Défauts",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLORS = {
    "primary": "#1B4F72",
    "accent": "#E67E22",
    "success": "#27AE60",
    "danger": "#C0392B",
    "warning": "#F39C12",
    "bg": "#F4F6F9",
}

SEVERITY_COLORS = {"high": "#C0392B", "medium": "#E67E22", "low": "#27AE60"}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .main { background-color: #F4F6F9; }
        .kpi-card {
            background: white;
            border-radius: 12px;
            padding: 1.2rem 1.4rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border-left: 4px solid #1B4F72;
            height: 100%;
        }
        .kpi-value { font-size: 2rem; font-weight: 700; color: #1B4F72; line-height: 1.1; }
        .kpi-label { font-size: 0.85rem; color: #666; margin-top: 0.3rem; }
        .insight-card {
            background: white;
            border-radius: 10px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.8rem;
            box-shadow: 0 1px 4px rgba(0,0,0,0.05);
            border-left: 4px solid #E67E22;
        }
        .insight-high { border-left-color: #C0392B; }
        .insight-medium { border-left-color: #E67E22; }
        .insight-low { border-left-color: #27AE60; }
        div[data-testid="stSidebar"] { background: #1B4F72; }
        div[data-testid="stSidebar"] * { color: white !important; }
        div[data-testid="stSidebar"] .stSelectbox label,
        div[data-testid="stSidebar"] .stFileUploader label { color: white !important; }
        h1, h2, h3 { color: #1B4F72; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, sub: str = "") -> None:
    sub_html = f'<div style="font-size:0.75rem;color:#999;margin-top:4px">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-value">{value}</div>'
        f'<div class="kpi-label">{label}</div>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def render_kpis(kpis: dict) -> None:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        kpi_card("Total défauts", f"{kpis['total_defects']:,}")
    with c2:
        kpi_card("Jours analysés", str(kpis["unique_dates"]))
    with c3:
        kpi_card("Équipes", str(kpis["unique_teams"]))
    with c4:
        kpi_card("Types de défauts", str(kpis["unique_defect_types"]))
    with c5:
        kpi_card("Références", str(kpis["unique_references"]))
    with c6:
        kpi_card("Moy. / jour", str(kpis["avg_daily_defects"]))


def pareto_chart(pareto: pd.DataFrame) -> go.Figure:
    if pareto.empty:
        return empty_figure("Diagramme de Pareto — Types de défauts")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=pareto["Defect_Type"],
            y=pareto["Count"],
            name="Nombre",
            marker_color=COLORS["primary"],
            text=pareto["Count"],
            textposition="outside",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=pareto["Defect_Type"],
            y=pareto["Cumulative_%"],
            name="Cumul %",
            mode="lines+markers",
            line=dict(color=COLORS["accent"], width=3),
            marker=dict(size=8),
        ),
        secondary_y=True,
    )
    fig.add_hline(y=80, line_dash="dash", line_color=COLORS["danger"], secondary_y=True)
    fig.update_layout(
        title="Diagramme de Pareto — Types de défauts",
        template="plotly_white",
        height=420,
        legend=dict(orientation="h", y=1.12),
        margin=dict(t=60),
    )
    fig.update_yaxes(title_text="Nombre de défauts", secondary_y=False)
    fig.update_yaxes(title_text="Cumul (%)", range=[0, 105], secondary_y=True)
    fig.update_xaxes(tickangle=-25)
    return fig


def team_chart(team_df: pd.DataFrame) -> go.Figure:
    if team_df.empty:
        return empty_figure("Répartition par équipe")
    colors = px.colors.qualitative.Set2[: len(team_df)]
    fig = px.pie(
        team_df,
        names="TEAM",
        values="Count",
        title="Répartition par équipe",
        color_discrete_sequence=colors,
        hole=0.4,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label+value")
    fig.update_layout(height=380, template="plotly_white")
    return fig


def trend_chart(daily: pd.DataFrame) -> go.Figure:
    if daily.empty:
        return empty_figure("Évolution quotidienne des défauts")
    fig = px.area(
        daily,
        x="Date",
        y="Count",
        title="Évolution quotidienne des défauts",
        color_discrete_sequence=[COLORS["primary"]],
    )
    fig.add_trace(
        go.Scatter(
            x=daily["Date"],
            y=daily["Count"].rolling(7, min_periods=1).mean(),
            name="Moyenne mobile 7j",
            line=dict(color=COLORS["accent"], width=2, dash="dot"),
        )
    )
    fig.update_layout(height=380, template="plotly_white", hovermode="x unified")
    return fig


def heatmap_chart(pivot: pd.DataFrame) -> go.Figure:
    if pivot.empty:
        return empty_figure("Matrice Référence × Type de défaut")
    fig = px.imshow(
        pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        text_auto=True,
        color_continuous_scale="Blues",
        title="Matrice Référence × Type de défaut",
        aspect="auto",
    )
    fig.update_layout(height=400, template="plotly_white")
    return fig


def location_chart(loc_df: pd.DataFrame) -> go.Figure:
    if loc_df.empty:
        return empty_figure("Top 10 zones (EXT1) — Points chauds")
    fig = px.bar(
        loc_df.sort_values("Count"),
        x="Count",
        y="Location",
        orientation="h",
        title="Top 10 zones (EXT1) — Points chauds",
        color="Count",
        color_continuous_scale="Reds",
    )
    fig.update_layout(height=400, template="plotly_white", showlegend=False)
    return fig


def cross_bar_chart(cross: pd.DataFrame, top_n: int = 12) -> go.Figure:
    if cross.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f"Top {top_n} combinaisons Référence / Défaut",
            template="plotly_white",
            height=450,
            annotations=[{"text": "Aucune donnée pour les filtres sélectionnés", "showarrow": False, "font": {"size": 14}}],
        )
        return fig
    top = cross.head(top_n).copy()
    top["Label"] = top["REFERENCE"] + " | " + top["DEFAUT"]
    fig = px.bar(
        top.sort_values("Count"),
        x="Count",
        y="Label",
        orientation="h",
        title=f"Top {top_n} combinaisons Référence / Défaut",
        color="Count",
        color_continuous_scale="Oranges",
    )
    fig.update_layout(height=450, template="plotly_white", showlegend=False)
    return fig


def empty_figure(title: str, message: str = "Aucune donnée pour les filtres sélectionnés") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=380,
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[{"text": message, "showarrow": False, "font": {"size": 14, "color": "#666"}}],
    )
    return fig


def plot_chart(fig: go.Figure, key: str) -> None:
    st.plotly_chart(fig, use_container_width=True, key=key)


def apply_filters(
    df: pd.DataFrame,
    sel_teams: list,
    sel_defects: list,
    sel_refs: list,
    date_range: tuple | None,
    all_teams: list,
    all_defects: list,
    all_refs: list,
) -> pd.DataFrame:
    teams = sel_teams if sel_teams else all_teams
    defects = sel_defects if sel_defects else all_defects
    refs = sel_refs if sel_refs else all_refs

    mask = df["TEAM"].isin(teams) & df["DEFAUT"].isin(defects) & df["REFERENCE"].isin(refs)
    filtered = df[mask]

    if date_range and df["DATE"].notna().any():
        filtered = filtered[
            (filtered["DATE"].dt.date >= date_range[0])
            & (filtered["DATE"].dt.date <= date_range[1])
        ]
    return filtered


@st.cache_data
def load_data(file_path: str) -> tuple[pd.DataFrame, dict]:
    sheets = load_report(file_path)
    df = sheets["All_Defects"]
    return df, sheets


def main() -> None:
    inject_css()

    logo_path = Path(__file__).parent / "leoni.png"
    if logo_path.exists():
        st.sidebar.image(str(logo_path), width=180)
    st.sidebar.title("Maintenance Analytics")
    st.sidebar.markdown("**Leoni Mateur Sud**")
    st.sidebar.divider()

    default_path = Path(__file__).parent / DEFAULT_FILE
    uploaded = st.sidebar.file_uploader("Charger un autre rapport Excel", type=["xlsx", "xls"])

    if uploaded:
        tmp = Path(__file__).parent / "_uploaded_report.xlsx"
        tmp.write_bytes(uploaded.getvalue())
        file_path = str(tmp)
        load_data.clear()
    elif default_path.exists():
        file_path = str(default_path)
    else:
        st.error("Aucun fichier Excel trouvé. Placez un rapport ou uploadez-en un.")
        st.stop()

    st.sidebar.success(f"📄 {Path(file_path).name}")

    df, sheets = load_data(file_path)

    # Sidebar filters (before KPIs so they reflect selection)
    st.sidebar.subheader("Filtres")
    all_teams = sorted(df["TEAM"].dropna().unique())
    all_defects = sorted(df["DEFAUT"].dropna().unique())
    all_refs = sorted(df["REFERENCE"].dropna().unique())

    if st.sidebar.button("Réinitialiser les filtres", use_container_width=True):
        for key in ("filter_teams", "filter_defects", "filter_refs", "filter_dates"):
            st.session_state.pop(key, None)
        st.rerun()

    if "filter_teams" not in st.session_state:
        st.session_state.filter_teams = all_teams
    if "filter_defects" not in st.session_state:
        st.session_state.filter_defects = all_defects
    if "filter_refs" not in st.session_state:
        st.session_state.filter_refs = all_refs

    sel_teams = st.sidebar.multiselect(
        "Équipes", all_teams, key="filter_teams",
        placeholder="Toutes les équipes",
    )
    sel_defects = st.sidebar.multiselect(
        "Types de défauts", all_defects, key="filter_defects",
        placeholder="Tous les types",
    )
    sel_refs = st.sidebar.multiselect(
        "Références", all_refs, key="filter_refs",
        placeholder="Toutes les références",
    )

    date_range = None
    if df["DATE"].notna().any():
        min_d, max_d = df["DATE"].min().date(), df["DATE"].max().date()
        if "filter_dates" not in st.session_state:
            st.session_state.filter_dates = (min_d, max_d)
        date_range = st.sidebar.slider(
            "Plage de dates",
            min_value=min_d,
            max_value=max_d,
            key="filter_dates",
        )

    if not sel_teams and not sel_defects and not sel_refs:
        st.sidebar.caption("Aucune sélection → toutes les valeurs sont incluses.")

    filtered = apply_filters(
        df, sel_teams, sel_defects, sel_refs, date_range,
        all_teams, all_defects, all_refs,
    )

    active_filters = []
    if sel_teams and set(sel_teams) != set(all_teams):
        active_filters.append(f"Équipes: {', '.join(sel_teams)}")
    if sel_defects and set(sel_defects) != set(all_defects):
        active_filters.append(f"Défauts: {len(sel_defects)} sélectionné(s)")
    if sel_refs and set(sel_refs) != set(all_refs):
        active_filters.append(f"Références: {len(sel_refs)} sélectionnée(s)")
    if date_range and df["DATE"].notna().any():
        full_range = (df["DATE"].min().date(), df["DATE"].max().date())
        if date_range != full_range:
            active_filters.append(f"Dates: {date_range[0]} → {date_range[1]}")

    kpis = compute_kpis(filtered)
    full_kpis = compute_kpis(df)

    st.title("🔧 Tableau de bord — Analyse des défauts")
    st.caption(
        f"Période : {full_kpis['date_start']} → {full_kpis['date_end']}  |  BOL 702092"
        + (f"  |  {len(filtered)} / {len(df)} défauts affichés" if len(filtered) != len(df) else "")
    )

    if active_filters:
        st.info("Filtres actifs : " + " · ".join(active_filters))

    render_kpis(kpis)
    st.divider()

    if filtered.empty:
        st.warning("Aucun défaut ne correspond aux filtres sélectionnés. Élargissez la sélection ou réinitialisez les filtres.")
        st.stop()

    tab_dash, tab_charts, tab_insights, tab_solutions, tab_data = st.tabs(
        ["📊 Vue d'ensemble", "📈 Graphiques", "💡 Insights", "🛠️ Solutions", "📋 Données"]
    )

    pareto = pareto_data(filtered)
    team_df = team_breakdown(filtered)
    cross = cross_ref_defect(filtered)
    daily = daily_trend(filtered)
    weekly = weekly_trend(filtered)
    locations = location_hotspots(filtered)
    pivot = heatmap_data(filtered)
    insights = generate_insights(filtered)
    solutions = get_solutions(filtered)

    with tab_dash:
        col1, col2 = st.columns([3, 2])
        with col1:
            plot_chart(pareto_chart(pareto), key="dash_pareto")
        with col2:
            plot_chart(team_chart(team_df), key="dash_team")

        col3, col4 = st.columns(2)
        with col3:
            plot_chart(trend_chart(daily), key="dash_trend")
        with col4:
            plot_chart(location_chart(locations), key="dash_location")

        plot_chart(cross_bar_chart(cross), key="dash_cross")

    with tab_charts:
        chart_type = st.selectbox(
            "Type de graphique",
            [
                "Pareto défauts",
                "Tendance quotidienne",
                "Tendance hebdomadaire",
                "Par équipe",
                "Heatmap Réf × Défaut",
                "Points chauds (EXT1)",
                "Top combinaisons",
                "Défauts par référence",
            ],
            key="chart_type_select",
        )

        if chart_type == "Pareto défauts":
            plot_chart(pareto_chart(pareto), key="charts_pareto")
        elif chart_type == "Tendance quotidienne":
            plot_chart(trend_chart(daily), key="charts_trend")
        elif chart_type == "Tendance hebdomadaire":
            if weekly.empty:
                plot_chart(empty_figure("Défauts par semaine"), key="charts_weekly")
            else:
                fig = px.bar(
                    weekly, x="Week", y="Count", title="Défauts par semaine",
                    color_discrete_sequence=[COLORS["primary"]],
                )
                fig.update_layout(template="plotly_white", height=420)
                plot_chart(fig, key="charts_weekly")
        elif chart_type == "Par équipe":
            c1, c2 = st.columns(2)
            with c1:
                plot_chart(team_chart(team_df), key="charts_team_pie")
            with c2:
                team_defect = filtered.groupby(["TEAM", "DEFAUT"]).size().reset_index(name="Count")
                if team_defect.empty:
                    plot_chart(empty_figure("Défauts par équipe et type"), key="charts_team_stack")
                else:
                    fig = px.bar(
                        team_defect, x="TEAM", y="Count", color="DEFAUT",
                        title="Défauts par équipe et type", barmode="stack",
                    )
                    fig.update_layout(template="plotly_white", height=380)
                    plot_chart(fig, key="charts_team_stack")
        elif chart_type == "Heatmap Réf × Défaut":
            plot_chart(heatmap_chart(pivot), key="charts_heatmap")
        elif chart_type == "Points chauds (EXT1)":
            plot_chart(location_chart(locations), key="charts_location")
        elif chart_type == "Top combinaisons":
            plot_chart(cross_bar_chart(cross, top_n=15), key="charts_cross")
        else:
            ref_counts = filtered.groupby("REFERENCE").size().reset_index(name="Count")
            if ref_counts.empty:
                plot_chart(empty_figure("Défauts par référence produit"), key="charts_refs")
            else:
                fig = px.bar(
                    ref_counts.sort_values("Count"), x="REFERENCE", y="Count",
                    title="Défauts par référence produit",
                    color="Count", color_continuous_scale="Blues",
                )
                fig.update_layout(template="plotly_white", height=420)
                plot_chart(fig, key="charts_refs")

    with tab_insights:
        st.subheader("Insights automatiques")
        st.markdown(
            "Analyse générée à partir des données filtrées. "
            "Les insights à **priorité haute** nécessitent une action immédiate."
        )

        if not insights:
            st.info("Pas assez de données pour générer des insights avec les filtres actuels.")
        else:
            for ins in insights:
                sev_class = f"insight-{ins.severity}"
                sev_color = SEVERITY_COLORS[ins.severity]
                st.markdown(
                    f'<div class="insight-card {sev_class}">'
                    f'<span style="background:{sev_color};color:white;padding:2px 8px;'
                    f'border-radius:4px;font-size:0.75rem;font-weight:600">'
                    f'{ins.severity.upper()}</span> '
                    f'<span style="color:#888;font-size:0.8rem;margin-left:8px">{ins.category}</span>'
                    f'<h4 style="margin:8px 0 4px">{ins.title}</h4>'
                    f'<p style="margin:0 0 8px">{ins.description}</p>'
                    f'<p style="margin:0;font-weight:500;color:#1B4F72">→ {ins.action}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.subheader("Résumé exécutif")
        if len(filtered) and not pareto.empty:
            top = pareto.iloc[0]
            pareto_pct = pareto.head(2)["Cumulative_%"].iloc[-1] if len(pareto) >= 2 else top["Cumulative_%"]
            st.markdown(
                f"""
                Sur **{len(filtered)} défauts** enregistrés (filtres appliqués), le type dominant est
                **{top['Defect_Type']}** ({top['Count']} cas, {top['Count']/len(filtered)*100:.0f}%).

                En appliquant la règle de Pareto, corriger les 2 premiers types de défauts
                permettrait d'éliminer environ **{pareto_pct:.0f}%** des non-conformités.

                L'équipe **{kpis['worst_team']}** concentre **{kpis['worst_team_pct']}%** des défauts
                affichés et mérite une attention particulière en termes de formation et de procédures.
                """
            )

    with tab_solutions:
        st.subheader("Plans d'action recommandés")
        st.markdown("Solutions priorisées par type de défaut, basées sur les bonnes pratiques maintenance.")

        for plan in solutions:
            with st.expander(
                f"**{plan['priority']}** — {plan['defect']} ({plan['count']} cas)",
                expanded=plan["priority"] == "P1",
            ):
                st.markdown(f"**Références impactées :** {', '.join(plan['references'])}")
                if plan["hotspots"]:
                    st.markdown(f"**Zones chaudes (EXT1) :** {', '.join(str(h) for h in plan['hotspots'])}")
                st.markdown("**Actions recommandées :**")
                for i, sol in enumerate(plan["solutions"], 1):
                    st.markdown(f"{i}. {sol}")

        st.divider()
        st.subheader("Export rapport")
        report_lines = ["# Rapport d'analyse défauts — Leoni Mateur Sud\n"]
        report_lines.append(f"Période: {kpis['date_start']} → {kpis['date_end']}\n")
        report_lines.append(f"Total défauts: {len(filtered)}\n\n## Insights\n")
        for ins in insights:
            report_lines.append(f"### [{ins.severity.upper()}] {ins.title}\n{ins.description}\n→ {ins.action}\n\n")
        report_lines.append("## Plans d'action\n")
        for plan in solutions:
            report_lines.append(f"### {plan['defect']} ({plan['count']} cas)\n")
            for sol in plan["solutions"]:
                report_lines.append(f"- {sol}\n")
            report_lines.append("\n")

        st.download_button(
            "📥 Télécharger le rapport (Markdown)",
            data="".join(report_lines),
            file_name="rapport_defauts_leoni.md",
            mime="text/markdown",
            key="download_report",
        )

    with tab_data:
        st.subheader("Explorateur de données")
        st.dataframe(
            filtered.sort_values("DATE", ascending=False),
            use_container_width=True,
            height=500,
        )
        csv = filtered.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 Exporter CSV filtré",
            data=csv,
            file_name="defauts_filtres.csv",
            mime="text/csv",
            key="download_csv",
        )


if __name__ == "__main__":
    main()
