# -*- coding: utf-8 -*-

"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

# help with: http://chairnerd.seatgeek.com/fuzzywuzzy-fuzzy-string-matching-in-python/

from difflib import SequenceMatcher
import heapq
import re
from typing import Callable, Collection, Generator, List, Sequence, Tuple, Union, Optional


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


_word_regex = re.compile(r'\W', re.IGNORECASE)


def _sort_tokens(a: str) -> str:
    a = _word_regex.sub(' ', a).lower().strip()
    return ' '.join(sorted(a.split()))


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


def _extraction_generator(query: str, choices: SortableCollection,
                          scorer: Callable = quick_ratio, score_cutoff: int = 0) -> Generator:
    try:
        for key, value in choices.items():
            score = scorer(query, key)
            if score >= score_cutoff:
                yield (key, score, value)
    except AttributeError:
        for choice in choices:
            score = scorer(query, choice)
            if score >= score_cutoff:
                yield (choice, score)


def extract(query: str, choices: SortableCollection, *,
            scorer: Callable = quick_ratio, score_cutoff: int = 0, limit: int = 10) -> List:
    it = _extraction_generator(query, choices, scorer, score_cutoff)
    def key(t): return t[1]
    if limit is not None:
        return heapq.nlargest(limit, it, key=key)
    return sorted(it, key=key, reverse=True)


def extract_one(query: str, choices: SortableCollection, *,
                scorer: Callable = quick_ratio, score_cutoff: int = 0) -> Optional[int]:
    it = _extraction_generator(query, choices, scorer, score_cutoff)
    def key(t): return t[1]
    try:
        return max(it, key=key)
    except Exception:
        # iterator could return nothing
        return None


def extract_or_exact(query: str, choices: SortableCollection, *,
                     limit: int = None, scorer=quick_ratio, score_cutoff=0) -> List[int]:
    matches = extract(query, choices, scorer=scorer,
                      score_cutoff=score_cutoff, limit=limit)
    if len(matches) == 0:
        return []

    if len(matches) == 1:
        return matches

    top = matches[0][1]
    second = matches[1][1]

    # check if the top one is exact or more than 30% more correct than the top
    if top == 100 or top > (second + 30):
        return [matches[0]]

    return matches


def extract_matches(query: str, choices: SortableCollection, *,
                    scorer: Callable = quick_ratio, score_cutoff: int = 0) -> List[int]:
    matches = extract(query, choices, scorer=scorer,
                      score_cutoff=score_cutoff, limit=None)
    if len(matches) == 0:
        return []

    top_score = matches[0][1]
    to_return = []
    index = 0
    while True:
        try:
            match = matches[index]
        except IndexError:
            break
        else:
            index += 1

        if match[1] != top_score:
            break

        to_return.append(match)

    return to_return


def finder(text: str, collection: Collection[str], *,
           key: Optional[Callable] = None, lazy: bool = True) -> Union[Generator[str], List[str]]:
    suggestions = []
    text = str(text)
    pat = '.*?'.join(map(re.escape, text))
    regex = re.compile(pat, flags=re.IGNORECASE)
    for item in collection:
        to_search = key(item) if key else item
        r = regex.search(to_search)
        if r:
            suggestions.append((len(r.group()), r.start(), item))

    def sort_key(tup: Tuple[str]) -> Tuple:
        if key:
            return tup[0], tup[1], key(tup[2])
        return tup

    if lazy:
        return (z for _, _, z in sorted(suggestions, key=sort_key))
    else:
        return [z for _, _, z in sorted(suggestions, key=sort_key)]


def find(text: str, collection: Collection[str], *, key: Optional[Callable] = None) -> Optional[List[str]]:
    try:
        return finder(text, collection, key=key, lazy=False)[0]
    except IndexError:
        return None
