"""Survey-grounded extensions: methods drawn from a literature review.

This module turns a literature survey of "property-guaranteed discrete mapping
constructions" into *runnable, verified* findings, so the review is checkable
rather than merely cited.  Each finding records how it relates to the rest of
the project: VALIDATES (we already had it; the survey confirms the theory),
EXTENDS (we had a toy version; this is the real one), or NEW (added from the
survey).  Reference-only items (hardware gate counts, quantum S-boxes, Orbiter
classification) are catalogued in docs/literature_review.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .distance_mappings import build_distance_increasing_mapping, distance_mapping_stats
from .gf import (
    AES_DEGREE,
    AES_GENERATOR,
    AES_MODULUS,
    build_exp_log,
    gf_mul,
    gf_pow,
)
from .generators.algebraic import build_zech_logarithm
from .generators.combinatorial import build_costas_array
from .generators.hashing import tabulation_4independence_failure
from .generators.rings import mba_null, obfuscation_inverse_pair
from .homomorphic import programmable_bootstrap_demo
from .properties import (
    CyclotomicCompressible,
    DistanceIncreasing,
    ThumbtackAutocorrelation,
)


@dataclass
class ExtensionFinding:
    name: str
    section: str          # the survey section
    relation: str         # VALIDATES | EXTENDS | NEW
    summary: str
    evidence: List[str] = field(default_factory=list)


def finding_equivalent_inverse_generators() -> ExtensionFinding:
    """Sec 1: one property-guaranteed table, several competing generators."""
    exp, log = build_exp_log(AES_GENERATOR, AES_MODULUS, AES_DEGREE)
    via_tables = [0] + [exp[(255 - log[x]) % 255] for x in range(1, 256)]
    via_fermat = [gf_pow(x, 254, AES_MODULUS, AES_DEGREE) for x in range(256)]

    def via_search(a):  # independent brute-force inverse
        if a == 0:
            return 0
        return next(b for b in range(1, 256) if gf_mul(a, b, AES_MODULUS, AES_DEGREE) == 1)

    via_brute = [via_search(x) for x in range(256)]
    agree = via_tables == via_fermat == via_brute
    return ExtensionFinding(
        name="Equivalent generators for the GF(2^8) inverse",
        section="1 (tower fields / S-box hardware)",
        relation="VALIDATES",
        summary="The inverse table is unique; log/antilog, Fermat x^254, and search "
                "are interchangeable generators competing only on cost.",
        evidence=[
            f"log/antilog == Fermat x^254 == search-inverse: {agree}",
            "Hardware lineage (Canright normal-basis 120->113 gates, then area-records "
            "via NAND/NOR) is the same table reached by a cheaper generator -- "
            "documented as reference in docs/literature_review.md.",
        ],
    )


def finding_zech_cyclotomic_compression() -> ExtensionFinding:
    """Sec 7: Zech table compresses along 2-cyclotomic cosets."""
    zech = build_zech_logarithm()
    result = CyclotomicCompressible().check(zech)
    return ExtensionFinding(
        name="Zech logarithm cyclotomic-coset compression",
        section="7 (Zech logarithms)",
        relation="EXTENDS",
        summary="Z(2x)=2Z(x) lets one entry per coset stand in for the whole orbit, "
                "shrinking the table for memory-constrained devices.",
        evidence=[
            f"identity holds, compression: {result.detail}",
            "gives our previously-bare Zech entry a real, verifiable guarantee.",
        ],
    )


def finding_ring_permutation_polynomials() -> ExtensionFinding:
    """Sec 3: Rivest-Black permutations over Z/2^w (RC6)."""
    from .generators.rings import build_rc6_mixing
    from .properties import Bijective, RivestBlackPermutation
    rc6 = build_rc6_mixing(8)
    rb = RivestBlackPermutation().check(rc6)
    bij = Bijective().check(rc6)
    return ExtensionFinding(
        name="Permutation polynomials over Z/2^w (RC6 mixing)",
        section="3 (permutation polynomials over rings)",
        relation="NEW",
        summary="Word-sized bijective scrambling with no field machinery; the "
                "Rivest-Black coefficient test predicts bijectivity exactly.",
        evidence=[
            f"RC6 x(2x+1) mod 2^8: bijective={bij.status.value}; {rb.detail}",
            "broadens the algebraic family from GF(2^n) monomials to ring polynomials.",
        ],
    )


def finding_mba_obfuscation() -> ExtensionFinding:
    """Sec 3.2: MBA null identity and an inverse permutation-polynomial pair."""
    null_ok = all(mba_null(x, y, 8) == 0 for x in range(256) for y in range(256))
    encode, decode = obfuscation_inverse_pair(8)
    roundtrip = all(decode(encode(x)) == x for x in range(256))
    return ExtensionFinding(
        name="Mixed Boolean-Arithmetic obfuscation pair",
        section="3.2 (null polynomials / MBA)",
        relation="NEW",
        summary="An identically-zero MBA expression plus inverse permutation "
                "polynomials give semantics-preserving code obfuscation.",
        evidence=[
            f"MBA E(x,y) == 0 for all 65536 inputs: {null_ok}",
            f"encode P and decode Q are mutual inverses mod 256: {roundtrip}",
            "decode o encode = identity ties obfuscation to the combinator algebra.",
        ],
    )


def finding_tabulation_independence() -> ExtensionFinding:
    """Sec 6: tabulation hashing is 3- but not 4-independent."""
    fail = tabulation_4independence_failure()
    return ExtensionFinding(
        name="Tabulation hashing independence limit",
        section="6 (statistical tabulation mappings)",
        relation="EXTENDS",
        summary="Simple tabulation gives 3-independence and Chernoff-style "
                "concentration, but provably fails 4-independence on a rectangle.",
        evidence=[
            f"rectangle keys {fail['keys']} XOR to {fail['xor']} "
            f"(cancels to zero: {fail['cancels_to_zero']})",
            "an honest property *limit* in the otherwise statistical hashing family.",
        ],
    )


def finding_distance_increasing_mapping() -> ExtensionFinding:
    """Sec 4: real distance-increasing mapping (vs our toy bit-vector probe)."""
    dim = build_distance_increasing_mapping(4)
    result = DistanceIncreasing().check(dim)
    stats = distance_mapping_stats(dim)
    return ExtensionFinding(
        name="Distance-increasing mapping (Ferreira-Swart-Vinck)",
        section="4 (distance-converting mappings)",
        relation="EXTENDS",
        summary="Binary words -> symbol permutations with strictly increasing "
                "Hamming distance, for permutation trellis codes on noisy channels.",
        evidence=[
            f"n=4 -> S_5: {result.detail}; min per-pair gain={stats['min_gain']}, "
            f"XSHD={stats['xshd']}",
            "the literature framing of the speculative 'distance-converting table'.",
        ],
    )


def finding_costas_autocorrelation() -> ExtensionFinding:
    """Sec 5: Costas arrays have ideal thumbtack autocorrelation."""
    costas = build_costas_array(11, 2)
    result = ThumbtackAutocorrelation().check(costas)
    return ExtensionFinding(
        name="Costas array thumbtack autocorrelation",
        section="5 (autocorrelation-guaranteed arrays)",
        relation="VALIDATES",
        summary="The distinct-difference property is equivalent to an ideal "
                "off-origin autocorrelation of at most 1 (radar/sonar waveforms).",
        evidence=[
            f"Welch array order 10: {result.detail}",
            "adds the application-facing property to our existing Costas generator.",
        ],
    )


def finding_homomorphic_lut() -> ExtensionFinding:
    """Sec 2: TFHE programmable bootstrapping and the negacyclic boundary."""
    demo = programmable_bootstrap_demo(8)
    sample = demo.rows[8]  # first input in the negated upper half
    return ExtensionFinding(
        name="Homomorphic LUT via negacyclic blind rotation (TFHE)",
        section="2 (homomorphic lookup tables)",
        relation="NEW",
        summary="A LUT evaluated by rotating a test polynomial in Z[X]/(X^N+1); "
                "exact only inside [0,N) -- a padding bit enforces the boundary.",
        evidence=[
            f"without padding, exact over full domain: {demo.exact_without_padding} "
            f"(e.g. r={sample[0]} intended {sample[1]} but read {sample[2]} -- sign-flipped)",
            f"with a padding bit confining r to [0,N): exact = {demo.exact_with_padding}",
            "the negacyclic sign-flip is another structural 'fundamental limit'.",
        ],
    )


EXTENSION_BUILDERS = [
    finding_equivalent_inverse_generators,
    finding_ring_permutation_polynomials,
    finding_mba_obfuscation,
    finding_homomorphic_lut,
    finding_distance_increasing_mapping,
    finding_costas_autocorrelation,
    finding_tabulation_independence,
    finding_zech_cyclotomic_compression,
]


def run_survey_extensions() -> List[ExtensionFinding]:
    return [build() for build in EXTENSION_BUILDERS]
