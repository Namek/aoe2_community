import sqlite3


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

        start_version = version

        if version == 0:
            c.execute('ALTER TABLE users ADD roles INTEGER DEFAULT 0 NOT NULL;')
            version += 1

        if version == 1:
            c.execute('ALTER TABLE matches_recordings ADD "order" INTEGER DEFAULT 0')

            rows = c.execute('SELECT match_id, recording_id, original_filename FROM recordings JOIN matches_recordings ON recording_id=recordings.id').fetchall()
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

            version += 1
        if start_version != version:
            c.execute('DELETE FROM migration')
            c.execute('INSERT INTO migration (version) VALUES (?)', [version])

        db.commit()
