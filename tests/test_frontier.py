"""Tests for the property-incompatibility frontier.

These pin the impossibility/tradeoff results that constitute the project's
headline claim: bent functions are unbalanced (no bent bijection) and bounded
in degree, linear maps have worst-case differential uniformity, NL/DU are
inverse-invariant, even-distance converters can't span, the minimum-width DU
bound, and the bijective vs correlation-immunity tension.
"""

import unittest

from pgdmc.frontier import (
    grid,
    min_width_for_differential_uniformity,
    run_frontier,
    search_max_correlation_immunity,
)


class TestFrontierResults(unittest.TestCase):
    def setUp(self):
        # small CI budget keeps the test fast; the finding (order 0) is robust
        self.results = {(r.prop_a, r.prop_b): r for r in run_frontier(ci_trials=300)}

    def test_has_all_three_verdicts(self):
        verdicts = {r.verdict for r in self.results.values()}
        self.assertEqual(verdicts, {"INCOMPATIBLE", "TRADEOFF", "COMPATIBLE"})

    def test_no_bent_bijection(self):
        r = self.results[("bijective", "perfect-nonlinear (bent)")]
        self.assertEqual(r.verdict, "INCOMPATIBLE")

    def test_linear_has_worst_du(self):
        r = self.results[("linear (nonlinearity 0)", "low differential uniformity")]
        self.assertEqual(r.verdict, "INCOMPATIBLE")
        self.assertTrue(any("256" in e for e in r.evidence))

    def test_inverse_invariance(self):
        r = self.results[("self-inverse direction", "asymmetric NL/DU profile")]
        self.assertEqual(r.verdict, "INCOMPATIBLE")
        self.assertTrue(any("112/112" in e and "4/4" in e for e in r.evidence))

    def test_aes_is_a_compatible_witness(self):
        r = self.results[("bijective", "high nonlinearity + low DU")]
        self.assertEqual(r.verdict, "COMPATIBLE")


class TestFrontierBounds(unittest.TestCase):
    def test_min_width_formula(self):
        # AES-grade DU=4 on n=8 needs essentially full width.
        self.assertEqual(min_width_for_differential_uniformity(8, 4), 7)
        self.assertEqual(min_width_for_differential_uniformity(8, 256), 1)

    def test_correlation_immunity_is_hard_for_bijections(self):
        # No first-order correlation-immune bijection turns up by random search.
        self.assertEqual(search_max_correlation_immunity(4, 1000, seed=1), 0)


class TestGrid(unittest.TestCase):
    def test_grid_symmetric_lookup(self):
        props, cells = grid()
        self.assertIn("bijective", props)
        # bent x bijective is impossible in either lookup order
        sym = cells.get(("bijective", "bent")) or cells.get(("bent", "bijective"))
        self.assertEqual(sym, "x")


if __name__ == "__main__":
    unittest.main()
