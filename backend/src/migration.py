from pathlib import Path
import sqlite3
import sys

from . import cfg, utils


def migrate(db_path):
    with sqlite3.connect(db_path) as db:
        c = db.cursor()
        c.execute('BEGIN')
        ret = c.execute('''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='migration' ''').fetchone()

        version = 0
        if ret[0] == 1:
            ret = c.execute('SELECT version FROM migration LIMIT 1').fetchone()
            if ret:
                version = ret[0]
        else:
            c.execute('CREATE TABLE migration ("version" INTEGER NOT NULL);')
            c.execute('INSERT INTO migration (version) VALUES (0)')

        db.commit()

        ctx = {'version': version, 'block_index': 0, 'db': db}

        print(f"Current database version: {version}")
        block(ctx, ver1)
        block(ctx, ver2)
        block(ctx, ver3)
        block(ctx, ver4)
        block(ctx, ver5)
        block(ctx, ver6)
        block(ctx, ver7)


def block(ctx, fn):
    if ctx['version'] <= ctx['block_index']:
        print(f"Running migration {ctx['block_index'] + 1}")
        db = ctx['db']
        cursor = db.cursor()
        cursor.execute('BEGIN')
        try:
            fn(cursor)
            ctx['version'] += 1
            cursor.execute('DELETE FROM migration')
            cursor.execute('INSERT INTO migration (version) VALUES (?)', [ctx['version']])
            db.commit()
        except:
            print(f"Error migrating from {ctx['version']}")
            db.rollback()
            sys.exit(1)

    ctx['block_index'] += 1


def ver1(c):
    c.execute('ALTER TABLE users ADD roles INTEGER DEFAULT 0 NOT NULL;')


def ver2(c):
    c.execute('ALTER TABLE matches_recordings ADD "order" INTEGER DEFAULT 0')

    rows = c.execute(
        'SELECT match_id, recording_id, original_filename FROM recordings JOIN matches_recordings ON recording_id=recordings.id').fetchall()
    rows = [dict(match_id=r[0], rec_id=r[1], filename=r[2]) for r in rows]
    matches_ids = set(map(lambda r: r['match_id'], rows))
    matches = [
        dict(id=match_id,
             recordings=[dict(id=x['rec_id'], filename=x['filename']) for x in rows if
                         x['match_id'] == match_id]) for
        match_id in matches_ids]

    for match in matches:
        recs = match['recordings']
        recs.sort(key=lambda r: r['filename'])

        for ri, recording in enumerate(recs):
            c.execute('UPDATE matches_recordings SET "order"=? WHERE recording_id=?', [ri, recording['id']])


def ver3(c):
    ret = c.execute(
        "select * from sqlite_master where type = 'table' and tbl_name = 'recordings' and sql like '%duration_seconds%'").fetchone()

    if not ret or not ret[0]:
        c.execute('ALTER TABLE recordings ADD "start_time_seconds" INTEGER DEFAULT 0 NOT NULL')
        c.execute('ALTER TABLE recordings ADD "duration_seconds" INTEGER DEFAULT 0 NOT NULL')

    print('Going to update start/duration times for recordings...')
    rows = c.execute('SELECT id, filename FROM recordings').fetchall()
    for (rid, filename) in rows:
        filepath = f'{cfg.RECORDINGS_PATH}/{filename}'
        if Path(filepath).exists():
            print(f'Updating recording: {filepath}')
            with open(filepath, 'rb') as file:
                try:
                    m = utils.get_match_info(file)
                    c.execute('UPDATE recordings SET start_time_seconds=? WHERE id=?', [m['start_time_seconds'], rid])
                    c.execute('UPDATE recordings SET duration_seconds=? WHERE id=?', [m['duration_seconds'], rid])
                except RuntimeError:
                    print(f"Couldn't process {filename}")
    print('Times updated.')


def ver4(c):
    print('Going to update start/duration times for recordings having duration=0...')
    rows = c.execute('SELECT id, filename FROM recordings WHERE duration_seconds=0').fetchall()
    for (rid, filename) in rows:
        filepath = f'{cfg.RECORDINGS_PATH}/{filename}'
        print(f'Updating recording: {filepath}')
        with open(filepath, 'rb') as file:
            try:
                m = utils.get_match_info(file)
                c.execute('UPDATE recordings SET start_time_seconds=? WHERE id=?', [m['start_time_seconds'], rid])
                c.execute('UPDATE recordings SET duration_seconds=? WHERE id=?', [m['duration_seconds'], rid])
            except:
                print(f"Couldn't process {filename}")
    print('Times updated.')


def ver5(c):
    c.execute('ALTER TABLE matches ADD "p0_civ_bans" TEXT')
    c.execute('ALTER TABLE matches ADD "p1_civ_bans" TEXT')


def ver6(c):
    c.execute('CREATE UNIQUE INDEX users_idx on users(name)')
    c.execute('CREATE UNIQUE INDEX recordings_idx on recordings(filename)')


def ver7(c):
    c.execute('ALTER TABLE matches ADD "watched" INT DEFAULT 0 NOT NULL')
