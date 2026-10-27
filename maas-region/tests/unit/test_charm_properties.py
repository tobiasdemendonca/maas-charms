# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

from unittest.mock import patch

import yaml
from hypothesis import given
from hypothesis import strategies as st

from charm import _next_track, _resolve_target_channel

tracks = st.builds(
    lambda major, minor: f"{major}.{minor}",
    st.integers(min_value=1, max_value=20),
    st.integers(min_value=0, max_value=100),
)


def version_key(track: str) -> tuple[int, ...]:
    return tuple(int(part) for part in track.split("."))


@given(declared=st.lists(tracks, min_size=1, unique_by=float), data=st.data())
def test_resolve_target_channel_round_trips_known_track(declared, data):
    # `track` is untyped in charmcraft.yaml, so Juju YAML-parses `track=3.10` into the
    # float 3.1. Only the tracks this charm knows can disambiguate it, so the property
    # is limited to those, generated without float collisions (e.g. "3.1" and "3.10").
    track = data.draw(st.sampled_from(declared))
    param = yaml.safe_load(track)

    with patch.dict("charm.MAAS_TRACK_BASES", {t: ["26.04"] for t in declared}, clear=True):
        assert _resolve_target_channel(param) == (track, f"{track}/stable")


@given(declared=st.lists(tracks, min_size=1, unique=True), data=st.data())
def test_next_track_follows_version_order(declared, data):
    ordered = sorted(declared, key=version_key)
    index = data.draw(st.integers(min_value=0, max_value=len(ordered) - 1))
    expected = ordered[index + 1] if index + 1 < len(ordered) else None

    with patch.dict("charm.MAAS_TRACK_BASES", {t: ["26.04"] for t in declared}, clear=True):
        assert _next_track(ordered[index]) == expected
