# Property-Guaranteed Discrete Mapping Construction (`pgdmc`)

> *"I wonder if we referenced it as a method to generate a computationally useful
> lookup table, we'd have a whole research field and category of similar methods."*

This repository is a runnable exploration of exactly that thought. It takes a
loose conversational hunch — that CRC tables, AES S-boxes, log/antilog tables,
LFSR sequences, Gray codes, FFT twiddle factors, Latin squares, Costas arrays,
Zobrist keys and the rest are all *the same kind of object* — and turns it into
working code that builds those tables, **verifies** the properties they
promise, lays them side by side on common axes, and then flips the question
around to ask what *new* tables a property-first view can produce.

The seed conversation is preserved in [`docs/conversation.md`](docs/conversation.md).
A longer written treatment of the taxonomy is in [`docs/taxonomy.md`](docs/taxonomy.md).

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

## What's implemented

Eight families, ~25 generators, ~20 property verifiers — all dependency-free
(pure Python standard library, no numpy):

- **Algebraic** — GF(2⁸) log/antilog, Zech logarithm, GF inverse map, permutation polynomial
- **Sequence** — maximal-length LFSR, de Bruijn sequence, Gray code
- **Transform** — FFT twiddle factors, Walsh–Hadamard matrix, DCT matrix, NTT roots
- **Cryptographic** — AES S-box, bent function, DES S-box (the search-found one)
- **Combinatorial** — Latin square, Costas array, Paley difference set, orthogonal array
- **Hashing** — Zobrist keys, tabulation hashing
- **Error-correction** — CRC table, Hamming(7,4) syndrome table
- **Speculative** — degree-bounded, multi-resolution, and distance-converting constructions

Every generator's *declared* guarantee is checked against its actual table on
every run (31/31 verified), so the catalog is self-testing.

## Run it

```bash
python explore.py             # the whole story, in four acts
python explore.py taxonomy    # the generators, grouped and annotated by axis
python explore.py specs       # confirm each generator meets its own guarantee
python explore.py matrix      # the cross-family property matrix (the payoff)
python explore.py speculative # property-first feasibility probes

python -m unittest discover -s tests   # 27 tests, asserting known constants
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

## The interesting half: what *can't* be built

The speculative probes (`python explore.py speculative`) are honest — several
"wouldn't it be nice" tables turn out to be **provably impossible**, and saying
so precisely is the point:

| Construction | Verdict | Finding |
|---|---|---|
| Entropy-redistribution bijection | **IMPOSSIBLE** | A bijection only relabels probability mass, so entropy is invariant — you cannot flatten a biased byte without a lossy/expanding map (extractors, arithmetic coding). |
| Distance-converting table (dist-1 → dist-*d*) | **CHARACTERISED** | Reduces to: an invertible binary matrix with all columns of weight *d*. The search discovers *d* must be **odd** (even-weight columns can't span). |
| Self-inverse / asymmetric profile | **CHARACTERISED** | Nonlinearity and differential uniformity are *inverse-invariant* (always equal forward/inverse); only a non-invariant property like **algebraic degree** can differ. |
| Correlation-immune bijection | **LIMITED** | Bijectivity caps achievable correlation immunity — a concrete property *incompatibility*. |
| Avalanche-optimal (exact SAC) | **SEARCH-FOUND** | 4608 exact-SAC bijections exist at n=3; smallest size and count are made precise. |
| Degree-bounded / multi-resolution / compositional-closure / disjoint-coverage / streaming-decomposable | **CONSTRUCTED** | Each is buildable with a clean recipe; see the probe output. |

Knowing which property *combinations* are unreachable is the "fundamental
limits" half of the proposed research field.

## Layout

```
pgdmc/
  core.py          Table / Generator / Property / Registry abstractions
  bitmath.py       Walsh-Hadamard, Mobius/ANF, popcount, GF(2) bit utilities
  gf.py            GF(2^n) arithmetic (the shared "polynomial machinery")
  properties.py    ~20 runtime-checkable property verifiers
  generators/      one module per family (+ speculative.py for the probes)
  catalog.py       assemble everything; build the property matrix; verify specs
  report.py        text rendering of taxonomy / matrix / probes
explore.py         CLI entry point
tests/             unittest suite asserting known constants (AES, bent, APN, ...)
docs/              the seed conversation and the taxonomy writeup
```

## Scope and honesty

This is an *exploration*, not a crypto/coding library — don't use these tables in
production. Property checks are exact where feasible and clearly marked
statistical (hashing) or bounded-by-width (large outputs report `n/a` rather than
running an intractable enumeration) where not. The verified constants (AES S-box
bytes, nonlinearity 112, differential uniformity 4, the bent bound, GF
multiplication example `{57}·{83}={c1}`) anchor the rest.
