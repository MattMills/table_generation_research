# Property-Guaranteed Discrete Mapping Construction (`pgdmc`)

> *"I wonder if we referenced it as a method to generate a computationally useful
> lookup table, we'd have a whole research field and category of similar methods."*

This repository is a runnable exploration of exactly that thought. It takes a
loose conversational hunch — that CRC tables, AES S-boxes, log/antilog tables,
LFSR sequences, Gray codes, FFT twiddle factors, Latin squares, Costas arrays,
Zobrist keys and the rest are all *the same kind of object* — and turns it into
working code that builds those tables, **verifies** the properties they
promise, lays them side by side on common axes, and uses that apparatus to map
the real prize: **which property guarantees provably cannot coexist.**

> **The headline is the [property-incompatibility frontier](docs/frontier.md).**
> A catalog tells you what exists; the frontier tells you what *can't* — and
> that is the claim with teeth. The catalog, matrix, and combinator algebra are
> the instrument used to find the boundary. Run `python explore.py frontier`.

The frontier is written up in [`docs/frontier.md`](docs/frontier.md). The seed
conversation is in [`docs/conversation.md`](docs/conversation.md), the taxonomy
in [`docs/taxonomy.md`](docs/taxonomy.md), the study of *combining* generators
in [`docs/combinations.md`](docs/combinations.md), and a literature review in
[`docs/literature_review.md`](docs/literature_review.md).

## The idea in one paragraph

A surprising number of "run an expensive generator once, then do cheap lookups
forever" tables share a single shape:

> **A generator process guarantees an algebraic or statistical *property*; the
> table is just the artifact; the property is the spec you rely on at runtime.**

They look unrelated only because each community files them under its own
mathematical ancestry — abstract algebra, coding theory, cryptography,
combinatorics, DSP. Put them in one room and compare them on the *properties*
instead of the *ancestry*, and structure appears.

## Three classifying axes

The conversation arrived at three axes that actually distinguish these methods.
They are first-class fields on every `Generator` in the code:

| Axis | Question | Field |
|------|----------|-------|
| **Family size** | Is the table unique, one of a parametric family, or a fresh random draw? | `family_size` |
| **Method** | Is generation a closed-form *recipe* or a *search*? | `constructive` |
| **Property class** | *Which* guarantee is being promised? | `guarantees` |

## The thesis: which guarantees provably cannot coexist

This is the contribution (`python explore.py frontier`, full writeup in
[`docs/frontier.md`](docs/frontier.md)). Each row is computed and witnessed live.

**Provably impossible:**

| Property A | Property B | Why | Witness |
|---|---|---|---|
| bijective | entropy-flattening | a bijection only relabels mass ⇒ entropy invariant | H(in)=H(out)=2.27 bits |
| bijective | perfect-nonlinear (bent) | permutation components are balanced; bent functions aren't | bent(6) weight 28≠32 |
| linear (NL=0) | low differential uniformity | linear ⇒ DU = 2ⁿ (worst) | rotate-by-1: NL 0, DU 256 |
| bent | algebraic degree > n/2 | bent degree ≤ n/2 (hard bound) | bent(6) degree 2 |
| self-inverse | asymmetric NL/DU | NL, DU are inverse-invariant | AES vs AES⁻¹: 112/112, 4/4 |
| distance-1→d | even d | even-weight columns can't span GF(2)ⁿ | weight-2 spans rank 3/4 |

**Bounded tradeoffs:** AES-grade DU=4 from width-w block lookups forces
**w ≥ 7** of 8 (a hard minimum width); no correlation-immune bijection appears
in random search up to n=6.

**Sharp positives:** AES S-box (bijective + NL 112 + DU 4); GF(2⁵) cube
(APN *and* algebraic degree 2 — low degree and low DU do coexist).

The point of stating impossibilities precisely is the same as the point of the
whole project: a reason that closes a door (an invariant, a counting fact, a
spanning obstruction) is worth more than another construction that happens to
work.

## What's implemented (the instrument)

Eight families, ~26 generators, ~27 property verifiers — all dependency-free
(pure Python standard library, no numpy):

- **Algebraic** — GF(2⁸) log/antilog, Zech logarithm (cyclotomic-compressible), GF inverse map, permutation polynomial, RC6 ring-polynomial mixing
- **Sequence** — maximal-length LFSR, de Bruijn sequence, Gray code
- **Transform** — FFT twiddle factors, Walsh–Hadamard matrix, DCT matrix, NTT roots
- **Cryptographic** — AES S-box, bent function, DES S-box (the search-found one)
- **Combinatorial** — Latin square, Costas array, Paley difference set, orthogonal array
- **Hashing** — Zobrist keys, tabulation hashing
- **Error-correction** — CRC table, Hamming(7,4) syndrome table
- **Speculative** — degree-bounded, multi-resolution, and distance-converting constructions

Every generator's *declared* guarantee is checked against its actual table on
every run (35/35 verified), so the catalog is self-testing.

## Run it

```bash
python explore.py             # the whole story, in seven acts
python explore.py frontier    # THE HEADLINE: which properties provably can't coexist
python explore.py taxonomy    # the generators, grouped and annotated by axis
python explore.py specs       # confirm each generator meets its own guarantee
python explore.py matrix      # the cross-family property matrix
python explore.py speculative # property-first feasibility probes
python explore.py combine     # combine generators into new-purpose tables
python explore.py literature  # survey-grounded extensions, made runnable

python -m unittest discover -s tests   # 58 tests, asserting known constants
```

## The payoff: one matrix, opposite ends

Running the broadly-applicable properties against every table is where the
framing earns its keep. The CRC table and the AES S-box are *both* 256-entry
byte permutations — the same artifact shape — yet:

```
table                     |  Bij  Inv   NL   DU  SAC   Aval   CI  Deg
AES S-box                 |    Y    N  112    4 0.0625 0.5049  0    7
CRC-8 table               |    Y    N    0  256  0.5   0.4062  0    1
8-bit Gray code           |    Y    N    0  256  0.5   0.2344  0    1
GF(2^5) cube              |    Y    N   12    2  0.5   0.54    0    2
```

`NL` (nonlinearity) splits them cleanly: the AES S-box is maximally non-linear
(112), while the CRC and Gray tables are perfectly *linear* (0) — which is
exactly why they're cheap checksum/counting tables and useless as cipher
S-boxes. Same shape, opposite spec. The GF(2⁵) cube is an APN map (differential
uniformity 2, the optimum). The matrix makes these cross-family facts visible at
a glance.

## The speculative probes (how the frontier is discovered)

The frontier above is distilled from property-first probes
(`python explore.py speculative`) — pick a property, ask what can be built, and
report honestly when the answer is "nothing":

| Construction | Verdict | Finding |
|---|---|---|
| Entropy-redistribution bijection | **IMPOSSIBLE** | A bijection only relabels probability mass, so entropy is invariant — needs a lossy/expanding map (extractors, arithmetic coding). |
| Distance-converting table (dist-1 → dist-*d*) | **CHARACTERISED** | Reduces to an invertible binary matrix with all columns of weight *d*; the search discovers *d* must be **odd**. |
| Self-inverse / asymmetric profile | **CHARACTERISED** | NL and DU are *inverse-invariant*; only a non-invariant property like **algebraic degree** can differ. |
| Minimum sub-table width (streaming) | **CHARACTERISED** | Block-diagonal width-w lookups give DU ≥ 2^(n−w+1); AES-grade DU=4 on n=8 needs **w ≥ 7**. |
| Avalanche-optimal (exact SAC) | **SEARCH-FOUND** | 4608 exact-SAC bijections at n=3 (exhaustive); found at n=4 by randomized search. |
| Degree-bounded / multi-resolution / compositional-closure / disjoint-coverage | **CONSTRUCTED** | Each is buildable with a clean recipe; see the probe output. |

The impossibilities and bounds here are exactly what the frontier
(`python explore.py frontier`) collects and cross-witnesses.

## Combining generators (the generative half)

The most direct evidence for "reframing surfaces new methods" is that the famous
tables are *already* combinations. `python explore.py combine` reproduces and
generalizes that:

> **AES S-box = (affine map) ∘ (GF(2⁸) inverse)** — verified byte-for-byte.

A small algebra of combinators (compose, Feistel, direct-sum, XOR) yields a
**property algebra of combination** — which guarantees survive, which are
created, which are destroyed:

| Combinator | Inputs | Effect | Witness |
|---|---|---|---|
| compose | affine ∘ nonlinear | nonlinearity is **free** | GF inverse NL 112 → S-box NL 112 |
| compose | nonlinear ∘ nonlinear | can **destroy** it | x⁷∘x⁷ = x⁴ (linear): NL 4 → 0 |
| Feistel | any (even lossy) function | **creates** bijectivity | bijection from squaring-mod-16 |
| direct-sum | two narrow S-boxes | **degrades** differential uniformity | DU 4 → 64 |
| XOR | permutation ⊕ permutation | **destroys** bijectivity | AES ⊕ Gray ≠ permutation |

And the combinatorial family turns out to be combinations all the way down:
two orthogonal **Latin squares → a Graeco-Latin square**; *k* MOLS → an
**orthogonal array** of strength 2; a **difference set developed under Z₇ → the
Fano plane** (the 2-(7,3,1) design). See [`docs/combinations.md`](docs/combinations.md).

## Survey-grounded extensions (existing works, made runnable)

`python explore.py literature` folds in methods from a literature survey of the
field, each verified live and tagged by how it relates to the project —
**VALIDATES** (confirms what we built), **EXTENDS** (the real version of a toy),
or **NEW**:

- **Equivalent generators** — log/antilog, Fermat x²⁵⁴, and search all produce
  the *identical* GF(2⁸) inverse (the unique table behind tower-field S-boxes).
- **Ring permutation polynomials** — RC6's `x(2x+1) mod 2ʷ`, with the exact
  Rivest–Black test. (Its matrix row is a lesson: a perfect *ring* permutation
  that is `NL=0, DU=256` — weak by GF(2) S-box metrics.)
- **MBA obfuscation** — an identically-zero Mixed Boolean-Arithmetic expression
  plus an inverse permutation-polynomial encode/decode pair.
- **Homomorphic LUT (TFHE)** — a plaintext model of programmable bootstrapping;
  the **negacyclic boundary** negates the upper half unless a padding bit is set.
- **Distance-increasing mapping** — the real Ferreira–Swart–Vinck DIM (binary
  words → symbol permutations), the literature framing of our distance probe.
- **Costas thumbtack autocorrelation**, **tabulation's 4-independence failure**,
  and **Zech cyclotomic-coset compression** (255 → 35 cosets, 7.3×).

See [`docs/literature_review.md`](docs/literature_review.md), which also catalogs
the reference-only items (Canright/Boyar–Peralta gate counts, masking, quantum
S-boxes, circuit bootstrapping, Orbiter classification).

## Layout

```
pgdmc/
  core.py          Table / Generator / Property / Registry abstractions
  bitmath.py       Walsh-Hadamard, Mobius/ANF, popcount, GF(2) bit utilities
  gf.py            GF(2^n) arithmetic (the shared "polynomial machinery")
  properties.py    ~27 runtime-checkable property verifiers
  frontier.py      THE HEADLINE: property-incompatibility results (impossible/tradeoff/compatible)
  generators/      one module per family (+ rings.py, speculative.py)
  combinators.py   compose / Feistel / direct-sum / XOR / whiten + property algebra
  combinatorial_combinations.py   MOLS -> Graeco-Latin / orthogonal array; difference set -> design
  distance_mappings.py   Ferreira-Swart-Vinck DCM/DIM (binary words -> permutations)
  homomorphic.py   plaintext model of TFHE programmable bootstrapping (negacyclic LUT)
  survey.py        literature-review extensions, each verified live
  catalog.py       assemble everything; build the property matrix; verify specs
  report.py        text rendering of frontier / taxonomy / matrix / probes / combinations / survey
explore.py         CLI entry point (leads with the frontier)
tests/             unittest suite asserting known constants (AES, bent, APN, Fano, RC6, frontier, ...)
docs/              the frontier (read first), conversation, taxonomy, combinations, literature review
```

## Scope and honesty

This is an *exploration*, not a crypto/coding library — don't use these tables in
production. Property checks are exact where feasible and clearly marked
statistical (hashing) or bounded-by-width (large outputs report `n/a` rather than
running an intractable enumeration) where not. The verified constants (AES S-box
bytes, nonlinearity 112, differential uniformity 4, the bent bound, GF
multiplication example `{57}·{83}={c1}`) anchor the rest.
