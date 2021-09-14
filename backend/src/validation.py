import re

from typing import List

def validate_maps(all_maps: List[str], recordings_maps: List[str]):
    expected_maps = [name.casefold() for name in (['Arabia', 'AnT - Arabia'] + all_maps)]

    for rec_map_name in recordings_maps:
        map_name = rec_map_name.replace('Pog Islands', 'Bog Islands').casefold()

        ok = False
        for expected_name in expected_maps:
            # e.g. "Gold Rush" in "HC3 - Gold Rush" or "AnT - Arabia" as "Arabia"
            if map_name in expected_name or map_name in ("AnT - " + expected_name).casefold():
                ok = True

            # replace prefix like "RBW4 - " or "HC3 - " to "AnT - " and check again
            elif map_name in re.sub(r'[a-zA-Z0-9]{,4} - ', 'AnT - ', expected_name).casefold():
                ok = True

        if not ok:
            return f"Mapa {map_name} jest spoza podanej puli: {', '.join(expected_maps)}."

    return True
