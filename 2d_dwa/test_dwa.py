"""Verification of the 2-D DWA behavioral model.

1. The selection patterns for the two input sequences given in the paper
   (Fig. 1 and Fig. 5) must match the hand-derived rotational patterns.
2. The 2-D DWA (row/column decoder model) must be bit-exact equivalent
   to a conventional 1-D DWA over 64 elements ("same operation as the
   conventional 1-D DWA", Section II-A).
"""

import numpy as np

from dwa_core import dwa_1d_masks, dwa_2d_masks, segmented_dwa_masks

SEQ_FIG1 = [3, 9, 15, 27, 13, 12, 34, 20, 13]
SEQ_FIG5 = [8, 9, 4, 18, 19, 35, 21, 19, 13]


def test_paper_sequences_match_1d_rotation():
    for seq in (SEQ_FIG1, SEQ_FIG5):
        m2 = dwa_2d_masks(seq, nbits=6)
        m1 = dwa_1d_masks(seq, 64)
        assert np.array_equal(m2, m1), f"mismatch for sequence {seq}"


def test_fig1_first_samples_hand_checked():
    """Spot-check the Fig. 1 pattern against the printed figure."""
    m = dwa_2d_masks(SEQ_FIG1, nbits=6).reshape(len(SEQ_FIG1), 8, 8)
    # d=3: row 0, columns 0-2
    assert m[0].sum() == 3 and m[0][0, 0:3].all()
    # d=9: row 0 cols 3-7 and row 1 cols 0-3
    assert m[1][0, 3:8].all() and m[1][1, 0:4].all() and m[1].sum() == 9
    # d=15: row 1 cols 4-7, row 2 full, row 3 cols 0-2
    assert m[2][1, 4:8].all() and m[2][2].all() and m[2][3, 0:3].all()
    assert m[2].sum() == 15
    # d=13 (5th sample): wraps: row 6 cols 6-7, row 7 full, row 0 cols 0-2
    assert m[4][6, 6:8].all() and m[4][7].all() and m[4][0, 0:3].all()
    assert m[4].sum() == 13


def test_equivalence_long_random():
    rng = np.random.default_rng(0)
    codes = rng.integers(0, 64, 20000)
    assert np.array_equal(dwa_2d_masks(codes, 6), dwa_1d_masks(codes, 64))


def test_edge_cases():
    codes = [0, 63, 0, 1, 63, 63, 8, 56, 0, 32, 32, 7, 57]
    assert np.array_equal(dwa_2d_masks(codes, 6), dwa_1d_masks(codes, 64))


def test_segmented_reconstructs_code():
    rng = np.random.default_rng(1)
    codes = rng.integers(0, 64, 5000)
    mm, lm = segmented_dwa_masks(codes, 6)
    assert np.array_equal(8 * mm.sum(axis=1) + lm.sum(axis=1), codes)


def test_element_usage_uniform():
    """First-order DWA property: every element used equally often
    (up to one rotation) for any input sequence."""
    rng = np.random.default_rng(2)
    codes = rng.integers(0, 64, 50000)
    usage = dwa_2d_masks(codes, 6).sum(axis=0)
    assert usage.max() - usage.min() <= 1


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS  {fn.__name__}")
    print(f"\nAll {len(fns)} checks passed.")
