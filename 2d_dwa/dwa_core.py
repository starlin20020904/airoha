"""Behavioral models of DAC element-selection (DEM) schemes.

Reproduces the algorithms of:
  Y. Guo et al., "A Novel 2-D Data-Weighted-Averaging Technique for
  Low-Power High-Resolution Zoom ADC," IEEE Access, vol. 14, 2026.

The 6-bit 2-D DAC is an 8x8 array of unit elements. Element (i, j)
(i = column, j = row) maps to the linear index k = 8*j + i, matching
Fig. 1 of the paper: (0, 0) is selected first and elements are used
row by row, rotationally.
"""

import numpy as np


# ---------------------------------------------------------------------------
# Reference: conventional 1-D DWA
# ---------------------------------------------------------------------------

def dwa_1d_masks(codes, n_elem):
    """Conventional 1-D DWA: rotate a single pointer over n_elem elements.

    Returns an array of shape (len(codes), n_elem) with 1 where the
    element is selected.
    """
    codes = np.asarray(codes, dtype=int)
    masks = np.zeros((len(codes), n_elem), dtype=np.uint8)
    ptr = 0
    for n, d in enumerate(codes):
        idx = (ptr + np.arange(d)) % n_elem
        masks[n, idx] = 1
        ptr = (ptr + d) % n_elem
    return masks


# ---------------------------------------------------------------------------
# Proposed 2-D DWA (row/column decoder model per Section II of the paper)
# ---------------------------------------------------------------------------

def dwa_2d_masks(codes, nbits=6, return_signals=False):
    """2-D DWA modeled at the row/column-decoder level.

    The state is the column pointer c (head of the unused elements within
    the current row, signal 'hd') and the row pointer r. Per sample the
    decoders compute:
      nfull  = 1 if the final row selected last sample was only partly used
      nrows  = number of selected rows = msb + carry + nfull   (Fig. 6)
      hd, tl = head/tail column of the first/last selected row (Fig. 11)
    and the cell masks follow the selection logic of Figs. 7/10:
      middle rows fully selected; first row selects columns >= hd;
      last row selects columns <= tl; a single row selects hd..tl.

    Returns masks of shape (len(codes), 2**nbits); linear index k = W*j + i.
    """
    assert nbits % 2 == 0, "2-D DWA needs an even number of bits"
    w = 2 ** (nbits // 2)          # row/column count (8 for 6-bit)
    n_elem = w * w
    codes = np.asarray(codes, dtype=int)
    if np.any((codes < 0) | (codes >= n_elem)):
        raise ValueError(f"codes must be in [0, {n_elem - 1}]")

    masks = np.zeros((len(codes), n_elem), dtype=np.uint8)
    signals = []
    r, c = 0, 0                    # row pointer, column pointer (hd)
    for n, d in enumerate(codes):
        if d == 0:
            signals.append(dict(msb=0, lsb=0, nfull=0, carry=0,
                                nrows=0, hd=c, tl=c, rows=[]))
            continue
        msb, lsb = d >> (nbits // 2), d % w
        nfull = 1 if c != 0 else 0
        end = c + d - 1            # last used position relative to row start
        nrows = end // w + 1
        carry = nrows - msb - nfull
        assert carry in (0, 1), "carry logic violated"
        tl = end % w
        rows = [(r + k) % w for k in range(nrows)]

        m = masks[n].reshape(w, w)      # m[j, i]
        if nrows == 1:
            m[rows[0], c:tl + 1] = 1                       # rone / cone
        else:
            m[rows[0], c:] = 1                             # rfirst / cfirst
            for j in rows[1:-1]:
                m[j, :] = 1                                # rmid
            m[rows[-1], :tl + 1] = 1                       # rlast / clast

        signals.append(dict(msb=msb, lsb=lsb, nfull=nfull, carry=carry,
                            nrows=nrows, hd=c, tl=tl, rows=rows))
        # pointer update: advance by d elements, row-major with wrap
        p = (w * r + c + d) % n_elem
        r, c = p // w, p % w

    if return_signals:
        return masks, signals
    return masks


# ---------------------------------------------------------------------------
# Baseline: no DEM (thermometer, fixed row-major selection)
# ---------------------------------------------------------------------------

def thermometer_masks(codes, n_elem):
    """No DEM: always select the first d elements in row-major order."""
    codes = np.asarray(codes, dtype=int)
    masks = (np.arange(n_elem)[None, :] < codes[:, None]).astype(np.uint8)
    return masks


# ---------------------------------------------------------------------------
# Baseline: segmented DAC (MSB/LSB sub-DACs, each with its own 1-D DWA)
# ---------------------------------------------------------------------------

def segmented_dwa_masks(codes, nbits=6):
    """Segmented architecture used by the prior art the paper compares to.

    The N-bit DAC splits into an (N/2)-bit MSB sub-DAC (2**(N/2) elements
    of weight 2**(N/2)) and an (N/2)-bit LSB sub-DAC (2**(N/2) unit
    elements). Each sub-DAC runs its own conventional DWA, which shapes
    the intrinsic mismatch inside each sub-DAC but not the segmentation
    mismatch between them (Eq. (2)-(8) of the paper).

    Returns (msb_masks, lsb_masks).
    """
    codes = np.asarray(codes, dtype=int)
    w = 2 ** (nbits // 2)
    msb_masks = dwa_1d_masks(codes >> (nbits // 2), w)
    lsb_masks = dwa_1d_masks(codes % w, w)
    return msb_masks, lsb_masks


# ---------------------------------------------------------------------------
# DAC output with element mismatch
# ---------------------------------------------------------------------------

def unit_dac_output(masks, sigma_ee, rng):
    """Output of a unit-element DAC whose elements are 1 + eps_i.

    Returns (actual, ideal); actual - ideal is the mismatch error.
    Element errors are zero-meaned so mismatch adds no net gain error,
    isolating the nonlinearity (standard practice for DEM analysis).
    """
    n_elem = masks.shape[1]
    eps = rng.normal(0.0, sigma_ee, n_elem)
    eps -= eps.mean()
    actual = masks @ (1.0 + eps)
    ideal = masks.sum(axis=1).astype(float)
    return actual, ideal


def segmented_dac_output(msb_masks, lsb_masks, nbits, sigma_ee, sigma_es, rng):
    """Output of the segmented DAC with intrinsic + segmentation mismatch.

    MSB elements have weight W = 2**(N/2); their relative mismatch scales
    as sigma_ee / sqrt(W) (area scaling). The segmentation mismatch is a
    gain error sigma_es between the LSB and MSB sub-DACs.
    """
    w = 2 ** (nbits // 2)
    eps_m = rng.normal(0.0, sigma_ee / np.sqrt(w), w)
    eps_m -= eps_m.mean()
    eps_l = rng.normal(0.0, sigma_ee, w)
    eps_l -= eps_l.mean()
    eps_seg = rng.normal(0.0, sigma_es)
    actual = (msb_masks @ (w * (1.0 + eps_m))
              + lsb_masks @ ((1.0 + eps_l) * (1.0 + eps_seg)))
    ideal = (w * msb_masks.sum(axis=1) + lsb_masks.sum(axis=1)).astype(float)
    return actual, ideal


# ---------------------------------------------------------------------------
# Spectrum / metric helpers
# ---------------------------------------------------------------------------

def power_spectrum(x, nfft=None):
    """One-sided Hann-windowed power spectrum, normalized so that a
    full-scale (amplitude = 1) sine reads 0 dBFS at its bin."""
    x = np.asarray(x, dtype=float)
    n = len(x) if nfft is None else nfft
    win = np.hanning(n)
    xw = (x[:n] - np.mean(x[:n])) * win
    spec = np.abs(np.fft.rfft(xw)) / np.sum(win) * 2.0
    return spec ** 2                      # power, 1.0 == full-scale sine


def sndr_sfdr(pspec, sig_bin, band_bins, guard=3):
    """In-band SNDR and SFDR from a power spectrum.

    sig_bin: bin index of the fundamental; band_bins: last in-band bin.
    """
    sig = pspec[sig_bin - guard:sig_bin + guard + 1].sum()
    inband = pspec[1:band_bins + 1].copy()
    lo = max(1, sig_bin - guard)
    inband[lo - 1:sig_bin + guard] = 0.0     # remove fundamental
    noise = inband.sum()
    sndr = 10 * np.log10(sig / noise) if noise > 0 else np.inf
    sfdr = 10 * np.log10(sig / inband.max()) if inband.max() > 0 else np.inf
    return sndr, sfdr


def dsm_quantized_sine(n, amp_dbfs, sig_bin, nbits, rng):
    """Sine re-quantized to nbits by a 2nd-order error-feedback digital
    delta-sigma modulator: Y(z) = U(z) + (1 - z^-1)^2 * E(z).

    This mimics the code stream a multi-bit noise-shaping ADC (such as the
    paper's zoom ADC) feeds to its DAC: the quantization noise is pushed
    out of band, so the in-band floor is set by the DAC mismatch, not by
    quantization. Returns codes in [0, 2**nbits - 1].
    """
    full = 2 ** nbits - 1
    mid = full / 2.0
    amp = mid * 10 ** (amp_dbfs / 20.0)
    t = np.arange(n)
    u = mid + amp * np.sin(2 * np.pi * sig_bin * t / n)
    codes = np.empty(n, dtype=int)
    e1 = e2 = 0.0
    dither = rng.uniform(-0.5, 0.5, n)
    for k in range(n):
        v = u[k] + 2.0 * e1 - e2
        # dither only perturbs the rounding decision; the full error v - y
        # is fed back, so the dither is noise-shaped along with it
        y = min(max(int(round(v + dither[k])), 0), full)
        e2, e1 = e1, v - y
        codes[k] = y
    return codes


def quantized_sine(n, amp_dbfs, sig_bin, nbits, rng):
    """Mid-tread quantized sine codes in [0, 2**nbits - 1] with 1-LSB
    triangular dither to decorrelate the quantization error."""
    full = 2 ** nbits - 1
    mid = full / 2.0
    amp = mid * 10 ** (amp_dbfs / 20.0)
    t = np.arange(n)
    x = mid + amp * np.sin(2 * np.pi * sig_bin * t / n)
    dither = rng.uniform(-0.5, 0.5, n) + rng.uniform(-0.5, 0.5, n)
    codes = np.clip(np.round(x + dither), 0, full).astype(int)
    return codes
