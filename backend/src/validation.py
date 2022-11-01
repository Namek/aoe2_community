import re

from typing import List

def validate_maps(allowed_maps: List[str], recordings_maps: List[str]):
    expected_maps = [name.casefold() for name in (['Arabia', 'KtsOTD - Arabia'] + allowed_maps)]
    prefixes = ['ANT ', 'ANT - ']

    for rec_map_name in recordings_maps:
        map_name = rec_map_name.replace('Pog Islands', 'Bog Islands').casefold()

        ok = False
        for expected_name in expected_maps:
            for prefix in prefixes:
                # e.g. "AnT - Arabia" as "Arabia"
                if map_name in expected_name or map_name in (prefix + expected_name).casefold():
                    ok = True

                # replace prefix like "RBW4 - " or "HC3 - " to "AnT - " and check again
                elif map_name in re.sub(r'[a-zA-Z0-9]{,4} - ', prefix, expected_name).casefold():
                    ok = True

        if not ok:
            map_names = ["\"" + name + "\"" for name in expected_maps]
            return f"Mapa \"{map_name}\" jest spoza podanej puli: {', '.join(map_names)}."

    return True
