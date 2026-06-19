"""Finite-field GF(2^n) arithmetic.

This is the "polynomial machinery" lineage from the conversation: the same
carry-less multiply + reduce that underlies CRC tables, AES S-boxes, and
log/antilog tables.  Keeping it in one place makes the shared ancestry of
those generators literal rather than rhetorical.
"""

from __future__ import annotations

from typing import List, Tuple

# AES / Rijndael field: GF(2^8) with reducing polynomial x^8+x^4+x^3+x+1.
AES_MODULUS = 0x11B
AES_DEGREE = 8
# 0x03 (the polynomial x+1) is a generator of the multiplicative group here.
AES_GENERATOR = 0x03


def gf_mul(a: int, b: int, modulus: int, degree: int) -> int:
    """Multiply two elements of GF(2^degree) modulo `modulus`."""
    result = 0
    high_bit = 1 << degree
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & high_bit:
            a ^= modulus
    return result


def gf_pow(a: int, e: int, modulus: int, degree: int) -> int:
    result = 1
    base = a
    while e:
        if e & 1:
            result = gf_mul(result, base, modulus, degree)
        base = gf_mul(base, base, modulus, degree)
        e >>= 1
    return result


def build_exp_log(generator: int, modulus: int, degree: int) -> Tuple[List[int], List[int]]:
    """Build antilog (exp) and log tables for GF(2^degree)*.

    `exp[i] = generator**i` for i in [0, 2^degree-1); `log[v]` is the inverse.
    These are exactly the tables that turn field multiplication into
    "add the logs, look up the antilog" -- the DSP/coding-theory staple.
    """
    order = (1 << degree) - 1  # size of the multiplicative group
    exp = [0] * (order + 1)
    log = [0] * (1 << degree)
    value = 1
    for i in range(order):
        exp[i] = value
        log[value] = i
        value = gf_mul(value, generator, modulus, degree)
    exp[order] = exp[0]  # convenient wraparound: g^order == 1
    log[0] = -1  # log(0) is undefined; sentinel
    return exp, log


def gf_inverse_via_tables(value: int, exp: List[int], log: List[int], degree: int) -> int:
    """Multiplicative inverse using log/antilog tables (0 maps to 0)."""
    if value == 0:
        return 0
    order = (1 << degree) - 1
    return exp[(order - log[value]) % order]


def is_generator(g: int, modulus: int, degree: int) -> bool:
    """True if g generates the full multiplicative group of GF(2^degree)."""
    order = (1 << degree) - 1
    seen = set()
    value = 1
    for _ in range(order):
        if value in seen:
            return False
        seen.add(value)
        value = gf_mul(value, g, modulus, degree)
    return len(seen) == order
