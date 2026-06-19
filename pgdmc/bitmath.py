"""Low-level bit and boolean-function math shared across property checks.

Everything here operates on plain Python ints and lists so the whole project
stays dependency-free. The functions are the workhorses behind the property
verifiers: Walsh-Hadamard spectra (for linearity / correlation), the Mobius
transform (for algebraic normal form / degree), and assorted bit utilities.
"""

from __future__ import annotations

from typing import List


def popcount(x: int) -> int:
    """Number of set bits (Hamming weight)."""
    return bin(x).count("1")


def dot_gf2(a: int, b: int) -> int:
    """Inner product of two bit-vectors over GF(2): parity of (a AND b)."""
    return popcount(a & b) & 1


def hamming_distance(a: int, b: int) -> int:
    """Hamming distance between two integers viewed as bit-vectors."""
    return popcount(a ^ b)


def component_function(sbox: List[int], mask: int, n: int) -> List[int]:
    """Truth table of the boolean function x -> (mask . S(x)) over GF(2).

    `mask` selects a linear combination of output bits.  This is how a
    vectorial map (S-box) is decomposed into the boolean "component functions"
    that linearity / correlation properties are really defined on.
    """
    return [dot_gf2(mask, sbox[x]) for x in range(1 << n)]


def fast_walsh_hadamard(values: List[int]) -> List[int]:
    """In-place-style fast Walsh-Hadamard transform on a length-2^n list.

    Returns a new list W where, if `values[x] = (-1)**f(x)` for a boolean
    function f, then ``W[a] = sum_x (-1)**(f(x) XOR a.x)``.  These are the
    Walsh coefficients; |W[a]| measures correlation of f with the linear
    function a.x.
    """
    w = list(values)
    length = len(w)
    h = 1
    while h < length:
        for i in range(0, length, h * 2):
            for j in range(i, i + h):
                a, b = w[j], w[j + h]
                w[j] = a + b
                w[j + h] = a - b
        h *= 2
    return w


def walsh_spectrum(truth_table: List[int]) -> List[int]:
    """Walsh spectrum of a boolean function given as a 0/1 truth table."""
    signed = [1 - 2 * bit for bit in truth_table]  # 0 -> +1, 1 -> -1
    return fast_walsh_hadamard(signed)


def mobius_transform(truth_table: List[int]) -> List[int]:
    """Binary Mobius transform: truth table -> algebraic normal form coeffs.

    Returns the ANF coefficient vector ``a`` where
    ``f(x) = XOR over u ( a[u] * prod_{i in u} x_i )``.
    """
    anf = list(truth_table)
    length = len(anf)
    h = 1
    while h < length:
        for i in range(0, length, h * 2):
            for j in range(i, i + h):
                anf[j + h] ^= anf[j]
        h *= 2
    return anf


def algebraic_degree(truth_table: List[int]) -> int:
    """Algebraic degree of a boolean function (max monomial degree in its ANF)."""
    anf = mobius_transform(truth_table)
    return max((popcount(u) for u in range(len(anf)) if anf[u]), default=0)


def is_power_of_two(x: int) -> bool:
    return x > 0 and (x & (x - 1)) == 0


def bits_for(n_values: int) -> int | None:
    """If n_values is a power of two return its log2, else None.

    Used to decide whether a table's size corresponds to a clean bit-width
    (and therefore whether bit-oriented properties even make sense for it).
    """
    if is_power_of_two(n_values):
        return n_values.bit_length() - 1
    return None
