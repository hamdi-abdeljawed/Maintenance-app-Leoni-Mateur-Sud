"""Defect data analysis and insight generation for Leoni maintenance reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


DEFECT_SOLUTIONS: dict[str, list[str]] = {
    "DETECTION MANQUE": [
        "Vérifier l'étalonnage des capteurs de détection sur les postes concernés.",
        "Contrôler la positionnement des pièces avant passage au poste de test.",
        "Former les opérateurs sur les critères de détection manquante.",
        "Mettre en place un contrôle visuel renforcé en fin de ligne.",
    ],
    "MANQUE CONTINUITE": [
        "Inspecter les connexions crimpage/soudure aux extrémités signalées (EXT1/EXT2).",
        "Vérifier la qualité des fils et des bornes aux postes TGX/BY/EL.",
        "Contrôler les paramètres de la machine de sertissage.",
        "Auditer la chaîne d'approvisionnement des composants électriques.",
    ],
    "Court-circuit": [
        "Analyser l'isolation des fils aux zones TGX73, TGX58 et BY023.",
        "Vérifier l'absence de fils nus ou de brins sortis après dénudage.",
        "Contrôler le routage des faisceaux pour éviter les frottements.",
        "Renforcer le contrôle qualité sur les postes à fort taux de court-circuit.",
    ],
    "DETECTION EN SURPLUS": [
        "Recalibrer les seuils de détection pour réduire les faux positifs.",
        "Vérifier la présence de composants en double ou mal positionnés.",
    ],
    "INVERSION": [
        "Mettre à jour les fiches de montage avec codes couleur renforcés.",
        "Former les équipes sur l'ordre de branchement correct par référence.",
        "Installer des guides visuels au poste pour les connexions critiques.",
    ],
    "BRANCHEMENT ERRONEE": [
        "Revoir les instructions de montage pour les références concernées.",
        "Mettre en place un contrôle croisé par un second opérateur.",
    ],
}


@dataclass
class Insight:
    severity: str  # high, medium, low
    category: str
    title: str
    description: str
    action: str


def load_report(excel_path: str) -> dict[str, pd.DataFrame]:
    """Load all sheets from the defect Excel report."""
    xl = pd.ExcelFile(excel_path)
    sheets = {name: pd.read_excel(excel_path, sheet_name=name) for name in xl.sheet_names}
    if "All_Defects" in sheets:
        sheets["All_Defects"] = _prepare_defects(sheets["All_Defects"])
    return sheets


def _prepare_defects(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["DATE"] = pd.to_datetime(out["DATE"], format="%d/%m/%y", errors="coerce")
    out["WEEK"] = out["DATE"].dt.isocalendar().week.astype("Int64")
    out["MONTH"] = out["DATE"].dt.to_period("M").astype(str)
    return out


def compute_kpis(df: pd.DataFrame) -> dict[str, Any]:
    total = len(df)
    by_defect = df["DEFAUT"].value_counts()
    top_defect = by_defect.index[0] if len(by_defect) else "—"
    top_pct = round(by_defect.iloc[0] / total * 100, 1) if total else 0
    by_team = df.groupby("TEAM").size()
    worst_team = by_team.idxmax() if len(by_team) else "—"
    worst_team_pct = round(by_team.max() / total * 100, 1) if total else 0
    date_range = (
        df["DATE"].min().strftime("%d/%m/%Y") if df["DATE"].notna().any() else "—",
        df["DATE"].max().strftime("%d/%m/%Y") if df["DATE"].notna().any() else "—",
    )
    daily = df.groupby(df["DATE"].dt.date).size()
    avg_daily = round(daily.mean(), 1) if len(daily) else 0
    return {
        "total_defects": total,
        "unique_dates": df["DATE"].nunique(),
        "unique_teams": df["TEAM"].nunique(),
        "unique_defect_types": df["DEFAUT"].nunique(),
        "unique_references": df["REFERENCE"].nunique(),
        "top_defect": top_defect,
        "top_defect_pct": top_pct,
        "worst_team": worst_team,
        "worst_team_pct": worst_team_pct,
        "date_start": date_range[0],
        "date_end": date_range[1],
        "avg_daily_defects": avg_daily,
    }


def pareto_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Defect_Type", "Count", "Cumulative_%"])
    counts = df["DEFAUT"].value_counts().reset_index()
    counts.columns = ["Defect_Type", "Count"]
    total = counts["Count"].sum()
    counts["Cumulative_%"] = (counts["Count"].cumsum() / total * 100).round(2) if total else 0
    return counts


def cross_ref_defect(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["REFERENCE", "DEFAUT", "Count"])
    cross = (
        df.groupby(["REFERENCE", "DEFAUT"])
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )
    return cross


def team_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["TEAM", "Count"])
    return df.groupby("TEAM").size().reset_index(name="Count").sort_values("Count", ascending=False)


def daily_trend(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Date", "Count"])
    trend = df.groupby(df["DATE"].dt.date).size().reset_index(name="Count")
    trend.columns = ["Date", "Count"]
    return trend.sort_values("Date")


def weekly_trend(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Week", "Count"])
    trend = df.groupby("WEEK").size().reset_index(name="Count")
    trend.columns = ["Week", "Count"]
    return trend.sort_values("Week")


def location_hotspots(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Location", "Count"])
    ext = df["EXT1"].value_counts().head(top_n).reset_index()
    ext.columns = ["Location", "Count"]
    return ext


def heatmap_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    pivot = pd.crosstab(df["REFERENCE"], df["DEFAUT"])
    return pivot


def generate_insights(df: pd.DataFrame) -> list[Insight]:
    insights: list[Insight] = []
    total = len(df)
    if total == 0:
        return insights

    kpis = compute_kpis(df)
    pareto = pareto_data(df)
    cross = cross_ref_defect(df)
    team = team_breakdown(df)
    locations = location_hotspots(df, 5)

    # 80/20 Pareto insight
    top2 = pareto.head(2)
    if len(top2) >= 2:
        combined_pct = top2["Cumulative_%"].iloc[-1]
        insights.append(
            Insight(
                severity="high",
                category="Pareto",
                title="Concentration des défauts (règle 80/20)",
                description=(
                    f"Les 2 principaux types — **{top2.iloc[0]['Defect_Type']}** "
                    f"({top2.iloc[0]['Count']} cas) et **{top2.iloc[1]['Defect_Type']}** "
                    f"({top2.iloc[1]['Count']} cas) — représentent **{combined_pct:.0f}%** "
                    "de tous les défauts."
                ),
                action="Prioriser les actions correctives sur ces 2 types pour un impact maximal.",
            )
        )

    # Worst reference × defect combo
    if len(cross):
        worst = cross.iloc[0]
        insights.append(
            Insight(
                severity="high",
                category="Référence",
                title="Combinaison référence / défaut la plus critique",
                description=(
                    f"**{worst['REFERENCE']}** avec **{worst['DEFAUT']}** "
                    f"({worst['Count']} occurrences, {worst['Count']/total*100:.1f}% du total)."
                ),
                action=f"Lancer un plan d'action ciblé sur {worst['REFERENCE']} — {worst['DEFAUT']}.",
            )
        )

    # Team imbalance
    if len(team) >= 2:
        top_team = team.iloc[0]
        bottom_team = team.iloc[-1]
        ratio = top_team["Count"] / max(bottom_team["Count"], 1)
        if ratio > 2:
            insights.append(
                Insight(
                    severity="medium",
                    category="Équipe",
                    title="Déséquilibre entre équipes",
                    description=(
                        f"L'équipe **{top_team['TEAM']}** enregistre {top_team['Count']} défauts "
                        f"({top_team['Count']/total*100:.0f}%) vs {bottom_team['Count']} pour "
                        f"l'équipe **{bottom_team['TEAM']}** (ratio {ratio:.1f}x)."
                    ),
                    action="Analyser les différences de procédure, formation ou charge entre équipes.",
                )
            )

    # Location hotspots
    if len(locations):
        top_loc = locations.iloc[0]
        loc_pct = top_loc["Count"] / total * 100
        if loc_pct > 10:
            insights.append(
                Insight(
                    severity="medium",
                    category="Localisation",
                    title="Point chaud géographique sur le faisceau",
                    description=(
                        f"La zone **{top_loc['Location']}** concentre {top_loc['Count']} défauts "
                        f"({loc_pct:.1f}% du total)."
                    ),
                    action=f"Inspection approfondie et contrôle renforcé au poste {top_loc['Location']}.",
                )
            )

    # Trend: recent vs earlier period
    daily = daily_trend(df)
    if len(daily) >= 14:
        recent = daily.tail(7)["Count"].mean()
        earlier = daily.head(max(len(daily) - 7, 7)).tail(7)["Count"].mean()
        if earlier > 0:
            change = (recent - earlier) / earlier * 100
            direction = "hausse" if change > 0 else "baisse"
            severity = "high" if abs(change) > 25 else "low"
            insights.append(
                Insight(
                    severity=severity,
                    category="Tendance",
                    title=f"Tendance récente : {direction} de {abs(change):.0f}%",
                    description=(
                        f"Moyenne des 7 derniers jours : {recent:.1f} défauts/jour vs "
                        f"{earlier:.1f} défauts/jour sur la période précédente."
                    ),
                    action=(
                        "Investiguer les causes de la hausse récente."
                        if change > 10
                        else "Maintenir les bonnes pratiques — la tendance est favorable."
                    ),
                )
            )

    # Court-circuit specific
    cc_count = (df["DEFAUT"] == "Court-circuit").sum()
    if cc_count > 0:
        cc_pct = cc_count / total * 100
        cc_locs = df[df["DEFAUT"] == "Court-circuit"]["EXT1"].value_counts().head(3)
        loc_str = ", ".join(f"{k} ({v})" for k, v in cc_locs.items())
        insights.append(
            Insight(
                severity="high" if cc_pct > 10 else "medium",
                category="Sécurité",
                title="Court-circuits détectés",
                description=(
                    f"**{cc_count}** court-circuits ({cc_pct:.1f}%). "
                    f"Zones principales : {loc_str}."
                ),
                action="Priorité sécurité : audit immédiat de l'isolation aux postes identifiés.",
            )
        )

    return insights


def get_solutions(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Generate prioritized action plans per defect type."""
    pareto = pareto_data(df)
    cross = cross_ref_defect(df)
    plans: list[dict[str, Any]] = []

    for _, row in pareto.iterrows():
        defect = row["Defect_Type"]
        count = row["Count"]
        pct = row["Cumulative_%"]
        solutions = DEFECT_SOLUTIONS.get(defect, ["Analyser les causes racines via méthode 5 Why."])
        affected_refs = cross[cross["DEFAUT"] == defect]["REFERENCE"].tolist()
        top_locs = (
            df[df["DEFAUT"] == defect]["EXT1"]
            .value_counts()
            .head(3)
            .index.tolist()
        )
        plans.append(
            {
                "defect": defect,
                "count": count,
                "priority": "P1" if pct <= 80 else "P2",
                "solutions": solutions,
                "references": affected_refs,
                "hotspots": top_locs,
            }
        )
    return plans
