"""
OsdagBridge — Report Chart Generators
Generates publication-quality charts for Design Reports.
"""

import os
import math
import logging
from typing import Dict, Optional

# Ensure non-interactive backend for background and GUI thread safety
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from osdagbridge.core.utils.common import (
    KEY_DD_M_ULS_SAG,
    KEY_DD_MU_BOT,
    KEY_DD_M_ULS_HOG,
    KEY_DD_MU_TOP,
    KEY_DD_M_ULS_OH,
    KEY_DD_MU_OH,
    KEY_DD_PUNCH_VED,
    KEY_DD_VRD_C_MPA,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_MP_ED_TYPE,
)

logger = logging.getLogger("osdagbridge.core.reports.charts")


def _safe_float(val, default=0.0) -> float:
    """Safely convert a string/number from input_dict to float."""
    if val in (None, "", "N.A.", "NA", "None"):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def generate_material_charts(input_dict: dict, output_dir: str) -> Dict[str, str]:
    """
    Generate the Chapter 7 Material Take-off & Quantity Summary charts:
    1. Structural Steel Tonnage Breakdown (Girders, Cross Bracing, End Diaphragms)
    2. Concrete Deck Volume (m^3) vs. Reinforcement Steel Weight (MT)

    Returns
    -------
    Dict[str, str]
        Mapping from figure key to relative/absolute file path:
        {
            'mat_steel_tonnage': path,
            'mat_concrete_rebar': path
        }
    """
    os.makedirs(output_dir, exist_ok=True)
    generated = {}

    # -------------------------------------------------------------------------
    # 1. Structural Steel Tonnage Chart
    # -------------------------------------------------------------------------
    try:
        girder_wt = _safe_float(input_dict.get("steel_girders_wt_total"))
        
        cb_top = _safe_float(input_dict.get("bracing_top_wt_total"))
        cb_bot = _safe_float(input_dict.get("bracing_bot_wt_total"))
        cb_diag = _safe_float(input_dict.get("bracing_diag_wt_total"))
        cb_total = cb_top + cb_bot + cb_diag
        
        # End diaphragms: use explicit key if available or estimate from cross bracing
        ed_wt = _safe_float(input_dict.get("end_diaphragm_wt_total"))
        if ed_wt <= 0.0 and cb_total > 0.0:
            # If cross-bracing is used at ends, approximate ~25% of intermediate bracing
            ed_wt = round(cb_total * 0.25, 2)

        studs_wt = _safe_float(input_dict.get("shear_studs_wt_total"))

        categories = ["Girders", "Cross Bracing", "End Diaphragms"]
        weights = [girder_wt, cb_total, ed_wt]
        colors = ["#1f77b4", "#2ca02c", "#ff7f0e"]

        # If shear studs exist and have weight, add them as well
        if studs_wt > 0.0:
            categories.append("Shear Studs")
            weights.append(studs_wt)
            colors.append("#9467bd")

        fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=200)
        bars = ax.bar(categories, weights, color=colors, edgecolor="#2c3e50", linewidth=1.0, width=0.55)

        ax.set_ylabel("Weight (Metric Tonnes / MT)", fontsize=11, fontweight="bold", color="#2c3e50")
        ax.set_title("Structural Steel Tonnage Breakdown", fontsize=13, fontweight="bold", pad=14, color="#1a252f")
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        ax.set_axisbelow(True)

        max_w = max(weights) if weights and max(weights) > 0 else 1.0
        ax.set_ylim(0, max_w * 1.25)

        # Add data value labels on top of each bar
        for bar in bars:
            h = bar.get_height()
            ax.annotate(
                f"{h:.2f} MT",
                xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
                color="#2c3e50"
            )

        ax.tick_params(axis="x", labelsize=10.5)
        ax.tick_params(axis="y", labelsize=10)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)

        fig.tight_layout()
        steel_chart_path = os.path.join(output_dir, "mat_steel_tonnage.png")
        fig.savefig(steel_chart_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        generated["mat_steel_tonnage"] = steel_chart_path.replace("\\", "/")

    except Exception as exc:
        logger.warning(f"Failed to generate steel tonnage chart: {exc}", exc_info=True)

    # -------------------------------------------------------------------------
    # 2. Concrete Volume vs. Reinforcement Steel Weight Chart
    # -------------------------------------------------------------------------
    try:
        concrete_vol = _safe_float(input_dict.get("concrete_deck_vol_total"))
        rebar_wt = _safe_float(input_dict.get("rebar_deck_wt_total"))

        labels = ["Concrete Deck\nVolume (m³)", "Reinforcement Steel\nWeight (MT)"]
        values = [concrete_vol, rebar_wt]
        bar_colors = ["#7f8c8d", "#e67e22"]
        units = ["m³", "MT"]

        fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=200)
        bars = ax.bar(labels, values, color=bar_colors, edgecolor="#2c3e50", linewidth=1.0, width=0.45)

        ax.set_ylabel("Quantity (Volume in m³ / Weight in MT)", fontsize=11, fontweight="bold", color="#2c3e50")
        ax.set_title("Concrete Volume vs. Reinforcement Steel Weight", fontsize=12.5, fontweight="bold", pad=14, color="#1a252f")
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        ax.set_axisbelow(True)

        max_v = max(values) if values and max(values) > 0 else 1.0
        ax.set_ylim(0, max_v * 1.25)

        for bar, unit in zip(bars, units):
            h = bar.get_height()
            ax.annotate(
                f"{h:.2f} {unit}",
                xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10.5,
                fontweight="bold",
                color="#2c3e50"
            )

        ax.tick_params(axis="x", labelsize=10.5)
        ax.tick_params(axis="y", labelsize=10)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)

        fig.tight_layout()
        conc_chart_path = os.path.join(output_dir, "mat_concrete_rebar.png")
        fig.savefig(conc_chart_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        generated["mat_concrete_rebar"] = conc_chart_path.replace("\\", "/")

    except Exception as exc:
        logger.warning(f"Failed to generate concrete vs rebar chart: {exc}", exc_info=True)

    return generated


def extract_overall_ur_data(bridge) -> Dict[str, float]:
    """
    Extract governing Utilization Ratios (UR = Demand / Capacity)
    for all 4 primary structural elements:
      1. Steel Plate Girders
      2. Concrete Deck Slab
      3. Cross Bracing
      4. End Diaphragms
    """
    output_dict = bridge.output_dict or {}
    pg = (output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}

    # 1. Steel Plate Girders — envelope over all design checks and all girders
    girder_ur = 0.0
    for gd in pg.values():
        if str(gd).startswith("EB"):
            continue
        for chk in (gd.get("checks") or []):
            try:
                girder_ur = max(girder_ur, float(chk.get("dcr") or 0.0))
            except (TypeError, ValueError):
                pass
        for lc_data in (gd.get("per_lc") or {}).values():
            for chk in (lc_data.get("checks") or []):
                try:
                    girder_ur = max(girder_ur, float(chk.get("dcr") or 0.0))
                except (TypeError, ValueError):
                    pass

    # 2. Concrete Deck Slab — envelope over ULS flexure, shear, punching shear
    deck_rpt = output_dict.get("deck_report_values", {}) or {}
    deck_urs = []
    for dem_k, cap_k in [
        (KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT),
        (KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP),
        (KEY_DD_M_ULS_OH, KEY_DD_MU_OH),
        (KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA),
        (KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC),
    ]:
        try:
            cap = float(deck_rpt.get(cap_k) or 0.0)
            dem = float(deck_rpt.get(dem_k) or 0.0)
            if cap > 0.0:
                deck_urs.append(dem / cap)
        except (TypeError, ValueError):
            pass
    deck_ur = max(deck_urs, default=0.0)

    # 3. Cross Bracing — maximum efficiency across all pairs, members and force types
    cb_pairs = bridge.get_cb_pairs()
    cb_ur = 0.0
    for pair in cb_pairs:
        for member in ("diagonal", "chord"):
            for force in ("compression", "tension"):
                try:
                    eff = bridge.get_cb_efficiency(pair, member, force)
                    if eff:
                        cb_ur = max(cb_ur, float(eff))
                except (TypeError, ValueError):
                    pass

    # 4. End Diaphragms
    ed_type = ""
    for k, v in bridge.input_dict.items():
        if str(k).startswith(KEY_MP_ED_TYPE) and v:
            ed_type = str(v)
            break
    ed_is_cb = "brac" in ed_type.strip().lower()
    ed_ur = cb_ur if ed_is_cb else float("nan")

    return {
        "Steel Plate Girders": girder_ur,
        "Concrete Deck Slab": deck_ur,
        "Cross Bracing": cb_ur,
        "End Diaphragms": ed_ur,
    }


def generate_ur_barchart(ur_data: Dict[str, float], output_path: str) -> str:
    """
    Generate Section 5.5 Overall Utilization Ratio Summary bar chart.

    Parameters
    ----------
    ur_data : Dict[str, float]
        Dictionary with element names and their corresponding governing UR.
    output_path : str
        Target PNG output file path.

    Returns
    -------
    str
        File path of the generated plot.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    labels = list(ur_data.keys())
    values = list(ur_data.values())

    colors = []
    for v in values:
        if v != v or math.isnan(v):
            colors.append("#bdc3c7")
        elif v <= 1.0:
            colors.append("#27ae60")  # Passing (green)
        else:
            colors.append("#e74c3c")  # Failing (red)

    fig, ax = plt.subplots(figsize=(8.0, 4.6), dpi=200)

    plot_values = [0.0 if (v != v or math.isnan(v)) else v for v in values]
    bars = ax.bar(labels, plot_values, color=colors, edgecolor="#2c3e50", linewidth=1.0, width=0.52)

    # Distinct horizontal reference line at UR = 1.0 (Red dashed line)
    ax.axhline(1.0, color="#c0392b", linestyle="--", linewidth=1.8, label="Limit Threshold (UR = 1.0)")

    ax.set_ylabel("Utilization Ratio (Demand / Capacity)", fontsize=11, fontweight="bold", color="#2c3e50")
    ax.set_title("Overall Design Check — Utilization Ratio Summary", fontsize=13, fontweight="bold", pad=14, color="#1a252f")

    max_val = max([v for v in plot_values if v > 0] or [1.0])
    ax.set_ylim(0, max(1.35, max_val * 1.25))

    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    # Annotate values above each bar
    for bar, raw_val in zip(bars, values):
        if raw_val == raw_val and not math.isnan(raw_val) and raw_val > 0:
            status_txt = f"{raw_val:.2f}"
            status_color = "#27ae60" if raw_val <= 1.0 else "#c0392b"
            ax.annotate(
                status_txt,
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold",
                color=status_color
            )
        elif raw_val == 0.0:
            ax.annotate(
                "0.00",
                xy=(bar.get_x() + bar.get_width() / 2, 0),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10.5,
                color="#7f8c8d"
            )
        else:
            ax.annotate(
                "N/A",
                xy=(bar.get_x() + bar.get_width() / 2, 0.02),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10.5,
                color="#7f8c8d"
            )

    ax.tick_params(axis="x", labelsize=10.5)
    ax.tick_params(axis="y", labelsize=10)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    ax.legend(loc="upper right", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path.replace("\\", "/")
