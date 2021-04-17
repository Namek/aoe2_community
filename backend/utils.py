def copy_file(source_file, dest_file, chunk_size=2 ** 16):
    source_file.seek(0)
    read, write, offset = source_file.read, dest_file.write, source_file.tell()
    while 1:
        buf = read(chunk_size)
        if not buf: break
        write(buf)
    source_file.seek(offset)


def get_match_info(data):
    from mgz.model import parse_match

    m = parse_match(data)

    return dict(
        map_name=m.map.name,
        game_version=m.version,
        game_map_type=m.type,
        players=m.players,
        teams=m.teams,
        completed=False,
        start_time_seconds=str(m.actions[0].timestamp.seconds),
        duration_seconds=m.duration.seconds,
    )
