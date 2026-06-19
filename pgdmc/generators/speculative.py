"""Speculative constructions: start from a desired property, probe feasibility.

This is the part the conversation actually asked for -- not cataloguing what
exists, but asking "given a property spec, what generator could produce it, and
what are the limits?"  Each exploration here runs real checks and returns an
honest verdict.  Several outcomes are the interesting kind:

  * ENTROPY REDISTRIBUTION by a bijection is *provably impossible* -- a
    permutation only reorders probability mass, so entropy is invariant.
  * DISTANCE-CONVERTING maps collapse to a crisp linear-algebra condition:
    they exist iff there is an invertible binary matrix with uniform column
    weight d -- which (the search discovers) forces d to be odd.
  * SELF-INVERSE-ASYMMETRIC reveals that nonlinearity and differential
    uniformity are *inverse-invariant*, so the asymmetry can only live in a
    property like algebraic degree.

Knowing which combinations are unreachable is exactly the "fundamental limits"
half of the proposed research field.
"""

from __future__ import annotations

import itertools
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..bitmath import algebraic_degree, component_function, popcount
from ..core import Family, FamilySize, Generator, Table
from ..gf import gf_pow
from ..properties import DifferentialUniformity, Nonlinearity, StrictAvalanche

# GF(2^5): x^5 + x^2 + 1 (irreducible & primitive).
GF32_MODULUS = 0x25
GF32_DEGREE = 5


@dataclass
class FeasibilityReport:
    """The outcome of probing one speculative construction."""

    name: str
    claim: str
    verdict: str  # CONSTRUCTED | IMPOSSIBLE | CHARACTERISED | SEARCH-FOUND | LIMITED
    evidence: List[str] = field(default_factory=list)
    takeaway: str = ""


# --- shared helpers ----------------------------------------------------------

def _self_map_table(name: str, data: List[int], n: int) -> Table:
    return Table(
        name=name,
        family=Family.SPECULATIVE,
        generator=name,
        data=data,
        domain_bits=n,
        codomain_bits=n,
    )


def _algebraic_degree_of_map(data: List[int], n: int) -> int:
    deg = 0
    for b in range(1, 1 << n):
        deg = max(deg, algebraic_degree(component_function(data, b, n)))
    return deg


def _nl_du(data: List[int], n: int) -> Tuple[int, int]:
    table = _self_map_table("tmp", data, n)
    nl = Nonlinearity().check(table).value
    du = DifferentialUniformity().check(table).value
    return nl, du


def _gf2_rank(vectors: List[int]) -> int:
    """Rank over GF(2) of integer bit-vectors."""
    basis: List[int] = []
    for v in vectors:
        cur = v
        for b in basis:
            cur = min(cur, cur ^ b)
        if cur:
            basis.append(cur)
            basis.sort(reverse=True)
    return len(basis)


def _gf2_basis_subset(vectors: List[int], n: int) -> Optional[List[int]]:
    """Return n independent vectors from the list, or None if they don't span."""
    basis: List[int] = []
    chosen: List[int] = []
    for v in vectors:
        cur = v
        for b in basis:
            cur = min(cur, cur ^ b)
        if cur:
            basis.append(cur)
            basis.sort(reverse=True)
            chosen.append(v)
            if len(chosen) == n:
                return chosen
    return None


# --- the explorations --------------------------------------------------------

def explore_entropy_redistribution() -> FeasibilityReport:
    """Can a *bijection* flatten a biased input distribution to uniform?  No."""
    # A deliberately biased distribution over 8 symbols.
    weights = [40, 25, 15, 10, 5, 3, 1, 1]
    total = sum(weights)
    p = [w / total for w in weights]

    def entropy(dist: List[float]) -> float:
        return -sum(x * math.log2(x) for x in dist if x > 0)

    h_in = entropy(p)
    # Apply the "best" bijection we can dream up -- any permutation of symbols.
    perm = list(range(8))
    random.Random(0).shuffle(perm)
    q = [0.0] * 8
    for i in range(8):
        q[perm[i]] = p[i]  # bijection just relabels symbols
    h_out = entropy(q)
    h_uniform = math.log2(8)

    return FeasibilityReport(
        name="Entropy redistribution table",
        claim="A single-lookup bijection that flattens a biased byte to uniform.",
        verdict="IMPOSSIBLE",
        evidence=[
            f"input entropy  = {h_in:.4f} bits",
            f"after bijection = {h_out:.4f} bits (identical -- mass is only relabeled)",
            f"uniform target = {h_uniform:.4f} bits (unreachable: gap {h_uniform - h_in:.4f})",
            "A bijection preserves the multiset of probabilities, hence entropy.",
        ],
        takeaway=(
            "Debiasing needs a non-injective (lossy) or expanding map -- exactly "
            "what randomness extractors and arithmetic coding use. The property "
            "'bijective AND entropy-flattening' is contradictory for equal domains."
        ),
    )


def explore_distance_converting() -> FeasibilityReport:
    """Map every Hamming-distance-1 input pair to distance exactly d.

    For an affine map x -> Mx, unit input differences map to columns of M, so
    'all distance-1 pairs -> distance exactly d' holds iff every column of M has
    weight d and M is invertible.  Existence therefore reduces to: do the
    weight-d vectors span GF(2)^n?
    """
    evidence: List[str] = []
    pattern: Dict[int, List[int]] = {}
    for n in (3, 4, 5):
        achievable = []
        for d in range(1, n + 1):
            vectors = [v for v in range(1, 1 << n) if popcount(v) == d]
            if vectors and _gf2_rank(vectors) == n:
                achievable.append(d)
        pattern[n] = achievable
        evidence.append(f"n={n}: distance-1 convertible to d in {achievable}")
    evidence.append(
        "Even d always fails: weight-even vectors live in the parity-zero "
        "subspace (dim n-1), so they can never span -> the matrix can't be "
        "invertible. Only odd d (that also span) are reachable."
    )
    return FeasibilityReport(
        name="Distance-converting table",
        claim="Bijection sending every distance-1 input pair to distance exactly d.",
        verdict="CHARACTERISED",
        evidence=evidence,
        takeaway=(
            "The vague idea becomes a clean theorem: achievable iff an invertible "
            "binary matrix has all columns of weight d, which forces d odd. The "
            "framework turned 'I wonder if...' into a decidable spanning question. "
            "The literature's version maps to symbol permutations instead of "
            "bit-vectors -- the DCM/DIM/DRM family (see pgdmc/distance_mappings.py)."
        ),
    )


def build_distance_converting_table(n: int = 4, d: int = 3) -> Table:
    """Concrete distance-(1->d) converter: linear map with weight-d columns."""
    vectors = [v for v in range(1, 1 << n) if popcount(v) == d]
    cols = _gf2_basis_subset(vectors, n)
    if cols is None:  # pragma: no cover - guarded by explore_distance_converting
        raise ValueError(f"no distance-{d} converter exists for n={n}")

    def apply(x: int) -> int:
        out = 0
        for i in range(n):
            if (x >> i) & 1:
                out ^= cols[i]
        return out

    data = [apply(x) for x in range(1 << n)]
    table = _self_map_table(f"distance-1->{d} converter (n={n})", data, n)
    table.notes = f"linear map; every single input-bit flip flips exactly {d} output bits."
    return table


def explore_avalanche_optimal() -> FeasibilityReport:
    """Smallest bijection meeting the strict avalanche criterion *exactly*."""
    sac = StrictAvalanche()
    smallest = None
    example = None
    count_n3 = 0
    for n in (2, 3):
        found_here = 0
        for perm in itertools.permutations(range(1 << n)):
            t = _self_map_table("p", list(perm), n)
            if sac.check(t).value == 0:
                found_here += 1
                if smallest is None:
                    smallest = n
                    example = list(perm)
        if n == 3:
            count_n3 = found_here
    # Past the n=3 ceiling: exhaustive 16! is hopeless, so sample randomly at n=4.
    rng = random.Random(0)
    n4_trials = 30000
    n4_found = None
    for _ in range(n4_trials):
        perm = list(range(16))
        rng.shuffle(perm)
        if sac.check(_self_map_table("p", perm, 4)).value == 0:
            n4_found = perm
            break
    return FeasibilityReport(
        name="Avalanche-optimal table",
        claim="Bijection where every input-bit flip flips every output bit w.p. exactly 1/2.",
        verdict="SEARCH-FOUND" if smallest is not None else "LIMITED",
        evidence=[
            f"smallest exact-SAC bijection: n={smallest}",
            f"example (n={smallest}): {example}",
            f"count of exact-SAC bijections at n=3: {count_n3} (of {math.factorial(8)}, exhaustive)",
            f"n=4 (randomized, {n4_trials} trials): "
            + (f"found {n4_found}" if n4_found else "none in budget"),
        ],
        takeaway=(
            "Exact (not just statistical) SAC bijections exist and are findable by "
            "exhaustive search at n=3 and randomized search at n=4; exact counts per "
            "n are an open-ended construction question the framework makes precise."
        ),
    )


def build_algebraic_degree_bounded_table() -> Table:
    """Low-degree permutation x -> x^3 over GF(2^5) (algebraic degree 2)."""
    data = [gf_pow(x, 3, GF32_MODULUS, GF32_DEGREE) for x in range(1 << GF32_DEGREE)]
    table = _self_map_table("GF(2^5) cube (degree-bounded)", data, GF32_DEGREE)
    table.notes = "x^3: bijective, nonlinear, algebraic degree 2 (cheap on encrypted data)."
    return table


def explore_algebraic_degree_bounded() -> FeasibilityReport:
    """Bijection whose every output bit is a low-degree polynomial of the input."""
    table = build_algebraic_degree_bounded_table()
    n = GF32_DEGREE
    deg = _algebraic_degree_of_map(table.data, n)
    bijective = sorted(table.data) == list(range(1 << n))
    return FeasibilityReport(
        name="Algebraic-degree-bounded table",
        claim="Bijection with every output bit expressible as a low-degree GF(2) polynomial.",
        verdict="CONSTRUCTED",
        evidence=[
            f"x^3 over GF(2^{n}): bijective = {bijective}",
            f"algebraic degree = {deg} (vs n-1 = {n - 1} for a generic bijection)",
        ],
        takeaway=(
            "Power maps x^(2^k+1) give provably low algebraic degree -- the basis "
            "for S-boxes evaluable under homomorphic encryption / MPC, where cost "
            "scales with degree. The property spec drives the construction directly."
        ),
    )


def explore_compositional_closure() -> FeasibilityReport:
    """A family of tables closed under composition (a group of lookups)."""
    # Multiply-by-generator on GF(2^5)*: in log space this is +k mod 31.
    order = (1 << GF32_DEGREE) - 1  # 31
    # Represent each member as the shift-by-k permutation on Z_order.
    members = [[(x + k) % order for x in range(order)] for k in range(order)]
    closed = True
    for a in range(order):
        for b in range(order):
            comp = [members[a][members[b][x]] for x in range(order)]
            if comp != members[(a + b) % order]:
                closed = False
                break
        if not closed:
            break
    # Skip-ahead: jumping K steps == member[K], one lookup instead of K.
    k_jump = 1000 % order
    return FeasibilityReport(
        name="Compositional-closure table family",
        claim="A family of tables where any chain of compositions stays in the family.",
        verdict="CONSTRUCTED" if closed else "LIMITED",
        evidence=[
            f"family size = {order} (multiply-by-g^k on GF(2^{GF32_DEGREE})*)",
            f"closed under composition: {closed}  (member_a o member_b = member_(a+b mod {order}))",
            f"fast-forward 1000 steps = member[{k_jump}] in one lookup, not 1000 compositions",
        ],
        takeaway=(
            "Cyclic groups of permutations give O(1) skip-ahead / rewind -- the "
            "engine behind jump-ahead in PRNGs and reversible simulation stepping."
        ),
    )


def build_multi_resolution_table() -> Table:
    """8-bit bijection whose top nibble is itself a valid 4-bit bijection."""
    def p_nibble(hi: int) -> int:  # a 4-bit bijection on the high nibble
        return gf_pow(hi, 7, 0x13, 4)

    def f(x: int) -> int:
        hi, lo = x >> 4, x & 0xF
        return (p_nibble(hi) << 4) | ((lo + hi) & 0xF)

    data = [f(x) for x in range(256)]
    table = _self_map_table("multi-resolution (8-bit, nibble-truncatable)", data, 8)
    table.notes = "truncating output to the top 4 bits yields a valid 4-bit bijection."
    return table


def explore_multi_resolution() -> FeasibilityReport:
    """A table that stays valid (with weaker guarantees) when truncated."""
    table = build_multi_resolution_table()
    full_bijective = sorted(table.data) == list(range(256))
    # Induced high-nibble map: top 4 bits of output as a function of high nibble.
    induced = {}
    consistent = True
    for x in range(256):
        hi = x >> 4
        top = table.data[x] >> 4
        if hi in induced and induced[hi] != top:
            consistent = False
        induced[hi] = top
    induced_bijective = sorted(induced[h] for h in range(16)) == list(range(16))
    return FeasibilityReport(
        name="Multi-resolution table",
        claim="A wide table whose truncation is still a valid (weaker) mapping.",
        verdict="CONSTRUCTED" if (full_bijective and induced_bijective) else "LIMITED",
        evidence=[
            f"full 8-bit map bijective: {full_bijective}",
            f"top-nibble map well-defined (depends only on high bits): {consistent}",
            f"induced 4-bit map bijective: {induced_bijective}",
        ],
        takeaway=(
            "A triangular / wreath-product construction makes precision a free "
            "choice at read time: read 4 bits for a rough answer, 8 for the full "
            "one, both provably valid. Useful for streaming / progressive systems."
        ),
    )


def explore_correlation_immune_bijection() -> FeasibilityReport:
    """How correlation-immune can a bijection be?  Probe the tension."""
    from ..properties import CorrelationImmunity
    ci = CorrelationImmunity()
    best_order = -1
    best_example = None
    n = 3
    for perm in itertools.permutations(range(1 << n)):
        t = _self_map_table("p", list(perm), n)
        order = ci.check(t).value
        if order > best_order:
            best_order = order
            best_example = list(perm)
    return FeasibilityReport(
        name="Correlation-immune bijection",
        claim="A bijection whose output is independent of any k input bits.",
        verdict="LIMITED",
        evidence=[
            f"max correlation-immunity order over all 3-bit bijections: {best_order}",
            f"witness: {best_example}",
            "Every nonzero component of a bijection is balanced (order >= implied), "
            "but high resiliency fights bijectivity and nonlinearity.",
        ],
        takeaway=(
            "Bijectivity caps achievable correlation immunity -- a concrete instance "
            "of property *incompatibility*. Resilient functions trade away the "
            "permutation property; you cannot have all of it at once."
        ),
    )


def explore_self_inverse_asymmetric() -> FeasibilityReport:
    """Can a map and its inverse have *different* property profiles?"""
    from .crypto import build_aes_sbox
    sbox = build_aes_sbox()
    inv = [0] * 256
    for x, y in enumerate(sbox.data):
        inv[y] = x
    nl_f, du_f = _nl_du(sbox.data, 8)
    nl_i, du_i = _nl_du(inv, 8)

    # Algebraic degree, by contrast, is NOT inverse-invariant.
    cube = [gf_pow(x, 3, GF32_MODULUS, GF32_DEGREE) for x in range(1 << GF32_DEGREE)]
    cube_inv = [gf_pow(x, 21, GF32_MODULUS, GF32_DEGREE) for x in range(1 << GF32_DEGREE)]  # 3*21=1 mod 31
    deg_f = _algebraic_degree_of_map(cube, GF32_DEGREE)
    deg_i = _algebraic_degree_of_map(cube_inv, GF32_DEGREE)

    return FeasibilityReport(
        name="Self-inverse / asymmetric-profile table",
        claim="One table optimizing different properties in the forward vs inverse direction.",
        verdict="CHARACTERISED",
        evidence=[
            f"AES S-box: nonlinearity fwd/inv = {nl_f}/{nl_i}, diff-uniformity fwd/inv = {du_f}/{du_i}",
            "  -> nonlinearity & differential uniformity are INVERSE-INVARIANT (always equal).",
            f"GF(2^5) cube: algebraic degree fwd = {deg_f}, inverse (x^21) = {deg_i}",
            "  -> algebraic degree CAN differ between a map and its inverse.",
        ],
        takeaway=(
            "The literal wish ('self-inverse yet asymmetric in NL/DU') is impossible, "
            "because those properties are preserved under inversion. The realizable "
            "asymmetry lives in non-invariant properties like algebraic degree -- the "
            "framework tells you *which* knobs can ever differ."
        ),
    )


def explore_disjoint_coverage() -> FeasibilityReport:
    """A family of permutations covering every (input, output) pair exactly once."""
    n = 8
    family = [[(x + k) % n for x in range(n)] for k in range(n)]  # the Z_n shifts
    counts = [[0] * n for _ in range(n)]
    for perm in family:
        for i in range(n):
            counts[i][perm[i]] += 1
    every_once = all(counts[i][j] == 1 for i in range(n) for j in range(n))
    return FeasibilityReport(
        name="Disjoint-coverage table family",
        claim="A set of tables where every input->output pair is realized by exactly one.",
        verdict="CONSTRUCTED" if every_once else "LIMITED",
        evidence=[
            f"family of {n} shift permutations on Z_{n}",
            f"every (input,output) pair covered exactly once: {every_once}",
            "This *is* the row set of the cyclic Latin square -- a sharply transitive set.",
        ],
        takeaway=(
            "Sharply transitive permutation sets (equivalently, the rows of a Latin "
            "square) give maximally-disagreeing ensembles -- a basis for voting / "
            "ensemble lookups -- and tie the speculative idea back to a classical object."
        ),
    )


def explore_streaming_decomposable() -> FeasibilityReport:
    """Minimum sub-table width to reconstruct a target differential uniformity.

    The earlier version of this probe just concatenated two tables (block
    diagonal) -- which is exactly the direct-sum combinator and answers nothing.
    The real question is: given a property spec, how narrow can the sub-tables
    be?  For block-diagonal width-w lookups the answer is a hard bound: a
    difference confined to one block leaves the other n-w bits free, so
        DU_whole >= DU_block * 2^(n-w) >= 2^(n-w+1),
    hence reaching target DU=t forces w >= n + 1 - log2(t).
    """
    n = 8
    bounds = []
    for t in (4, 16, 64):
        w = max(1, n + 1 - int(math.log2(t)))
        bounds.append(f"target DU<= {t}: minimum block width w >= {w} (of n={n})")

    # Empirical confirmation: two width-4 blocks cannot beat the bound.
    block = [gf_pow(x, 7, 0x13, 4) for x in range(16)]  # x^7 over GF(2^4)
    data = [(block[x >> 4] << 4) | block[x & 0xF] for x in range(256)]
    measured = DifferentialUniformity().check(_self_map_table("d", data, 8)).value

    return FeasibilityReport(
        name="Minimum sub-table width for a property (streaming decomposition)",
        claim="The minimum narrow-lookup width that still reconstructs a target DU.",
        verdict="CHARACTERISED",
        evidence=bounds + [
            f"two width-4 blocks measured DU={measured} >= bound 2^(n-w+1)=32 (cannot beat it)",
            "AES-grade DU=4 on n=8 needs w>=7 -- essentially the full width.",
        ],
        takeaway=(
            "Block-diagonal decomposition trades diffusion for memory, and the "
            "property fixes a hard *minimum* width (w >= n+1-log2(DU)). The open, "
            "interesting version is non-block factorings (AES 'T-tables' reconstruct "
            "a *specific* map via lookups+XOR, not an arbitrary property) -- the "
            "minimum width for a general property under richer combiners is open."
        ),
    )


EXPLORERS = [
    explore_entropy_redistribution,
    explore_distance_converting,
    explore_avalanche_optimal,
    explore_algebraic_degree_bounded,
    explore_compositional_closure,
    explore_multi_resolution,
    explore_correlation_immune_bijection,
    explore_self_inverse_asymmetric,
    explore_disjoint_coverage,
    explore_streaming_decomposable,
]


def run_all_explorations() -> List[FeasibilityReport]:
    return [explore() for explore in EXPLORERS]


# Constructive speculative successes that are clean self-maps also enter the
# catalog, so the cross-property matrix includes the *new* tables alongside the
# classical ones.
GENERATORS = [
    Generator(
        name="degree-bounded bijection",
        family=Family.SPECULATIVE,
        description="Low algebraic-degree permutation (x^3 over GF(2^5)).",
        build=build_algebraic_degree_bounded_table,
        guarantees=["bijective"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
    ),
    Generator(
        name="multi-resolution bijection",
        family=Family.SPECULATIVE,
        description="8-bit bijection whose truncation to 4 bits is still bijective.",
        build=build_multi_resolution_table,
        guarantees=["bijective"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
    ),
    Generator(
        name="distance converter",
        family=Family.SPECULATIVE,
        description="Linear bijection flipping exactly d output bits per input-bit flip.",
        build=build_distance_converting_table,
        guarantees=["bijective"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
    ),
]
