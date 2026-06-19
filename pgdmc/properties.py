"""Property verifiers: the runtime-checkable guarantees a table may possess.

These are the specs the conversation kept circling: reversibility,
non-linearity, differential uniformity, orthogonality, uniform distribution,
distance / covering properties.  Each is expressed as a `Property` that can be
run against *any* table -- reporting `n/a` when it does not apply.  Running the
broadly-applicable ones against every table is what surfaces the cross-family
relationships ("the CRC table is bijective but perfectly *linear*; the AES
S-box is bijective and maximally *non*-linear") that the framing predicts.
"""

from __future__ import annotations

from typing import Dict, List

from .bitmath import (
    algebraic_degree,
    component_function,
    hamming_distance,
    popcount,
    walsh_spectrum,
)
from .core import Property, PropertyResult, Status, Table

# FWHT / output-mask enumeration get expensive past these widths; beyond them
# the bit-oriented properties report n/a rather than burning the machine.
_MAX_N = 16
_MAX_M = 16


def _is_bit_self_map(table: Table) -> bool:
    return (
        table.data is not None
        and table.domain_bits is not None
        and table.codomain_bits is not None
        and len(table.data) == (1 << table.domain_bits)
    )


class Bijective(Property):
    name = "bijective"
    description = "The mapping is a permutation: every output occurs exactly once."

    def applicable(self, table: Table) -> bool:
        return (
            table.data is not None
            and table.domain_bits is not None
            and table.domain_bits == table.codomain_bits
        )

    def check(self, table: Table) -> PropertyResult:
        n = len(table.data)
        ok = sorted(table.data) == list(range(n))
        return PropertyResult(Status.PASS if ok else Status.FAIL)


class Involution(Property):
    name = "involution"
    description = "Applying the table twice is the identity (it is its own inverse)."

    def applicable(self, table: Table) -> bool:
        return (
            table.data is not None
            and table.domain_bits is not None
            and table.domain_bits == table.codomain_bits
            and sorted(table.data) == list(range(len(table.data)))
        )

    def check(self, table: Table) -> PropertyResult:
        data = table.data
        ok = all(data[data[x]] == x for x in range(len(data)))
        return PropertyResult(Status.PASS if ok else Status.FAIL)


class Balanced(Property):
    name = "balanced"
    description = "Every output bit is 0 as often as 1 across the domain."

    def applicable(self, table: Table) -> bool:
        return _is_bit_self_map(table) and table.codomain_bits <= 32

    def check(self, table: Table) -> PropertyResult:
        n, m = table.domain_bits, table.codomain_bits
        size = 1 << n
        worst = 0
        for j in range(m):
            ones = sum((table.data[x] >> j) & 1 for x in range(size))
            worst = max(worst, abs(ones - size // 2))
        return PropertyResult(Status.PASS if worst == 0 else Status.FAIL, worst,
                              f"max bit imbalance {worst}")


class Nonlinearity(Property):
    name = "nonlinearity"
    description = "Hamming distance from the nearest affine function (higher = better)."

    def applicable(self, table: Table) -> bool:
        return _is_bit_self_map(table) and table.domain_bits <= _MAX_N and table.codomain_bits <= _MAX_M

    def check(self, table: Table) -> PropertyResult:
        n, m = table.domain_bits, table.codomain_bits
        max_corr = 0
        for b in range(1, 1 << m):  # nonzero output masks -> component functions
            spectrum = walsh_spectrum(component_function(table.data, b, n))
            max_corr = max(max_corr, max(abs(w) for w in spectrum))
        nl = (1 << (n - 1)) - max_corr // 2
        # PASS is informational here: nonlinearity is a measured quantity, but a
        # value of 0 (purely affine) is the meaningful "fails to be nonlinear".
        status = Status.PASS if nl > 0 else Status.FAIL
        return PropertyResult(status, nl, f"nonlinearity {nl}")


class DifferentialUniformity(Property):
    name = "differential-uniformity"
    description = "Max count over (a!=0,b) of x with S(x+a)+S(x)=b (lower = better)."

    def applicable(self, table: Table) -> bool:
        return (
            table.data is not None
            and table.domain_bits is not None
            and table.codomain_bits is not None
            and table.domain_bits <= _MAX_N
            and len(table.data) == (1 << table.domain_bits)
        )

    def check(self, table: Table) -> PropertyResult:
        n = table.domain_bits
        size = 1 << n
        data = table.data
        worst = 0
        for a in range(1, size):
            counts: Dict[int, int] = {}
            for x in range(size):
                d = data[x] ^ data[x ^ a]
                counts[d] = counts.get(d, 0) + 1
                if counts[d] > worst:
                    worst = counts[d]
        # Lower is better; a linear map hits the worst possible value (= size).
        status = Status.PASS if worst < size else Status.FAIL
        return PropertyResult(status, worst, f"max differential {worst}/{size}")


class StrictAvalanche(Property):
    name = "sac"
    description = "Each input-bit flip flips each output bit with probability 1/2."

    def applicable(self, table: Table) -> bool:
        return _is_bit_self_map(table) and table.domain_bits <= _MAX_N

    def check(self, table: Table) -> PropertyResult:
        n, m = table.domain_bits, table.codomain_bits
        size = 1 << n
        worst = 0.0
        for i in range(n):
            for j in range(m):
                flips = 0
                for x in range(size):
                    diff = table.data[x] ^ table.data[x ^ (1 << i)]
                    flips += (diff >> j) & 1
                worst = max(worst, abs(flips / size - 0.5))
        worst = round(worst, 4)
        return PropertyResult(Status.PASS if worst == 0 else Status.FAIL, worst,
                              f"max deviation from 1/2: {worst}")


class AvalancheMean(Property):
    name = "avalanche"
    description = "Mean fraction of output bits changed by a single input-bit flip."

    def applicable(self, table: Table) -> bool:
        return _is_bit_self_map(table) and table.domain_bits <= _MAX_N

    def check(self, table: Table) -> PropertyResult:
        n, m = table.domain_bits, table.codomain_bits
        size = 1 << n
        total = 0
        for i in range(n):
            for x in range(size):
                total += popcount(table.data[x] ^ table.data[x ^ (1 << i)])
        mean = total / (n * size * m)
        mean = round(mean, 4)
        # Ideal avalanche is 0.5; we just report the measured mean.
        return PropertyResult(Status.PASS, mean, f"mean change {mean}")


class CorrelationImmunity(Property):
    name = "correlation-immunity"
    description = "Largest k s.t. output is independent of any k input bits."

    def applicable(self, table: Table) -> bool:
        return _is_bit_self_map(table) and table.domain_bits <= _MAX_N and table.codomain_bits <= _MAX_M

    def check(self, table: Table) -> PropertyResult:
        n, m = table.domain_bits, table.codomain_bits
        order = n  # start optimistic, lower it per component
        for b in range(1, 1 << m):
            spectrum = walsh_spectrum(component_function(table.data, b, n))
            min_w = n
            for a in range(1, 1 << n):
                if spectrum[a] != 0:
                    w = popcount(a)
                    if w < min_w:
                        min_w = w
            order = min(order, min_w - 1)
        order = max(order, 0)
        return PropertyResult(Status.PASS if order >= 1 else Status.FAIL, order,
                              f"correlation-immune up to order {order}")


class AlgebraicDegree(Property):
    name = "algebraic-degree"
    description = "Max degree of any output bit as a polynomial over GF(2)."

    def applicable(self, table: Table) -> bool:
        return _is_bit_self_map(table) and table.domain_bits <= _MAX_N and table.codomain_bits <= _MAX_M

    def check(self, table: Table) -> PropertyResult:
        n, m = table.domain_bits, table.codomain_bits
        deg = 0
        for b in range(1, 1 << m):
            deg = max(deg, algebraic_degree(component_function(table.data, b, n)))
        return PropertyResult(Status.PASS, deg, f"algebraic degree {deg}")


# --- specialised properties: each applies to one or two table kinds ----------

class Orthogonal(Property):
    name = "orthogonal"
    description = "Rows of the associated matrix are mutually orthogonal."

    def applicable(self, table: Table) -> bool:
        return "matrix" in table.meta

    def check(self, table: Table) -> PropertyResult:
        rows = table.meta["matrix"]
        worst = 0.0
        for i in range(len(rows)):
            for k in range(i + 1, len(rows)):
                dot = sum(a * b for a, b in zip(rows[i], rows[k]))
                worst = max(worst, abs(dot))
        worst = round(worst, 6)
        return PropertyResult(Status.PASS if worst < 1e-6 else Status.FAIL, worst,
                              f"max |off-diagonal inner product|: {worst}")


class GrayAdjacent(Property):
    name = "gray-adjacent"
    description = "Consecutive entries (cyclically) differ in exactly one bit."

    def applicable(self, table: Table) -> bool:
        return bool(table.meta.get("gray"))

    def check(self, table: Table) -> PropertyResult:
        data = table.data
        violations = sum(
            1 for i in range(len(data))
            if hamming_distance(data[i], data[(i + 1) % len(data)]) != 1
        )
        return PropertyResult(Status.PASS if violations == 0 else Status.FAIL,
                              violations, f"{violations} adjacency violations")


class FullCover(Property):
    name = "full-cover"
    description = "The sequence visits each state in its space exactly once."

    def applicable(self, table: Table) -> bool:
        return "cover" in table.meta

    def check(self, table: Table) -> PropertyResult:
        kind, bits = table.meta["cover"]
        if kind == "all":
            expected = set(range(1 << bits))
        elif kind == "nonzero":
            expected = set(range(1, 1 << bits))
        else:  # pragma: no cover - defensive
            return PropertyResult(Status.NA)
        seen = set(table.data)
        ok = seen == expected and len(table.data) == len(expected)
        return PropertyResult(Status.PASS if ok else Status.FAIL, len(seen),
                              f"{len(seen)}/{len(expected)} states visited")


class DeBruijnWindows(Property):
    name = "debruijn"
    description = "Every length-k window appears exactly once in the cyclic sequence."

    def applicable(self, table: Table) -> bool:
        return "window_bits" in table.meta

    def check(self, table: Table) -> PropertyResult:
        k = table.meta["window_bits"]
        seq = table.data
        n = len(seq)
        windows = set()
        for i in range(n):
            w = 0
            for j in range(k):
                w = (w << 1) | seq[(i + j) % n]
            windows.add(w)
        ok = len(windows) == n == (1 << k)
        return PropertyResult(Status.PASS if ok else Status.FAIL, len(windows),
                              f"{len(windows)}/{1 << k} distinct windows")


class LatinSquare(Property):
    name = "latin-square"
    description = "Every symbol occurs once per row and once per column."

    def applicable(self, table: Table) -> bool:
        return "square" in table.meta

    def check(self, table: Table) -> PropertyResult:
        square = table.meta["square"]
        n = len(square)
        full = list(range(n))
        rows_ok = all(sorted(row) == full for row in square)
        cols_ok = all(sorted(square[r][c] for r in range(n)) == full for c in range(n))
        ok = rows_ok and cols_ok
        return PropertyResult(Status.PASS if ok else Status.FAIL, n, f"order {n}")


class UniformDifferences(Property):
    name = "uniform-differences"
    description = "Every nonzero difference of set members occurs equally often."

    def applicable(self, table: Table) -> bool:
        return "diff_set" in table.meta and "modulus" in table.meta

    def check(self, table: Table) -> PropertyResult:
        members = table.meta["diff_set"]
        v = table.meta["modulus"]
        counts: Dict[int, int] = {r: 0 for r in range(1, v)}
        for a in members:
            for b in members:
                if a != b:
                    counts[(a - b) % v] += 1
        values = set(counts.values())
        ok = len(values) == 1
        lam = next(iter(values)) if ok else None
        return PropertyResult(Status.PASS if ok else Status.FAIL, lam,
                              f"lambda={lam}" if ok else "non-uniform")


class Costas(Property):
    name = "costas"
    description = "All displacement vectors between dots are distinct."

    def applicable(self, table: Table) -> bool:
        return "costas" in table.meta

    def check(self, table: Table) -> PropertyResult:
        p = table.meta["costas"]
        n = len(p)
        ok = True
        for d in range(1, n):
            diffs = [p[i + d] - p[i] for i in range(n - d)]
            if len(set(diffs)) != len(diffs):
                ok = False
                break
        return PropertyResult(Status.PASS if ok else Status.FAIL, n, f"order {n}")


class OrthogonalArrayProp(Property):
    name = "orthogonal-array"
    description = "Every pair of columns shows each level-pair equally often."

    def applicable(self, table: Table) -> bool:
        return "oa" in table.meta

    def check(self, table: Table) -> PropertyResult:
        spec = table.meta["oa"]
        rows, levels = spec["rows"], spec["levels"]
        ncols = len(rows[0])
        expected = len(rows) // (levels * levels)
        ok = True
        for c1 in range(ncols):
            for c2 in range(c1 + 1, ncols):
                counts: Dict[tuple, int] = {}
                for row in rows:
                    key = (row[c1], row[c2])
                    counts[key] = counts.get(key, 0) + 1
                if len(counts) != levels * levels or set(counts.values()) != {expected}:
                    ok = False
                    break
            if not ok:
                break
        return PropertyResult(Status.PASS if ok else Status.FAIL, spec["strength"],
                              f"strength {spec['strength']}")


class DistinctEntries(Property):
    name = "distinct-keys"
    description = "All entries in the random ensemble are distinct (no collisions)."

    def applicable(self, table: Table) -> bool:
        return "ensemble" in table.meta

    def check(self, table: Table) -> PropertyResult:
        ens = table.meta["ensemble"]
        distinct = len(set(ens))
        ok = distinct == len(ens)
        return PropertyResult(Status.PASS if ok else Status.FAIL, distinct,
                              f"{distinct}/{len(ens)} distinct")


class BitBalance(Property):
    name = "bit-balance"
    description = "Each bit position is ~50% ones across the ensemble (statistical)."

    def applicable(self, table: Table) -> bool:
        return "ensemble" in table.meta and "ensemble_bits" in table.meta

    def check(self, table: Table) -> PropertyResult:
        ens = table.meta["ensemble"]
        w = table.meta["ensemble_bits"]
        worst = 0.0
        for j in range(w):
            ones = sum((v >> j) & 1 for v in ens)
            worst = max(worst, abs(ones / len(ens) - 0.5))
        worst = round(worst, 3)
        # Statistical guarantee: allow a tolerance band rather than exact 1/2.
        return PropertyResult(Status.PASS if worst <= 0.1 else Status.FAIL, worst,
                              f"max bit bias {worst} (tol 0.1)")


class RootOfUnity(Property):
    name = "root-of-unity"
    description = "The base element is a primitive Nth root of unity (mod p)."

    def applicable(self, table: Table) -> bool:
        return "ntt" in table.meta

    def check(self, table: Table) -> PropertyResult:
        spec = table.meta["ntt"]
        p, order, root = spec["modulus"], spec["order"], spec["root"]
        if pow(root, order, p) != 1:
            return PropertyResult(Status.FAIL, None, "root^order != 1")
        # primitive: no smaller positive power is 1
        primitive = all(pow(root, k, p) != 1 for k in range(1, order))
        return PropertyResult(Status.PASS if primitive else Status.FAIL, order,
                              f"primitive root of order {order}")


class ComplexRootOfUnity(Property):
    name = "complex-root-of-unity"
    description = "Coefficients are the N complex Nth roots of unity."

    def applicable(self, table: Table) -> bool:
        return "complex" in table.meta

    def check(self, table: Table) -> PropertyResult:
        coeffs = table.meta["complex"]
        n = len(coeffs)
        unit = all(abs(abs(c) - 1.0) < 1e-9 for c in coeffs)
        closes = abs(coeffs[1] ** n - 1.0) < 1e-6 if n > 1 else True
        ok = unit and closes
        return PropertyResult(Status.PASS if ok else Status.FAIL, n,
                              f"{n} unit-modulus roots")


# Properties that make sense to run against *every* table -- the matrix columns.
MATRIX_PROPERTIES: List[Property] = [
    Bijective(),
    Involution(),
    Nonlinearity(),
    DifferentialUniformity(),
    StrictAvalanche(),
    AvalancheMean(),
    CorrelationImmunity(),
    AlgebraicDegree(),
]

# Specialised, design-specific properties.
SPECIALISED_PROPERTIES: List[Property] = [
    Balanced(),
    Orthogonal(),
    GrayAdjacent(),
    FullCover(),
    DeBruijnWindows(),
    LatinSquare(),
    UniformDifferences(),
    Costas(),
    OrthogonalArrayProp(),
    DistinctEntries(),
    BitBalance(),
    RootOfUnity(),
    ComplexRootOfUnity(),
]

ALL_PROPERTIES: List[Property] = MATRIX_PROPERTIES + SPECIALISED_PROPERTIES
PROPERTY_BY_NAME: Dict[str, Property] = {p.name: p for p in ALL_PROPERTIES}
