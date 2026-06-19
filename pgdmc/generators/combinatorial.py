"""Combinatorial / constraint-satisfaction generators: the table *is* a solution.

The artifact is a configuration satisfying a balance or distinctness
constraint: Latin squares, Costas arrays, perfect difference sets, orthogonal
arrays.  These sit closest to "the table is the answer to a constraint
problem" -- the framing the conversation lands on for the whole field.
"""

from __future__ import annotations

from typing import List

from ..core import Family, FamilySize, Generator, Table


def build_cyclic_latin_square(n: int = 7) -> Table:
    """Cyclic Latin square L[r][c] = (r+c) mod n."""
    square = [[(r + c) % n for c in range(n)] for r in range(n)]
    return Table(
        name=f"cyclic Latin square (order {n})",
        family=Family.COMBINATORIAL,
        generator="Latin square",
        notes="each symbol once per row and column; rows are the +k shifts.",
        meta={"square": square},
    )


def build_costas_array(p: int = 11, g: int = 2) -> Table:
    """Welch-construction Costas array of order p-1.

    positions[i] = g^(i+1) mod p - 1, a permutation whose displacement
    vectors are all distinct (the property sonar/radar waveforms rely on).
    """
    positions: List[int] = []
    val = 1
    for _ in range(p - 1):
        val = (val * g) % p
        positions.append(val - 1)
    return Table(
        name=f"Costas array (order {p - 1})",
        family=Family.COMBINATORIAL,
        generator="Costas array",
        notes=f"Welch construction from primitive root {g} mod {p}.",
        meta={"costas": positions},
    )


def build_difference_set(p: int = 7) -> Table:
    """Paley difference set: quadratic residues mod a prime p = 3 (mod 4).

    Yields a (p, (p-1)/2, (p-3)/4) perfect difference set -- every nonzero
    residue occurs equally often among member differences.
    """
    residues = sorted({(x * x) % p for x in range(1, p)})
    return Table(
        name=f"Paley difference set (mod {p})",
        family=Family.COMBINATORIAL,
        generator="difference set",
        data=residues,
        notes="quadratic residues; uniform difference multiset.",
        meta={"diff_set": residues, "modulus": p},
    )


def build_orthogonal_array(p: int = 3) -> Table:
    """Orthogonal array OA(p^2, p+1, p, 2) from linear functions over GF(p).

    Each row is (x, y, y+x, y+2x, ..., y+(p-1)x) mod p; any two columns show
    every ordered level pair exactly once (strength 2) -- the balance that
    fractional-factorial experiment designs exploit.
    """
    rows: List[List[int]] = []
    for x in range(p):
        for y in range(p):
            row = [x] + [(y + i * x) % p for i in range(p)]
            rows.append(row)
    return Table(
        name=f"orthogonal array OA({p * p}, {p + 1}, {p}, 2)",
        family=Family.COMBINATORIAL,
        generator="orthogonal array",
        notes="strength-2 array: every column pair balanced over level pairs.",
        meta={"oa": {"rows": rows, "levels": p, "strength": 2}},
    )


GENERATORS = [
    Generator(
        name="Latin square",
        family=Family.COMBINATORIAL,
        description="Square where every symbol appears once per row and column.",
        build=build_cyclic_latin_square,
        guarantees=["latin-square"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
    ),
    Generator(
        name="Costas array",
        family=Family.COMBINATORIAL,
        description="Permutation with all-distinct displacement vectors.",
        build=build_costas_array,
        guarantees=["costas"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
    ),
    Generator(
        name="difference set",
        family=Family.COMBINATORIAL,
        description="Set whose pairwise differences hit each residue equally.",
        build=build_difference_set,
        guarantees=["uniform-differences"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
    ),
    Generator(
        name="orthogonal array",
        family=Family.COMBINATORIAL,
        description="Array balanced over every choice of t columns.",
        build=build_orthogonal_array,
        guarantees=["orthogonal-array"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
    ),
]
