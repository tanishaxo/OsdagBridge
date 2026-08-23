# ── Column width presets ──────────────────────────────────
COL_LABEL   = "5.5cm"   # standard left-label column
COL_VALUE   = "10.0cm"  # standard right-value column
COL_NARROW  = "2.2cm"
COL_MEDIUM  = "3.5cm"
COL_WIDE    = "8.0cm"

# ── Document Settings ─────────────────────────────────────
PAGE_MARGIN = "0.75in"
DOC_LINE_SPACING = "1.15"

# ── Color ─────────────────────────────────────────────────
OSDAG_GREEN = "91B014"

# ── Table Layout & Spacing ────────────────────────────────
TABLE_COL_SEP = "6pt"
TABLE_ARRAY_STRETCH = "1.12"
TABLE_LT_PRE = "0pt"
TABLE_LT_POST = "6pt"
TABLE_RULE_WIDTH = "0.5pt"
TABLE_EXTRA_ROW_HEIGHT = "0.6pt"
ROW_EXTRA   = "\\\\[6pt]"  

SPEC_KV = f"|L{{{COL_LABEL}}}|p{{{COL_VALUE}}}|"

def lt_header(caption, col_spec, header_cells, ncols):

    return (
        rf"\begin{{longtable}}{{{col_spec}}}" + "\n"
        rf"\caption{{{caption}}}\\" + "\n"
        r"\hline" + "\n"
        + header_cells + "\n"
        r"\hline" + "\n"
        r"\endfirsthead" + "\n"
        rf"\multicolumn{{{ncols}}}{{l}}{{\textit{{...continued from previous page}}}}\\" + "\n"
        r"\hline" + "\n"
        + header_cells + "\n"
        r"\hline" + "\n"
        r"\endhead" + "\n"
        r"\hline" + "\n"
        rf"\multicolumn{{{ncols}}}{{r}}{{\textit{{Continued on next page...}}}}\\" + "\n"
        r"\endfoot" + "\n"
        r"\hline" + "\n"
        r"\endlastfoot" + "\n"
    )