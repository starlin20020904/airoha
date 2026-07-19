"""Spectrum comparison figure (reproduces the conclusion of paper Fig. 14).

A -3 dBFS sine, re-quantized to 6 bits by a 2nd-order digital delta-sigma
modulator (mimicking the code stream of the paper's zoom ADC, so the
in-band quantization noise is far below the mismatch errors), drives
three DAC configurations built from the same unit elements:

  No DEM          - fixed thermometer selection: mismatch appears as
                    harmonic distortion in band.
  Segmented DWA   - MSB/LSB sub-DACs with their own DWAs (prior art):
                    intrinsic mismatch is shaped, but the segmentation
                    mismatch between sub-DACs is NOT shaped.
  2-D DWA         - proposed: first-order shaping of the whole 64-element
                    array, no segmentation error at all.

Conditions follow the paper: 0.5% element mismatch, 1% segmentation
mismatch, OSR = 64, spectra averaged over several mismatch realizations.
"""

import numpy as np
import matplotlib.pyplot as plt

from dwa_core import (dwa_2d_masks, thermometer_masks, segmented_dwa_masks,
                      unit_dac_output, segmented_dac_output,
                      power_spectrum, sndr_sfdr, dsm_quantized_sine)
import plot_style as ps

ps.apply_style()
FIGDIR = "figures"

NBITS = 6
NFFT = 2 ** 16
OSR = 64
SIG_BIN = 57                      # in-band, non-divisor of NFFT
BAND_BINS = NFFT // (2 * OSR)     # = 512
SIGMA_EE = 0.005                  # 0.5 % element mismatch
SIGMA_ES = 0.01                   # 1 % segmentation mismatch
N_AVG = 16                        # mismatch realizations averaged
FS_AMP = (2 ** NBITS - 1) / 2.0   # full-scale sine amplitude in LSBs


def averaged_spectra():
    rng = np.random.default_rng(2026)
    codes = dsm_quantized_sine(NFFT, -3.0, SIG_BIN, NBITS, rng)

    masks = {
        "No DEM": thermometer_masks(codes, 64),
        "2-D DWA": dwa_2d_masks(codes, NBITS),
    }
    seg_masks = segmented_dwa_masks(codes, NBITS)

    out_spec = {k: np.zeros(NFFT // 2 + 1) for k in
                ["No DEM", "Segmented DWA", "2-D DWA"]}
    err_spec = {k: np.zeros(NFFT // 2 + 1) for k in out_spec}

    for _ in range(N_AVG):
        for name, m in masks.items():
            actual, ideal = unit_dac_output(m, SIGMA_EE, rng)
            out_spec[name] += power_spectrum(actual / FS_AMP)
            err_spec[name] += power_spectrum((actual - ideal) / FS_AMP)
        actual, ideal = segmented_dac_output(*seg_masks, NBITS,
                                             SIGMA_EE, SIGMA_ES, rng)
        out_spec["Segmented DWA"] += power_spectrum(actual / FS_AMP)
        err_spec["Segmented DWA"] += power_spectrum((actual - ideal) / FS_AMP)

    for k in out_spec:
        out_spec[k] /= N_AVG
        err_spec[k] /= N_AVG
    return out_spec, err_spec


def main():
    out_spec, err_spec = averaged_spectra()
    freqs = np.arange(NFFT // 2 + 1) / NFFT      # cycles/sample
    band_edge = BAND_BINS / NFFT

    colors = {"No DEM": ps.C_NODEM,
              "Segmented DWA": ps.C_SEGMENTED,
              "2-D DWA": ps.C_2DDWA}

    metrics = {name: sndr_sfdr(spec, SIG_BIN, BAND_BINS)
               for name, spec in out_spec.items()}

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))

    ax = axes[0]
    for name, spec in out_spec.items():
        ax.semilogx(freqs[1:], 10 * np.log10(spec[1:] + 1e-30),
                    color=colors[name], lw=0.9, alpha=0.9, label=name)
    ax.axvspan(freqs[1], band_edge, color=ps.GRID, alpha=0.45, zorder=0)
    ax.text(band_edge * 0.9, 3, "signal band (OSR = 64)", ha="right",
            fontsize=8.5, color=ps.TEXT_SECONDARY)
    ax.set_xlabel("normalized frequency  f / fs")
    ax.set_ylabel("DAC output (dBFS)")
    ax.set_ylim(-140, 10)
    ax.set_title("(a) DAC output spectrum")
    ax.legend(loc="upper right", fontsize=9)

    ax = axes[1]
    for name, spec in err_spec.items():
        sndr, sfdr = metrics[name]
        ax.semilogx(freqs[1:], 10 * np.log10(spec[1:] + 1e-30),
                    color=colors[name], lw=0.9, alpha=0.9,
                    label=f"{name}:  SNDR {sndr:.0f} dB, "
                          f"SFDR {sfdr:.0f} dB")
    # slope triangle: the 2-D DWA error rises 20 dB/decade (first order)
    fx, fy = [4e-2, 4e-1], [-70.0, -50.0]
    ax.semilogx(fx, fy, "--", color=ps.TEXT_SECONDARY, lw=1.2)
    ax.semilogx(fx, [fy[0], fy[0]], "-", color=ps.TEXT_SECONDARY, lw=0.7)
    ax.semilogx([fx[1], fx[1]], fy, "-", color=ps.TEXT_SECONDARY, lw=0.7)
    ax.text(1.25e-1, -71.5, "1 decade", fontsize=8,
            color=ps.TEXT_SECONDARY, ha="center", va="top")
    ax.text(3.7e-1, -60, "20 dB", fontsize=8,
            color=ps.TEXT_SECONDARY, ha="right", va="center")
    ax.text(3.5e-2, -46, "2-D DWA error: +20 dB/dec\n(first-order shaped)",
            fontsize=8.5, color=ps.TEXT_SECONDARY, ha="left", va="top")
    ax.axvspan(freqs[1], band_edge, color=ps.GRID, alpha=0.45, zorder=0)
    ax.set_xlabel("normalized frequency  f / fs")
    ax.set_ylabel("DAC mismatch error (dBFS)")
    ax.set_ylim(-140, -40)
    ax.set_title("(b) Mismatch error only (output − ideal)")
    ax.legend(loc="upper left", fontsize=8.5)

    fig.suptitle("Mismatch shaping comparison — 6-bit DAC, 0.5% element / "
                 "1% segmentation mismatch, −3 dBFS sine, "
                 f"{N_AVG}-run average (cf. paper Fig. 14)")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(f"{FIGDIR}/fig4_spectrum_comparison.png")
    plt.close(fig)

    for name, (sndr, sfdr) in metrics.items():
        print(f"{name:15s}  SNDR = {sndr:6.1f} dB   SFDR = {sfdr:6.1f} dB")


if __name__ == "__main__":
    main()
    print("spectrum figure written to", FIGDIR)
