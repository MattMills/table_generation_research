# A taxonomy of property-guaranteed discrete mapping construction

This document is the written companion to the code. It expands the seed
conversation ([`conversation.md`](conversation.md)) into a structured taxonomy
and records what the implementation actually found.

## The unifying shape

Every object below is built once, expensively, and then used many times,
cheaply. What makes them a *category* rather than a coincidence is that the
expensive step exists to guarantee a **property** that would be costly or
impossible to check per-operation at runtime:

```
        generator (expensive, run once)
   spec  ─────────────────────────────────▶  table (the artifact)
 (a property)                                   │
                                                ▼
                                      runtime lookups (cheap, exact,
                                      relying on the guaranteed property)
```

The *values* in the table are incidental; the *property of the mapping* is the
product. That is the through-line connecting a CRC table to a Costas array.

## The three axes

| Axis | Values | Why it matters |
|------|--------|----------------|
| **Family size** | unique · parametric · random ensemble | Determines whether "which table" is a question at all. A given GF polynomial fixes one log table; Zobrist hashing gives a fresh valid table per seed. |
| **Method** | recipe (constructive) · search | Algebraic generators follow closed forms; DES S-boxes were *found* by searching candidates against criteria. Different methodology, different guarantees of optimality. |
| **Property class** | reversibility, non-linearity, differential uniformity, orthogonality, distance, uniform distribution, covering, … | The actual spec. Some property classes are provably incompatible (see "limits" below). |

## The catalog, by family

| Family | Generator | Method | Family size | Guaranteed property |
|--------|-----------|--------|-------------|---------------------|
| Algebraic | GF log/antilog | recipe | parametric | covers every nonzero element |
| Algebraic | Zech logarithm | recipe | parametric | (derived addition table) |
| Algebraic | GF inverse map | recipe | parametric | bijective, involution |
| Algebraic | permutation polynomial | recipe | parametric | bijective |
| Sequence | maximal-length LFSR | recipe | parametric | visits all 2ⁿ−1 nonzero states |
| Sequence | de Bruijn | recipe | parametric | every n-window once |
| Sequence | Gray code | recipe | unique | bijective, single-bit adjacency |
| Transform | FFT twiddles | recipe | unique | complex Nth roots of unity |
| Transform | Walsh–Hadamard | recipe | unique | orthogonal rows |
| Transform | DCT | recipe | unique | orthonormal rows |
| Transform | NTT | recipe | parametric | primitive root of unity (mod p) |
| Cryptographic | AES S-box | recipe | unique | bijective, NL 112, DU 4 |
| Cryptographic | bent function | recipe | parametric | maximal nonlinearity |
| Cryptographic | DES S-box | **search** | unique | low differential / linear bias |
| Combinatorial | Latin square | recipe | parametric | symbol once per row & column |
| Combinatorial | Costas array | recipe | parametric | distinct displacement vectors |
| Combinatorial | difference set | recipe | parametric | uniform difference multiset |
| Combinatorial | orthogonal array | recipe | parametric | strength-2 column balance |
| Hashing | Zobrist | **random** | random ensemble | distinct keys, uniform bits (statistical) |
| Hashing | tabulation | **random** | random ensemble | k-independence (statistical) |
| Error-correction | CRC table | recipe | parametric | bijective (linear) |
| Error-correction | syndrome table | recipe | unique | bijective syndrome↔error |
| Speculative | degree-bounded | recipe | parametric | bijective, algebraic degree 2 |
| Speculative | multi-resolution | recipe | parametric | bijective + truncatable |
| Speculative | distance converter | recipe | parametric | constant per-bit output distance |

Notice the axes do real work: the hashing family is the only one that is
*random ensemble* + *statistical guarantee*, which is precisely why it feels
different from the algebraic families even though it produces the same kind of
artifact. And DES is the lone *search* method among the classical S-boxes.

## The cross-family property matrix

This is the comparison the conversation asked for — every broadly-applicable
property run against every table (live output of `python explore.py matrix`):

```
table                                        |  Bij  Inv   NL   DU  SAC Aval   CI  Deg
--------------------------------------------------------------------------------------
GF(2^8) inverse map                          |    Y    Y  112    4 0.0469 0.5032    0    7
GF(2^4) x^7 permutation                      |    Y    N    4    4 0.25 0.5625    0    3
8-bit Gray code                              |    Y    N    0  256  0.5 0.2344    0    1
AES S-box                                    |    Y    N  112    4 0.0625 0.5049    0    7
bent function (n=6)                          |    ·    ·   28   32    0  0.5    0    2
DES S-box S1                                 |    ·    ·   14   16 0.25 0.6198    0    5
CRC-8 table (poly 0x7)                       |    Y    N    0  256  0.5 0.4062    0    1
Hamming(7,4) syndrome table                  |    Y    N    0    8  0.5 0.7222    0    2
GF(2^5) cube (degree-bounded)                |    Y    N   12    2  0.5 0.54    0    2
distance-1->3 converter (n=4)                |    Y    Y    0   16  0.5 0.75    0    1
```

Things this surfaces that the siloed view hides:

- **Same artifact, opposite spec.** The CRC-8 table and the AES S-box are both
  byte bijections. The CRC table has nonlinearity **0** (it is GF(2)-linear,
  which is *why* it makes a cheap checksum) and the worst possible differential
  uniformity (256). The AES S-box has nonlinearity **112** and differential
  uniformity **4**. The framework puts them in the same row format and lets the
  numbers do the talking.
- **The Gray code is linear too.** `g(i) = i ⊕ (i>>1)` is a linear bijection, so
  it also lands at nonlinearity 0 — sharing a column-profile with CRC despite
  coming from a totally different lineage (sequence vs coding theory).
- **The affine layer is cosmetic for NL/DU.** The raw GF(2⁸) inverse map already
  has nonlinearity 112 and differential uniformity 4; the AES affine wrapper
  changes neither. The cross-matrix makes the inheritance obvious.
- **APN in the wild.** The GF(2⁵) cube map reaches differential uniformity 2
  (the optimum for odd n) — visible right next to the byte-width boxes.

## Fundamental limits (the most interesting output)

The property-first probes (`python explore.py speculative`) include several that
resolve to impossibility or a crisp characterization. These are the "what
property combinations are achievable" results the conversation predicted:

- **Entropy redistribution by a bijection is impossible.** A bijection only
  relabels symbols, so it permutes the multiset of probabilities and leaves
  entropy unchanged. "Bijective AND debiasing" is contradictory on equal
  domains; you need a lossy or expanding map (the domain of randomness
  extractors and arithmetic coding).
- **Distance conversion ⇒ an odd-weight spanning condition.** A table sending
  every Hamming-distance-1 input pair to output distance exactly *d* exists (in
  the linear case) iff there is an invertible binary matrix whose columns all
  have weight *d*. Even *d* is impossible — even-weight vectors live in the
  parity-zero subspace and cannot span — so only odd *d* (that also span) work.
  The vague wish became a decidable linear-algebra question.
- **Inverse-invariance constrains "asymmetric" tables.** Nonlinearity and
  differential uniformity are identical for a map and its inverse, so you can
  never make them differ between the forward and reverse directions. Algebraic
  degree is *not* inverse-invariant (x³ over GF(2⁵) has degree 2; its inverse
  x²¹ has degree 3), so that is where asymmetry can actually live.
- **Bijectivity caps correlation immunity.** Searching all 3-bit bijections, the
  best achievable correlation-immunity order is 0 — a concrete instance of two
  property classes that fight each other.

## Why the field doesn't already exist (and what it would add)

Each community optimizes one property and files its tables by ancestry: crypto
wants non-linearity, coding theory wants distance, DSP wants orthogonality,
experiment design wants balance. They rarely compare *construction methods*
across property classes. A unified "property-guaranteed discrete mapping
construction" view would (a) make the cross-family matrix above routine, (b)
turn speculative "wouldn't it be nice" tables into decidable existence questions,
and (c) map the incompatibility frontier between property classes. This repo is a
small, runnable down-payment on (a)–(c).
