"""Human-readable rendering of the taxonomy, the property matrix, and probes.

Pure text so it works in any terminal or CI log.  The matrix renderer is
deliberately compact: numbers where a property is a measured quantity
(nonlinearity, differential uniformity, ...), Y/N where it is a yes/no, and a
dot where the property simply does not apply to that kind of table.
"""

from __future__ import annotations

from typing import List, Tuple

from .catalog import SpecCheck
from .core import PropertyResult, Registry, Status, Table
from .generators.speculative import FeasibilityReport
from .properties import MATRIX_PROPERTIES

_HEADERS = {
    "bijective": "Bij",
    "involution": "Inv",
    "nonlinearity": "NL",
    "differential-uniformity": "DU",
    "sac": "SAC",
    "avalanche": "Aval",
    "correlation-immunity": "CI",
    "algebraic-degree": "Deg",
}


def _rule(width: int, ch: str = "-") -> str:
    return ch * width


def _cell(result: PropertyResult) -> str:
    if result.status is Status.NA:
        return "·"
    if result.value is None:
        return "Y" if result.status is Status.PASS else "N"
    if isinstance(result.value, float):
        return f"{result.value:g}"
    return str(result.value)


def render_taxonomy(registry: Registry) -> str:
    """The catalog as a taxonomy, annotated with the three classifying axes."""
    lines = ["TAXONOMY OF LOOKUP-TABLE GENERATORS",
             "(axes: constructive vs search  |  unique/parametric/random  |  property class)",
             ""]
    for family, gens in registry.by_family().items():
        lines.append(f"## {family.value.upper()}")
        for gen in gens:
            method = "recipe" if gen.constructive else "search"
            guarantees = ", ".join(gen.guarantees) if gen.guarantees else "(derived)"
            lines.append(f"  - {gen.name}")
            lines.append(f"      {gen.description}")
            lines.append(f"      method={method}  family={gen.family_size.value}  "
                         f"guarantees=[{guarantees}]")
        lines.append("")
    return "\n".join(lines)


def render_matrix(matrix: List[Tuple[Table, List[PropertyResult]]],
                  properties=MATRIX_PROPERTIES) -> str:
    """The cross-family property matrix -- the centrepiece comparison."""
    headers = [_HEADERS.get(p.name, p.name[:4]) for p in properties]
    name_w = max(len(t.name) for t, _ in matrix)
    name_w = max(name_w, len("table"))
    col_w = max(4, max(len(h) for h in headers))

    out = []
    header = "table".ljust(name_w) + " | " + " ".join(h.rjust(col_w) for h in headers)
    out.append(header)
    out.append(_rule(len(header)))
    for table, row in matrix:
        cells = " ".join(_cell(r).rjust(col_w) for r in row)
        out.append(table.name.ljust(name_w) + " | " + cells)
    out.append("")
    out.append("legend: Y/N = holds/fails;  numbers = measured value;  · = not applicable")
    out.append("  NL  nonlinearity (higher=better, 0=affine)   DU  max differential (lower=better)")
    out.append("  SAC max deviation from 1/2 (0=exact)         Aval mean output-bit change (~0.5 ideal)")
    out.append("  CI  correlation-immunity order               Deg  algebraic degree")
    return "\n".join(out)


def render_spec_checks(checks: List[SpecCheck]) -> str:
    """Confirm every generator actually satisfies the property it advertises."""
    out = ["SPEC VERIFICATION (does each generator meet its declared guarantee?)", ""]
    passed = 0
    total = 0
    for check in checks:
        if not check.results:
            out.append(f"  ~  {check.generator.name}: (no exact guarantee declared)")
            continue
        parts = []
        for name, res in check.results.items():
            total += 1
            ok = res.status is Status.PASS
            passed += ok
            detail = f"={res.value}" if res.value is not None else ""
            parts.append(f"{name}{detail}:{'ok' if ok else res.status.value}")
        mark = "PASS" if check.all_pass else "FAIL"
        out.append(f"  {mark}  {check.generator.name}: " + "; ".join(parts))
    out.append("")
    out.append(f"  {passed}/{total} declared guarantees verified.")
    return "\n".join(out)


def render_feasibility(reports: List[FeasibilityReport]) -> str:
    """The speculative probes: claim, verdict, evidence, takeaway."""
    out = ["SPECULATIVE CONSTRUCTIONS (property-first: what can actually be built?)", ""]
    for r in reports:
        out.append(f"### {r.name}  ->  [{r.verdict}]")
        out.append(f"    claim: {r.claim}")
        for e in r.evidence:
            out.append(f"      - {e}")
        if r.takeaway:
            out.append(f"    takeaway: {r.takeaway}")
        out.append("")
    return "\n".join(out)


def render_combine() -> str:
    """Combining generators: new tables, new purposes, and a property algebra."""
    from .combinators import (
        build_combinations,
        composition_findings,
        feistel_mixing_progression,
    )
    from .combinatorial_combinations import (
        build_difference_set_design,
        build_graeco_latin,
        build_mols_orthogonal_array,
    )
    from .properties import GraecoLatinOrthogonal, OrthogonalArrayProp, TwoDesign

    out = ["COMBINING GENERATORS (two generators -> a new alternate-purpose table)", ""]

    out.append("A) General combinator algebra (compose / Feistel / direct-sum / XOR)")
    out.append("")
    for c in build_combinations():
        out.append(f"  {c.combinator.upper():11s} {c.name}")
        out.append(f"      from: {' + '.join(c.parents)}")
        metric_str = "  ".join(f"{k}={v}" for k, v in c.metrics.items())
        out.append(f"      result: {metric_str}")
        out.append(f"      purpose: {c.new_purpose}")
        out.append(f"      effect:  {c.effect}")
        out.append("")

    out.append("  Property algebra of composition (computed live):")
    for line in composition_findings():
        out.append(f"    {line}")
    out.append("")
    out.append("  Feistel diffusion vs rounds (a function -> a strong bijection):")
    out.extend(feistel_mixing_progression())
    out.append("")

    out.append("B) Combining combinatorial generators into higher structures")
    out.append("")
    gl = build_graeco_latin(5)
    oa = build_mols_orthogonal_array(5, 3)
    design = build_difference_set_design(7)
    rows = [
        ("Latin square x Latin square -> Graeco-Latin", gl,
         GraecoLatinOrthogonal().check(gl)),
        ("k MOLS -> orthogonal array (strength 2)", oa,
         OrthogonalArrayProp().check(oa)),
        ("difference set + cyclic action -> 2-design", design,
         TwoDesign().check(design)),
    ]
    for label, table, result in rows:
        status = result.status.value
        out.append(f"  [{status}] {label}")
        out.append(f"          -> {table.name}: {result.detail}")
    out.append("")
    out.append("  The orthogonal array is literally a stack of Latin squares, and the")
    out.append("  Fano plane is a difference set developed under Z_7 -- combinatorial")
    out.append("  'generators' that are themselves combinations.")
    return "\n".join(out)


def render_survey() -> str:
    """Survey-grounded extensions: validated, extended, or newly added methods."""
    from .survey import run_survey_extensions

    out = ["SURVEY-GROUNDED EXTENSIONS (a literature review, made runnable)", ""]
    out.append("Each method below is checked live. Relation to the project:")
    out.append("  VALIDATES = survey confirms what we built; "
               "EXTENDS = real version of a toy; NEW = added.")
    out.append("")
    for f in run_survey_extensions():
        out.append(f"### [{f.relation}] {f.name}")
        out.append(f"    survey section {f.section}")
        out.append(f"    {f.summary}")
        for e in f.evidence:
            out.append(f"      - {e}")
        out.append("")
    return "\n".join(out)
