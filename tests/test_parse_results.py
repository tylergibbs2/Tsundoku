from typing import cast

from tsundoku import utils


def parse_title(title: str) -> utils.ParserResult:
    return utils.parse_anime_title(title)


def assert_parse_result_contains(title: str, like: utils.ParserResult) -> None:
    result = utils.parse_anime_title(title)
    assert result == {**result, **like}


def test_1() -> None:
    assert_parse_result_contains(
        "[SubsPlease] Chainsaw Man - 12 (1080p) [179132FA].mkv",
        cast(
            utils.ParserResult,
            {
                "release_group": "SubsPlease",
                "anime_title": "Chainsaw Man",
                "episode_number": "12",
                "video_resolution": "1080p",
            },
        ),
    )


def test_2() -> None:
    assert_parse_result_contains(
        "[SubsPlease] NieR Automata Ver1.1a - 04 (720p) [CC00E892].mkv",
        cast(
            utils.ParserResult,
            {
                "release_group": "SubsPlease",
                "anime_title": "NieR Automata Ver1.1a",
                "episode_number": "04",
                "video_resolution": "720p",
            },
        ),
    )


def test_3() -> None:
    assert_parse_result_contains(
        "[SubsPlease] NieR Automata Ver1.1a - 04v2 (720p) [CC00E892].mkv",
        cast(
            utils.ParserResult,
            {
                "release_group": "SubsPlease",
                "anime_title": "NieR Automata Ver1.1a",
                "episode_number": "04",
                "video_resolution": "720p",
                "release_version": "2",
            },
        ),
    )


def test_4() -> None:
    assert_parse_result_contains(
        "[SubsPlease] Tomo-chan wa Onnanoko! - 03 (480p) [F21C23E2].mkv",
        cast(
            utils.ParserResult,
            {
                "release_group": "SubsPlease",
                "anime_title": "Tomo-chan wa Onnanoko!",
                "episode_number": "03",
                "video_resolution": "480p",
            },
        ),
    )


def test_5() -> None:
    assert_parse_result_contains(
        "[ASW] Shadowverse Flame - 41 [1080p HEVC x265 10Bit][AAC]",
        cast(
            utils.ParserResult,
            {
                "release_group": "ASW",
                "anime_title": "Shadowverse Flame",
                "episode_number": "41",
                "video_resolution": "1080p",
            },
        ),
    )


def test_6() -> None:
    assert_parse_result_contains(
        "[SubsPlease] Bocchi the Rock! (01-12) (1080p) [Batch]",
        cast(
            utils.ParserResult,
            {
                "release_group": "SubsPlease",
                "anime_title": "Bocchi the Rock!",
                "episode_number": ["01", "12"],
                "video_resolution": "1080p",
                "release_information": "Batch",
            },
        ),
    )


def test_7() -> None:
    assert_parse_result_contains(
        "[ASW] Shadowverse Flame - 41 [1920x1080 HEVC x265 10Bit][AAC]",
        cast(
            utils.ParserResult,
            {
                "release_group": "ASW",
                "anime_title": "Shadowverse Flame",
                "episode_number": "41",
                "video_resolution": "1080p",
            },
        ),
    )


def test_8() -> None:
    assert_parse_result_contains(
        "[M-L-Stuffs] Futari wa Precure (Pretty Cure) 01",
        cast(
            utils.ParserResult,
            {
                "release_group": "M-L-Stuffs",
                "anime_title": "Futari wa Precure (Pretty Cure)",
                "episode_number": "01",
            },
        ),
    )


def test_parse_titles_batch() -> None:
    # Files belonging to a single release parse together and preserve order.
    titles = [
        "[SubsPlease] Chainsaw Man - 01 (1080p) [ABCD1234].mkv",
        "[SubsPlease] Chainsaw Man - 02 (1080p) [EF567890].mkv",
        "[SubsPlease] Chainsaw Man - 03 (1080p) [12ABEF34].mkv",
    ]

    results = utils.parse_anime_titles(titles)

    assert len(results) == len(titles)
    assert [r.get("episode_number") for r in results] == ["01", "02", "03"]
    assert all(r.get("anime_title") == "Chainsaw Man" for r in results)
    assert [r.get("file_name") for r in results] == titles


def test_parse_titles_empty() -> None:
    assert utils.parse_anime_titles([]) == []
