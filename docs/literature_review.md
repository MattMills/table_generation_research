# Literature review: existing works on property-guaranteed mappings

This note reviews an external survey of *property-guaranteed discrete mapping
constructions* and records what was folded into `pgdmc`. The survey's central
claim is the same as this project's: composite-field S-boxes, TFHE programmable
bootstrapping, distance-converting mappings, Costas arrays, tabulation hashing,
and Zech logarithms are not separate curiosities but one discipline —
deterministic generators that front-load algebraic, combinatorial, or
statistical constraints into a precomputed table.

Everything marked **runnable** below is verified live by
`python explore.py literature` and the `tests/test_survey.py` suite. Everything
marked **reference** is out of scope for a pure-Python, dependency-free model
(hardware synthesis, quantum circuits, encryption) but is recorded for context.

## What we folded in (runnable)

| Survey section | Method | Relation | Where |
|---|---|---|---|
| 1 | Inverse table reached by interchangeable generators (log/antilog, Fermat x²⁵⁴, search) | VALIDATES the "unique table, competing generators" axis | `survey.py` |
| 2 | TFHE programmable bootstrapping: negacyclic blind rotation + padding bit | NEW homomorphic-LUT model | `homomorphic.py` |
| 3 | Permutation polynomials over Z/2ʷ + Rivest–Black test (RC6) | NEW ring-polynomial generator | `generators/rings.py` |
| 3.2 | MBA null identity + inverse permutation-polynomial pair | NEW obfuscation combination | `generators/rings.py` |
| 4 | Distance-increasing mapping (Ferreira–Swart–Vinck) | EXTENDS the toy distance-converter | `distance_mappings.py` |
| 5 | Costas thumbtack autocorrelation (≤1 off-origin) | VALIDATES + adds a property | `properties.py` |
| 6 | Tabulation hashing 4-independence failure (the rectangle) | EXTENDS the hashing family with a real limit | `generators/hashing.py` |
| 7 | Zech cyclotomic-coset compression, Z(2x)=2Z(x) | EXTENDS the bare Zech entry | `properties.py` |

Selected verified results (live numbers):

- **One table, many generators.** log/antilog, Fermat `x²⁵⁴`, and brute-force
  search produce the *identical* 256-byte GF(2⁸) inverse. The table is unique;
  generators compete only on cost — exactly the survey's framing of the
  tower-field hardware work.
- **Rivest–Black is exact.** RC6's `x(2x+1) mod 2⁸` is a bijection, and the
  coefficient predicate (a₁ odd; even- and odd-index coefficient sums even)
  agrees with bijectivity for every test case. A genuinely *non-field* algebraic
  generator joins the catalog.
- **A cross-family surprise.** In the property matrix, RC6's mixing scores
  `NL=0, DU=256` — GF(2)-linear-grade *weak* as an S-box — despite being an
  excellent ring permutation, because it preserves bit 0 (= x₀) and flipping the
  top input bit yields a constant XOR difference. "Good by Rivest–Black, bad by
  GF(2) S-box criteria" is precisely the kind of insight the unified view
  surfaces.
- **Zech compresses 7.3×.** The identity `Z(2x)=2Z(x)` holds across the table,
  so the 255 entries collapse to 35 two-cyclotomic cosets.
- **The negacyclic wall.** A LUT read by blind rotation in `Z[X]/(Xᴺ+1)` is
  exact on `[0,N)` but returns `−f` on `[N,2N)`; a padding bit restores
  exactness. Another structural "fundamental limit," alongside the project's
  impossibility results.
- **Tabulation's honest ceiling.** Four "rectangle" keys XOR to zero, the exact
  obstruction to 4-independence (while 3-independence and Chernoff bounds hold).

## Recorded as reference (not modeled)

These are real and important but need hardware/quantum/crypto machinery beyond a
pure-math model:

- **§1 Tower-field S-boxes.** GF(2⁸) ≅ GF((2⁴)²) ≅ GF(((2²)²)²); inversion drops
  to one GF(2⁴) inversion plus multiplications, and GF(2²) inversion is a linear
  bit-swap. Canright's normal-basis design (≈120 gates), Boyar–Peralta's
  logic-minimized 113-gate variant, and later *area* records that replace AND
  with NAND/NOR are all *generators* of the same unique inverse table, optimized
  for silicon. Our "equivalent generators" finding is the pure-math shadow of
  this.
- **§1.3 Masking / side-channel resilience.** Tower fields make additive masks
  propagate predictably through the (linear) GF(2²) step, enabling CPA-resistant
  implementations.
- **§1.4 Quantum / dynamic S-boxes.** OTQuSbox-style session S-boxes from
  quantum entropy (reported NL 108, DU 10); in-circuit S-boxes whose T-gate cost
  is reduced via normal-basis decomposition.
- **§2 CKKS vs TFHE; circuit bootstrapping + vertical packing (6–20-bit LUTs);
  the Fixed-Point TFHE accelerator (≈35 µs/PBS on FPGA); multi-key TFHE.**
- **§3.3 Chebyshev** towers (closure under composition, `Tₘ∘Tₙ=Tₘₙ` — the named
  classical instance of this project's compositional-closure probe) and
  **permutation pentanomials** `Xʳ B(X^{q−1})`.
- **§5.3 Orbiter** isomorph-free classification of Costas/orthogonal arrays /
  t-designs via group actions; **circular Costas** and the Golomb–Moreno
  conjecture.

## The transferable point

The survey's most useful meta-claim, which this repository now demonstrates
mechanically: optimization techniques move across domains once the objects are
recognized as the same kind. The cyclotomic-coset reduction that shrinks a Zech
table is structurally the kind of symmetry one would look for to shrink a TFHE
test polynomial before vertical packing; the logic-minimization heuristics that
shrink an AES S-box could target the gate implementation of a permutation
trellis code. Naming the field is what makes the transfer obvious.
