"""Sequence generators: feedback/recurrence machinery produces the table.

A shift register or a recurrence walks state space in a way that guarantees a
covering or adjacency property -- maximal-length LFSRs (every nonzero state
once), de Bruijn sequences (every window once), Gray codes (one-bit steps).
"""

from __future__ import annotations

from typing import List

from ..bitmath import popcount
from ..core import Family, FamilySize, Generator, Table

def _lfsr_period(tap_mask: int, n: int) -> List[int]:
    """Run a Fibonacci LFSR from state 1 and return the states it visits.

    `tap_mask` holds the feedback-polynomial coefficients c_0..c_{n-1}; the
    leading x^n term is implicit.  The new top bit is the parity of
    (state AND tap_mask).
    """
    state = 1
    states: List[int] = []
    seen = set()
    for _ in range(1 << n):
        if state in seen:
            break
        seen.add(state)
        states.append(state)
        feedback = popcount(state & tap_mask) & 1
        state = (state >> 1) | (feedback << (n - 1))
    return states


def build_lfsr(n: int = 8) -> Table:
    """Maximal-length LFSR: visits all 2^n-1 nonzero states before repeating.

    We scan feedback masks for the smallest one achieving full period, so the
    "maximal-length" (primitive-polynomial) guarantee is *discovered and
    verified* here rather than asserted from a hard-coded table.
    """
    full = (1 << n) - 1
    chosen, states = None, None
    for tap_mask in range(1, 1 << n):
        seq = _lfsr_period(tap_mask, n)
        if len(seq) == full:  # maximal length <=> primitive feedback polynomial
            chosen, states = tap_mask, seq
            break
    if states is None:  # pragma: no cover - defensive
        raise RuntimeError(f"no maximal feedback mask found for n={n}")
    return Table(
        name=f"{n}-bit maximal-length LFSR",
        family=Family.SEQUENCE,
        generator="LFSR (m-sequence)",
        data=states,
        notes=f"primitive feedback mask {hex(chosen)}; period {len(states)} = 2^{n}-1.",
        meta={"cover": ("nonzero", n), "tap_mask": chosen},
    )


def build_de_bruijn(n: int = 4) -> Table:
    """de Bruijn sequence B(2,n): every n-bit window appears exactly once.

    Built with the greedy "prefer-one" (Martin's) algorithm, which is
    guaranteed to produce a de Bruijn sequence.
    """
    seq = [0] * (n - 1)  # seed with n-1 zeros
    seen = set()
    while True:
        # try to append 1, else 0, keeping each n-window unique
        for bit in (1, 0):
            window = 0
            for b in seq[-(n - 1):] if n > 1 else []:
                window = (window << 1) | b
            window = (window << 1) | bit
            if window not in seen:
                seen.add(window)
                seq.append(bit)
                break
        else:
            break  # no extension possible -> done
    seq = seq[: 1 << n]  # the cyclic sequence has length exactly 2^n
    return Table(
        name=f"de Bruijn B(2,{n})",
        family=Family.SEQUENCE,
        generator="de Bruijn",
        data=seq,
        notes=f"cyclic bit sequence of length 2^{n}; all {n}-bit windows once.",
        meta={"window_bits": n},
    )


def build_gray_code(n: int = 8) -> Table:
    """Binary reflected Gray code: consecutive codewords differ in one bit.

    Note for the matrix: g(i) = i XOR (i>>1) is *linear* over GF(2), so this
    bijection has nonlinearity 0 -- a vivid foil to the AES S-box.
    """
    data = [i ^ (i >> 1) for i in range(1 << n)]
    return Table(
        name=f"{n}-bit Gray code",
        family=Family.SEQUENCE,
        generator="Gray code",
        data=data,
        domain_bits=n,
        codomain_bits=n,
        notes="g(i)=i^(i>>1); single-bit adjacency, but a linear bijection.",
        meta={"gray": True},
    )


GENERATORS = [
    Generator(
        name="LFSR (m-sequence)",
        family=Family.SEQUENCE,
        description="Shift register with polynomial feedback; maximal-length sequence.",
        build=build_lfsr,
        guarantees=["full-cover"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,  # choice of primitive polynomial
    ),
    Generator(
        name="de Bruijn",
        family=Family.SEQUENCE,
        description="Sequence in which every length-n window appears exactly once.",
        build=build_de_bruijn,
        guarantees=["debruijn"],
        constructive=True,
        family_size=FamilySize.PARAMETRIC,
    ),
    Generator(
        name="Gray code",
        family=Family.SEQUENCE,
        description="Ordering of codewords with single-bit transitions.",
        build=build_gray_code,
        guarantees=["bijective", "gray-adjacent"],
        constructive=True,
        family_size=FamilySize.UNIQUE,  # the reflected Gray code is canonical
    ),
]
