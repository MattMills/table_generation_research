"""pgdmc -- Property-Guaranteed Discrete Mapping Construction.

A small research exploration of the idea that CRC tables, S-boxes, log/antilog
tables, LFSR sequences, Latin squares, FFT twiddles, Zobrist keys (and more)
are all instances of one pattern: an expensive generator produces a table whose
runtime value is a *property* it provably has.

Public surface:
    Table, Generator, Property, Registry   -- the core abstractions
    build_registry, build_catalog          -- assemble everything
    property_matrix, verify_specs          -- compare and self-test
    run_all_explorations                   -- probe the speculative constructions
"""

from __future__ import annotations

from .catalog import (
    build_catalog,
    build_registry,
    property_matrix,
    verify_specs,
)
from .core import (
    Family,
    FamilySize,
    Generator,
    Property,
    PropertyResult,
    Registry,
    Status,
    Table,
)
from .generators.speculative import run_all_explorations

__all__ = [
    "Family",
    "FamilySize",
    "Generator",
    "Property",
    "PropertyResult",
    "Registry",
    "Status",
    "Table",
    "build_catalog",
    "build_registry",
    "property_matrix",
    "verify_specs",
    "run_all_explorations",
]
