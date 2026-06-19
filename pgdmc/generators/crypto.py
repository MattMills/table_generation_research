"""Cryptographic generators: security constraints produce the table.

Here the *spec* is the property -- non-linearity, low differential
uniformity, resistance to linear/differential cryptanalysis -- and the
construction is judged by it.  Two contrasting methodologies appear: the AES
S-box is constructive (algebra + affine), while the DES S-boxes were found by
search against (partly classified) criteria.
"""

from __future__ import annotations

from ..core import Family, FamilySize, Generator, Table
from ..gf import AES_DEGREE, AES_GENERATOR, AES_MODULUS, build_exp_log, gf_inverse_via_tables
from ..bitmath import dot_gf2


def _rotl8(x: int, r: int) -> int:
    return ((x << r) | (x >> (8 - r))) & 0xFF


def build_aes_sbox() -> Table:
    """AES S-box: GF(2^8) inverse followed by an affine transform.

    Filed under cryptography by *purpose*, though its machinery is the same
    field inverse that appears in `algebraic.py`.  The affine layer leaves
    nonlinearity and differential uniformity untouched while removing fixed
    points and algebraic simplicity.
    """
    exp, log = build_exp_log(AES_GENERATOR, AES_MODULUS, AES_DEGREE)
    data = []
    for x in range(256):
        inv = gf_inverse_via_tables(x, exp, log, AES_DEGREE)
        s = inv ^ _rotl8(inv, 1) ^ _rotl8(inv, 2) ^ _rotl8(inv, 3) ^ _rotl8(inv, 4) ^ 0x63
        data.append(s)
    return Table(
        name="AES S-box",
        family=Family.CRYPTOGRAPHIC,
        generator="AES S-box",
        data=data,
        domain_bits=8,
        codomain_bits=8,
        notes="GF(2^8) inverse + affine; nonlinearity 112, diff. uniformity 4.",
    )


def build_bent_function(n: int = 6) -> Table:
    """Maiorana-McFarland bent function f(a,b) = a . b (maximal nonlinearity).

    A bent function is as far from every affine function as possible; its
    Walsh spectrum is perfectly flat at +-2^(n/2).  Represented as a single-bit
    output map so the nonlinearity verifier can confirm the extremal value.
    """
    half = n // 2
    data = []
    for x in range(1 << n):
        a = x >> half
        b = x & ((1 << half) - 1)
        data.append(dot_gf2(a, b))
    return Table(
        name=f"bent function (n={n})",
        family=Family.CRYPTOGRAPHIC,
        generator="bent function",
        data=data,
        domain_bits=n,
        codomain_bits=1,
        notes="Maiorana-McFarland a.b; flat Walsh spectrum, max nonlinearity.",
    )


# The real DES S1 substitution box (FIPS 46-3), as four rows of sixteen.
_DES_S1 = [
    [14, 4, 13, 1, 2, 15, 11, 8, 3, 10, 6, 12, 5, 9, 0, 7],
    [0, 15, 7, 4, 14, 2, 13, 1, 10, 6, 12, 11, 9, 5, 3, 8],
    [4, 1, 14, 8, 13, 6, 2, 11, 15, 12, 9, 7, 3, 10, 5, 0],
    [15, 12, 8, 2, 4, 9, 1, 7, 5, 11, 3, 14, 10, 0, 6, 13],
]


def build_des_sbox() -> Table:
    """DES S-box S1: a 6->4 table designed (partly by classified search).

    Input bits b0..b5; the outer bits (b0,b5) select the row and the middle
    four bits select the column.  This is the canonical *search-found* table,
    in contrast to the AES S-box's algebraic recipe.
    """
    data = []
    for x in range(64):
        row = ((x >> 5) & 1) << 1 | (x & 1)
        col = (x >> 1) & 0xF
        data.append(_DES_S1[row][col])
    return Table(
        name="DES S-box S1",
        family=Family.CRYPTOGRAPHIC,
        generator="DES S-box",
        data=data,
        domain_bits=6,
        codomain_bits=4,
        notes="6->4 substitution; found by search against cryptanalytic criteria.",
    )


GENERATORS = [
    Generator(
        name="AES S-box",
        family=Family.CRYPTOGRAPHIC,
        description="GF inverse + affine transform with proven nonlinearity.",
        build=build_aes_sbox,
        guarantees=["bijective", "nonlinearity", "differential-uniformity"],
        constructive=True,
        family_size=FamilySize.UNIQUE,
    ),
    Generator(
        name="bent function",
        family=Family.CRYPTOGRAPHIC,
        description="Maximally nonlinear boolean function (flat Walsh spectrum).",
        build=build_bent_function,
        guarantees=["nonlinearity"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
    ),
    Generator(
        name="DES S-box",
        family=Family.CRYPTOGRAPHIC,
        description="Hand/search-designed 6->4 box resisting differential attacks.",
        build=build_des_sbox,
        guarantees=["nonlinearity", "differential-uniformity"],
        constructive=False,  # found by search, not a closed-form recipe
        family_size=FamilySize.UNIQUE,
    ),
]
