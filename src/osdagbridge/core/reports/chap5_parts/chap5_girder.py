# =============================================================================
# Chapter 5 — Plate Girder table data builders (Tables 5.1 – 5.13)
# Extracted from chap5.py — DO NOT add business logic here.
# =============================================================================
from __future__ import annotations

import re

from osdagbridge.core.utils.common import (
    KEY_DESIGN_MODE,
    KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_WIDTH,
    KEY_SD_BS_FCD,
    KEY_SD_BS_FCDW_LC,
    KEY_SD_BS_FCDW_WB,
    KEY_SD_BS_FPSD,
    KEY_SD_BS_R,
    KEY_SD_CLASS_FLANGE,
    KEY_SD_CLASS_WEB,
    KEY_SD_COMPOSITE_IZ,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
    KEY_SD_EFFECTIVE_SLAB_WIDTH,
    KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_FLANGE_SLENDERNESS,
    KEY_SD_HIGH_SHEAR,
    KEY_SD_IS_FQ,
    KEY_SD_IS_FQD,
    KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV,
    KEY_SD_LTB_CHI,
    KEY_SD_LTB_LAMBDA,
    KEY_SD_LTB_MB,
    KEY_SD_LTB_MCR,
    KEY_SD_MDV,
    KEY_SD_MD_CAPACITY,
    KEY_SD_MN_AXIAL,
    KEY_SD_MN_MOMENT,
    KEY_SD_MN_RATIO,
    KEY_SD_MU_APPLIED,
    KEY_SD_PANEL_CD,
    KEY_SD_PNA_DEPTH,
    KEY_SD_SECTION_CLASS,
    KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IZ,
    KEY_SD_SECTION_PROP_ZUZ,
    KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SHEAR_AV,
    KEY_SD_SHEAR_KV,
    KEY_SD_SHEAR_LAMBDA_W,
    KEY_SD_SHEAR_TAU_B,
    KEY_SD_SHEAR_VCR,
    KEY_SD_SHEAR_VU,
    KEY_SD_STIFF_END_COUNT,
    KEY_SD_STIFF_END_THICK,
    KEY_SD_STIFF_INT_SPACING,
    KEY_SD_STIFF_INT_THICK,
    KEY_SD_STIFF_LONG,
    KEY_SD_STIFF_METHOD,
    KEY_SD_STRESS_STEEL,
    KEY_SD_STRESS_STEEL_ALLOWABLE,
    KEY_SD_TOP_FLANGE_THICKNESS,
    KEY_SD_TOP_FLANGE_WIDTH,
    KEY_SD_TOTAL_DEPTH,
    KEY_SD_ULS_PER_GIRDER,
    KEY_SD_WEB_CLASS_LIMIT,
    KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_THICKNESS,
    KEY_SPAN,
    KEY_UTIL_FLEXURE,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LTB,
    KEY_UTIL_SHEAR,
)

from osdagbridge.core.reports.report_utils import _render_value, _tex


def _expand_page_breakable_groups(table_rows: str) -> str:
    """Replace ``multirow`` groups with ordinary, self-identifying rows.

    A ``longtable`` can break between any two rows but a ``multirow`` cell
    cannot span that break.  Repeating the girder label keeps every continued
    row readable and prevents detached labels on the following page.
    """
    group_start = re.compile(
        r"\\multirow\{\d+\}\{\*\}\{\\makecell\{(?P<label>[^{}]+)\}\}\s*&"
    )
    expanded = []
    position = 0
    while match := group_start.search(table_rows, position):
        expanded.append(table_rows[position:match.start()])
        group_end = table_rows.find(r"\hline", match.end())
        if group_end < 0:
            group_end = len(table_rows)
        label = match.group("label")
        group = label + " &" + table_rows[match.end():group_end]
        group = re.sub(r"(?m)^\s*&", label + " &", group)
        group = re.sub(r"\\cline\{2-(\d+)\}", r"\\cline{1-\1}", group)
        expanded.append(group)
        position = group_end
    expanded.append(table_rows[position:])
    return "".join(expanded)


def _build_girder_tables(bridge, girder_entries):
    """Build all plate-girder table content strings (t51 – g_summary).

    Returns a dict whose keys match the variable names used in the LaTeX
    return block of ch5_design_checks().
    """
    # ──────────────────────────────────────────────────────────────────
    # Shared micro-helpers
    # ──────────────────────────────────────────────────────────────────
    def _interaction_status(ratio):
        if ratio < 0.90:
            return "PASS"
        elif ratio < 1.00:
            return "WARN"
        return r"\textcolor{red}{FAIL}"

    def _dfmt(v, nd=2):
        try:
            return f"{float(v):.{nd}f}"
        except (TypeError, ValueError):
            return ""

    def _mpa(v):
        s = _dfmt(v, nd=2)
        return (s + " MPa") if s else ""

    def _stress_status(actual, allow):
        try:
            return "PASS" if float(actual) <= float(allow) else r"\textcolor{red}{FAIL}"
        except (TypeError, ValueError):
            return "---"

    def _ge_status(provided, required):
        try:
            return "PASS" if float(provided) >= float(required) else r"\textcolor{red}{FAIL}"
        except (TypeError, ValueError):
            return "---"

    def _fat_status(s):
        if s is None or str(s).strip() == "":
            return "---"
        return r"\textcolor{red}{" + str(s) + "}" if "FAIL" in str(s).upper() else str(s)

    def _with_unit(value, unit):
        s = _dfmt(value, nd=2)
        if not s:
            return ""
        u = (unit or "").strip()
        return (s + " " + u) if u else s

    def _defl_status(actual, allowable):
        try:
            return "PASS" if float(actual) <= float(allowable) else r"\textcolor{red}{FAIL}"
        except (TypeError, ValueError):
            return "---"

    # ──────────────────────────────────────────────────────────────────
    # Table 5.1 — Girder Section Properties
    # ──────────────────────────────────────────────────────────────────
    t51_rows = []
    for lbl, _ in girder_entries:
        t51_rows.append(
            r"\multirow{13}{*}{\makecell{" + lbl + r"}} & \textnormal{Depth, D (mm)} & "
            + _render_value(bridge.output_dict, KEY_SD_TOTAL_DEPTH) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Top Flange Width, $b_f$ (mm)} & "
            + _render_value(bridge.output_dict, KEY_SD_TOP_FLANGE_WIDTH) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Bottom Flange Width, $b_f$ (mm)} & "
            + _render_value(bridge.output_dict, KEY_SD_BOTTOM_FLANGE_WIDTH) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Top Flange Thickness, $t_f$ (mm)} & "
            + _render_value(bridge.output_dict, KEY_SD_TOP_FLANGE_THICKNESS) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Bottom Flange Thickness, $t_f$ (mm)} & "
            + _render_value(bridge.output_dict, KEY_SD_BOTTOM_FLANGE_THICKNESS) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Web Thickness, $t_w$ (mm)} & "
            + _render_value(bridge.output_dict, KEY_SD_WEB_THICKNESS) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Gross Area, A (cm$^2$)} & "
            + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_AREA) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Moment of Inertia, $I_z$ (cm$^4$)} & "
            + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_IZ) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Elastic Section Modulus, $Z_{ez}$ (cm$^3$)} & "
            + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_ZZ) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Plastic Section Modulus, $Z_{pz}$ (cm$^3$)} & "
            + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_ZUZ) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Effective Slab Width, $b_{eff}$ (mm)} & "
            + _render_value(bridge.output_dict, KEY_SD_EFFECTIVE_SLAB_WIDTH) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Transformed Composite $I_z$ (cm$^4$)} & "
            + _render_value(bridge.output_dict, KEY_SD_COMPOSITE_IZ) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Depth to Plastic Neutral Axis (mm)} & "
            + _render_value(bridge.output_dict, KEY_SD_PNA_DEPTH) + r" \\[6pt]" + "\n"
            r"\hline"
        )
    t51_content = "\n".join(t51_rows)

    # ──────────────────────────────────────────────────────────────────
    # Table 5.2 — Section Classification
    # ──────────────────────────────────────────────────────────────────
    t52_rows = []
    for lbl, _ in girder_entries:
        t52_rows.append(
            r"\multirow{3}{*}{\makecell{" + lbl + r"}} & Top Flange & "
            + _render_value(bridge.output_dict, KEY_SD_FLANGE_SLENDERNESS)
            + r" & " + _render_value(bridge.output_dict, KEY_SD_FLANGE_CLASS_LIMIT)
            + r" & " + _render_value(bridge.output_dict, KEY_SD_CLASS_FLANGE) + r" \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Web & " + _render_value(bridge.output_dict, KEY_SD_WEB_SLENDERNESS)
            + r" & " + _render_value(bridge.output_dict, KEY_SD_WEB_CLASS_LIMIT)
            + r" & " + _render_value(bridge.output_dict, KEY_SD_CLASS_WEB) + r" \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Overall Section & --- & --- & "
            + _render_value(bridge.output_dict, KEY_SD_SECTION_CLASS) + r" \\[6pt]" + "\n"
            r"\hline"
        )
    t52_content = "\n".join(t52_rows)

    # ──────────────────────────────────────────────────────────────────
    # Table 5.3 — Moment Capacity Check
    # ──────────────────────────────────────────────────────────────────
    try:
        _flex_ur = float(bridge.output_dict.get(KEY_UTIL_FLEXURE)) / 100.0
        _flex_ur_str = f"{_flex_ur:.2f}"
        _flex_status = "PASS" if _flex_ur <= 1.0 else r"\textcolor{red}{FAIL}"
    except (TypeError, ValueError):
        _flex_ur_str = ""
        _flex_status = "---"
    t53_rows = []
    for lbl, _ in girder_entries:
        t53_rows.append(
            r"\multirow{3}{*}{\makecell{" + lbl + r"}} & Applied Moment, $M_u$ & Governing LC (ULS) & "
            + _render_value(bridge.output_dict, KEY_SD_MU_APPLIED, " kN-m") + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Design Moment Capacity, $M_d$ & IRC 22 Cl. 603.3.1 & "
            + _render_value(bridge.output_dict, KEY_SD_MD_CAPACITY, " kN-m") + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Utilization Ratio, $M_u / M_d$ & $M_u / M_d$ & "
            + _flex_ur_str + r" & " + _flex_status + r" \\[6pt]" + "\n"
            r"\hline"
        )
    t53_content = "\n".join(t53_rows)

    # ──────────────────────────────────────────────────────────────────
    # Table 5.4 — Shear Capacity Check
    # ──────────────────────────────────────────────────────────────────
    try:
        _shear_ur = float(bridge.output_dict.get(KEY_UTIL_SHEAR)) / 100.0
        _shear_ur_str = f"{_shear_ur:.2f}"
        _shear_status = "PASS" if _shear_ur <= 1.0 else r"\textcolor{red}{FAIL}"
    except (TypeError, ValueError):
        _shear_ur_str = ""
        _shear_status = "---"
    t54_rows = []
    for lbl, _ in girder_entries:
        t54_rows.append(
            r"\multirow{8}{*}{\makecell{" + lbl + r"}} & Applied Shear, $V_u$ & Governing LC (ULS) & "
            + _render_value(bridge.output_dict, KEY_SD_SHEAR_VU, " kN") + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Shear Area, $A_v$ & $d_w \times t_w$ & "
            + _render_value(bridge.output_dict, KEY_SD_SHEAR_AV, " mm$^2$") + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Panel Aspect Ratio, c/d & --- & "
            + _render_value(bridge.output_dict, KEY_SD_PANEL_CD) + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Shear Buckling Coefficient, $k_v$ & IS 800 Cl. 8.4.2.2 & "
            + _render_value(bridge.output_dict, KEY_SD_SHEAR_KV) + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Web Slenderness, $\lambda_w$ & $\sqrt{f_{yw}/(\sqrt{3}\,\tau_{cr})}$ & "
            + _render_value(bridge.output_dict, KEY_SD_SHEAR_LAMBDA_W) + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Design Shear Stress, $\tau_b$ & IRC 22 Cl. 603.3.3.2 & "
            + _render_value(bridge.output_dict, KEY_SD_SHEAR_TAU_B, " MPa") + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Shear Buckling Resistance, $V_{cr}$ & $A_v \times \tau_b$ & "
            + _render_value(bridge.output_dict, KEY_SD_SHEAR_VCR, " kN") + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Utilization Ratio, $V_u / V_d$ & $V_u / V_d$ & "
            + _shear_ur_str + r" & " + _shear_status + r" \\[6pt]" + "\n"
            r"\hline"
        )
    t54_content = "\n".join(t54_rows)

    # ──────────────────────────────────────────────────────────────────
    # Table 5.5 — Interaction Checks
    # ──────────────────────────────────────────────────────────────────
    try:
        _mv_ur = float(bridge.output_dict.get(KEY_UTIL_INTERACTION)) / 100.0
        _mv_ur_str = f"{_mv_ur:.2f}"
        _mv_status = _interaction_status(_mv_ur)
    except (TypeError, ValueError):
        _mv_ur_str = ""
        _mv_status = "---"
    _mn_r  = bridge.output_dict.get(KEY_SD_MN_RATIO)
    _mn_ax = bridge.output_dict.get(KEY_SD_MN_AXIAL)
    _mn_mo = bridge.output_dict.get(KEY_SD_MN_MOMENT)
    if _mn_r is None or _mn_ax is None or _mn_mo is None:
        _mn_cond = _mn_val = _mn_status = "N/A"
    else:
        _mn_cond   = f"{_mn_ax:.2f} + {_mn_mo:.2f} = {_mn_r:.3f}"
        _mn_val    = f"{_mn_r:.3f}"
        _mn_status = _interaction_status(_mn_r)
    t55_rows = []
    for lbl, _ in girder_entries:
        t55_rows.append(
            r"\multirow{4}{*}{\makecell{" + lbl + r"}} & High Shear Condition? & $V_u > 0.6\,V_d$ & "
            + _render_value(bridge.output_dict, KEY_SD_HIGH_SHEAR) + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Reduced Moment Capacity, $M_{dv}$ & IRC 22 Cl. 603.3.3.3 & "
            + _render_value(bridge.output_dict, KEY_SD_MDV, " kN-m") + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Interaction Check: $M_u \leq M_{dv}$ & --- & "
            + _mv_ur_str + r" & " + _mv_status + r" \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Interaction Check: $N_u/N_{Rd} + M_u/M_{dv} \leq 1.0$ & "
            + _mn_cond + r" & " + _mn_val + r" & " + _mn_status + r" \\[6pt]" + "\n"
            r"\hline"
        )
    t55_content = "\n".join(t55_rows)

    # ──────────────────────────────────────────────────────────────────
    # Table 5.6 — LTB Check
    # ──────────────────────────────────────────────────────────────────
    try:
        _ltb_ur = float(bridge.output_dict.get(KEY_UTIL_LTB)) / 100.0
        _ltb_ur_str = f"{_ltb_ur:.2f}"
        _ltb_status = _interaction_status(_ltb_ur)
    except (TypeError, ValueError):
        _ltb_ur_str = ""
        _ltb_status = "---"
    t56_rows = []
    for lbl, _ in girder_entries:
        t56_rows.append(
            r"\multirow{5}{*}{\makecell{" + lbl + r"}} & Elastic Critical Moment, $M_{cr}$ & IRC 22 Cl. 603.3.3.1 & "
            + _render_value(bridge.output_dict, KEY_SD_LTB_MCR, " kN-m") + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Non-dim. Slenderness, $\bar{\lambda}_{LT}$ & $\sqrt{M_p / M_{cr}}$ & "
            + _render_value(bridge.output_dict, KEY_SD_LTB_LAMBDA) + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & LTB Reduction Factor, $\chi_{LT}$ & IS 800 Cl. 8.2.2 & "
            + _render_value(bridge.output_dict, KEY_SD_LTB_CHI) + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & LTB Resistance, $M_b$ & $\chi_{LT}\,M_p / \gamma_{m0}$ & "
            + _render_value(bridge.output_dict, KEY_SD_LTB_MB, " kN-m") + r" & --- \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & $M_u \leq M_b$ & $M_u / M_b$ & "
            + _ltb_ur_str + r" & " + _ltb_status + r" \\[6pt]" + "\n"
            r"\hline"
        )
    t56_content = "\n".join(t56_rows)

    # ──────────────────────────────────────────────────────────────────
    # Table 5.7 — Stiffener Design Summary
    # ──────────────────────────────────────────────────────────────────
    t57_rows = []
    for lbl, _ in girder_entries:
        t57_rows.append(
            r"\multirow{6}{*}{\makecell{" + lbl + r"}} & \textnormal{Shear Buckling Design Method} & "
            + _render_value(bridge.output_dict, KEY_SD_STIFF_METHOD) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Intermediate Stiffener Thickness (mm)} & "
            + _render_value(bridge.output_dict, KEY_SD_STIFF_INT_THICK) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Intermediate Stiffener Spacing (mm)} & "
            + _render_value(bridge.output_dict, KEY_SD_STIFF_INT_SPACING) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{End Panel Stiffener Thickness (mm)} & "
            + _render_value(bridge.output_dict, KEY_SD_STIFF_END_THICK) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{No. of End Panel Stiffeners} & "
            + _render_value(bridge.output_dict, KEY_SD_STIFF_END_COUNT) + r" \\[6pt]" + "\n"
            r"\cline{2-3}" + "\n"
            r" & \textnormal{Longitudinal Stiffeners} & "
            + _render_value(bridge.output_dict, KEY_SD_STIFF_LONG) + r" \\[6pt]" + "\n"
            r"\hline"
        )
    t57_content = "\n".join(t57_rows)

    # ──────────────────────────────────────────────────────────────────
    # Table 5.8 — Intermediate Stiffener Checks (custom mode only)
    # ──────────────────────────────────────────────────────────────────
    _iys_status = _ge_status(bridge.output_dict.get(KEY_SD_IS_IYS_PROV),
                             bridge.output_dict.get(KEY_SD_IS_IYS_MIN))
    _fqd_status = _ge_status(bridge.output_dict.get(KEY_SD_IS_FQD),
                             bridge.output_dict.get(KEY_SD_IS_FQ))
    t58_rows = []
    for lbl, _ in girder_entries:
        t58_rows.append(
            r"\multirow{2}{*}{\makecell{" + lbl + r"}} & Min. Moment of Inertia, $I_s$ & "
            + _render_value(bridge.output_dict, KEY_SD_IS_IYS_MIN, " mm$^4$") + r" & "
            + _render_value(bridge.output_dict, KEY_SD_IS_IYS_PROV, " mm$^4$") + r" & "
            + _iys_status + r" \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Buckling Resistance, $F_{qd} \geq F_q$ & "
            + _render_value(bridge.output_dict, KEY_SD_IS_FQ, " kN") + r" & "
            + _render_value(bridge.output_dict, KEY_SD_IS_FQD, " kN") + r" & "
            + _fqd_status + r" \\[6pt]" + "\n"
            r"\hline"
        )
    t58_content = "\n".join(t58_rows)

    _is_custom = str(bridge.input_dict.get(KEY_DESIGN_MODE, "Optimized")).strip().lower() in {"custom", "customized"}
    if _is_custom:
        t58_block = (
            r"\vspace{1em}" + "\n\n"
            r"\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}" + "\n"
            r"\caption{Intermediate Stiffener Checks}\\" + "\n"
            r"\hline" + "\n"
            r"\textbf{} & \textbf{Check} & \textbf{Required} & \textbf{Provided} & \textbf{Status} \\[6pt]" + "\n"
            r"\hline" + "\n"
            r"\endfirsthead" + "\n\n"
            r"\hline" + "\n\n"
            r"\textbf{} & \textbf{Check} & \textbf{Required} & \textbf{Provided} & \textbf{Status} \\[6pt]" + "\n\n"
            r"\hline" + "\n\n"
            r"\endhead" + "\n"
            + _expand_page_breakable_groups(t58_content) + "\n"
            r"\end{longtable}" + "\n"
            r"\noindent\textit{Note: IS 800 Cl. 8.7.1.2}" + "\n"
        )
    else:
        t58_block = ""

    # ──────────────────────────────────────────────────────────────────
    # Table 5.9 — Bearing Stiffener Checks
    # ──────────────────────────────────────────────────────────────────
    _bs_r = bridge.output_dict.get(KEY_SD_BS_R)

    def _bs_check(resist_key):
        prov = bridge.output_dict.get(resist_key)
        if prov is None or float(prov) <= 0.0 or _bs_r is None:
            return ("N/A", "N/A", "N/A")
        req_s  = f"{_bs_r} kN"
        prov_s = f"{prov} kN"
        status = "PASS" if float(prov) >= float(_bs_r) else r"\textcolor{red}{FAIL}"
        return (req_s, prov_s, status)

    _wb_req, _wb_prov, _wb_st = _bs_check(KEY_SD_BS_FCDW_WB)
    _lc_req, _lc_prov, _lc_st = _bs_check(KEY_SD_BS_FCDW_LC)
    _ps_req, _ps_prov, _ps_st = _bs_check(KEY_SD_BS_FPSD)
    _cb_req, _cb_prov, _cb_st = _bs_check(KEY_SD_BS_FCD)
    t59_rows = []
    for lbl, _ in girder_entries:
        t59_rows.append(
            r"\multirow{4}{*}{\makecell{" + lbl + r"}} & Web Buckling Resistance & "
            + _wb_req + r" & " + _wb_prov + r" & " + _wb_st + r" \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Local Crushing Resistance & "
            + _lc_req + r" & " + _lc_prov + r" & " + _lc_st + r" \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Bearing Capacity & "
            + _ps_req + r" & " + _ps_prov + r" & " + _ps_st + r" \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Column Buckling Resistance & "
            + _cb_req + r" & " + _cb_prov + r" & " + _cb_st + r" \\[6pt]" + "\n"
            r"\hline"
        )
    t59_content = "\n".join(t59_rows)

    # ──────────────────────────────────────────────────────────────────
    # Table 5.10 — Deflection Checks
    # ──────────────────────────────────────────────────────────────────
    try:
        _span_m = float(bridge.input_dict.get(KEY_SPAN))
        _allow_live_mm  = _span_m * 1000.0 / 800.0
        _allow_total_mm = _span_m * 1000.0 / 600.0
    except (TypeError, ValueError):
        _allow_live_mm = _allow_total_mm = None
    _allow_live_str  = (f"L/800 = {_allow_live_mm:.1f} mm")  if _allow_live_mm  is not None else ""
    _allow_total_str = (f"L/600 = {_allow_total_mm:.1f} mm") if _allow_total_mm is not None else ""

    t510_rows = []
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        _live_mm  = bridge.output_dict.get(f"{KEY_SD_DEFL_LIVE}.G{_gi}")
        _total_mm = bridge.output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")
        t510_rows.append(
            r"\multirow{2}{*}{\makecell{" + lbl + r"}} & Live Load Deflection, $\delta_{LL}$ (mm) & "
            + _allow_live_str + r" & "
            + _dfmt(_live_mm,  nd=3) + r" & "
            + _defl_status(_live_mm,  _allow_live_mm) + r" \\[6pt]" + "\n"
            r"\cline{2-5}" + "\n"
            r" & Total Load Deflection, $\delta_{total}$ (mm) & "
            + _allow_total_str + r" & "
            + _dfmt(_total_mm, nd=3) + r" & "
            + _defl_status(_total_mm, _allow_total_mm) + r" \\[6pt]" + "\n"
            r"\hline"
        )
    t510_content = "\n".join(t510_rows)

    # ──────────────────────────────────────────────────────────────────
    # Table 5.11 — SLS Steel Stress
    # ──────────────────────────────────────────────────────────────────
    _dr_511        = bridge.output_dict.get("design_results", {}) or {}
    _steel_sigma   = _dr_511.get(KEY_SD_STRESS_STEEL)
    _steel_allow   = _dr_511.get(KEY_SD_STRESS_STEEL_ALLOWABLE)
    _steel_sig_str = _mpa(_steel_sigma)
    _steel_alw_str = _mpa(_steel_allow)
    _steel_status  = _stress_status(_steel_sigma, _steel_allow)

    t511_rows = []
    for lbl, _ in girder_entries:
        t511_rows.append(
            r"\makecell{" + lbl + r"} & Structural Steel ($0.9\,f_y$) & "
            + _steel_alw_str + r" & "
            + _steel_sig_str + r" & "
            + _steel_status + r" \\[6pt]" + "\n"
            r"\hline"
        )
    t511_content = "\n".join(t511_rows)

    # ──────────────────────────────────────────────────────────────────
    # Table 5.12 — Fatigue Assessment
    # ──────────────────────────────────────────────────────────────────
    _fat_cat = ((bridge.output_dict.get("design_results", {}) or {})
                .get(KEY_SD_ULS_PER_GIRDER, {}) or {}).get("fatigue", {}) or {}

    t512_rows = []
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        _g = _fat_cat.get(f"G{_gi}", {}) or {}
        t512_rows.append(
            r"\makecell{" + lbl + r"} & "
            + _mpa(_g.get("demand")) + r" & "
            + _mpa(_g.get("capacity")) + r" & "
            + _dfmt(_g.get("ur"), nd=2) + r" & "
            + _fat_status(_g.get("status")) + r" \\[6pt]" + "\n"
            r"\hline"
        )
    t512_content = "\n".join(t512_rows)

    # ──────────────────────────────────────────────────────────────────
    # Table 5.13 — Girder Design Summary (DCR / controlling check)
    # ──────────────────────────────────────────────────────────────────
    _pg_summary = (bridge.output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}

    g_summary_rows = []
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        g_data = _pg_summary.get(f"G{_gi}", {}) or {}
        checks = g_data.get("checks") or []
        if not checks:
            g_summary_rows.append(lbl + r" &  &  &  &  &  &  \\[6pt]" + "\n" + r"\hline")
            continue

        ctrl = max(checks, key=lambda c: c.get("dcr") or 0.0)

        ctrl_lc, best_dcr = None, None
        for lc_name, lc_data in (g_data.get("per_lc") or {}).items():
            if str(lc_name).lower().startswith("envelope"):
                continue
            for chk in lc_data.get("checks") or []:
                if chk.get("id") == ctrl.get("check_id"):
                    d = chk.get("dcr") or 0.0
                    if best_dcr is None or d > best_dcr:
                        best_dcr, ctrl_lc = d, lc_name
        if ctrl_lc is None:
            ctrl_lc = (g_data.get("demand") or {}).get("governing_combination") or ""

        g_summary_rows.append(
            lbl + r" & " + _tex(str(ctrl_lc)) + r" & " + _tex(str(ctrl.get("name", "")))
            + r" & " + _with_unit(ctrl.get("demand"),   ctrl.get("demand_unit"))
            + r" & " + _with_unit(ctrl.get("capacity"), ctrl.get("capacity_unit"))
            + r" & " + _dfmt(ctrl.get("dcr"), nd=3)
            + r" & " + _fat_status(ctrl.get("status")) + r" \\[6pt]" + "\n"
            r"\hline"
        )
    g_summary_table_content = "\n".join(g_summary_rows)

    # All Chapter 5 girder tables are longtables: do not return a page-spanning
    # \multirow cell in any of them.
    t51_content = _expand_page_breakable_groups(t51_content)
    t52_content = _expand_page_breakable_groups(t52_content)
    t53_content = _expand_page_breakable_groups(t53_content)
    t54_content = _expand_page_breakable_groups(t54_content)
    t55_content = _expand_page_breakable_groups(t55_content)
    t56_content = _expand_page_breakable_groups(t56_content)
    t57_content = _expand_page_breakable_groups(t57_content)
    t58_content = _expand_page_breakable_groups(t58_content)
    t59_content = _expand_page_breakable_groups(t59_content)
    t510_content = _expand_page_breakable_groups(t510_content)

    return {
        "t51_content":             t51_content,
        "t52_content":             t52_content,
        "t53_content":             t53_content,
        "t54_content":             t54_content,
        "t55_content":             t55_content,
        "t56_content":             t56_content,
        "t57_content":             t57_content,
        "t58_content":             t58_content,
        "t58_block":               t58_block,
        "t59_content":             t59_content,
        "t510_content":            t510_content,
        "t511_content":            t511_content,
        "t512_content":            t512_content,
        "g_summary_table_content": g_summary_table_content,
    }
