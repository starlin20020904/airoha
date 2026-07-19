"""Shared matplotlib style for the 2-D DWA report figures (light theme)."""

import matplotlib as mpl

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e3e2df"

# Validated categorical order (dataviz palette, light mode):
C_NODEM = "#008300"      # green  - No DEM baseline
C_SEGMENTED = "#2a78d6"  # blue   - segmented DWA (prior art)
C_2DDWA = "#eb6834"      # orange - proposed 2-D DWA
C_SELECTED = "#d62d20"   # red, matching the paper's Fig. 1 convention


def use_chinese():
    """Register the system CJK font (WenQuanYi Zen Hei, supports
    Traditional Chinese) and make it the default text font."""
    from matplotlib import font_manager
    font_manager.fontManager.addfont(
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
    mpl.rcParams["font.family"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
    mpl.rcParams["axes.unicode_minus"] = False


def apply_style():
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.edgecolor": TEXT_SECONDARY,
        "axes.labelcolor": TEXT_PRIMARY,
        "axes.titlecolor": TEXT_PRIMARY,
        "xtick.color": TEXT_SECONDARY,
        "ytick.color": TEXT_SECONDARY,
        "text.color": TEXT_PRIMARY,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "font.size": 10,
        "axes.titlesize": 11,
        "figure.titlesize": 13,
        "lines.linewidth": 1.6,
        "legend.frameon": False,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
    })
