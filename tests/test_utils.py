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
