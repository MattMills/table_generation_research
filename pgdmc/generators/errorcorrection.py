"""Error-detection/correction generators: distance properties produce the table.

CRC tables (the conversation's opening example) and syndrome decoding tables.
The CRC byte table is the sharpest illustration of the whole thesis: it is the
*same shape* of artifact as the AES S-box -- a 256-entry byte permutation -- but
its property profile is the polar opposite (perfectly linear, useless for
crypto, ideal for cheap linear checksums).
"""

from __future__ import annotations

from typing import List

from ..core import Family, FamilySize, Generator, Table


def build_crc_table(poly: int = 0x07, width: int = 8) -> Table:
    """CRC lookup table: table[b] = remainder of feeding byte b through `poly`.

    For a degree-`width` polynomial with nonzero constant term this is a
    GF(2)-linear bijection on bytes -- hence bijective, but nonlinearity 0.
    """
    mask = (1 << width) - 1
    top = 1 << (width - 1)
    table: List[int] = []
    for b in range(256):
        crc = b & mask
        for _ in range(8):
            crc = ((crc << 1) ^ poly) & mask if (crc & top) else (crc << 1) & mask
        table.append(crc)
    return Table(
        name=f"CRC-{width} table (poly {hex(poly)})",
        family=Family.ERROR_CORRECTION,
        generator="CRC table",
        data=table,
        domain_bits=8,
        codomain_bits=width,
        notes="byte-at-a-time checksum table; a *linear* bijection.",
    )


# Systematic Hamming(7,4) parity-check matrix H (3 rows x 7 columns).
# Column i (1-indexed) is the syndrome produced by a single error at position i.
_H = [
    [1, 1, 0, 1, 1, 0, 0],
    [1, 0, 1, 1, 0, 1, 0],
    [0, 1, 1, 1, 0, 0, 1],
]


def build_hamming_syndrome() -> Table:
    """Hamming(7,4) syndrome table: syndrome -> error position (0 = none).

    A perfect code, so the map syndrome <-> single-error position is a
    bijection on the 8 syndrome values -- distance properties yielding a clean
    reversible decode table.
    """
    data = [0] * 8  # syndrome 0 -> no error
    for pos in range(1, 8):
        syndrome = (_H[0][pos - 1] << 2) | (_H[1][pos - 1] << 1) | _H[2][pos - 1]
        data[syndrome] = pos
    return Table(
        name="Hamming(7,4) syndrome table",
        family=Family.ERROR_CORRECTION,
        generator="syndrome table",
        data=data,
        domain_bits=3,
        codomain_bits=3,
        notes="maps each syndrome to the bit position to flip; a bijection.",
    )


GENERATORS = [
    Generator(
        name="CRC table",
        family=Family.ERROR_CORRECTION,
        description="Polynomial-division table for byte-at-a-time checksums.",
        build=build_crc_table,
        guarantees=["bijective"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
    ),
    Generator(
        name="syndrome table",
        family=Family.ERROR_CORRECTION,
        description="Maps error syndromes to corrections for a linear code.",
        build=build_hamming_syndrome,
        guarantees=["bijective"],
        constructive=True,
        family_size=FamilySize.UNIQUE,
    ),
]
