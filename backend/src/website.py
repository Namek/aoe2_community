import datetime
import random
import re
import os
from typing import (List, Optional)

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware


from . import cfg, crud, models, schemas, utils
from .database import web_db as get_db
from .validation import validate_maps

ROLE_ADMIN = 1

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=cfg.SESSION_SECRET)


if cfg.CORS_ALLOW_ORIGIN:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[cfg.CORS_ALLOW_ORIGIN or '*'],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def get_current_user(request: Request, db: Session = Depends(get_db)):
    if 'user_id' not in request.session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Nie można!")
    return crud.get_user(db, request.session['user_id'])


def get_current_admin_user(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not user or user.roles != ROLE_ADMIN:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Nie można!")
    return user


@app.post('/api/auth/check')
def auth_check(db: Session = Depends(get_db), user: models.User = Depends(get_current_admin_user)):
    return {"id": user.id, "roles": user.roles}


@app.post('/api/auth')
def auth_log_in(request: Request, response: Response, db: Session = Depends(get_db), password: str = Form(...)):
    user = crud.get_user_by_password(db, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nie można!")

    if user.roles != ROLE_ADMIN:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Nie można!")

    request.session['user_id'] = user.id
    return {"id": user.id, "roles": user.roles}


@app.delete('/api/auth')
def auth_log_out(request: Request):
    request.session.clear()


@app.delete('/api/match/{match_id}')
def remove_match(match_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin_user)):
    if current_user.roles != ROLE_ADMIN:
        raise HTTPException(401, detail="Nie można!")

    MR = models.AssocMatchesRecordings
    RP = models.AssocRecordingsPlayers

    recordings_ids = db.execute(select(MR.recording_id).filter_by(match_id=match_id)).all()
    recordings_ids = [r[0] for r in recordings_ids]
    db.execute(delete(MR).where(MR.match_id == match_id))
    db.execute(delete(RP).where(RP.recording_id.in_(recordings_ids)))
    db.execute(delete(models.Recording).where(models.Recording.id.in_(recordings_ids)))
    db.execute(delete(models.Match).where(models.Match.id == match_id))
    db.commit()


@app.post('/api/match')
def post_match(
    new_match: schemas.MatchIn = Depends(schemas.MatchIn.as_form),
    password: str = Form(...),
    recording_files: List[UploadFile] = File(...),
    recording_times: List[int] = Form(...),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_password(db, password)

    if user is None:
        raise HTTPException(status_code=500, detail="Błędne hasło. Nie wymyślaj swojego :)")

    is_admin = int(user.roles) == ROLE_ADMIN

    if new_match.civ_draft:
        new_match.civ_draft = new_match.civ_draft.replace('https://aoe2cm.net/draft/', '')

    # check duplicates of civ bans
    if new_match.p0_civ_bans:
        if len(set(new_match.p0_civ_bans)) != len(new_match.p0_civ_bans) or len(set(new_match.p1_civ_bans)) != len(new_match.p1_civ_bans):
            raise HTTPException(500, detail="Powtórzone bany cywilizacji")

    # frontend may sent empty file
    recording_files = [file for file in recording_files if file.filename]

    # check if there are no duplicates by filenames
    if len(set([file.filename for idx, file in enumerate(recording_files)])) != len(recording_files):
        raise HTTPException(500, detail="Duplikaty plików")

    all_maps = new_match.p0_maps + new_match.p1_maps

    if (new_match.p0_map_ban and new_match.p0_map_ban in all_maps) \
            or (new_match.p1_map_ban and new_match.p1_map_ban in all_maps):
        raise HTTPException(500, detail='Zbanowana mapa nie może być grana ;)')

    recordings = []
    for idx, file in enumerate(recording_files):
        try:
            match_info = utils.get_match_info(file.file)
            recordings.append((file, match_info, recording_times[idx]))
        except:
            raise HTTPException(500, detail=f"Uszkodzony plik nagrania: {file.filename}")
    recordings.sort(key=lambda r: r[0].filename)

    # check duplicates by map names (but ignore restored matches)
    map_names = [r[1]['map_name']
                 for r in recordings if r[1]['start_time_seconds'] <= 5]
    if len(set(map_names)) > len(recordings):
        raise HTTPException(500, detail=f'Powtórzono mapy: {", ".join(map_names)}')

    # verify whether all the given recordings match the maps
    if not is_admin:
        recordings_maps = [match_info['map_name'] for (_, match_info, _) in recordings]
        result = validate_maps(all_maps, recordings_maps)
        if type(result) == str:
            raise HTTPException(500, detail=str)

    def update_dict(original_dict, **kwargs):
        return {**original_dict, **kwargs}

    db_match = models.Match(**update_dict(
        new_match.dict(),
        date=int(datetime.datetime.strptime(new_match.date, '%Y-%m-%d').timestamp()),
        p0_maps='||'.join(new_match.p0_maps),
        p1_maps='||'.join(new_match.p1_maps),
        p0_civ_bans='||'.join(new_match.p0_civ_bans) if new_match.p0_civ_bans else None,
        p1_civ_bans='||'.join(new_match.p1_civ_bans) if new_match.p1_civ_bans else None,
        upload_user_id=user.id,
        watch_status=models.WatchStatus.UNTOUCHED
    ))

    db.add(db_match)
    db.flush()
    db.refresh(db_match)

    match_id = db_match.id

    saved_files = []
    for i, (file, match_info, mod_time) in enumerate(recordings):
        new_filename = 'rec_match{}_{}'.format(match_id, i)
        teams = match_info['teams']
        order = i

        db_recording = models.Recording(
            filename=new_filename,
            original_filename=file.filename,
            mod_time=mod_time,
            map_name=match_info['map_name'],
            completed=1 if match_info['completed'] else 0,
            game_version=match_info['game_version'],
            game_map_type=match_info['game_map_type'],
            team_count=len(teams),
            start_time_seconds=match_info['start_time_seconds'],
            duration_seconds=match_info['duration_seconds']
        )
        db.add(db_recording)
        db.flush()
        db.refresh(db_recording)
        recording_id = db_recording.id

        db_match_rec_assoc = models.AssocMatchesRecordings(match_id=match_id, recording_id=recording_id, order=order)
        db.add(db_match_rec_assoc)
        db.flush()

        players = match_info['players']
        for pi, player in enumerate(players):
            profile_id = player['user_id']
            number = player['number']
            team_index = 0
            for ti, team in enumerate(teams):
                if number in team:
                    team_index = ti

            db_player_rec_assoc = models.AssocRecordingsPlayers(
                recording_id=recording_id,
                profile_id=profile_id,
                name=player['name'],
                civ=player['civilization'],
                team_index=team_index
            )
            db.add(db_player_rec_assoc)
            db.flush()

        with open(f'{cfg.RECORDINGS_PATH}/{new_filename}', 'wb') as fp:
            utils.copy_file(file.file, fp)
            saved_files.append(new_filename)

    if len(recordings) == len(saved_files):
        db.commit()
    else:
        db.rollback()
        raise HTTPException(500)


@app.patch("/api/match/{match_id}")
def patch_match(match_id: int, patch: schemas.MatchPatch, db: Session = Depends(get_db), user: models.User = Depends(get_current_admin_user)):
    crud.patch_match(db, match_id, patch)
    db.commit()


@app.get('/api/matches', response_model=List[schemas.MatchOut])
def get_matches(db: Session = Depends(get_db)):
    matches = crud.get_matches(db)

    # generate fake recordings
    for match in matches:
        n = len(match.recordings)

        while n > 0 and n < match.best_of:
            prev = match.recordings[n - 1]
            newRec = models.Recording(
                game_version=prev.game_version, id=prev.id + 1)
            match.recordings.append(newRec)
            n += 1

    return matches


@app.get('/api/match/{match_id}/recording/{rec_id}', response_class=FileResponse)
def get_match_recording(match_id: int, rec_id: int, db: Session = Depends(get_db)):
    match: models.Match = db.query(models.Match).filter(models.Match.id == match_id).first()
    recordings = match.recordings
    match_date = datetime.datetime.fromtimestamp(match.date).strftime('%Y-%m-%d')

    rec_ = list(filter(lambda r: r.id == rec_id, recordings))[:1]
    if rec_:
        rec = rec_[0]
        number = recordings.index(rec) + 1
    else:
        # generate a fake one
        last = max(recordings, key=lambda r: r.id)
        random.seed(match.date)
        rec = random.choice(recordings)
        number = len(recordings) + (rec_id - last.id)

    path = os.path.join(cfg.RECORDINGS_PATH, rec.filename)
    download_filename = "{} {} - {} vs {} - {} BO{}.aoe2record" \
        .format(match_date, number, match.p0_name, match.p1_name, match.group, match.best_of)

    return FileResponse(path=path, filename=download_filename)


@app.get('/api/calendar', response_model=List[schemas.CalendarEntry])
def get_calendar_entries(db: Session = Depends(get_db)):
    return crud.get_calendar_entries(db)

@app.get('/', response_class=FileResponse)
@app.get('/admin', response_class=FileResponse)
@app.get('/logout', response_class=FileResponse)
def index():
    return FileResponse(os.path.join(cfg.STATICS_PATH, 'index.html'))


app.mount("/", StaticFiles(directory=cfg.STATICS_PATH), name="static")
