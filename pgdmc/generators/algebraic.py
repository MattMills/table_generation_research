"""Algebraic generators: polynomial machinery produces the table.

The GF family from the conversation.  Run finite-field arithmetic once, get a
table, then do "real" work with cheap lookups.  Note where the *same* GF
inverse shows up here (as a raw reversible map) and in `crypto.py` (wrapped in
an affine layer to become the AES S-box) -- that duplication is the point: the
artifact is filed by ancestry here and by purpose there.
"""

from __future__ import annotations

from typing import List

from ..core import Family, FamilySize, Generator, Table
from ..gf import (
    AES_DEGREE,
    AES_GENERATOR,
    AES_MODULUS,
    build_exp_log,
    gf_inverse_via_tables,
    gf_pow,
)

# A small GF(2^4) field for compact, inspectable nonlinear bijections.
GF16_MODULUS = 0x13  # x^4 + x + 1
GF16_DEGREE = 4


def build_gf_log_antilog() -> Table:
    """Antilog (and implicit log) table for GF(2^8): reversible multiplication."""
    exp, log = build_exp_log(AES_GENERATOR, AES_MODULUS, AES_DEGREE)
    antilog = exp[: (1 << AES_DEGREE) - 1]  # exp[0..254] = every nonzero element once
    return Table(
        name="GF(2^8) log/antilog",
        family=Family.ALGEBRAIC,
        generator="GF log/antilog",
        data=antilog,
        notes="antilog[i]=g^i; multiplication becomes add-logs-then-antilog.",
        meta={"cover": ("nonzero", AES_DEGREE), "log": log},
    )


def build_zech_logarithm() -> Table:
    """Zech logarithm table: lets you *add* in log representation.

    Z[i] is defined by 1 + g^i = g^(Z[i]).  Same GF lineage as log/antilog,
    solving the otherwise-awkward addition step when you live in log space.
    """
    exp, log = build_exp_log(AES_GENERATOR, AES_MODULUS, AES_DEGREE)
    order = (1 << AES_DEGREE) - 1
    zech: List[int] = []
    for i in range(order):
        s = 1 ^ exp[i]  # 1 + g^i in the field (addition is XOR)
        zech.append(log[s] if s != 0 else -1)  # -1: result is 0 (log undefined)
    return Table(
        name="GF(2^8) Zech logarithm",
        family=Family.ALGEBRAIC,
        generator="Zech logarithm",
        data=zech,
        notes="Z[i] s.t. 1+g^i=g^Z[i]; -1 marks the additive-zero case.",
        meta={"zech": {"modulus": order, "char": 2}},
    )


def build_gf_inverse() -> Table:
    """The raw multiplicative-inverse map on GF(2^8) (0 -> 0).

    Bijective, an involution, and -- before any affine wrapper -- already
    carries the nonlinearity and differential-uniformity that the AES S-box is
    famous for.  Surfacing it here lets the matrix show those properties are
    inherited from the field inverse, not from the affine step.
    """
    exp, log = build_exp_log(AES_GENERATOR, AES_MODULUS, AES_DEGREE)
    data = [gf_inverse_via_tables(x, exp, log, AES_DEGREE) for x in range(1 << AES_DEGREE)]
    return Table(
        name="GF(2^8) inverse map",
        family=Family.ALGEBRAIC,
        generator="GF inverse",
        data=data,
        domain_bits=AES_DEGREE,
        codomain_bits=AES_DEGREE,
        notes="x -> x^-1 with 0->0; an involution with AES-grade NL/DU.",
    )


def build_permutation_polynomial(degree: int = 7) -> Table:
    """A monomial permutation x -> x^degree over GF(2^4).

    x^d permutes the field iff gcd(d, 2^n-1)=1.  For GF(2^4), gcd(7,15)=1, so
    x^7 is a compact nonlinear bijection -- a baby S-box from pure algebra.
    """
    data = [gf_pow(x, degree, GF16_MODULUS, GF16_DEGREE) for x in range(1 << GF16_DEGREE)]
    return Table(
        name=f"GF(2^4) x^{degree} permutation",
        family=Family.ALGEBRAIC,
        generator="permutation polynomial",
        data=data,
        domain_bits=GF16_DEGREE,
        codomain_bits=GF16_DEGREE,
        notes=f"monomial x^{degree}; bijective since gcd({degree}, 15)=1.",
    )


GENERATORS = [
    Generator(
        name="GF log/antilog",
        family=Family.ALGEBRAIC,
        description="Antilog/log tables turning field multiplication into addition.",
        build=build_gf_log_antilog,
        guarantees=["full-cover"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,  # choice of field + generator
        references="Standard in Reed-Solomon / DSP implementations.",
    ),
    Generator(
        name="Zech logarithm",
        family=Family.ALGEBRAIC,
        description="Table enabling addition while staying in log representation.",
        build=build_zech_logarithm,
        guarantees=["cyclotomic-compressible"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
    ),
    Generator(
        name="GF inverse",
        family=Family.ALGEBRAIC,
        description="Multiplicative inverse map; nonlinear, reversible.",
        build=build_gf_inverse,
        guarantees=["bijective", "involution"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
    ),
    Generator(
        name="permutation polynomial",
        family=Family.ALGEBRAIC,
        description="Monomial/permutation polynomial giving a bijective mapping.",
        build=build_permutation_polynomial,
        guarantees=["bijective"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
    ),
]
