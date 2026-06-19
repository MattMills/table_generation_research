"""Tests for combining generators.

The headline assertions are real facts: the AES S-box *is* a composition of two
simpler generators, a Feistel network manufactures a bijection from a lossy
function, composing x^7 with itself linearizes it, and a difference set develops
into the Fano plane.
"""

import unittest

from pgdmc.combinators import (
    aes_affine_table,
    build_combinations,
    compose,
    direct_sum,
    feistel,
    gf16_power_table,
    gf_inverse_table,
    whiten,
    xor_combine,
)
from pgdmc.combinatorial_combinations import (
    build_difference_set_design,
    build_graeco_latin,
    build_mols_orthogonal_array,
    mols,
)
from pgdmc.generators.crypto import build_aes_sbox
from pgdmc.generators.sequence import build_gray_code
from pgdmc.properties import (
    Bijective,
    DifferentialUniformity,
    GraecoLatinOrthogonal,
    Nonlinearity,
    OrthogonalArrayProp,
    TwoDesign,
)


def _passes(prop, table):
    return prop.check(table).status.value == "PASS"


class TestComposition(unittest.TestCase):
    def test_aes_is_affine_after_inverse(self):
        """The canonical 'two generators -> a famous table' result."""
        combined = compose(gf_inverse_table(), aes_affine_table())
        self.assertEqual(combined.data, build_aes_sbox().data)

    def test_composition_preserves_bijection(self):
        combined = compose(gf_inverse_table(), aes_affine_table())
        self.assertTrue(_passes(Bijective(), combined))

    def test_composition_can_destroy_nonlinearity(self):
        # x^7 o x^7 = x^49 = x^4 over GF(2^4): the linear Frobenius map.
        x7 = gf16_power_table(7)
        collapse = compose(x7, x7)
        x4 = gf16_power_table(4)
        self.assertEqual(collapse.data, x4.data)
        self.assertEqual(Nonlinearity().check(collapse).value, 0)
        self.assertGreater(Nonlinearity().check(x7).value, 0)

    def test_whiten_preserves_nl_and_du(self):
        sbox = build_aes_sbox()
        w = whiten(sbox, 0x5A, 0x3C)
        self.assertEqual(Nonlinearity().check(w).value, 112)
        self.assertEqual(DifferentialUniformity().check(w).value, 4)


class TestFeistel(unittest.TestCase):
    def test_creates_bijection_from_non_bijection(self):
        lossy = [(x * x) % 16 for x in range(16)]  # collisions -> not a bijection
        self.assertNotEqual(sorted(lossy), list(range(16)))
        net = feistel(lossy, half_bits=4, rounds=3)
        self.assertTrue(_passes(Bijective(), net))


class TestOtherCombinators(unittest.TestCase):
    def test_xor_of_permutations_breaks_bijectivity(self):
        xored = xor_combine(build_aes_sbox(), build_gray_code(8))
        self.assertFalse(_passes(Bijective(), xored))

    def test_direct_sum_widens_but_weakens(self):
        x7 = gf16_power_table(7)
        wide = direct_sum(x7, x7)
        self.assertTrue(_passes(Bijective(), wide))
        # Differential uniformity degrades multiplicatively vs the 4-bit part.
        part_du = DifferentialUniformity().check(x7).value
        wide_du = DifferentialUniformity().check(wide).value
        self.assertGreater(wide_du, part_du)


class TestCombinatorialCombinations(unittest.TestCase):
    def test_mols_are_pairwise_orthogonal(self):
        n = 5
        squares = mols(n)
        self.assertEqual(len(squares), n - 1)
        for i in range(len(squares)):
            for j in range(i + 1, len(squares)):
                pairs = {(squares[i][r][c], squares[j][r][c])
                         for r in range(n) for c in range(n)}
                self.assertEqual(len(pairs), n * n)

    def test_graeco_latin_orthogonal(self):
        self.assertTrue(_passes(GraecoLatinOrthogonal(), build_graeco_latin(5)))

    def test_mols_build_orthogonal_array(self):
        self.assertTrue(_passes(OrthogonalArrayProp(), build_mols_orthogonal_array(5, 3)))

    def test_difference_set_develops_to_fano_plane(self):
        design = build_difference_set_design(7)
        result = TwoDesign().check(design)
        self.assertEqual(result.status.value, "PASS")
        self.assertEqual(result.value, 1)  # lambda = 1 -> the 2-(7,3,1) Fano plane


class TestCombinationCatalog(unittest.TestCase):
    def test_all_combinations_build(self):
        combos = build_combinations()
        self.assertTrue(len(combos) >= 5)
        for c in combos:
            self.assertTrue(c.parents and c.new_purpose and c.effect)


if __name__ == "__main__":
    unittest.main()
