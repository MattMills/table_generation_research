"""A plaintext model of TFHE programmable bootstrapping, from survey section 2.

TFHE evaluates an arbitrary lookup table f homomorphically by "blind rotation"
of a test polynomial V(X) in the negacyclic ring Z[X]/(X^N + 1): the answer is
the constant coefficient of X^{-r}.V(X), where r is the (encrypted) input.

We model the *plaintext* arithmetic only -- no encryption -- to expose the
structural property guarantee and its sharp constraint:

  readout(r) = (-1)^floor(r/N) * f(r mod N).

So inputs in the lower half [0, N) read f exactly, but inputs in [N, 2N) come
back NEGATED -- the negacyclic boundary.  A "padding bit" (forcing the input's
MSB to 0) confines r to [0, N) and restores an exact, bijection-safe LUT.  This
is the same negative result as the project's other "fundamental limits": the
table guarantee holds only inside a structurally mandated region.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List


def encode_test_polynomial(f: Callable[[int], int], n: int) -> List[int]:
    """Encode LUT f over {0..N-1} into the test polynomial's coefficients."""
    return [f(i) for i in range(n)]


def negacyclic_readout(v: List[int], r: int) -> int:
    """Constant coefficient of X^{-r}.V(X) in Z[X]/(X^N+1).

    Derivation: the term landing at position 0 comes from coefficient r mod N,
    carrying the sign (-1)^floor(r/N) from each wrap across X^N = -1.
    """
    n = len(v)
    sign = -1 if (r // n) % 2 else 1
    return sign * v[r % n]


@dataclass
class PBSReport:
    n: int
    rows: List[tuple]          # (input r, intended f(r mod N), no-padding, padded)
    exact_without_padding: bool
    exact_with_padding: bool


def programmable_bootstrap_demo(n: int = 8) -> PBSReport:
    """Demonstrate the negacyclic sign-flip and the padding-bit remedy.

    Inputs range over the rotation domain [0, 2N).  Without a padding bit the
    upper half is negated; with one, every input is read exactly.
    """
    def f(i: int) -> int:
        return (3 * i + 1) % n  # an arbitrary small LUT on {0..N-1}

    v = encode_test_polynomial(f, n)
    rows = []
    no_pad_ok = True
    pad_ok = True
    for r in range(2 * n):
        intended = f(r % n)
        no_pad = negacyclic_readout(v, r)
        # padding bit forces the MSB to 0 -> input confined to [0, N)
        padded_r = r & (n - 1)
        padded = negacyclic_readout(v, padded_r)
        rows.append((r, intended, no_pad, padded))
        if no_pad != intended:
            no_pad_ok = False
        if padded != f(padded_r % n):
            pad_ok = False
    return PBSReport(n=n, rows=rows, exact_without_padding=no_pad_ok,
                     exact_with_padding=pad_ok)
