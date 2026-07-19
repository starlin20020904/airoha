# 2-D DWA — Python behavioral reproduction

Behavioral-level reproduction of the core ideas of:

> Y. Guo, J. Hu, Q. Li, X. Zhang, and Q. Xie, "A Novel 2-D
> Data-Weighted-Averaging Technique for Low-Power High-Resolution Zoom
> ADC," IEEE Access, vol. 14, pp. 102658–102667, 2026.

The 2-D DWA arranges an N-bit unit-element DAC as a 2^(N/2) × 2^(N/2)
array and selects elements rotationally, row by row. It is bit-exact
equivalent to a conventional 1-D DWA over all 2^N elements (first-order
mismatch shaping), but only needs two (N/2)-bit DWAs plus row/column
selection logic — and, unlike segmented approaches, it has **no
segmentation mismatch error**.

## Files

| File | Purpose |
|------|---------|
| `dwa_core.py` | Algorithms: 1-D DWA, 2-D DWA (row/column decoder model with `carry`/`nfull`/`hd`/`tl` signals per the paper's Figs. 6–11), segmented dual-DWA baseline, mismatched-DAC output, digital ΔΣ code generator, spectrum/SNDR/SFDR helpers |
| `test_dwa.py` | Verification (run `python3 test_dwa.py`) |
| `run_selection_figures.py` | Generates figures 1–3 |
| `run_spectrum_figures.py` | Generates figure 4 |
| `figures/` | Output PNGs |

## How to run

```bash
pip install -r requirements.txt
python3 test_dwa.py                 # 6 checks, all should pass
python3 run_selection_figures.py
python3 run_spectrum_figures.py
```

## Figures and what they show

| Figure | Reproduces | Message |
|--------|-----------|---------|
| `fig1_selection_pattern.png` | Paper Fig. 1 | The 8×8 selection pattern for input sequence {3, 9, 15, 27, 13, 12, 34, 20, 13}; matches the paper cell-for-cell |
| `fig2_usage_uniformity.png` | (concept) | Cumulative element usage: thermometer selection wears out the bottom rows; 2-D DWA uses every element equally (max−min ≤ 1) |
| `fig3_equivalence.png` | Section II-A + Table 1 | 2-D DWA is bit-exact identical to 1-D DWA over 20,000 random samples, while its control-signal count grows as 7·2^(N/2) instead of 2^N |
| `fig4_spectrum_comparison.png` | Paper Fig. 14 | Output and mismatch-error spectra under 0.5 % element / 1 % segmentation mismatch. 2-D DWA: SNDR ≈ 107 dB (paper: 107.5 dB), first-order-shaped error (+20 dB/dec); the segmented baseline is limited by unshaped segmentation error |

## Modeling notes and simplifications

- The DAC input codes for the spectrum figure come from a 2nd-order
  **digital** delta-sigma modulator (−3 dBFS sine, OSR 64). This mimics
  the noise-shaped code stream that the paper's zoom ADC feeds to its
  DAC, so the in-band floor is set by DAC mismatch, not quantization —
  the analog zoom ADC itself (coarse SAR + fine DSM) is not modeled.
- The "Segmented DWA" baseline runs an independent DWA in each sub-DAC
  but does **not** implement the MES/DSM segmentation-error shaping of
  [17]/[21]; it isolates what segmentation alone costs. The paper's
  hybrid methods land between this baseline and the 2-D DWA.
- Element mismatch is Gaussian (σ = 0.5 %), zero-meaned to remove the
  gain-error component; segmentation mismatch is a 1 % gain error on the
  LSB sub-DAC, per the paper's simulation conditions.
- 6-bit DAC (8×8) is used throughout, matching the paper's worked
  example; `dwa_2d_masks` accepts any even N.
