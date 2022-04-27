import unittest

from regular.regular import Regular


class TestRegular(unittest.TestCase):
    def test_equal(self):
        x = Regular.from_regex(r"a+")
        y = Regular.from_regex(r"aa*")
        z = Regular.from_regex(r"a*")

        self.assertEqual(x, y)
        self.assertNotEqual(x, z)
        self.assertNotEqual(y, z)

    def test_subset(self):
        x = Regular.from_regex(r"a")
        y = Regular.from_regex(r"a?")
        z = Regular.from_regex(r"a*")

        self.assertLess(x, y)
        self.assertLess(y, z)
        self.assertLess(x, z)

        self.assertGreater(y, x)
        self.assertGreater(z, y)
        self.assertGreater(z, x)

    def test_identity(self):
        a = Regular.from_finite({"a"})
        aa = Regular.from_finite({"aa"})
        empty_str = Regular.from_finite({""})
        empty_lang = Regular.from_finite(set())

        self.assertEqual(a | a, a)
        self.assertEqual(a & a, a)
        self.assertEqual(~(~a), a)

        self.assertEqual(a + a, aa)
        self.assertEqual(a - a, empty_lang)

        self.assertEqual(a + empty_str, a)
        self.assertEqual(a + empty_lang, empty_lang)

    def test_distributive(self):
        a = Regular.from_finite({"a"})
        b = Regular.from_finite({"b"})
        c = Regular.from_finite({"c"})

        self.assertEqual(a + (b | c), a + b | a + c)


if __name__ == "__main__":
    unittest.main()
