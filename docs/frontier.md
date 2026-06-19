# The property-incompatibility frontier

This is the document to read first. The catalog, the cross-property matrix, the
combinator algebra, and the survey extensions are all *infrastructure*. The
contribution of treating lookup tables as "property-guaranteed discrete mapping
constructions" is the question they let you answer:

> **Which property guarantees provably cannot coexist in one table?**

A catalog tells you what exists. A frontier tells you what *can't* — and that is
the claim with teeth. Every result below is computed at runtime
(`python explore.py frontier`) and pinned by `tests/test_frontier.py`.

## Provably cannot coexist

| Property A | Property B | Why | Witness |
|---|---|---|---|
| bijective | entropy-flattening | a bijection only relabels probability mass ⇒ entropy is invariant | H(in)=H(out)=2.27 bits, can't reach 3.0 |
| bijective | perfect-nonlinear (bent) | permutation components are balanced; bent functions are unbalanced (and vectorial bent needs m ≤ n/2) | bent(n=6) weight 28 ≠ 32 |
| linear (NL=0) | low differential uniformity | linear L ⇒ L(x⊕a)⊕L(x)=L(a) constant ⇒ DU = 2ⁿ | rotate-by-1: NL 0, DU 256 |
| perfect-nonlinear (bent) | algebraic degree > n/2 | a bent function has degree ≤ n/2 (hard bound) | bent(n=6) degree 2 ≤ 3 |
| self-inverse direction | asymmetric NL/DU | NL and DU are inverse-invariant ⇒ equal forward and backward | AES vs AES⁻¹: NL 112/112, DU 4/4 |
| distance-1→d converter | even d | even-weight columns lie in a dim-(n−1) subspace ⇒ can't span ⇒ not invertible | weight-2 vectors span rank 3/4 |

These are qualitatively different from "we couldn't build it." Each has a reason
that closes the door: an invariant (entropy, NL/DU under inversion), a counting
fact (balanced vs unbalanced), or a linear-algebra obstruction (spanning).

## Coexist only under a quantitative bound

| Property A | Property B | The bound |
|---|---|---|
| low differential uniformity | narrow block decomposition | width-w block lookups give DU ≥ 2^(n−w+1); AES-grade DU=4 on n=8 forces **w ≥ 7** (essentially full width) |
| bijective | correlation-immunity (order ≥ 1) | random search finds **order 0** up to n=6; resilient permutations are rare and need special construction |

The minimum-width bound is the honest answer to a question an earlier version of
this project hand-waved (the "streaming-decomposable" probe). Cheap narrow
decomposition and strong differential uniformity are not just hard to combine —
there is a hard floor on how narrow the sub-tables can be.

## Coexist (sharp positive witnesses)

The boundary is only sharp if the positive side is named too:

| Property A | Property B | Witness |
|---|---|---|
| bijective | high nonlinearity + low DU | AES S-box (NL 112, DU 4) |
| low algebraic degree | low DU (APN) + nonlinearity | GF(2⁵) cube (degree 2, DU 2) |

The cube is the instructive one: minimal algebraic degree *and* optimal
differential uniformity coexist (APN quadratics exist) — so "low degree" and
"low DU" are compatible, even though "low degree" feels like it should be a
weakness. The frontier is not monotone; you have to check.

## The compatibility grid

```
          | bijective nonlinear    low-DU low-degre  balanced      bent corr-immu
bijective |         -        ok        ok        ok        ok         x         ~
nonlinear |        ok         -        ok        ok         ·        ok         ·
   low-DU |        ok        ok         -        ok         ·         ·         ·
low-degre |        ok        ok        ok         -         ·        ok         ·
 balanced |        ok         ·         ·         ·         -         x         ·
     bent |         x        ok         ·        ok         x         -         ~
corr-immu |         ~         ·         ·         ·         ·         ~         -
```

`ok` coexist · `x` impossible · `~` bounded tradeoff · `·` not analysed.

## What is honestly still open

The most interesting cells are the ones the dependency-free, small-bit-width
model cannot fully reach:

- **The exact correlation-immunity ceiling for bijections.** Random search shows
  order 0 is overwhelmingly typical up to n=6, but the *maximum* achievable
  order as a function of n (via algebraic constructions of resilient
  permutations) is not settled here.
- **Minimum sub-table width under richer combiners.** The bound above is for
  block-diagonal decomposition. AES "T-tables" reconstruct a *specific* map via
  lookups + XOR; the minimum width to reconstruct an arbitrary *property* under
  such non-block factorings is open.
- **Triple incompatibilities.** This frontier is pairwise. Some property triples
  may be jointly impossible even when each pair is fine — the natural next
  dimension.

## Why this is the thesis

If this were a paper, the abstract would lead with the frontier, not the
catalog. "Here is a unified language for property-guaranteed tables" is a
framing; "here are the property combinations that provably cannot coexist, with
proofs, and here is the boundary's shape" is a result. The catalog, matrix, and
combinator algebra are the apparatus that makes the boundary discoverable and
checkable — which is exactly their job.
