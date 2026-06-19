"""Combinators: build a new table by combining two (or more) generators.

This is the operational core of the conversation's claim that reframing
"surfaces new methods". The famous tables were *already* combinations -- the AES
S-box is the GF inverse composed with an affine map -- so a small algebra of
combinators (compose, XOR, direct-sum, whiten, Feistel) both reproduces known
constructions and manufactures new ones.

The interesting output is a *property algebra of combination*: which guarantees
survive a combinator, which are created, and which are destroyed. Examples the
code verifies live:

  * Feistel CREATES bijectivity from an arbitrary (even lossy) function.
  * compose(affine, nonlinear) PRESERVES nonlinearity (-> reproduces AES).
  * compose(x^7, x^7) over GF(2^4) DESTROYS it (the result is the linear x^4).
  * XOR-combining two bijections DESTROYS the permutation property.
  * direct-sum widens a table cheaply but keeps the weak (decomposable) profile.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .core import Family, Table
from .gf import AES_DEGREE, AES_GENERATOR, AES_MODULUS, build_exp_log, gf_inverse_via_tables, gf_pow
from .properties import (
    AvalancheMean,
    Bijective,
    DifferentialUniformity,
    Nonlinearity,
)

GF16_MODULUS = 0x13
GF16_DEGREE = 4


def _rotl8(x: int, r: int) -> int:
    return ((x << r) | (x >> (8 - r))) & 0xFF


# --- combinator primitives ---------------------------------------------------

def compose(first: Table, second: Table, name: Optional[str] = None) -> Table:
    """Functional composition (second o first): apply `first`, then `second`."""
    if first.domain_bits != second.domain_bits:
        raise ValueError("compose needs two self-maps of equal width")
    n = first.domain_bits
    data = [second.data[first.data[x]] for x in range(1 << n)]
    return Table(
        name=name or f"({second.generator} o {first.generator})",
        family=Family.COMPOSITE,
        generator="compose",
        data=data,
        domain_bits=n,
        codomain_bits=n,
        notes=f"composition of {first.name} then {second.name}.",
    )


def xor_combine(first: Table, second: Table, name: Optional[str] = None) -> Table:
    """Pointwise XOR of two equal-width maps (generally NOT a bijection)."""
    n = first.domain_bits
    data = [first.data[x] ^ second.data[x] for x in range(1 << n)]
    return Table(
        name=name or f"({first.generator} XOR {second.generator})",
        family=Family.COMPOSITE,
        generator="xor",
        data=data,
        domain_bits=n,
        codomain_bits=max(first.codomain_bits, second.codomain_bits),
        notes=f"pointwise XOR of {first.name} and {second.name}.",
    )


def direct_sum(first: Table, second: Table, name: Optional[str] = None) -> Table:
    """Block-diagonal combination on the concatenated input (n1+n2 bits)."""
    n1, n2 = first.domain_bits, second.domain_bits
    lo_mask = (1 << n2) - 1
    data = []
    for z in range(1 << (n1 + n2)):
        x, y = z >> n2, z & lo_mask
        data.append((first.data[x] << n2) | second.data[y])
    return Table(
        name=name or f"({first.generator} (+) {second.generator})",
        family=Family.COMPOSITE,
        generator="direct-sum",
        data=data,
        domain_bits=n1 + n2,
        codomain_bits=n1 + n2,
        notes=f"independent blocks: {first.name} on high bits, {second.name} on low bits.",
    )


def whiten(table: Table, pre: int, post: int, name: Optional[str] = None) -> Table:
    """Key whitening: x -> table(x XOR pre) XOR post (affine-equivalent)."""
    n = table.domain_bits
    data = [table.data[x ^ pre] ^ post for x in range(1 << n)]
    return Table(
        name=name or f"whiten({table.generator})",
        family=Family.COMPOSITE,
        generator="whiten",
        data=data,
        domain_bits=n,
        codomain_bits=n,
        notes=f"{table.name} with input/output masks {hex(pre)}/{hex(post)}.",
    )


def feistel(round_function: List[int], half_bits: int, rounds: int,
            name: Optional[str] = None) -> Table:
    """Build a bijection on 2*half_bits from ANY function on half_bits.

    The Feistel round (L,R) -> (R, L XOR F(R)) is invertible no matter what F
    is -- so this combinator *creates* the bijection property from a function
    that need not have it.  Three+ rounds give strong mixing (Luby-Rackoff).
    """
    n = half_bits
    mask = (1 << n) - 1
    data = []
    for z in range(1 << (2 * n)):
        left, right = z >> n, z & mask
        for _ in range(rounds):
            left, right = right, left ^ round_function[right & mask]
        data.append((left << n) | right)
    return Table(
        name=name or f"Feistel[{rounds}r] on {2 * n} bits",
        family=Family.COMPOSITE,
        generator="feistel",
        data=data,
        domain_bits=2 * n,
        codomain_bits=2 * n,
        notes=f"{rounds}-round Feistel network from an arbitrary {n}-bit function.",
    )


# --- parent tables used by the example combinations --------------------------

def gf_inverse_table() -> Table:
    exp, log = build_exp_log(AES_GENERATOR, AES_MODULUS, AES_DEGREE)
    data = [gf_inverse_via_tables(x, exp, log, AES_DEGREE) for x in range(256)]
    return Table("GF(2^8) inverse", Family.ALGEBRAIC, "GF inverse", data, 8, 8)


def aes_affine_table() -> Table:
    """The AES affine layer as a standalone bijection (no field inverse)."""
    data = []
    for x in range(256):
        data.append(x ^ _rotl8(x, 1) ^ _rotl8(x, 2) ^ _rotl8(x, 3) ^ _rotl8(x, 4) ^ 0x63)
    return Table("AES affine map", Family.ALGEBRAIC, "AES affine", data, 8, 8,
                 notes="x -> A.x + 0x63; an invertible affine map over GF(2)^8.")


def gf16_power_table(power: int) -> Table:
    data = [gf_pow(x, power, GF16_MODULUS, GF16_DEGREE) for x in range(16)]
    return Table(f"GF(2^4) x^{power}", Family.ALGEBRAIC, f"x^{power}", data, 4, 4)


def _squaring_mod16() -> List[int]:
    """A deliberately NON-bijective 4-bit function (collisions) for Feistel."""
    return [(x * x) % 16 for x in range(16)]


# --- the curated example combinations ----------------------------------------

@dataclass
class Combination:
    """A new table built from existing generators, plus what it is *for*."""

    name: str
    parents: List[str]
    combinator: str
    table: Table
    new_purpose: str
    effect: str  # property created / preserved / destroyed
    metrics: Dict[str, str] = field(default_factory=dict)


def _bit_metrics(table: Table) -> Dict[str, str]:
    """Compact property snapshot for a bit-width self-map."""
    out: Dict[str, str] = {}
    bij = Bijective().evaluate(table)
    out["bijective"] = "Y" if bij.status.value == "PASS" else ("N" if bij.status.value == "FAIL" else "·")
    nl = Nonlinearity().evaluate(table)
    out["NL"] = str(nl.value) if nl.value is not None else "·"
    du = DifferentialUniformity().evaluate(table)
    out["DU"] = str(du.value) if du.value is not None else "·"
    av = AvalancheMean().evaluate(table)
    out["avalanche"] = str(av.value) if av.value is not None else "·"
    return out


def build_combinations() -> List[Combination]:
    """A spread of combinations chosen to exercise the whole property algebra."""
    combos: List[Combination] = []

    # 1. Reproduce a famous table: AES S-box = affine o inverse.
    sbox = compose(gf_inverse_table(), aes_affine_table(), name="AES S-box (= affine o inverse)")
    combos.append(Combination(
        name=sbox.name,
        parents=["GF(2^8) inverse", "AES affine map"],
        combinator="compose",
        table=sbox,
        new_purpose="cipher substitution box: removes fixed points and algebraic simplicity",
        effect="PRESERVES nonlinearity & differential uniformity (affine is free); breaks structure",
        metrics=_bit_metrics(sbox),
    ))

    # 2. CREATE bijectivity from a non-bijective function via Feistel.
    feis = feistel(_squaring_mod16(), half_bits=4, rounds=3,
                   name="Feistel[3r] from squaring-mod-16 (non-bijective)")
    combos.append(Combination(
        name=feis.name,
        parents=["squaring mod 16 (non-bijective 4-bit function)"],
        combinator="feistel",
        table=feis,
        new_purpose="invertible 8-bit mixing/block map from a lossy table",
        effect="CREATES bijectivity (the input function has collisions, the output is a permutation)",
        metrics=_bit_metrics(feis),
    ))

    # 3. DESTROY nonlinearity: x^7 o x^7 = x^49 = x^4 (Frobenius, linear).
    x7 = gf16_power_table(7)
    collapse = compose(x7, x7, name="x^7 o x^7 over GF(2^4)  (= x^4, linear)")
    combos.append(Combination(
        name=collapse.name,
        parents=["GF(2^4) x^7", "GF(2^4) x^7"],
        combinator="compose",
        table=collapse,
        new_purpose="cautionary: composing nonlinear maps need not stay nonlinear",
        effect=f"DESTROYS nonlinearity ({_bit_metrics(x7)['NL']} -> {_bit_metrics(collapse)['NL']}); result is the linear x^4",
        metrics=_bit_metrics(collapse),
    ))

    # 4. Widen cheaply but weakly: direct sum of two 4-bit S-boxes.
    wide = direct_sum(x7, x7, name="x^7 (+) x^7  (8-bit, decomposable)")
    combos.append(Combination(
        name=wide.name,
        parents=["GF(2^4) x^7", "GF(2^4) x^7"],
        combinator="direct-sum",
        table=wide,
        new_purpose="wide bijection computed as two narrow lookups (streaming-decomposable)",
        effect="PRESERVES bijectivity, but differential uniformity degrades multiplicatively "
               "(4 -> 64): no cross-block mixing",
        metrics=_bit_metrics(wide),
    ))

    # 5. DESTROY bijectivity: XOR two bijections.
    from .generators.sequence import build_gray_code
    xored = xor_combine(sbox, build_gray_code(8), name="AES S-box XOR Gray code")
    combos.append(Combination(
        name=xored.name,
        parents=["AES S-box", "8-bit Gray code"],
        combinator="xor",
        table=xored,
        new_purpose="attempted mixing of two permutations",
        effect="DESTROYS bijectivity: the XOR of two permutations is generally not one",
        metrics=_bit_metrics(xored),
    ))

    return combos


def feistel_mixing_progression() -> List[str]:
    """Show diffusion strengthen with Feistel rounds (the Luby-Rackoff intuition).

    Note: the *vectorial* nonlinearity stays 0 by construction -- a Feistel
    swaps halves, so one output block is a linear copy of an input block, which
    is always a linear component.  Avalanche is the honest diffusion signal here.
    """
    f = _squaring_mod16()
    lines = []
    for rounds in (1, 2, 3, 4):
        table = feistel(f, 4, rounds)
        m = _bit_metrics(table)
        lines.append(f"  {rounds} round(s): bijective={m['bijective']}  "
                     f"avalanche={m['avalanche']}  (NL stays {m['NL']}: swap leaves a linear block)")
    return lines


def composition_findings() -> List[str]:
    """The property-algebra summary, computed from live numbers."""
    inv = gf_inverse_table()
    sbox = compose(inv, aes_affine_table())
    x7 = gf16_power_table(7)
    collapse = compose(x7, x7)
    return [
        "PRESERVED  bijection o bijection -> bijection "
        f"(AES S-box bijective={_bit_metrics(sbox)['bijective']}).",
        "FREE       affine o nonlinear keeps nonlinearity "
        f"(inverse NL={_bit_metrics(inv)['NL']} -> S-box NL={_bit_metrics(sbox)['NL']}).",
        "DESTROYED  nonlinear o nonlinear can linearize "
        f"(x^7 NL={_bit_metrics(x7)['NL']} -> x^7ox^7 NL={_bit_metrics(collapse)['NL']}).",
        "CREATED    Feistel makes a bijection from a non-bijective function (see progression).",
        "LOST       XOR of two permutations is generally not a permutation.",
    ]
