#!/usr/bin/env python3
"""Run the full property-guaranteed discrete mapping construction exploration.

    python explore.py              # everything
    python explore.py taxonomy     # just the taxonomy
    python explore.py matrix       # just the cross-family property matrix
    python explore.py specs        # verify each generator meets its guarantee
    python explore.py speculative  # just the speculative feasibility probes
    python explore.py combine      # combine generators into new-purpose tables
    python explore.py literature   # survey-grounded extensions, made runnable

The story, in order: (1) lay every generator from every lineage side by side,
(2) confirm each meets the property it promises, (3) run the broadly-applicable
properties against *all* of them to surface cross-family relationships,
(4) flip the question around -- pick a property first and ask what can be built,
(5) combine generators and watch which properties are created or destroyed,
then (6) fold in methods excavated from a literature survey, each made runnable.
"""

from __future__ import annotations

import sys

from pgdmc.catalog import build_catalog, build_registry, property_matrix, verify_specs
from pgdmc.generators.speculative import run_all_explorations
from pgdmc.report import (
    render_combine,
    render_feasibility,
    render_matrix,
    render_spec_checks,
    render_survey,
    render_taxonomy,
)

SECTIONS = ("taxonomy", "specs", "matrix", "speculative", "combine", "literature")


def _banner(title: str) -> str:
    bar = "=" * 78
    return f"\n{bar}\n{title}\n{bar}"


def main(argv: list[str]) -> int:
    which = argv[1] if len(argv) > 1 else "all"
    if which not in SECTIONS and which != "all":
        print(f"unknown section {which!r}; choose from: all, {', '.join(SECTIONS)}")
        return 2

    registry = build_registry()
    catalog = build_catalog()

    if which in ("all", "taxonomy"):
        print(_banner("1. TAXONOMY"))
        print(render_taxonomy(registry))

    if which in ("all", "specs"):
        print(_banner("2. SPEC VERIFICATION"))
        print(render_spec_checks(verify_specs(catalog)))

    if which in ("all", "matrix"):
        print(_banner("3. CROSS-FAMILY PROPERTY MATRIX"))
        print("Every broadly-applicable property run against every table.")
        print("Note how the CRC table and AES S-box -- both 256-entry byte")
        print("bijections -- sit at opposite ends of nonlinearity.\n")
        print(render_matrix(property_matrix(catalog)))

    if which in ("all", "speculative"):
        print(_banner("4. SPECULATIVE CONSTRUCTIONS"))
        print(render_feasibility(run_all_explorations()))

    if which in ("all", "combine"):
        print(_banner("5. COMBINING GENERATORS"))
        print("Two generators in, one new-purpose table out -- and a record of")
        print("which property each combinator creates, preserves, or destroys.\n")
        print(render_combine())

    if which in ("all", "literature"):
        print(_banner("6. SURVEY-GROUNDED EXTENSIONS"))
        print("Methods drawn from a literature review, made runnable and verified.\n")
        print(render_survey())

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
