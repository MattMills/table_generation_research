"""Permutation polynomials over the ring Z/2^w (machine-word arithmetic).

From the survey, section 3: unlike finite *fields*, polynomials over the ring
Z/2^w obey the Rivest-Black characterization -- P is a permutation iff a1 is
odd and the even- and odd-indexed higher coefficient sums are both even.  This
gives bijective, word-sized scrambling tables with no field machinery, which is
exactly why RC6 uses x(2x+1) mod 2^32.

Also here: Mixed Boolean-Arithmetic (MBA) null identities and a pair of inverse
permutation polynomials used for obfuscation -- an encode/decode combination
whose round-trip is the identity.
"""

from __future__ import annotations

from typing import List

from ..core import Family, FamilySize, Generator, Table


def permutation_polynomial_mod_2w(coeffs: List[int], w: int = 8) -> Table:
    """Build the table of P(x) = sum a_i x^i over Z/2^w (w small enough to tabulate)."""
    m = 1 << w
    data = [sum(c * pow(x, i, m) for i, c in enumerate(coeffs)) % m for x in range(m)]
    return Table(
        name=f"Z/2^{w} perm. poly {coeffs}",
        family=Family.ALGEBRAIC,
        generator="ring permutation polynomial",
        data=data,
        domain_bits=w,
        codomain_bits=w,
        notes="Rivest-Black: permutation iff a1 odd and higher even/odd coeff sums even.",
        meta={"pp_mod": {"coeffs": coeffs, "w": w}},
    )


def build_rc6_mixing(w: int = 8) -> Table:
    """RC6's mixing map x(2x+1) = 2x^2 + x, tabulated over Z/2^w.

    RC6 uses w=32; we tabulate a small w so the whole bijection is inspectable.
    """
    table = permutation_polynomial_mod_2w([0, 1, 2], w)
    table.name = f"RC6 mixing x(2x+1) mod 2^{w}"
    table.generator = "RC6 mixing"
    table.notes = "x(2x+1): trivially satisfies Rivest-Black; used in RC6 at w=32."
    return table


# --- Mixed Boolean-Arithmetic obfuscation (section 3.2) ----------------------

def mba_null(x: int, y: int, w: int = 8) -> int:
    """An MBA expression that is identically zero over Z/2^w."""
    m = (1 << w) - 1
    return (x - y + 2 * ((~x & y) & m) - (x ^ y)) % (1 << w)


def obfuscation_inverse_pair(w: int = 8):
    """Return (encode, decode) inverse permutation polynomials over Z/2^w.

    P(x) = 248 x^2 + 97 x and Q(x) = 136 x^2 + 161 x are mutual inverses mod 256;
    wrapping a value as Q(.)/P(.) is a semantics-preserving obfuscation.
    """
    m = 1 << w

    def encode(x: int) -> int:
        return (248 * x * x + 97 * x) % m

    def decode(x: int) -> int:
        return (136 * x * x + 161 * x) % m

    return encode, decode


GENERATORS = [
    Generator(
        name="RC6 mixing",
        family=Family.ALGEBRAIC,
        description="Ring permutation polynomial x(2x+1) mod 2^w (RC6's diffusion).",
        build=build_rc6_mixing,
        guarantees=["bijective", "rivest-black"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
        references="Rivest, Robshaw, Sidney, Yin -- RC6; Rivest -- permutations mod 2^w.",
    ),
]
