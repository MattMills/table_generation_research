"""Tests for GF arithmetic, generators, and property verifiers.

These assert against *known constants* (the canonical AES S-box bytes, its
nonlinearity 112 and differential uniformity 4, the bent-function bound, etc.)
so the exploration is self-verifying rather than merely self-consistent.
"""

import unittest

from pgdmc.bitmath import algebraic_degree, popcount, walsh_spectrum
from pgdmc.catalog import build_catalog, verify_specs
from pgdmc.gf import (
    AES_DEGREE,
    AES_MODULUS,
    build_exp_log,
    gf_inverse_via_tables,
    gf_mul,
    is_generator,
)
from pgdmc.generators.algebraic import build_gf_inverse
from pgdmc.generators.crypto import build_aes_sbox, build_bent_function
from pgdmc.generators.errorcorrection import build_crc_table
from pgdmc.generators.sequence import build_de_bruijn, build_gray_code, build_lfsr
from pgdmc.properties import (
    Bijective,
    DeBruijnWindows,
    DifferentialUniformity,
    FullCover,
    GrayAdjacent,
    Involution,
    Nonlinearity,
)


class TestGF(unittest.TestCase):
    def test_known_multiplication(self):
        # Canonical AES spec example: {57} . {83} = {c1}.
        self.assertEqual(gf_mul(0x57, 0x83, AES_MODULUS, AES_DEGREE), 0xC1)

    def test_three_is_generator(self):
        self.assertTrue(is_generator(0x03, AES_MODULUS, AES_DEGREE))

    def test_inverse_round_trip(self):
        exp, log = build_exp_log(0x03, AES_MODULUS, AES_DEGREE)
        for x in range(1, 256):
            inv = gf_inverse_via_tables(x, exp, log, AES_DEGREE)
            self.assertEqual(gf_mul(x, inv, AES_MODULUS, AES_DEGREE), 1)
        # 0 maps to 0 by convention.
        self.assertEqual(gf_inverse_via_tables(0, exp, log, AES_DEGREE), 0)


class TestAESSBox(unittest.TestCase):
    def setUp(self):
        self.sbox = build_aes_sbox()

    def test_canonical_first_row(self):
        ref = [0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5,
               0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76]
        self.assertEqual(self.sbox.data[:16], ref)

    def test_specific_values(self):
        self.assertEqual(self.sbox.data[0x53], 0xED)
        self.assertEqual(self.sbox.data[0x00], 0x63)

    def test_is_permutation(self):
        self.assertTrue(Bijective().check(self.sbox).status.value == "PASS")

    def test_nonlinearity_112(self):
        self.assertEqual(Nonlinearity().check(self.sbox).value, 112)

    def test_differential_uniformity_4(self):
        self.assertEqual(DifferentialUniformity().check(self.sbox).value, 4)


class TestOtherGenerators(unittest.TestCase):
    def test_gf_inverse_is_involution(self):
        inv = build_gf_inverse()
        self.assertEqual(Involution().check(inv).status.value, "PASS")
        # Inherits AES-grade properties before any affine layer.
        self.assertEqual(Nonlinearity().check(inv).value, 112)
        self.assertEqual(DifferentialUniformity().check(inv).value, 4)

    def test_bent_function_max_nonlinearity(self):
        # For n=6 the bent bound is 2^5 - 2^2 = 28.
        bent = build_bent_function(6)
        self.assertEqual(Nonlinearity().check(bent).value, 28)

    def test_gray_code_is_linear_bijection(self):
        gray = build_gray_code(8)
        self.assertEqual(Bijective().check(gray).status.value, "PASS")
        self.assertEqual(GrayAdjacent().check(gray).status.value, "PASS")
        # The reflected Gray code is a *linear* map -> nonlinearity 0.
        self.assertEqual(Nonlinearity().check(gray).value, 0)

    def test_crc_table_is_linear_bijection(self):
        crc = build_crc_table()
        self.assertEqual(Bijective().check(crc).status.value, "PASS")
        self.assertEqual(Nonlinearity().check(crc).value, 0)  # same shape, opposite spec

    def test_lfsr_full_period(self):
        lfsr = build_lfsr(8)
        self.assertEqual(len(lfsr.data), 255)
        self.assertEqual(FullCover().check(lfsr).status.value, "PASS")

    def test_de_bruijn_windows(self):
        db = build_de_bruijn(5)
        self.assertEqual(len(db.data), 32)
        self.assertEqual(DeBruijnWindows().check(db).status.value, "PASS")


class TestBitmath(unittest.TestCase):
    def test_popcount(self):
        self.assertEqual(popcount(0b10110), 3)

    def test_walsh_parseval(self):
        # Sum of squared Walsh coefficients = 2^(2n) (Parseval).
        tt = [0, 1, 1, 0, 1, 0, 0, 1]  # a 3-variable function
        spectrum = walsh_spectrum(tt)
        self.assertEqual(sum(w * w for w in spectrum), 2 ** (2 * 3))

    def test_algebraic_degree_of_and(self):
        # f(x0,x1) = x0 AND x1 has algebraic degree 2.
        tt = [0, 0, 0, 1]
        self.assertEqual(algebraic_degree(tt), 2)


class TestSpecVerification(unittest.TestCase):
    def test_all_declared_guarantees_hold(self):
        """Every generator must actually satisfy the property it advertises."""
        checks = verify_specs(build_catalog())
        failures = [c.generator.name for c in checks if c.results and not c.all_pass]
        self.assertEqual(failures, [], f"generators failing their own spec: {failures}")


if __name__ == "__main__":
    unittest.main()
