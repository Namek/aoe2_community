from dotenv import load_dotenv

import string
import types
import json
import random
import datetime
from pathlib import Path
import os

from beaker.middleware import SessionMiddleware
import bottle
from bottle import abort, run, static_file, request, response, route
from bottle_sqlite import SQLitePlugin
from mgz.summary import Summary

from migrate import migrate

load_dotenv()
RECORDINGS_PATH = os.getenv('RECORDINGS_PATH') or './database/files'
CORS_ALLOW_ORIGIN = os.getenv('CORS_ALLOW_ORIGIN') 
STATICS_PATH = os.getenv('STATICS_PATH') or './static'
DB_TEMPLATE_PATH = os.getenv('DB_TEMPLATE_PATH') or './database/app.template.db'
DB_PATH = os.getenv('DB_PATH') or './database/app.db'
SESSIONS_DATA_DIR = os.getenv('SESSIONS_PATH') or './database/sessions/data'
SESSIONS_LOCK_DIR = os.getenv('SESSIONS_PATH') or './database/sessions/lock'
SESSION_SECRET = os.getenv('SESSION_SECRET') or ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(30))

def _copy_file(source_file, dest_file, chunk_size=2 ** 16):
    source_file.seek(0)
    read, write, offset = source_file.read, dest_file.write, source_file.tell()
    while 1:
        buf = read(chunk_size)
        if not buf: break
        write(buf)
    source_file.seek(offset)


if not Path(DB_PATH).exists():
    with open(DB_PATH, 'wb') as fp:
        with open(DB_TEMPLATE_PATH, 'rb') as source:
            _copy_file(source, fp)

if not Path(DB_PATH).exists():
    print("Database file '{}' does not exist!".format(DB_PATH))
    exit(1)

migrate(DB_PATH)

for dir in [SESSIONS_DATA_DIR, SESSIONS_LOCK_DIR, RECORDINGS_PATH]:
    try:
        os.mkdir(dir)
    except:
        pass


app = bottle.app()
app.install(SQLitePlugin(dbfile=DB_PATH, autocommit=False))

if CORS_ALLOW_ORIGIN:
    def add_cors_headers(res):
        res.headers['Access-Control-Allow-Origin'] = CORS_ALLOW_ORIGIN or '*'
        res.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
        res.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
        res.headers['Access-Control-Allow-Credentials'] = 'true'

    @bottle.hook('before_request')
    def enable_cors():
        add_cors_headers(response)

    orig_default_error_handler = app.default_error_handler

    def error_handler(self, out):
        add_cors_headers(response)
        out.apply(response)
        return orig_default_error_handler(out)

    app.default_error_handler = types.MethodType(error_handler, app)


def get_match_info(data):
    s = Summary(data)

    return dict(
        map_name=s.get_map()['name'],
        game_version=s.get_version(),
        match_settings=s.get_settings(),
        players=s.get_players(),
        teams=s.get_teams(),
        completed=s.get_completed(),
        platform=s.get_platform(),
        profile_ids=s.get_profile_ids()
    )

@route('/api/auth/check', method='POST')
def auth_check(db):
    session = request.environ.get('beaker.session')

    if 'user_id' not in session:
        abort(401)

    user = db.execute('SELECT id, roles FROM users WHERE id=? LIMIT 1', [session['user_id']]).fetchone()
    if not user:
        abort(403)

    response.set_header('Content-Type', 'application/json')
    return dict(id=user['id'], roles=user['roles'])

@route('/api/auth', method='POST')
def auth_log_in(db):
    password = request.forms.get('password')
    user = db.execute('SELECT id, roles FROM users WHERE password=? LIMIT 1', [password]).fetchone()

    if user is None:
        abort(401, "No user")

    session = request.environ['beaker.session']
    session['user_id'] = user[0]
    session.save()
    session.persist()

    return dict(id=user['id'], roles=user['roles'])


@route('/api/auth', method=['OPTIONS', 'DELETE'])
def auth_log_out(db):
    if request.method == 'OPTIONS':
        # CORS
        return "ok"

    request.environ.get('beaker.session').delete()
    return "ok"


@route('/api/match/<match_id:int>', method=['OPTIONS', 'DELETE'])
def remove_match(match_id, db):
    if request.method == 'OPTIONS':
        # CORS
        return "ok"

    session = request.environ.get('beaker.session')
    if 'user_id' not in session:
        abort(401)

    user = db.execute('SELECT id FROM users WHERE id=? AND roles=1 LIMIT 1', [session['user_id']]).fetchone()
    if not user:
        abort(403)

    recordings_ids = db.execute("SELECT recording_id as id FROM matches_recordings WHERE match_id=?", [match_id]).fetchall()
    recordings_ids = [r['id'] for r in recordings_ids]
    recordings_ids_as_str = ",".join([str(num) for num in recordings_ids])

    db.execute('BEGIN')
    db.execute('DELETE FROM matches_recordings WHERE match_id=(?)', [match_id])
    db.execute('DELETE FROM recordings_players WHERE recording_id IN ({})'.format(recordings_ids_as_str))
    db.execute('DELETE FROM recordings WHERE id IN ({})'.format(recordings_ids_as_str))
    db.execute('DELETE FROM matches WHERE id=?', [match_id])
    db.commit()


@route('/api/match', method='POST')
def post_match(db):
    group = request.forms.get('group')
    civ_draft = request.forms.get('civ_draft').replace('https://aoe2cm.net/draft/', '')
    date = int(datetime.datetime.strptime(request.forms.get('date'), '%Y-%m-%d').timestamp())
    best_of = request.forms.get('best_of')
    p0_maps = '||'.join(request.forms.dict.get('p0_maps[]'))
    p1_maps = '||'.join(request.forms.dict.get('p1_maps[]'))
    p0_name = request.forms.get('p0_name')
    p1_name = request.forms.get('p1_name')
    p0_map_ban = request.forms.get('p0_map_ban')
    p1_map_ban = request.forms.get('p1_map_ban')
    password = request.forms.get('password')
    recording_files = request.files.dict.get('recording_files[]')
    recording_times = request.forms.dict.get('recording_times[]')

    user = db.execute('SELECT id FROM users WHERE password=? LIMIT 1', [password]).fetchone()

    if user is None:
        abort(503, "Wrong password")

    user_id = user[0]

    recordings = [(file, get_match_info(file.file), recording_times[idx]) for idx, file in enumerate(recording_files)]
    recordings.sort(key=lambda r: r[2])

    db.execute('BEGIN')
    res = db.execute(
        "INSERT INTO matches ('group', 'civ_draft', 'date', 'best_of', 'p0_maps', 'p1_maps', 'p0_name', 'p1_name',"
        " 'p0_map_ban', 'p1_map_ban', 'upload_user_id') VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
        [group, civ_draft, date, best_of, p0_maps, p1_maps, p0_name, p1_name, p0_map_ban, p1_map_ban, user_id])

    match_id = res.lastrowid

    saved_files = []
    for i, (file, match_info, mod_time) in enumerate(recordings):
        new_filename = 'rec_match{}_{}'.format(match_id, i)
        game_version = " ".join(str(x) for x in match_info['game_version'])
        match_settings = match_info['match_settings']
        completed = 1 if match_info['completed'] else 0
        game_map_type = match_settings['type'][1]
        teams = match_info['teams']
        team_count = len(teams)

        res = db.execute(
            "INSERT INTO recordings ('filename', 'original_filename', 'mod_time', 'map_name', 'completed', 'game_version', 'game_map_type', 'team_count') VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [new_filename, file.filename, mod_time, match_info['map_name'], completed, game_version, game_map_type,
             team_count])
        recording_id = res.lastrowid
        db.execute("INSERT INTO matches_recordings ('match_id', 'recording_id') VALUES (?, ?)",
                   [match_id, recording_id])

        players = match_info['players']
        for pi, player in enumerate(players):
            profile_id = player['user_id']
            number = player['number']
            team_index = 0
            for ti, team in enumerate(teams):
                if number in team:
                    team_index = ti

            db.execute(
                "INSERT INTO recordings_players ('recording_id', 'name', 'civ', 'team_index', 'profile_id') VALUES (?, ?, ?, ?, ?)",
                [recording_id, player['name'], player['civilization'], team_index, profile_id])

        with open('{}/{}'.format(RECORDINGS_PATH, new_filename), 'wb') as fp:
            _copy_file(file.file, fp)
            saved_files.append(new_filename)

    if len(recordings) == len(saved_files):
        db.commit()
    else:
        db.rollback()
        response.status = 500


@route('/api/matches', method='GET')
def get_matches(db):
    rows = db.execute("SELECT * FROM matches").fetchall()
    matches = [dict(r) for r in rows]

    for match in matches:
        match.pop('upload_user_id')
        match['p0_maps'] = match['p0_maps'].split('||')
        match['p1_maps'] = match['p1_maps'].split('||')
        rows = db.execute(
            "SELECT game_version, recording_id as id FROM recordings JOIN matches_recordings ON recording_id=recordings.id WHERE match_id=?",
            [match['id']]).fetchall()
        match['recordings'] = [dict(r) for r in rows]

        # generate fake recordings
        best_of = match['best_of']
        recs = match['recordings']
        n = len(recs)
        while n < best_of:
            prev = recs[n - 1]
            recs.append(dict(game_version=prev['game_version'], id=prev['id'] + 1))
            n += 1

    response.set_header('Content-Type', 'application/json')
    return json.dumps(matches)


@route('/api/match/<match_id:int>/recording/<rec_id:int>', method='GET')
def get_match_recording(match_id, rec_id, db):
    match = dict(
        db.execute("SELECT `date`, p0_name, p1_name, best_of, `group` FROM matches WHERE id=?", [match_id]).fetchone())
    match_date = datetime.datetime.fromtimestamp(match['date']).strftime('%Y-%m-%d')
    rows = db.execute("SELECT filename, completed, recording_id as id FROM recordings JOIN matches_recordings"
                      " ON matches_recordings.recording_id = recordings.id WHERE matches_recordings.match_id = ?",
                      [match_id]).fetchall()
    recordings = [dict(r) for r in rows]
    recordings.sort(key=lambda r: r['id'])

    rec_ = list(filter(lambda r: r['id'] == rec_id, recordings))[:1]
    if rec_:
        rec = rec_[0]
        number = recordings.index(rec) + 1

    else:
        # generate a fake one
        last = max(recordings, key=lambda r: r['id'])
        random.seed(match['date'])
        rec = random.choice(recordings)
        number = len(recordings) + (rec_id - last['id'])

    download_filename = "{} {} - {} vs {} - {} BO{}.aoe2record" \
        .format(match_date, number, match['p0_name'], match['p1_name'], match['group'], match['best_of'])

    return static_file(rec['filename'], RECORDINGS_PATH, download=download_filename)


@route('/gen_passwords/<count>')
def generate_passwords(count, db):
    import secrets

    generated = []
    for i in range(0, int(count)):
        password_length = 14
        generated.append(secrets.token_urlsafe(password_length))

    return ",".join(generated)


@route('/')
def index(db):
    return static_file('index.html', root=STATICS_PATH)


@route('/<fpath:path>')
def hello(fpath, db):
    return static_file(fpath, root=STATICS_PATH)


session_opts = {
    'session.type': 'file',
    'session.data_dir': SESSIONS_DATA_DIR,
    'session.lock_dir': SESSIONS_LOCK_DIR,
    'session.cookie_expires': False,
    'session.auto': True,
    'session.secret': SESSION_SECRET,
    'session.secure': True,
    'session.httponly': True,
    'session.timeout': 60*60*24*7  # one week
}
app = SessionMiddleware(app, session_opts)

run(app, host='0.0.0.0', port=8080)
