from mgz.model import parse_match
from mgz.summary import Summary

def copy_file(source_file, dest_file, chunk_size=2 ** 16):
    source_file.seek(0)
    read, write, offset = source_file.read, dest_file.write, source_file.tell()
    while 1:
        buf = read(chunk_size)
        if not buf: break
        write(buf)
    source_file.seek(offset)


def get_match_info(data):
    try:
        # some files seems broken for this library when using the `Summary`.
        m = parse_match(data)
        players = [dict(name=p.name, user_id=p.profile_id, number=p.number, civilization=p.civilization) for p in m.players]

        return dict(
            map_name=m.map.name,
            game_version=f"{m.version.name} {m.version.value}",
            game_map_type=m.type,
            players=players,
            teams=m.teams,
            completed=False,
            start_time_seconds=str(m.actions[0].timestamp.seconds),
            duration_seconds=m.duration.seconds,
        )
    except RuntimeError:
        # the `parse_match` method doesn't work for restored recordings, thus, let's try with the `Summary`.
        s = Summary(data)

        return dict(
            map_name=s.get_map()['name'],
            game_version=" ".join(str(x) for x in s.get_version()),
            game_map_type=s.get_settings()['type'][1],
            players=s.get_players(),
            teams=s.get_teams(),
            completed=s.get_completed(),
            start_time_seconds=int(s.get_start_time()/1000),
            duration_seconds=int(s.get_duration()/1000),
        )
