# Seed conversation

This is the conversation that this repository explores. It is preserved here
verbatim as the origin and motivation for the `pgdmc` package. The code in this
repo is an attempt to take the ideas below seriously enough to *run* them.

---

> **I wonder if we referenced it as a method to generate a computationally
> useful lookup table, we'd have a whole research field and category of similar
> methods.**

That's a genuinely interesting thought. Because when you frame it that way, you
start noticing things that are obviously siblings but nobody treats as related
because they come from different mathematical lineages.

CRC polynomial tables, for instance. Same basic premise — run some polynomial
math once to generate a lookup table that makes a checksum operation fast.
S-boxes in AES — a lookup table generated from GF(256) inverses plus an affine
transform, designed to give you specific non-linearity properties. Permutation
tables in crypto. Log/antilog tables for DSP.

They're all the same shape of thing: run some generator process that guarantees
specific algebraic or statistical properties, get a table, use the table at
runtime. The generator process is the interesting part, the table is the
artifact, and the properties are the spec.

But right now these are scattered across abstract algebra, combinatorics,
cryptography, coding theory, and signal processing, and they're all categorized
by their mathematical ancestry rather than by what they actually do. Nobody
teaches a class called "construction methods for computationally useful lookup
tables and their property guarantees."

And your instinct is probably right that framing it that way would surface new
methods. When you stop asking "what does this algebraic structure imply" and
start asking "what other generators could give me a 256-entry table where
nothing collides," you're asking a much more open-ended question that doesn't
presuppose the solution has to come from polynomial rings.

---

> **I wonder, can you create such a list, what is on it aside from the ones you
> referenced, what is common and uncommon about them?**

(Catalogued lookup table generators and synthesized their common mathematical
properties.) The taxonomy becomes interesting once you lay them side by side:

**Algebraic generators** (the GF family — polynomial machinery produces the
table): GF(2^n) log/antilog tables (reversible multiplication); Zech's logarithm
tables (fast addition in log representation); AES S-boxes (GF(256) inverse +
affine, optimized for non-linearity); permutation polynomials over finite
fields.

**Sequence generators** (feedback/recurrence machinery): LFSR maximal-length
sequences (every nonzero state once); de Bruijn sequences (every n-bit substring
once); Gray codes (adjacent entries differ by one bit).

**Transform coefficient generators** (roots of unity / orthogonality): FFT
twiddle factors; Walsh–Hadamard matrices; Number Theoretic Transform tables;
DCT coefficient tables.

**Cryptographic property generators** (security constraints): DES S-boxes
(hand-designed, partly classified criteria); bent functions (maximally
non-linear); Rijndael's S-box.

**Combinatorial / constraint-satisfaction generators** (the table is a solution
to a constraint problem): Latin squares; Costas arrays; perfect difference sets;
orthogonal arrays.

**Hash / distribution generators** (statistical uniformity): Zobrist hashing;
tabulation hashing.

**Error correction generators** (distance properties): syndrome tables;
Berlekamp–Massey intermediate tables.

**What they all share:** generation is expensive, lookup is cheap; the table
satisfies a provable property that would be expensive to verify per-operation at
runtime; the specific values don't matter, only the properties of the mapping
matter.

**What differentiates them (the axes that would define the field):**

1. Is the table **unique or a family**? (One GF table for a given polynomial vs
   a fresh Zobrist table per seed.)
2. Is generation **constructive or search-based**? (Algebraic recipe vs DES's
   search against criteria.)
3. What **property class** is guaranteed? (Reversibility, non-linearity,
   orthogonality, uniform distribution, maximum distance — and some of these are
   provably incompatible.)

The field might be called "property-guaranteed discrete mapping construction,"
and it doesn't exist as a unified field because each community cares about one
property and has no reason to talk to the communities that care about different
ones.

---

> **I wonder what other types of lookup tables we could find if we were to
> explore property-guaranteed discrete mapping constructions, perhaps you could
> brainstorm some**

Start with a property you want guaranteed, then ask what generator could produce
a table satisfying it:

- **Compositional closure tables** — any chain of K compositions is itself a
  valid table in the family (a group of lookup tables). Useful for skip-ahead /
  rewind in PRNGs and reversible simulation.
- **Multi-resolution tables** — truncating the output still gives a valid
  mapping with weaker guarantees.
- **Algebraic degree-bounded tables** — every output bit is a low-degree
  polynomial of the input bits (matters for homomorphic encryption / MPC).
- **Correlation-immune but high-throughput tables** — knowing any K input bits
  gives zero information about the output.
- **Avalanche-optimal tables** — every input bit flip changes exactly half the
  output bits, exactly (not statistically).
- **Distance-converting tables** — input pairs with Hamming distance D map to
  output pairs with a guaranteed distance.
- **Self-inverse asymmetric tables** — applying twice gives identity, but the
  forward and inverse directions optimize different property profiles.
- **Entropy redistribution tables** — given a biased input distribution, produce
  a table whose output distribution is provably uniform.
- **Differential uniformity with structural constraints** — good crypto
  properties *and* an implementation as at most N two-input gates.
- **Disjoint coverage table families** — a set of tables where every
  input-output pair is covered by exactly one member.
- **Streaming-decomposable tables** — a 16-bit table that decomposes into two
  8-bit lookups plus a cheap combine.

The research field would be: given a formal property spec, what are all the
generator methods that produce conforming tables, what are the trade-offs, and
what are the fundamental limits on which property combinations are achievable?

---

## How this repo responds

- The **taxonomy** and **three axes** become the `Generator` data model and
  `python explore.py taxonomy`.
- "Lay them side by side" becomes the **cross-property matrix**
  (`python explore.py matrix`): every property run against every table.
- The **brainstorm** becomes the speculative probes
  (`python explore.py speculative`), which return honest verdicts — including
  that entropy-redistribution-by-bijection is *impossible* and
  distance-conversion reduces to an odd-weight spanning condition. Those
  "fundamental limits" are the most interesting output.
