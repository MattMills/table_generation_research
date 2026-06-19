"""Transform-coefficient generators: roots of unity / orthogonality constraints.

Tables precomputed so a transform becomes a fixed pattern of multiply-adds:
FFT twiddle factors, Walsh-Hadamard and DCT matrices, and the number-theoretic
transform (an FFT moved into a prime field to dodge floating-point error).
"""

from __future__ import annotations

import cmath
import math
from typing import List

from ..core import Family, FamilySize, Generator, Table


def build_fft_twiddles(n: int = 8) -> Table:
    """Complex Nth roots of unity: w_k = exp(-2*pi*i*k/n)."""
    coeffs = [cmath.exp(-2j * math.pi * k / n) for k in range(n)]
    return Table(
        name=f"FFT twiddle factors (N={n})",
        family=Family.TRANSFORM,
        generator="FFT twiddles",
        notes="precomputed roots of unity for butterfly multiply-adds.",
        meta={"complex": coeffs},
    )


def build_walsh_hadamard(order_bits: int = 3) -> Table:
    """Sylvester-Hadamard matrix H_{2^k}: recursive +-1 orthogonal matrix."""
    n = 1 << order_bits
    matrix = [[1]]
    while len(matrix) < n:
        size = len(matrix)
        new = [[0] * (2 * size) for _ in range(2 * size)]
        for i in range(size):
            for j in range(size):
                v = matrix[i][j]
                new[i][j] = v
                new[i][j + size] = v
                new[i + size][j] = v
                new[i + size][j + size] = -v
        matrix = new
    return Table(
        name=f"Walsh-Hadamard H_{n}",
        family=Family.TRANSFORM,
        generator="Walsh-Hadamard",
        notes="recursive +-1 matrix; rows mutually orthogonal.",
        meta={"matrix": matrix},
    )


def build_dct_matrix(n: int = 8) -> Table:
    """Orthonormal DCT-II matrix (the JPEG cosine basis)."""
    matrix: List[List[float]] = []
    for k in range(n):
        scale = math.sqrt(1.0 / n) if k == 0 else math.sqrt(2.0 / n)
        row = [scale * math.cos(math.pi * (2 * i + 1) * k / (2 * n)) for i in range(n)]
        matrix.append(row)
    return Table(
        name=f"DCT-II matrix (N={n})",
        family=Family.TRANSFORM,
        generator="DCT",
        notes="cosine basis used by JPEG; rows orthonormal.",
        meta={"matrix": matrix},
    )


def build_ntt_table() -> Table:
    """Number-theoretic transform roots: powers of a primitive root mod p.

    p=257 (a Fermat prime) has 256 | p-1, and 3 is a primitive root, so the
    powers of 3 give an exact, floating-point-free FFT analogue.
    """
    p, order, root = 257, 256, 3
    powers = [pow(root, k, p) for k in range(order)]
    return Table(
        name="NTT roots (p=257)",
        family=Family.TRANSFORM,
        generator="NTT",
        data=powers,
        notes="powers of a primitive 256th root of unity mod 257.",
        meta={"ntt": {"modulus": p, "order": order, "root": root}},
    )


GENERATORS = [
    Generator(
        name="FFT twiddles",
        family=Family.TRANSFORM,
        description="Precomputed complex roots of unity for FFT butterflies.",
        build=build_fft_twiddles,
        guarantees=["complex-root-of-unity"],
        constructive=True,
        family_size=FamilySize.UNIQUE,
    ),
    Generator(
        name="Walsh-Hadamard",
        family=Family.TRANSFORM,
        description="Recursive orthogonal +-1 matrix.",
        build=build_walsh_hadamard,
        guarantees=["orthogonal"],
        constructive=True,
        family_size=FamilySize.UNIQUE,
    ),
    Generator(
        name="DCT",
        family=Family.TRANSFORM,
        description="Cosine transform coefficient matrix.",
        build=build_dct_matrix,
        guarantees=["orthogonal"],
        constructive=True,
        family_size=FamilySize.UNIQUE,
    ),
    Generator(
        name="NTT",
        family=Family.TRANSFORM,
        description="FFT in a prime field: powers of a primitive root of unity.",
        build=build_ntt_table,
        guarantees=["root-of-unity"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
    ),
]
