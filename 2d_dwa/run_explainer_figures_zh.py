"""Chinese (Traditional) versions of the explainer figures.

fig5_architecture_flow_zh.png - 訊號流程圖(為什麼拆成列/行解碼器)
fig6_worked_example_zh.png    - {8, 9, 4, 18} 逐步範例(對應論文 Fig. 5)

注:row = 列(橫)、column = 行(直),與論文座標一致(j 為列、i 為行)。
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

from dwa_core import dwa_2d_masks
import plot_style as ps

ps.apply_style()
ps.use_chinese()
FIGDIR = "figures"

BOX_KW = dict(boxstyle="round,pad=0.35", linewidth=1.2)


def box(ax, x, y, text, fc="white", ec=ps.TEXT_SECONDARY, fontsize=9.5,
        color=ps.TEXT_PRIMARY):
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
            color=color, bbox=dict(facecolor=fc, edgecolor=ec, **BOX_KW),
            zorder=3)


def arrow(ax, xy_from, xy_to, label=None, color=None, lx=0, ly=0,
          fontsize=8.5):
    color = color or ps.TEXT_SECONDARY
    ax.add_patch(FancyArrowPatch(xy_from, xy_to, arrowstyle="-|>",
                                 mutation_scale=14, color=color,
                                 lw=1.4, zorder=2))
    if label:
        mx = (xy_from[0] + xy_to[0]) / 2 + lx
        my = (xy_from[1] + xy_to[1]) / 2 + ly
        ax.text(mx, my, label, fontsize=fontsize, ha="center",
                va="center", color=color,
                bbox=dict(facecolor=ps.SURFACE, edgecolor="none", pad=1))


# ---------------------------------------------------------------------------
# 圖 5(中文):架構訊號流程
# ---------------------------------------------------------------------------

def fig_architecture_zh():
    fig, ax = plt.subplots(figsize=(11, 8.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    box(ax, 5, 9.45,
        "DAC 輸入  d[5:0]     (例:d = 13 = 001 101$_2$ = 15$_8$)\n"
        "任務:從指標 P 開始,選出接下來連續的 13 個元件(可繞回)",
        fc="#fdf3ee", ec=ps.C_2DDWA, fontsize=10)

    box(ax, 2.35, 7.9,
        "MSB  d[5:3] = 001$_2$ = 1\n(代表幾個「整列」,一列 8 個)", fontsize=9)
    box(ax, 7.65, 7.9,
        "LSB  d[2:0] = 101$_2$ = 5\n(代表不足一列的零頭元件數)", fontsize=9)
    arrow(ax, (4.35, 9.1), (2.6, 8.35))
    arrow(ax, (5.65, 9.1), (7.4, 8.35))

    box(ax, 7.65, 6.1,
        "行(column)解碼器(先動作,時脈 clk2e)\n"
        "3-bit DWA:hd ← hd + LSB (mod 8)\n"
        "nfull:上一次的最後一列是否只用了一半?\n"
        "carry:這次的 LSB 是否把那半列填滿、\n"
        "又溢出到新的一列?",
        fc="#eef4fc", ec=ps.C_SEGMENTED)
    box(ax, 2.35, 6.1,
        "列(row)解碼器(時脈 clk2)\n"
        "選取列數 = MSB + carry + nfull\n"
        "3-bit DWA 旋轉列指標",
        fc="#eef4fc", ec=ps.C_SEGMENTED)
    arrow(ax, (2.35, 7.55), (2.35, 6.75))
    arrow(ax, (7.65, 7.55), (7.65, 7.05))
    arrow(ax, (5.75, 6.1), (4.05, 6.1), label="carry、nfull\n(八進位的「進位」)",
          color=ps.C_2DDWA, ly=0.45)

    box(ax, 2.35, 4.15,
        "列選擇邏輯\n"
        "$r_{first}$ / $r_{mid}$ / $r_{last}$ / $r_{one}$\n"
        "每一列一條訊號(共 8 條)")
    box(ax, 7.65, 4.15,
        "行選擇邏輯\n"
        "$c_{first}$ = (i ≥ hd)、$c_{last}$ = (i ≤ tl)、$c_{one}$\n"
        "每一行一條訊號(共 8 條)")
    arrow(ax, (2.35, 5.45), (2.35, 4.8))
    arrow(ax, (7.65, 5.15), (7.65, 4.8))

    box(ax, 5, 2.55,
        "每個單位電容 cell 只把自己的「列訊號」與「行訊號」做 AND:\n"
        "sel(i, j) = $r_{mid}$ + $r_{first}\\cdot c_{first}$ + "
        "$r_{last}\\cdot c_{last}$ + $r_{one}\\cdot c_{one}$",
        fc="#fdf3ee", ec=ps.C_2DDWA)
    arrow(ax, (2.35, 3.5), (3.7, 3.0))
    arrow(ax, (7.65, 3.5), (6.3, 3.0))

    box(ax, 5, 1.15,
        "8×8 單位元件 CDAC — 被選取的區域永遠是 row-major 順序下連續的一段:\n"
        "殘缺的首列 + 若干整列 + 殘缺的末列",
        fontsize=9)
    arrow(ax, (5, 2.0), (5, 1.7))

    ax.text(0.15, 0.02,
            "為什麼要拆?選連續 d 個元件其實就是指標加法 P ← (P + d) mod 64。"
            "把 P 寫成八進位兩位數(列, 行),一個 64 路的旋轉就變成兩個 8 路"
            "旋轉加一個進位——和直式加法一模一樣。\n"
            "1-D DWA 需要 $2^N$ 路旋轉移位器與 $2^N$ 條控制線(8-bit 時 256 條);"
            "2-D 只需兩個 $2^{N/2}$ 路 DWA 與 $7\\cdot2^{N/2}$ 條行列共享訊號線"
            "(電晶體數省 46%,論文 Table 1)。",
            fontsize=9, color=ps.TEXT_SECONDARY, va="bottom")

    ax.set_title("2-D DWA 訊號流程 — 一個 64 元件的旋轉,拆成「八進位兩位數」的加法",
                 fontsize=13, pad=14)
    fig.savefig(f"{FIGDIR}/fig5_architecture_flow_zh.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 圖 6(中文):逐步範例
# ---------------------------------------------------------------------------

SEQ = [8, 9, 4, 18]
STORY = [
    "LSB = 0,行指標不動。\n恰好用掉 MSB = 1 個整列。\n列數 = 1 + 0 + 0 = 1",
    "第 1 列被填滿,還溢出\n1 個元件到第 2 列 ⇒ carry = 1。\n列數 = 1 + 1 + 0 = 2",
    "第 2 列上次只用了一半\n⇒ nfull = 1:繼續填它,\n4 個剛好裝下。列數 = 0 + 0 + 1 = 1",
    "一般情況:續用第 2 列 ($r_{first}$)、\n整列取第 3 列 ($r_{mid}$)、\n"
    "第 4 列取到一半 ($r_{last}$)。列數 = 2+0+1 = 3",
]
ROLE_ROWS = [None, None, None, {2: "$r_{first}$", 3: "$r_{mid}$",
                                4: "$r_{last}$"}]


def fig_worked_example_zh():
    masks, sig = dwa_2d_masks(SEQ, nbits=6, return_signals=True)
    masks = masks.reshape(-1, 8, 8)
    used_before = masks.cumsum(axis=0) - masks

    fig, axes = plt.subplots(1, 4, figsize=(13, 4.9))
    for n, ax in enumerate(axes):
        s = sig[n]
        for j in range(8):
            for i in range(8):
                if masks[n, j, i]:
                    fc = ps.C_SELECTED
                elif used_before[n, j, i]:
                    fc = "#dddcd8"
                else:
                    fc = "white"
                ax.add_patch(Rectangle((i, j), 1, 1, facecolor=fc,
                                       edgecolor=ps.TEXT_SECONDARY, lw=0.5))
        ax.annotate("起點 (hd)", xy=(s["hd"] + 0.5, s["rows"][0] + 1),
                    xytext=(s["hd"] + 0.5, 9.4), ha="center", fontsize=8.5,
                    color=ps.C_2DDWA,
                    arrowprops=dict(arrowstyle="->", color=ps.C_2DDWA))
        if ROLE_ROWS[n]:
            for j, role in ROLE_ROWS[n].items():
                ax.text(8.25, j + 0.5, role, fontsize=9, va="center",
                        color=ps.C_SEGMENTED)
        ax.set_xlim(-0.2, 9.4)
        ax.set_ylim(-3.6, 10.1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"取樣 {n + 1}:d = {SEQ[n]}(MSB {s['msb']}、"
                     f"LSB {s['lsb']})", fontsize=10.5)
        ax.text(4, -0.7,
                f"nfull = {s['nfull']}   carry = {s['carry']}   "
                f"列數 = {s['nrows']}",
                ha="center", fontsize=9.5, color=ps.TEXT_PRIMARY,
                fontweight="bold")
        ax.text(4, -1.3, STORY[n], ha="center", va="top", fontsize=8.8,
                color=ps.TEXT_SECONDARY)

    fig.suptitle("兩個解碼器如何合作 — 輸入序列 {8, 9, 4, 18}(論文 Fig. 5)\n"
                 "紅 = 本次取樣選取,灰 = 先前取樣已用;選取列數 = MSB + carry + nfull",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(f"{FIGDIR}/fig6_worked_example_zh.png")
    plt.close(fig)


if __name__ == "__main__":
    fig_architecture_zh()
    fig_worked_example_zh()
    print("Chinese explainer figures written to", FIGDIR)
