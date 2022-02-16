from pathlib import Path
from re import A
from sqlalchemy import delete, join, select, update

from mgz.model import parse_match
from mgz.summary import Summary

from . import cfg
from .database import get_db
from .models import Recording, AssocRecordingsPlayers


def get_match_info(data):
    try:
        # some files seems broken for this library when using the `Summary`.
        m = parse_match(data)
        players = [dict(name=p.name, user_id=p.profile_id, number=p.number,
                        civilization=p.civilization) for p in m.players]

        return dict(
            map_name=m.map.name,
            game_version=f"{m.version.name} {m.version.value}",
            game_map_type=m.type,
            players=players,
            teams=m.teams,
            completed=False,
            start_time_seconds=int(m.actions[0].timestamp.seconds),
            duration_seconds=m.duration.seconds,
        )
    except RuntimeError:
        # the `parse_match` method doesn't work for restored recordings, thus, let's try with the `Summary`.
        data.seek(0)
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


def retry_recordings_parsing():
    with get_db() as db:
        _recordings_to_update = \
            select(Recording.id, Recording.filename).\
            where(Recording.map_name == None)

        recordings_to_update = db.execute(_recordings_to_update).all()

        print(f'Found {len(recordings_to_update)} recordings info to update.')

        for rec in recordings_to_update:
            filepath = f'{cfg.RECORDINGS_PATH}/{rec.filename}'
            print(f'The recording does not have data parsed: {filepath}...')
            if Path(filepath).exists():
                print(f'Updating recording parse data')
                with open(filepath, 'rb') as file:
                    try:
                        m = get_match_info(file)
                        teams = m['teams']

                        db.execute(update(Recording).where(Recording.id == rec.id).values(
                            map_name=m['map_name'],
                            completed=1 if m['completed'] else 0,
                            game_version=m['game_version'],
                            game_map_type=m['game_map_type'],
                            team_count=len(teams),
                            start_time_seconds=m['start_time_seconds'],
                            duration_seconds=m['duration_seconds']
                        ))

                        db.execute(delete(AssocRecordingsPlayers)
                                   .where(AssocRecordingsPlayers.recording_id == rec.id))

                        for pi, player in enumerate(m['players']):
                            profile_id = player['user_id']
                            number = player['number']
                            team_index = 0
                            for ti, team in enumerate(teams):
                                if number in team:
                                    team_index = ti

                            db_player_rec_assoc = AssocRecordingsPlayers(
                                recording_id=rec.id,
                                profile_id=profile_id,
                                name=player['name'],
                                civ=player['civilization'],
                                team_index=team_index
                            )
                            db.add(db_player_rec_assoc)

                        print(f'Update done for: {filepath}')
                        db.commit()

                    except Exception:
                        print(f"Couldn't process {rec.filename}")
            else:
                print('...but the file does not exist. Ignoring.')
