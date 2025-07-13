"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

# help with: http://chairnerd.seatgeek.com/fuzzywuzzy-fuzzy-string-matching-in-python/

from collections.abc import Callable, Collection, Generator, Sequence
from difflib import SequenceMatcher

SortableCollection = Collection[str] | Sequence[str]


def quick_ratio(a: str, b: str) -> int:
    m = SequenceMatcher(None, a, b)
    return round(100 * m.quick_ratio())


def _extraction_generator(
    query: str,
    choices: list[str],
    scorer: Callable = quick_ratio,
    score_cutoff: int = 0,
) -> Generator:
    for choice in choices:
        score = scorer(query, choice)
        if score >= score_cutoff:
            yield (choice, score)


def extract_one(
    query: str,
    choices: list[str],
    *,
    scorer: Callable = quick_ratio,
    score_cutoff: int = 0,
) -> tuple[str, int] | None:
    it = _extraction_generator(query, choices, scorer, score_cutoff)

    def key(t: tuple[str, int]) -> int:
        return t[1]

    try:
        return max(it, key=key)
    except Exception:
        # iterator could return nothing
        return None
