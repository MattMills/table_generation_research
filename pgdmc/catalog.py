"""Assemble every generator and property; run everything against everything.

`build_registry` populates the registry; `build_catalog` instantiates one
table per generator; `property_matrix` evaluates the broadly-applicable
properties against every table.  That matrix is the concrete payoff of the
framing: tables filed under different mathematical lineages, finally compared
on the same property axes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .core import Generator, Property, PropertyResult, Registry, Status, Table
from .generators import ALL_GENERATORS
from .properties import (
    MATRIX_PROPERTIES,
    PROPERTY_BY_NAME,
    SPECIALISED_PROPERTIES,
)


def build_registry() -> Registry:
    reg = Registry()
    for gen in ALL_GENERATORS:
        reg.add_generator(gen)
    for prop in MATRIX_PROPERTIES + SPECIALISED_PROPERTIES:
        reg.add_property(prop)
    return reg


def build_catalog() -> List[Tuple[Generator, Table]]:
    """One representative table per generator (default parameters)."""
    catalog = []
    for gen in ALL_GENERATORS:
        catalog.append((gen, gen()))
    return catalog


def property_matrix(
    catalog: List[Tuple[Generator, Table]],
    properties: List[Property] = MATRIX_PROPERTIES,
) -> List[Tuple[Table, List[PropertyResult]]]:
    """Evaluate each property against each table."""
    matrix = []
    for _gen, table in catalog:
        row = [prop.evaluate(table) for prop in properties]
        matrix.append((table, row))
    return matrix


@dataclass
class SpecCheck:
    """Did a generator's table actually meet the property it promises?"""

    generator: Generator
    table: Table
    results: Dict[str, PropertyResult]

    @property
    def all_pass(self) -> bool:
        return all(r.status is Status.PASS for r in self.results.values())


def verify_specs(catalog: List[Tuple[Generator, Table]]) -> List[SpecCheck]:
    """Confirm each generator's *declared* guarantees against its table.

    This is the self-test of the catalog: every generator claims a property
    class; here we run the matching verifier and confirm the claim holds.
    """
    checks = []
    for gen, table in catalog:
        results: Dict[str, PropertyResult] = {}
        for guarantee in gen.guarantees:
            prop = PROPERTY_BY_NAME.get(guarantee)
            if prop is None:  # pragma: no cover - guards typos in guarantee names
                results[guarantee] = PropertyResult(Status.NA, detail="no verifier")
            else:
                results[guarantee] = prop.evaluate(table)
        checks.append(SpecCheck(gen, table, results))
    return checks
