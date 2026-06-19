"""Core abstractions for property-guaranteed discrete mapping construction.

The thesis from the seed conversation: CRC tables, S-boxes, log/antilog
tables, LFSR sequences, Latin squares, Zobrist keys ... are all the same
*shape* of thing -- run an expensive generator once, get a table, rely at
runtime on a property the generator guarantees.  They look unrelated only
because each community files them under its own mathematical ancestry.

This module gives that shape three first-class types:

    Table       -- the artifact (a discrete mapping plus metadata)
    Generator   -- the process that produces tables of a kind
    Property    -- a runtime-checkable guarantee a table may or may not have

and a Registry that lets us lay every generator from every family side by
side and run every property against every table.  The Generator metadata
fields are not decoration -- they are exactly the classifying axes the
conversation arrived at:

    * family_size  -> "is the table unique, or one of a family?"
    * constructive -> "is generation a recipe, or a search?"
    * guarantees   -> "which property class is being promised?"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class Family(str, Enum):
    """The mathematical lineages tables are usually filed under."""

    ALGEBRAIC = "algebraic"
    SEQUENCE = "sequence"
    TRANSFORM = "transform"
    CRYPTOGRAPHIC = "cryptographic"
    COMBINATORIAL = "combinatorial"
    HASHING = "hashing"
    ERROR_CORRECTION = "error-correction"
    SPECULATIVE = "speculative"
    COMPOSITE = "composite"  # produced by combining two or more generators


class FamilySize(str, Enum):
    """How many valid tables a generator's spec admits."""

    UNIQUE = "unique"                 # the spec + params pin down one table
    PARAMETRIC = "parametric family"  # a discrete knob selects among many
    RANDOM = "random ensemble"        # any seed gives a fresh valid table


@dataclass
class Table:
    """A generated lookup table: the artifact at the centre of the framework.

    `data` is the primary one-dimensional view -- ``data[i]`` is the output
    for input ``i`` (for self-maps / sequences).  Richer structure (matrices,
    complex coefficients, families of sub-tables, the originating set) lives
    in `meta`, so a single type can host S-boxes, Hadamard matrices and
    difference sets without lying about their shape.
    """

    name: str
    family: Family
    generator: str
    data: Optional[List[int]] = None
    domain_bits: Optional[int] = None     # set only when input is a clean bit-width
    codomain_bits: Optional[int] = None   # set only when output is a clean bit-width
    notes: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_self_map(self) -> bool:
        return (
            self.data is not None
            and self.domain_bits is not None
            and self.domain_bits == self.codomain_bits
        )

    def __len__(self) -> int:
        return len(self.data) if self.data is not None else 0


@dataclass
class Generator:
    """A process that produces tables of a particular kind."""

    name: str
    family: Family
    description: str
    build: Callable[..., Table]
    guarantees: List[str]                      # property names it is designed to meet
    constructive: bool                         # recipe (True) vs search (False)
    family_size: FamilySize
    references: str = ""

    def __call__(self, **params: Any) -> Table:
        return self.build(**params)


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NA = "n/a"


@dataclass
class PropertyResult:
    status: Status
    value: Any = None          # measured quantity (nonlinearity, max deviation, ...)
    detail: str = ""

    def render(self) -> str:
        if self.status is Status.NA:
            return "·"
        if self.value is None:
            return self.status.value
        return f"{self.status.value}({self.value})"


class Property:
    """A runtime-checkable guarantee.

    Subclasses implement `applicable` (does this property even make sense for
    the table?) and `check` (does the table have it, and by how much?).  The
    split is what lets us build an honest cross-family matrix: a property that
    does not apply reports `n/a` rather than a misleading pass/fail.
    """

    name: str = "property"
    description: str = ""

    def applicable(self, table: Table) -> bool:  # pragma: no cover - interface
        raise NotImplementedError

    def check(self, table: Table) -> PropertyResult:  # pragma: no cover - interface
        raise NotImplementedError

    def evaluate(self, table: Table) -> PropertyResult:
        if not self.applicable(table):
            return PropertyResult(Status.NA)
        return self.check(table)


@dataclass
class Registry:
    """Holds every generator and property so they can be compared en masse."""

    generators: List[Generator] = field(default_factory=list)
    properties: List[Property] = field(default_factory=list)

    def add_generator(self, gen: Generator) -> Generator:
        self.generators.append(gen)
        return gen

    def add_property(self, prop: Property) -> Property:
        self.properties.append(prop)
        return prop

    def by_family(self) -> Dict[Family, List[Generator]]:
        out: Dict[Family, List[Generator]] = {}
        for gen in self.generators:
            out.setdefault(gen.family, []).append(gen)
        return out
