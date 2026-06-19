"""Combining combinatorial generators into higher-purpose structures.

The combinatorial family is special: several of its members are *already*
combinations of simpler ones, which is exactly the phenomenon the request is
about.

  * Two orthogonal Latin squares superimpose into a Graeco-Latin (Euler)
    square -- new purpose: pairing two sets of treatments without repeats
    (tournament scheduling, fractional designs).
  * k mutually orthogonal Latin squares (MOLS) stack into an orthogonal array
    of strength 2 -- so the OA generator in `generators/combinatorial.py` is
    itself a *combination* of Latin-square generators.
  * A difference set "developed" under the cyclic group (combining the set with
    the group action) yields a symmetric 2-design; the Paley (7,3,1) set
    develops into the Fano plane.
"""

from __future__ import annotations

from typing import List

from .core import Family, Table


def mols(n: int) -> List[List[List[int]]]:
    """The n-1 mutually orthogonal Latin squares of prime order n.

    L_a[r][c] = (a*r + c) mod n for a = 1..n-1.  Any two are orthogonal because
    a != b makes (a-b) invertible mod the prime n.
    """
    return [[[(a * r + c) % n for c in range(n)] for r in range(n)]
            for a in range(1, n)]


def build_graeco_latin(n: int = 5) -> Table:
    """Superimpose two orthogonal Latin squares into a Graeco-Latin square."""
    squares = mols(n)
    a_sq, b_sq = squares[0], squares[1]
    return Table(
        name=f"Graeco-Latin square (order {n})",
        family=Family.COMBINATORIAL,
        generator="Graeco-Latin (2 MOLS)",
        notes="two orthogonal Latin squares; all n^2 symbol pairs occur once.",
        meta={"graeco": (a_sq, b_sq)},
    )


def build_mols_orthogonal_array(n: int = 5, k: int = 3) -> Table:
    """Stack k MOLS (plus row/col indices) into an OA(n^2, k+2, n, 2)."""
    squares = mols(n)
    k = min(k, len(squares))
    rows: List[List[int]] = []
    for r in range(n):
        for c in range(n):
            rows.append([r, c] + [squares[i][r][c] for i in range(k)])
    return Table(
        name=f"OA from {k} MOLS (order {n})",
        family=Family.COMBINATORIAL,
        generator="MOLS -> orthogonal array",
        notes=f"OA({n * n}, {k + 2}, {n}, 2) assembled from {k} orthogonal Latin squares.",
        meta={"oa": {"rows": rows, "levels": n, "strength": 2}},
    )


def build_difference_set_design(p: int = 7) -> Table:
    """Develop a Paley difference set into a symmetric 2-design.

    Blocks are the translates D, D+1, ..., D+(p-1) of the quadratic-residue
    difference set D mod p.  For p=7 this is the 2-(7,3,1) design -- the Fano
    plane, the projective plane of order 2.
    """
    residues = sorted({(x * x) % p for x in range(1, p)})  # the difference set D
    blocks = [frozenset((d + i) % p for d in residues) for i in range(p)]
    name = f"2-design from difference set (mod {p})"
    if p == 7:
        name += "  [= Fano plane]"
    return Table(
        name=name,
        family=Family.COMBINATORIAL,
        generator="difference set -> 2-design",
        notes="cyclic translates of a difference set form a symmetric 2-design.",
        meta={"design": {"blocks": blocks, "points": p, "base": residues}},
    )
