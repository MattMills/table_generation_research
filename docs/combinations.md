# Combining generators

This note extends the taxonomy ([`taxonomy.md`](taxonomy.md)) with the most
generative operation in the framework: **combining generators**. It responds to
the observation that the seed conversation's whole premise — that a property-first
reframing *surfaces new methods* — is most directly demonstrated by composition,
because the famous tables were already combinations.

Run it: `python explore.py combine`.

## Why combination is the high-yield direction

A single generator answers "what table has property P?". A *combinator* answers
the richer question "if I have a table with property P and one with property Q,
what does combining them give me?" — and the answer is frequently a table with a
*new* purpose that neither parent serves. Crucially, combinators are
**generative of new generators**: a Feistel combinator is a recipe that turns
*any* function into a bijection, so it manufactures an unbounded supply of
bijection-generators out of arbitrary tables.

The canonical proof that this is how real tables are built:

> **AES S-box = (AES affine map) ∘ (GF(2⁸) inverse).**

The code verifies this byte-for-byte (`test_aes_is_affine_after_inverse`). Two
generators from the *algebraic* family compose into the headline object of the
*cryptographic* family.

## A property algebra of composition

Running the combinators and measuring the result yields a small algebra of what
each operation does to the guarantees. Every row below is computed live by
`python explore.py combine`:

| Combinator | Inputs | Effect on properties | Witness |
|---|---|---|---|
| compose | bijection ∘ bijection | **preserves** bijectivity | AES S-box is a bijection |
| compose | affine ∘ nonlinear | nonlinearity is **free** (unchanged) | GF inverse NL 112 → S-box NL 112 |
| compose | nonlinear ∘ nonlinear | can **destroy** nonlinearity | x⁷∘x⁷ = x⁴ (linear): NL 4 → 0 |
| Feistel | any function (even lossy) | **creates** bijectivity | bijection from squaring-mod-16 |
| direct-sum | two narrow S-boxes | preserves bijectivity, **degrades** differential uniformity | DU 4 → 64 (multiplicative) |
| XOR | permutation ⊕ permutation | **destroys** bijectivity | AES ⊕ Gray is not a permutation |

Three of these are genuinely useful design facts:

- **Affine layers are free for NL/DU.** Pre- or post-composing with an affine
  bijection changes neither nonlinearity nor differential uniformity. That is
  *why* the AES S-box can bolt an affine map onto the GF inverse to kill fixed
  points and algebraic simplicity without paying any nonlinearity cost.
- **Composition is not monotone in nonlinearity.** `x⁷ ∘ x⁷ = x⁴⁹ = x⁴` over
  GF(2⁴), and x⁴ is the (linear) Frobenius map. Stacking strong S-boxes can
  *cancel* their strength — a real pitfall, and a "fundamental limit" in the
  same spirit as the speculative impossibilities.
- **Feistel manufactures invertibility.** `(L,R) ↦ (R, L ⊕ F(R))` is a bijection
  for *any* F, so the Feistel combinator promotes an arbitrary (even
  many-to-one) lookup table into a reversible one. Note the subtlety the code is
  careful about: a Feistel's *vectorial* nonlinearity stays 0, because the swap
  leaves one output block as a linear copy of an input block; **avalanche** is
  the honest diffusion metric, and it climbs with rounds (the Luby–Rackoff
  intuition).

## Combinatorial generators are themselves combinations

The combinatorial family is the clearest case where "generators" are really
combinations of simpler ones:

- **Two orthogonal Latin squares → a Graeco-Latin (Euler) square.** Superimpose
  `L₁` and `L₂`; all n² ordered symbol pairs occur exactly once. New purpose:
  pairing two factors without repeats (tournament scheduling, Sudoku-like
  layouts, fractional designs). Verified for order 5 (25/25 distinct pairs).
- **k mutually orthogonal Latin squares → an orthogonal array of strength 2.**
  Stack the row index, column index, and `k` MOLS as columns: every pair of
  columns is balanced. So the orthogonal-array generator in
  `generators/combinatorial.py` is *defined* by combining Latin-square
  generators — `OA(n², k+2, n, 2)` from `k` MOLS.
- **A difference set developed under its cyclic group → a symmetric 2-design.**
  The translates `D, D+1, …, D+(v−1)` of the Paley (7,3,1) difference set are the
  blocks of a 2-(7,3,1) design — **the Fano plane**, the projective plane of
  order 2. Verified: every pair of points lies in exactly λ=1 block.

This closes a loop with the main taxonomy: objects that looked like atomic
"generators" (orthogonal arrays, projective planes) are combinations, which is
exactly the structure the unified view predicts.

## What this adds to the proposed field

If "property-guaranteed discrete mapping construction" were a real field, the
combinator algebra above would be one of its core chapters: a calculus of how
property guarantees transform under composition, summation, Feistel wrapping and
superposition — including the negative results (composition can linearize; XOR
can de-permute; direct sums degrade differential uniformity). Knowing the
algebra lets you *design backwards* from a target property to a sequence of
combinations that reaches it — which is precisely what S-box and block-cipher
designers already do by hand, without naming it as a general method.
