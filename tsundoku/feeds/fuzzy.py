# -*- coding: utf-8 -*-

"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

# help with: http://chairnerd.seatgeek.com/fuzzywuzzy-fuzzy-string-matching-in-python/

from difflib import SequenceMatcher
from typing import (
    Callable,
    Collection,
    Generator,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

SortableCollection = Union[Collection[str], Sequence[str]]


def quick_ratio(a: str, b: str) -> int:
    m = SequenceMatcher(None, a, b)
    return int(round(100 * m.quick_ratio()))


def _extraction_generator(
    query: str,
    choices: List[str],
    scorer: Callable = quick_ratio,
    score_cutoff: int = 0,
) -> Generator:
    for choice in choices:
        score = scorer(query, choice)
        if score >= score_cutoff:
            yield (choice, score)


def extract_one(
    query: str,
    choices: List[str],
    *,
    scorer: Callable = quick_ratio,
    score_cutoff: int = 0
) -> Optional[Tuple[str, int]]:
    it = _extraction_generator(query, choices, scorer, score_cutoff)

    def key(t: Tuple[str, int]) -> int:
        return t[1]

    try:
        return max(it, key=key)
    except Exception:
        # iterator could return nothing
        return None
