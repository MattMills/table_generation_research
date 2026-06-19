"""Hash / distribution generators: statistical uniformity produces the table.

The odd family out on the axes the conversation drew: these are *random
ensembles* whose guarantees are *statistical*, not exact.  Zobrist and
tabulation hashing fill a table with random words and rely on independence
properties that hold with overwhelming probability rather than by
construction.  Seeded for reproducibility.
"""

from __future__ import annotations

import random
from typing import List

from ..core import Family, FamilySize, Generator, Table

_WORD_BITS = 32


def build_zobrist(squares: int = 64, pieces: int = 12, seed: int = 1234) -> Table:
    """Zobrist keys: a random word per (square, piece); positions hash by XOR.

    The runtime trick is incremental: moving a piece is two XORs.  The
    guarantee -- near-uniform, low-collision hashing -- is probabilistic, which
    is exactly what distinguishes this family from the algebraic ones.
    """
    rng = random.Random(seed)
    keys: List[int] = [rng.getrandbits(_WORD_BITS) for _ in range(squares * pieces)]
    return Table(
        name="Zobrist hash keys",
        family=Family.HASHING,
        generator="Zobrist hashing",
        data=keys,
        notes=f"{squares}x{pieces} random {_WORD_BITS}-bit keys; XOR-combined.",
        meta={"ensemble": keys, "ensemble_bits": _WORD_BITS},
    )


def build_tabulation(blocks: int = 4, seed: int = 99) -> Table:
    """Tabulation hashing tables: one random table per input byte.

    hash(x) = XOR over byte-blocks of T_block[byte].  Provably 3-independent,
    yet only lookups and XORs at runtime.  We expose the concatenated tables as
    the ensemble; full independence is asserted by theory, not enumerated here.
    """
    rng = random.Random(seed)
    tables = [[rng.getrandbits(_WORD_BITS) for _ in range(256)] for _ in range(blocks)]
    flat = [v for tbl in tables for v in tbl]
    return Table(
        name="tabulation hashing tables",
        family=Family.HASHING,
        generator="tabulation hashing",
        data=flat,
        notes=f"{blocks} x 256 random words; XOR of per-byte lookups (3-independent).",
        meta={"ensemble": flat, "ensemble_bits": _WORD_BITS, "blocks": tables},
    )


def tabulation_4independence_failure(seed: int = 7):
    """Demonstrate why simple tabulation hashing is 3- but not 4-independent.

    Four keys forming a "rectangle" -- (a,c),(a,d),(b,c),(b,d) in two byte
    positions -- always satisfy h(w) XOR h(x) XOR h(y) XOR h(z) = 0, because
    each table entry appears an even number of times and cancels.  This is the
    exact structural limit noted in the survey (Patrascu-Thorup).
    """
    rng = random.Random(seed)
    t0 = [rng.getrandbits(_WORD_BITS) for _ in range(256)]
    t1 = [rng.getrandbits(_WORD_BITS) for _ in range(256)]

    def h(lo: int, hi: int) -> int:
        return t0[lo] ^ t1[hi]

    a, b, c, d = 0x11, 0x22, 0x33, 0x44
    w, x, y, z = h(a, c), h(a, d), h(b, c), h(b, d)
    return {
        "keys": [(a, c), (a, d), (b, c), (b, d)],
        "xor": w ^ x ^ y ^ z,
        "cancels_to_zero": (w ^ x ^ y ^ z) == 0,
    }


GENERATORS = [
    Generator(
        name="Zobrist hashing",
        family=Family.HASHING,
        description="Random per-feature keys combined by XOR for incremental hashing.",
        build=build_zobrist,
        guarantees=["distinct-keys", "bit-balance"],
        constructive=False,  # drawn from randomness, not computed from a recipe
        family_size=FamilySize.RANDOM,
    ),
    Generator(
        name="tabulation hashing",
        family=Family.HASHING,
        description="Random byte tables giving provable k-independence via lookups+XOR.",
        build=build_tabulation,
        guarantees=["distinct-keys", "bit-balance"],
        constructive=False,
        family_size=FamilySize.RANDOM,
    ),
]
