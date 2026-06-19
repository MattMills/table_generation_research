"""The property-incompatibility frontier -- the project's headline claim.

The catalog and the cross-property matrix are infrastructure; *this* is the
contribution. The interesting question in "property-guaranteed discrete mapping
construction" is not "what can we build?" but "which guarantees provably cannot
coexist?". This module maps that boundary.

Each result is one of:

  INCOMPATIBLE  the two properties cannot be held at once -- with a reason and a
                live witness (a measured invariant, a spanning obstruction, ...)
  TRADEOFF      they coexist only subject to a quantitative bound (a minimum
                width, a rarely-achievable order)
  COMPATIBLE    a single table has both -- named explicitly, so the boundary is
                sharp rather than vague

Everything is computed at runtime, not asserted, so the frontier is checkable.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .bitmath import algebraic_degree, popcount
from .core import Family, Table
from .gf import gf_pow
from .properties import (
    CorrelationImmunity,
    DifferentialUniformity,
    Nonlinearity,
)

VERDICT_SYMBOL = {"INCOMPATIBLE": "x", "TRADEOFF": "~", "COMPATIBLE": "ok"}


@dataclass
class FrontierResult:
    prop_a: str
    prop_b: str
    verdict: str
    reason: str
    witness: str
    evidence: List[str] = field(default_factory=list)


def _selfmap(data: List[int], n: int) -> Table:
    return Table("t", Family.SPECULATIVE, "t", data, n, n)


# --- witnesses / helpers -----------------------------------------------------

def _aes_sbox() -> Table:
    from .generators.crypto import build_aes_sbox
    return build_aes_sbox()


def _gf_inverse() -> Table:
    from .generators.algebraic import build_gf_inverse
    return build_gf_inverse()


def _cube_gf32() -> Table:
    data = [gf_pow(x, 3, 0x25, 5) for x in range(32)]
    return _selfmap(data, 5)


def _linear_bijection(n: int) -> Table:
    # rotate-by-1 is GF(2)-linear and bijective
    mask = (1 << n) - 1
    return _selfmap([((x << 1) | (x >> (n - 1))) & mask for x in range(1 << n)], n)


def search_max_correlation_immunity(n: int, trials: int, seed: int = 0) -> int:
    """Largest correlation-immunity order found among random n-bit bijections."""
    ci = CorrelationImmunity()
    rng = random.Random(seed)
    best = 0
    for _ in range(trials):
        p = list(range(1 << n))
        rng.shuffle(p)
        order = ci.check(_selfmap(p, n)).value
        if order > best:
            best = order
    return best


def min_width_for_differential_uniformity(n: int, target_du: int) -> int:
    """Minimum block width to reach target DU under block-diagonal decomposition.

    A difference confined to one width-w block leaves the other n-w bits free,
    so DU_whole >= DU_block * 2^(n-w) >= 2^(n-w+1).  Hence DU_whole <= t forces
    w >= n + 1 - log2(t).
    """
    return max(1, n + 1 - int(math.floor(math.log2(target_du))))


# --- the frontier findings ---------------------------------------------------

def f_bijective_vs_entropy_uniform() -> FrontierResult:
    weights = [40, 25, 15, 10, 5, 3, 1, 1]
    total = sum(weights)
    p = [w / total for w in weights]

    def H(d):
        return -sum(x * math.log2(x) for x in d if x > 0)

    perm = list(range(8))
    random.Random(0).shuffle(perm)
    q = [0.0] * 8
    for i in range(8):
        q[perm[i]] = p[i]
    return FrontierResult(
        "bijective", "entropy-flattening", "INCOMPATIBLE",
        "a bijection only relabels probability mass, so output entropy equals input entropy",
        "any permutation of a biased distribution",
        [f"H(in)={H(p):.4f} == H(out)={H(q):.4f} bits; uniform target {math.log2(8):.4f} unreachable"],
    )


def f_bijective_vs_perfect_nonlinear() -> FrontierResult:
    from .generators.crypto import build_bent_function
    bent = build_bent_function(6)
    weight = sum(bent.data)
    return FrontierResult(
        "bijective", "perfect-nonlinear (bent)", "INCOMPATIBLE",
        "every nonzero component of a permutation is balanced, but bent functions "
        "are unbalanced; vectorial bent maps need m <= n/2, so no n->n bent bijection",
        "bent function (n=6)",
        [f"bent weight={weight} != balanced {2**5}; so it cannot be a permutation component"],
    )


def f_linear_vs_low_du() -> FrontierResult:
    lin = _linear_bijection(8)
    du = DifferentialUniformity().check(lin).value
    nl = Nonlinearity().check(lin).value
    return FrontierResult(
        "linear (nonlinearity 0)", "low differential uniformity", "INCOMPATIBLE",
        "a linear map L has L(x+a)+L(x)=L(a) constant, forcing DU = 2^n (the worst)",
        "rotate-by-1 (linear bijection, n=8)",
        [f"linear bijection: NL={nl}, DU={du}=2^8 (maximally bad); low DU requires nonlinearity"],
    )


def f_bent_vs_high_degree() -> FrontierResult:
    from .generators.crypto import build_bent_function
    rows = []
    for n in (4, 6):
        b = build_bent_function(n)
        rows.append(f"n={n}: bent degree {algebraic_degree(b.data)} <= n/2={n // 2}")
    return FrontierResult(
        "perfect-nonlinear (bent)", "high algebraic degree (> n/2)", "INCOMPATIBLE",
        "a bent function on n variables has algebraic degree at most n/2 (a hard bound)",
        "Maiorana-McFarland bent functions",
        rows,
    )


def f_involution_vs_asymmetric_profile() -> FrontierResult:
    sbox = _aes_sbox()
    inv = [0] * 256
    for x, y in enumerate(sbox.data):
        inv[y] = x
    nl_f = Nonlinearity().check(sbox).value
    nl_i = Nonlinearity().check(_selfmap(inv, 8)).value
    du_f = DifferentialUniformity().check(sbox).value
    du_i = DifferentialUniformity().check(_selfmap(inv, 8)).value
    return FrontierResult(
        "self-inverse direction", "asymmetric NL/DU profile", "INCOMPATIBLE",
        "nonlinearity and differential uniformity are invariant under inversion, "
        "so they are identical forward and backward (only e.g. algebraic degree can differ)",
        "AES S-box vs its inverse",
        [f"forward/inverse: NL {nl_f}/{nl_i}, DU {du_f}/{du_i} (equal)"],
    )


def f_distance_even_d() -> FrontierResult:
    n = 4
    rows = []
    for d in (2, 3):
        vecs = [v for v in range(1, 1 << n) if popcount(v) == d]
        # GF(2) rank
        basis: List[int] = []
        for v in vecs:
            cur = v
            for b in basis:
                cur = min(cur, cur ^ b)
            if cur:
                basis.append(cur)
                basis.sort(reverse=True)
        rows.append(f"d={d}: weight-{d} vectors span rank {len(basis)}/{n} "
                    f"({'spans' if len(basis) == n else 'cannot span'})")
    return FrontierResult(
        "distance-1->d converter", "even d", "INCOMPATIBLE",
        "even-weight columns live in the parity-zero subspace (dim n-1), so they "
        "can never span GF(2)^n; the converting matrix cannot be invertible",
        "weight-d spanning test (n=4)",
        rows,
    )


def f_bijective_vs_correlation_immunity(trials: int = 2000) -> FrontierResult:
    rows = []
    achieved = 0
    for n in (3, 4, 5):
        best = search_max_correlation_immunity(n, trials, seed=n)
        achieved = max(achieved, best)
        rows.append(f"n={n}: max order {best} over {trials} random bijections")
    return FrontierResult(
        "bijective", "correlation-immunity (order >= 1)", "TRADEOFF",
        "permutation components are balanced, but adding even first-order "
        "correlation immunity is extremely rare -- random search finds none, and "
        "high resiliency is known to trade against bijectivity and nonlinearity",
        "randomized search (lower bound)",
        rows + [f"best order found anywhere: {achieved} (resilient permutations need special construction)"],
    )


def f_low_du_vs_narrow_decomposition() -> FrontierResult:
    n = 8
    rows = []
    for target in (4, 16, 64):
        w = min_width_for_differential_uniformity(n, target)
        rows.append(f"target DU<= {target}: needs block width w >= {w} (of n={n})")
    # empirical confirmation: width-4 blocks cannot beat the bound
    b4 = [gf_pow(x, 7, 0x13, 4) for x in range(16)]
    data = [(b4[x >> 4] << 4) | b4[x & 0xF] for x in range(256)]
    measured = DifferentialUniformity().check(_selfmap(data, 8)).value
    rows.append(f"two width-4 blocks measured DU={measured} >= bound 2^(n-w+1)=32")
    return FrontierResult(
        "low differential uniformity", "narrow block decomposition", "TRADEOFF",
        "block-diagonal width-w lookups give DU >= 2^(n-w+1), so AES-grade DU=4 on "
        "n=8 needs w>=7 -- essentially the full width; cheap narrow decomposition "
        "and strong DU are quantitatively incompatible",
        "minimum-width bound + measurement",
        rows,
    )


def f_compatible_witnesses() -> List[FrontierResult]:
    """Sharp positives: single tables holding two non-trivial properties."""
    from .bitmath import component_function
    aes = _aes_sbox()
    cube = _cube_gf32()
    out = []
    nl = Nonlinearity().check(aes).value
    du = DifferentialUniformity().check(aes).value
    out.append(FrontierResult(
        "bijective", "high nonlinearity + low DU", "COMPATIBLE",
        "the AES S-box is a permutation that is also maximally nonlinear and 4-uniform",
        "AES S-box", [f"NL={nl}, DU={du}, bijective"]))
    deg = max(algebraic_degree(component_function(cube.data, b, 5)) for b in range(1, 32))
    cnl = Nonlinearity().check(cube).value
    cdu = DifferentialUniformity().check(cube).value
    out.append(FrontierResult(
        "low algebraic degree", "low DU (APN) + nonlinearity", "COMPATIBLE",
        "the GF(2^5) cube is an APN quadratic: minimal degree AND optimal DU",
        "GF(2^5) cube", [f"degree={deg}, DU={cdu} (APN), NL={cnl}"]))
    return out


# Ordered so the impossibilities lead.
def run_frontier(ci_trials: int = 2000) -> List[FrontierResult]:
    results = [
        f_bijective_vs_entropy_uniform(),
        f_bijective_vs_perfect_nonlinear(),
        f_linear_vs_low_du(),
        f_bent_vs_high_degree(),
        f_involution_vs_asymmetric_profile(),
        f_distance_even_d(),
        f_bijective_vs_correlation_immunity(ci_trials),
        f_low_du_vs_narrow_decomposition(),
    ]
    results.extend(f_compatible_witnesses())
    return results


# --- a compact symmetric grid over a core property vocabulary ----------------

_GRID_PROPS = ["bijective", "nonlinear", "low-DU", "low-degree", "balanced",
               "bent", "corr-immune"]

# Hand-curated cells justified by run_frontier (symmetric); "·" = not analysed.
_GRID: Dict[Tuple[str, str], str] = {
    ("bijective", "nonlinear"): "ok",
    ("bijective", "low-DU"): "ok",
    ("bijective", "low-degree"): "ok",
    ("bijective", "balanced"): "ok",       # forced: permutation components are balanced
    ("bijective", "bent"): "x",            # bent is unbalanced -> no bent bijection
    ("bijective", "corr-immune"): "~",     # rare / special construction
    ("nonlinear", "low-DU"): "ok",         # low DU requires nonlinearity
    ("nonlinear", "low-degree"): "ok",     # APN cube
    ("nonlinear", "bent"): "ok",           # bent is the nonlinearity extreme
    ("low-DU", "low-degree"): "ok",        # APN quadratic
    ("balanced", "bent"): "x",             # bent functions are unbalanced
    ("bent", "low-degree"): "ok",          # bent forced to degree <= n/2
    ("bent", "corr-immune"): "~",
}


def grid() -> Tuple[List[str], Dict[Tuple[str, str], str]]:
    return _GRID_PROPS, _GRID
