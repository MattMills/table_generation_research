"""Tests for the survey-grounded extensions.

These pin the facts the literature review contributes: the Rivest-Black
characterization, the MBA null and inverse-PP pair, Zech cyclotomic
compression, tabulation's 4-independence failure, a verified distance-increasing
mapping, Costas thumbtack autocorrelation, the negacyclic LUT boundary, and the
agreement of several inverse generators.
"""

import unittest

from pgdmc.distance_mappings import build_distance_increasing_mapping, distance_mapping_stats
from pgdmc.generators.hashing import tabulation_4independence_failure
from pgdmc.generators.rings import (
    build_rc6_mixing,
    mba_null,
    obfuscation_inverse_pair,
    permutation_polynomial_mod_2w,
)
from pgdmc.homomorphic import negacyclic_readout, programmable_bootstrap_demo
from pgdmc.properties import (
    Bijective,
    CyclotomicCompressible,
    DistanceIncreasing,
    RivestBlackPermutation,
    ThumbtackAutocorrelation,
)
from pgdmc.generators.algebraic import build_zech_logarithm
from pgdmc.generators.combinatorial import build_costas_array
from pgdmc.survey import run_survey_extensions


def _passes(prop, table):
    return prop.check(table).status.value == "PASS"


class TestRingPolynomials(unittest.TestCase):
    def test_rc6_is_rivest_black_permutation(self):
        rc6 = build_rc6_mixing(8)
        self.assertTrue(_passes(Bijective(), rc6))
        self.assertTrue(_passes(RivestBlackPermutation(), rc6))

    def test_rivest_black_rejects_non_permutation(self):
        # a1 even -> not a permutation; the predicate and reality must agree.
        bad = permutation_polynomial_mod_2w([0, 2, 1], 8)  # a1 = 2 (even)
        self.assertFalse(_passes(Bijective(), bad))
        self.assertFalse(_passes(RivestBlackPermutation(), bad))

    def test_mba_null_is_zero(self):
        self.assertTrue(all(mba_null(x, y, 8) == 0 for x in range(256) for y in range(256)))

    def test_obfuscation_pair_round_trips(self):
        encode, decode = obfuscation_inverse_pair(8)
        self.assertTrue(all(decode(encode(x)) == x for x in range(256)))


class TestZechCompression(unittest.TestCase):
    def test_cyclotomic_identity_and_ratio(self):
        zech = build_zech_logarithm()
        result = CyclotomicCompressible().check(zech)
        self.assertEqual(result.status.value, "PASS")
        self.assertEqual(result.value, 7.29)  # 255 entries -> 35 cosets


class TestTabulation(unittest.TestCase):
    def test_4independence_failure(self):
        self.assertTrue(tabulation_4independence_failure()["cancels_to_zero"])


class TestDistanceMapping(unittest.TestCase):
    def test_star_construction_is_dim(self):
        for n in (3, 4, 5):
            dim = build_distance_increasing_mapping(n)
            result = DistanceIncreasing().check(dim)
            self.assertEqual(result.status.value, "PASS")
            self.assertEqual(result.value, "DIM")
            self.assertGreaterEqual(distance_mapping_stats(dim)["min_gain"], 1)


class TestCostasAutocorrelation(unittest.TestCase):
    def test_thumbtack(self):
        result = ThumbtackAutocorrelation().check(build_costas_array(11, 2))
        self.assertEqual(result.status.value, "PASS")
        self.assertLessEqual(result.value, 1)


class TestHomomorphicLUT(unittest.TestCase):
    def test_negacyclic_sign_flip_and_padding(self):
        demo = programmable_bootstrap_demo(8)
        self.assertFalse(demo.exact_without_padding)  # upper half is negated
        self.assertTrue(demo.exact_with_padding)      # padding bit fixes it

    def test_readout_formula(self):
        v = [5, 1, 7, 3]  # N = 4
        # lower half exact, upper half negated
        self.assertEqual(negacyclic_readout(v, 2), 7)
        self.assertEqual(negacyclic_readout(v, 6), -7)  # 6 = 2 + N


class TestSurveyRuns(unittest.TestCase):
    def test_all_findings_build(self):
        findings = run_survey_extensions()
        self.assertEqual(len(findings), 8)
        for f in findings:
            self.assertIn(f.relation, {"VALIDATES", "EXTENDS", "NEW"})
            self.assertTrue(f.evidence)


if __name__ == "__main__":
    unittest.main()
