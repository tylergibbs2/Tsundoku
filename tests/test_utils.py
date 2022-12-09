import unittest

from tsundoku import utils


class TestSimplifyResolution(unittest.TestCase):
    def test_1080p_standard(self):
        self.assertEqual(utils.normalize_resolution("1080p"), "1080p")

    def test_1080p_as_dimensions(self):
        self.assertEqual(utils.normalize_resolution("1920x1080"), "1080p")

    def test_1080p_as_dimensions_with_spaces(self):
        self.assertEqual(utils.normalize_resolution("1920 x 1080"), "1080p")

    def test_4k_uppercase(self):
        self.assertEqual(utils.normalize_resolution("4K"), "4k")

    def test_4k_as_dimensions(self):
        self.assertEqual(utils.normalize_resolution("2160x3840"), "4k")

    def test_empty(self):
        self.assertEqual(utils.normalize_resolution(""), "")


class TestCompareVersionStrings(unittest.TestCase):
    def test_v0_v0(self):
        self.assertEqual(utils.compare_version_strings("v0", "v0"), 0)

    def test_v1_v0(self):
        self.assertEqual(utils.compare_version_strings("v1", "v0"), 1)

    def test_v0_v1(self):
        self.assertEqual(utils.compare_version_strings("v0", "v1"), -1)

    def test_v100_v99(self):
        self.assertEqual(utils.compare_version_strings("v100", "v99"), 1)

    def test_v02_v1(self):
        self.assertEqual(utils.compare_version_strings("v0.2", "v1"), -1)
