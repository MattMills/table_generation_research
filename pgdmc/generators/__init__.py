"""All generator families, aggregated into one list.

Importing here is what literally puts the scattered communities "in one room":
algebra, sequences, transforms, cryptography, combinatorics, hashing, coding,
and the speculative constructions, side by side under one registry.
"""

from __future__ import annotations

from . import (
    algebraic,
    combinatorial,
    crypto,
    errorcorrection,
    hashing,
    sequence,
    speculative,
    transform,
)

ALL_GENERATORS = (
    algebraic.GENERATORS
    + sequence.GENERATORS
    + transform.GENERATORS
    + crypto.GENERATORS
    + combinatorial.GENERATORS
    + hashing.GENERATORS
    + errorcorrection.GENERATORS
    + speculative.GENERATORS
)

__all__ = ["ALL_GENERATORS"]
