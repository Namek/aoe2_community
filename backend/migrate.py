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

        if start_version != version:
            c.execute('DELETE FROM migration')
            c.execute('INSERT INTO migration (version) VALUES (?)', [version])

        db.commit()
