# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

import re

from hypothesis import given
from hypothesis import strategies as st

from backups import as_size

PREFIXES = ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi", "Yi", "Ri", "Qi"]
SIZE_PATTERN = re.compile(r"(\d+\.\d)(Ki|Mi|Gi|Ti|Pi|Ei|Zi|Yi|Ri|Qi)?B")
# Up to 1 EiB: far beyond any backup, and below where float log precision distorts the unit.
# Uniform draws almost never land next to a unit boundary, so also sample around 1024**k.
sizes = st.integers(min_value=0, max_value=1024**6) | st.builds(
    lambda power, offset: max(0, 1024**power + offset),
    st.integers(min_value=0, max_value=6),
    st.integers(min_value=-100, max_value=100),
)


def parse(text: str) -> tuple[float, int]:
    match = SIZE_PATTERN.fullmatch(text)
    assert match, f"unparseable size {text!r}"
    return float(match[1]), PREFIXES.index(match[2] or "")


@given(size=sizes)
def test_as_size_round_trips(size):
    value, power = parse(as_size(size))
    # One decimal place of the displayed unit is the only precision lost.
    assert abs(value * 1024**power - size) <= 0.05 * 1024**power


@given(size=sizes.filter(bool))
def test_as_size_uses_largest_whole_unit(size):
    value, _ = parse(as_size(size))
    assert value < 1024, f"{size} rendered as {as_size(size)!r}"
