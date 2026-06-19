"""Distance-preserving mappings (Ferreira-Swart-Vinck), from survey section 4.

These map binary inputs to *permutation* sequences while controlling Hamming
distance, for permutation trellis codes on noisy (e.g. power-line) channels:

  DCM  distance-conserving:  d_p(y_i,y_j) >= d_c(x_i,x_j)
  DIM  distance-increasing:  d_p(y_i,y_j) >  d_c(x_i,x_j)   (for i != j)
  DRM  distance-reducing:    bounded controlled reduction

This is the literature's version of the speculative "distance-converting table"
explored in `generators/speculative.py` -- but mapping to symbol permutations
rather than bit-vectors.  The construction below is found by the transposition
search the survey describes; the "star" transpositions tau_i = (0, i+1) yield a
DIM for every n, verified by the DistanceIncreasing property.
"""

from __future__ import annotations

from typing import List, Tuple

from .core import Family, Table


def _apply_transpositions(bits: Tuple[int, ...], m: int,
                          swaps: List[Tuple[int, int]]) -> Tuple[int, ...]:
    perm = list(range(m))
    for i, bit in enumerate(bits):
        if bit:
            a, b = swaps[i]
            perm[a], perm[b] = perm[b], perm[a]
    return tuple(perm)


def build_distance_increasing_mapping(n: int = 4) -> Table:
    """DIM from {0,1}^n to permutations of M = n+1 symbols (star transpositions).

    Each input bit i, when set, swaps position 0 with position i+1.  The result
    is injective and strictly distance-increasing for all tested n.
    """
    m = n + 1
    swaps = [(0, i + 1) for i in range(n)]
    inputs = [tuple((v >> i) & 1 for i in range(n)) for v in range(1 << n)]
    outputs = [_apply_transpositions(x, m, swaps) for x in inputs]
    return Table(
        name=f"distance-increasing mapping (n={n} -> S_{m})",
        family=Family.COMBINATORIAL,
        generator="distance-increasing mapping",
        notes="binary words -> symbol permutations, strictly increasing Hamming distance.",
        meta={"distance_map": {"inputs": inputs, "outputs": outputs,
                               "symbols": m, "swaps": swaps}},
    )


def distance_mapping_stats(table: Table) -> dict:
    """XSHD (summed distances) and the minimum per-pair distance gain."""
    spec = table.meta["distance_map"]
    ins, outs = spec["inputs"], spec["outputs"]

    def hd(a, b):
        return sum(1 for x, y in zip(a, b) if x != y)

    pairs = [(i, j) for i in range(len(ins)) for j in range(i + 1, len(ins))]
    xshd = sum(hd(outs[i], outs[j]) for i, j in pairs)
    min_gain = min(hd(outs[i], outs[j]) - hd(ins[i], ins[j]) for i, j in pairs)
    return {"xshd": xshd, "min_gain": min_gain, "pairs": len(pairs)}
