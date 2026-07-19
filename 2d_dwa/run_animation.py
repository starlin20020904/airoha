"""Animated GIF of the 2-D DWA selection process (Chinese labels).

anim_2d_dwa.gif - plays the paper's Fig. 1 input sequence
{3, 9, 15, 27, 13, 12, 34, 20, 13} sample by sample: red = elements
selected this sample, gray shading = how many times each element has
been used so far. The side panel shows the decoder signals.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.animation import PillowWriter

from dwa_core import dwa_2d_masks
import plot_style as ps

ps.apply_style()
ps.use_chinese()
FIGDIR = "figures"

SEQ = [3, 9, 15, 27, 13, 12, 34, 20, 13]
GRAY = ["white", "#e0dfdb", "#bdbcb6", "#98978f"]   # usage count 0..3


def draw_frame(ax_grid, ax_txt, n, masks, sig, used_before):
    ax_grid.clear()
    ax_txt.clear()
    for a in (ax_grid, ax_txt):
        a.axis("off")

    if n < 0:                       # intro frame
        mask = np.zeros((8, 8), dtype=int)
        used = np.zeros((8, 8), dtype=int)
    else:
        mask = masks[n]
        used = used_before[n]

    for j in range(8):
        for i in range(8):
            fc = ps.C_SELECTED if mask[j, i] else GRAY[min(used[j, i], 3)]
            ax_grid.add_patch(Rectangle((i, j), 1, 1, facecolor=fc,
                                        edgecolor=ps.TEXT_SECONDARY, lw=0.6))
    ax_grid.set_xlim(-0.7, 8.3)
    ax_grid.set_ylim(-1.2, 9.6)
    ax_grid.set_aspect("equal")
    ax_grid.text(-0.35, 0.5, "j=0", ha="right", va="center", fontsize=9,
                 color=ps.TEXT_SECONDARY)
    ax_grid.text(-0.35, 7.5, "j=7", ha="right", va="center", fontsize=9,
                 color=ps.TEXT_SECONDARY)
    ax_grid.text(0.5, -0.65, "i=0", ha="center", fontsize=9,
                 color=ps.TEXT_SECONDARY)
    ax_grid.text(7.5, -0.65, "i=7", ha="center", fontsize=9,
                 color=ps.TEXT_SECONDARY)

    if n < 0:
        ax_grid.set_title("初始狀態:指標在 (i=0, j=0)", fontsize=13)
        ax_txt.text(0, 0.92, "2-D DWA 元件選擇動畫\n\n"
                    "輸入序列(論文 Fig. 1):\n{3, 9, 15, 27, 13, 12, 34, 20, 13}\n\n"
                    "紅色 = 本次取樣選取的元件\n"
                    "灰階 = 該元件累計被用過幾次\n\n"
                    "觀察重點:選取區塊沿著列的方向\n"
                    "一圈一圈旋轉,每個元件被使用的\n"
                    "次數保持均勻 → 一階失配整形",
                    fontsize=11.5, va="top", ha="left")
        return

    s = sig[n]
    # arrow marking where this sample's selection starts
    ax_grid.annotate("起點 (hd)", xy=(s["hd"] + 0.5, s["rows"][0] + 1),
                     xytext=(s["hd"] + 0.5, 9.25), ha="center", fontsize=10,
                     color=ps.C_2DDWA,
                     arrowprops=dict(arrowstyle="->", color=ps.C_2DDWA,
                                     lw=1.6))
    ax_grid.set_title(f"取樣 {n + 1} / {len(SEQ)}", fontsize=13)

    wrapped = any(s["rows"][k + 1] < s["rows"][k]
                  for k in range(len(s["rows"]) - 1))
    lines = [
        f"輸入  d = {SEQ[n]}",
        f"拆位:MSB = {s['msb']}(整列)、LSB = {s['lsb']}(零頭)",
        "",
        f"nfull = {s['nfull']}"
        + ("(上次的末列只用一半 → 續用)" if s["nfull"] else ""),
        f"carry = {s['carry']}"
        + ("(半列被填滿、溢出 → 多選一列)" if s["carry"] else ""),
        "",
        f"選取列數 = MSB + carry + nfull = {s['nrows']}",
        f"首列從行 hd = {s['hd']} 開始,末列到行 tl = {s['tl']} 為止",
    ]
    if wrapped:
        lines += ["", "★ 指標繞回最下列 — 完成一輪旋轉!"]
    ax_txt.text(0, 0.92, "\n".join(lines), fontsize=11.5, va="top",
                ha="left", linespacing=1.55)


def main():
    masks, sig = dwa_2d_masks(SEQ, nbits=6, return_signals=True)
    masks = masks.reshape(-1, 8, 8)
    used_before = (masks.cumsum(axis=0) - masks)

    fig, (ax_grid, ax_txt) = plt.subplots(
        1, 2, figsize=(9.6, 5.2), width_ratios=[1, 1.15])
    fig.subplots_adjust(left=0.04, right=0.99, top=0.9, bottom=0.03)

    writer = PillowWriter(fps=1)
    with writer.saving(fig, f"{FIGDIR}/anim_2d_dwa.gif", dpi=100):
        draw_frame(ax_grid, ax_txt, -1, masks, sig, used_before)
        writer.grab_frame()
        writer.grab_frame()          # hold intro for 2 s
        for n in range(len(SEQ)):
            draw_frame(ax_grid, ax_txt, n, masks, sig, used_before)
            writer.grab_frame()
            writer.grab_frame()      # hold each sample for 2 s
    plt.close(fig)
    print("animation written to", f"{FIGDIR}/anim_2d_dwa.gif")


if __name__ == "__main__":
    main()
