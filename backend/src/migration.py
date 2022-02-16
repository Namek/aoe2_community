from pathlib import Path
import sqlite3
import sys

from . import cfg, utils
from .recordings import get_match_info

# TODO a more automated migration system, based on sqlalchemy and alembic?
# from .database import get_db, engine
# models.Base.metadata.create_all(bind=engine)


def migrate(db_path):
    print(f'Migration: opening "{db_path}"')
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
        block(ctx, ver8)
        block(ctx, ver9)
        block(ctx, ver10)
        block(ctx, ver11)
        block(ctx, ver12)


def block(ctx, fn):
    if ctx['version'] <= ctx['block_index']:
        print(f"Running migration {ctx['block_index'] + 1}")
        db = ctx['db']
        cursor = db.cursor()
        cursor.execute('BEGIN TRANSACTION')
        try:
            fn(cursor)
            ctx['version'] += 1
            cursor.execute('DELETE FROM migration')
            cursor.execute('INSERT INTO migration (version) VALUES (?)', [ctx['version']])
            db.commit()
            print(f"Migration {ctx['block_index'] + 1} committed.")
        except:
            print(f"Error migrating from {ctx['version']}:")
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
                    m = get_match_info(file)
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
                m = get_match_info(file)
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


def ver8(c):
    c.execute('ALTER TABLE matches RENAME COLUMN "watched" TO "watch_status"')


def ver9(c):
    # stuff for discord bot
    c.execute('''
        CREATE TABLE "message_sources" (
            "id"            INTEGER NOT NULL,
            "guild_id"      INTEGER NOT NULL,
            "channel_id"    INTEGER NOT NULL,
            "channel_name"  TEXT NOT NULL,
            "created_at"    DATETIME DEFAULT CURRENT_TIMESTAMP,
            "modified_at"    DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY("id" AUTOINCREMENT)
        );
    ''')

    c.execute('CREATE UNIQUE INDEX message_sources_idx on message_sources(guild_id, channel_id)')

    c.execute('''
        CREATE TABLE "messages" (
            "id"            INTEGER NOT NULL,
            "content"       TEXT NOT NULL,
            "source_id"     INTEGER NOT NULL,
            "original_id"   TEXT NOT NULL,
            "is_parsed"     INTEGER NOT NULL DEFAULT 0,
            "created_at"    DATETIME DEFAULT CURRENT_TIMESTAMP,
            "modified_at"    DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY("id" AUTOINCREMENT)
        );
    ''')
    c.execute('''
        CREATE TABLE "calendar" (
            "id"            INTEGER NOT NULL,
            "datetime"      DATETIME NOT NULL,
            "description"   TEXT NOT NULL,
            "message_id"    INTEGER,
            "created_at"    DATETIME DEFAULT CURRENT_TIMESTAMP,
            "modified_at"    DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY("id" AUTOINCREMENT)
        );
    ''')


def ver10(c):
    c.execute('ALTER TABLE messages ADD "is_manually_ignored" INTEGER NOT NULL DEFAULT 0;')


def ver11(c):
    # make most fields nullable
    c.execute('''
        CREATE TABLE recordings__copy (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            mod_time TEXT,
            original_filename INTEGER,
            map_name TEXT,
            completed INTEGER,
            game_version TEXT,
            team_count INTEGER,
            game_map_type TEXT,
            "start_time_seconds" INTEGER DEFAULT 0,
            "duration_seconds" INTEGER DEFAULT 0
        );
    ''')
    c.execute('INSERT INTO recordings__copy SELECT * FROM recordings')
    c.execute('DROP TABLE recordings')
    c.execute('ALTER TABLE recordings__copy RENAME TO recordings')


def ver12(c):
    # tri-state value: enabled, disabled, unknown (default)
    c.execute('ALTER TABLE calendar ADD "spectate_on" INTEGER DEFAULT NULL;')
    c.execute('ALTER TABLE calendar ADD "spectate_link" TEXT DEFAULT NULL;')
