"""Tests for the speculative feasibility probes.

The point of these is that the *verdicts* are real results, not narration:
entropy-flattening by a bijection is genuinely impossible, distance conversion
genuinely reduces to an odd-weight spanning condition, and so on.
"""

import unittest

from pgdmc.generators.speculative import (
    build_distance_converting_table,
    explore_algebraic_degree_bounded,
    explore_compositional_closure,
    explore_disjoint_coverage,
    explore_distance_converting,
    explore_entropy_redistribution,
    explore_multi_resolution,
    explore_self_inverse_asymmetric,
    explore_streaming_decomposable,
)
from pgdmc.bitmath import hamming_distance


class TestSpeculative(unittest.TestCase):
    def test_entropy_redistribution_impossible(self):
        r = explore_entropy_redistribution()
        self.assertEqual(r.verdict, "IMPOSSIBLE")

    def test_distance_converting_only_odd(self):
        r = explore_distance_converting()
        self.assertEqual(r.verdict, "CHARACTERISED")
        # n=4 should admit exactly the odd distances {1, 3}.
        self.assertIn("n=4: distance-1 convertible to d in [1, 3]", r.evidence)

    def test_distance_converter_flips_exactly_d(self):
        table = build_distance_converting_table(n=4, d=3)
        n = 4
        for x in range(1 << n):
            for i in range(n):
                flipped = hamming_distance(table.data[x], table.data[x ^ (1 << i)])
                self.assertEqual(flipped, 3)

    def test_degree_bounded_constructed(self):
        r = explore_algebraic_degree_bounded()
        self.assertEqual(r.verdict, "CONSTRUCTED")
        self.assertTrue(any("degree = 2" in e for e in r.evidence))

    def test_compositional_closure(self):
        r = explore_compositional_closure()
        self.assertEqual(r.verdict, "CONSTRUCTED")

    def test_multi_resolution(self):
        r = explore_multi_resolution()
        self.assertEqual(r.verdict, "CONSTRUCTED")

    def test_disjoint_coverage(self):
        r = explore_disjoint_coverage()
        self.assertEqual(r.verdict, "CONSTRUCTED")

    def test_streaming_decomposable(self):
        r = explore_streaming_decomposable()
        self.assertEqual(r.verdict, "CONSTRUCTED")

    def test_self_inverse_nl_du_invariant(self):
        r = explore_self_inverse_asymmetric()
        self.assertEqual(r.verdict, "CHARACTERISED")
        # NL/DU must be equal forward vs inverse; degree must differ.
        self.assertTrue(any("112/112" in e for e in r.evidence))
        self.assertTrue(any("degree fwd = 2, inverse (x^21) = 3" in e for e in r.evidence))


if __name__ == "__main__":
    unittest.main()
