# -*- coding: utf-8 -*-

"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

# help with: http://chairnerd.seatgeek.com/fuzzywuzzy-fuzzy-string-matching-in-python/

import re
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


def ratio(a: str, b: str) -> int:
    m = SequenceMatcher(None, a, b)
    return int(round(100 * m.ratio()))


def quick_ratio(a: str, b: str) -> int:
    m = SequenceMatcher(None, a, b)
    return int(round(100 * m.quick_ratio()))


def partial_ratio(a: str, b: str) -> int:
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    m = SequenceMatcher(None, short, long)

    blocks = m.get_matching_blocks()

    scores = []
    for i, j, n in blocks:
        start = max(j - i, 0)
        end = start + len(short)
        o = SequenceMatcher(None, short, long[start:end])
        r = o.ratio()

        if r > 99 / 100:
            return 100
        scores.append(r)

    return int(round(100 * max(scores)))


_word_regex = re.compile(r"\W", re.IGNORECASE)


def _sort_tokens(a: str) -> str:
    a = _word_regex.sub(" ", a).lower().strip()
    return " ".join(sorted(a.split()))


def token_sort_ratio(a: str, b: str) -> int:
    a = _sort_tokens(a)
    b = _sort_tokens(b)
    return ratio(a, b)


def quick_token_sort_ratio(a: str, b: str) -> int:
    a = _sort_tokens(a)
    b = _sort_tokens(b)
    return quick_ratio(a, b)


def partial_token_sort_ratio(a: str, b: str) -> int:
    a = _sort_tokens(a)
    b = _sort_tokens(b)
    return partial_ratio(a, b)


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
