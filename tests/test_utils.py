import unittest

from tsundoku import utils


class TestSimplifyResolution(unittest.TestCase):
    def test_1080p_standard(self) -> None:
        assert utils.normalize_resolution("1080p") == "1080p"

    def test_1080p_as_dimensions(self) -> None:
        assert utils.normalize_resolution("1920x1080") == "1080p"

    def test_1080p_as_dimensions_with_spaces(self) -> None:
        assert utils.normalize_resolution("1920 x 1080") == "1080p"

    def test_4k_uppercase(self) -> None:
        assert utils.normalize_resolution("4K") == "4k"

    def test_4k_as_dimensions(self) -> None:
        assert utils.normalize_resolution("2160x3840") == "4k"

    def test_empty(self) -> None:
        assert utils.normalize_resolution("") == ""


class TestCompareVersionStrings(unittest.TestCase):
    def test_v0_v0(self) -> None:
        assert utils.compare_version_strings("v0", "v0") == 0

    def test_v1_v0(self) -> None:
        assert utils.compare_version_strings("v1", "v0") == 1

    def test_v0_v1(self) -> None:
        assert utils.compare_version_strings("v0", "v1") == -1

    def test_v100_v99(self) -> None:
        assert utils.compare_version_strings("v100", "v99") == 1

    def test_v02_v1(self) -> None:
        assert utils.compare_version_strings("v0.2", "v1") == -1

    def test_semver_1(self) -> None:
        assert utils.compare_version_strings("1.0.0", "1.0.0") == 0

    def test_semver_2(self) -> None:
        assert utils.compare_version_strings("1.0.0", "1.0.1") == -1

    def test_semver_3(self) -> None:
        assert utils.compare_version_strings("1.0.1", "1.0.0") == 1

    def test_semver_4(self) -> None:
        assert utils.compare_version_strings("1.0.0", "1.1.0") == -1

    def test_semver_5(self) -> None:
        assert utils.compare_version_strings("1.1.0", "1.0.0") == 1

    def test_semver_6(self) -> None:
        assert utils.compare_version_strings("1.0.0", "2.0.0") == -1

    def test_semver_7(self) -> None:
        assert utils.compare_version_strings("2.0.0", "1.0.0") == 1
