import pytest
from src.validation import validate_maps


def test_map_names():
    cases = [
        [["Bog Islands"], ["AnT - Pog Islands"]],
        [["TidePool"], ["AnT - Tidepool"]],
        [["HC3 - Gold Rush"], ["AnT - Gold Rush"]],
        [["RBW4 - Meadow"], ["AnT - Meadow"]],
        [["ANT - Bypass"], ["ANT Bypass"]],
    ]

    for [official_maps, recordings_maps] in cases:
        assert(validate_maps(official_maps, recordings_maps) == True)