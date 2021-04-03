from dotenv import load_dotenv
import json
import random

from mgz.summary import Summary
from bottle import Bottle, run, static_file, request, response
from bottle_sqlite import SQLitePlugin
import datetime
import os


load_dotenv()
RECORDINGS_PATH = os.getenv('RECORDINGS_PATH') or './database/files'
ENABLE_LOCAL_CORS = bool(os.getenv('ENABLE_LOCAL_CORS'))
STATICS_PATH = os.getenv('STATICS_PATH') or './static'
DB_PATH = './database/app.db'


class EnableCors(object):
    name = 'enable_cors'
    api = 2

    def apply(self, fn, context):
        def _enable_cors(*args, **kwargs):
            # set CORS headers
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

            if request.method != 'OPTIONS':
                # actual request; reply with the actual response
                return fn(*args, **kwargs)

        return _enable_cors


app = Bottle()
app.install(SQLitePlugin(dbfile=DB_PATH, autocommit=False))

if ENABLE_LOCAL_CORS:
    app.install(EnableCors())

try:
    os.mkdir(RECORDINGS_PATH)
except:
    pass


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


def _copy_file(file, fp, chunk_size=2 ** 16):
    file.seek(0)
    read, write, offset = file.read, fp.write, file.tell()
    while 1:
        buf = read(chunk_size)
        if not buf: break
        write(buf)
    file.seek(offset)


@app.route('/api/match', method='POST')
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
        raise Exception()

    user_id = user[0]

    recordings = [(file, get_match_info(file.file), recording_times[idx]) for idx, file in enumerate(recording_files)]
    recordings.sort(key=lambda r: r[2])
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


@app.route('/api/matches', method='GET')
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


@app.route('/api/match/<match_id:int>/recording/<rec_id:int>', method='GET')
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


@app.route('/gen_passwords/<count>')
def generate_passwords(count, db):
    import secrets

    generated = []
    for i in range(0, int(count)):
        password_length = 14
        generated.append(secrets.token_urlsafe(password_length))

    return ",".join(generated)


@app.route('/')
def index(db):
    return static_file('index.html', root=STATICS_PATH)


@app.route('/<fpath:path>')
def hello(fpath, db):
    return static_file(fpath, root=STATICS_PATH)


run(app, host='0.0.0.0', port=8080)
