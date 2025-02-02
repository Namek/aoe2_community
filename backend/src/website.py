from datetime import datetime, date
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
from .recordings import get_match_info
from .validation import validate_maps

ROLE_ADMIN = 1
START_TIME_SECONDS_TO_MARK_AS_RESTORE = 5

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=cfg.SESSION_SECRET)


if cfg.CORS_ALLOW_ORIGIN:
    print("Enable CORS: " + cfg.CORS_ALLOW_ORIGIN)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[cfg.CORS_ALLOW_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def get_current_user(request: Request, db: Session = Depends(get_db)):
    if 'user_id' not in request.session:
        return None
    return crud.get_user(db, request.session['user_id'])


def ensure_current_user(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Nie można!")
    return user


def ensure_current_admin_user(request: Request, db: Session = Depends(get_db), user: models.User = Depends(ensure_current_user)):
    if not user or user.roles != ROLE_ADMIN:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Nie można!")
    return user


@app.post('/api/auth/check')
def auth_check(db: Session = Depends(get_db), user: models.User = Depends(ensure_current_admin_user)):
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
def remove_match(match_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(ensure_current_admin_user)):
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


def log_upload_fail_and_raise(db: Session, user_id: Optional[int], details: str):
    db_activity_log = models.ActivityLog(
        type=models.ActivityLogType.NEW_MATCH_UPLOAD_FAIL,
        table=models.Match.__tablename__,
        user_id=user_id,
        details=details
    )
    db.add(db_activity_log)
    db.commit()
    raise HTTPException(500, detail=details)


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
        log_upload_fail_and_raise(db, None, "Błędne hasło. Nie wymyślaj swojego :)")

    is_admin = int(user.roles) == ROLE_ADMIN

    if not new_match.date:
        log_upload_fail_and_raise(db, user.id, 'Brak daty.')
    match_date = datetime.strptime(new_match.date, '%Y-%m-%d').date()
    date_days_diff = date.today() - match_date

    if date_days_diff.days > 360:
        log_upload_fail_and_raise(db, user.id, 'Podano datę daleko w przeszłości.')
    if (-date_days_diff.days) > 2:
        # 2 days in the future is for not managing timezones
        log_upload_fail_and_raise(db, user.id, 'Czy graliście w przyszłości? Sprawdź datę.')

    if new_match.civ_draft:
        new_match.civ_draft = new_match.civ_draft.replace('https://aoe2cm.net/draft/', '')

    # check duplicates of civ bans
    if new_match.p0_civ_bans:
        if len(set(new_match.p0_civ_bans)) != len(new_match.p0_civ_bans) or len(set(new_match.p1_civ_bans)) != len(new_match.p1_civ_bans):
            log_upload_fail_and_raise(db, user.id, "Powtórzone bany cywilizacji")

    # frontend may have sent an empty file, filter it out
    recording_files = [file for file in recording_files if file.filename]
    recording_files_sizes = list(set([utils.get_file_size(file.file) for file in recording_files]))

    # check if there are no duplicates by file names and file sizes
    if len(set([file.filename for idx, file in enumerate(recording_files)])) != len(recording_files) or len(recording_files_sizes) != len(recording_files):
        log_upload_fail_and_raise(db, user.id, "Wykryto duplikaty plików. Jeśli zagraliście mniej gier to nie ma potrzeby wrzucania sztucznych nagrań, strona sama je wygeneruje.")

    all_maps = new_match.p0_maps + new_match.p1_maps

    if (new_match.p0_map_ban and new_match.p0_map_ban in all_maps) \
            or (new_match.p1_map_ban and new_match.p1_map_ban in all_maps):
        log_upload_fail_and_raise(db, user.id, 'Zbanowana mapa nie może być grana ;)')

    should_fail_on_wrong_file = cfg.CAN_FAIL_ON_RECORDING_PARSE and not is_admin
    has_failing_files = False

    recordings = []
    for idx, file in enumerate(recording_files):
        match_info = None
        try:
            match_info = get_match_info(file.file)
        except:
            has_failing_files = True
            if should_fail_on_wrong_file:
                log_upload_fail_and_raise(db, user.id, f"Uszkodzony plik nagrania: {file.filename}")

        recordings.append((file, match_info, recording_times[idx]))
    recordings.sort(key=lambda r: r[0].filename)

    if not has_failing_files and should_fail_on_wrong_file:
        # check duplicates by map names (but ignore restored matches)
        map_names = [r[1]['map_name']
                     for r in recordings if r[1]['start_time_seconds'] <= START_TIME_SECONDS_TO_MARK_AS_RESTORE]
        if len(set(map_names)) > len(recordings):
            log_upload_fail_and_raise(db, user.id, f'Powtórzono mapy: {", ".join(map_names)}')

        # verify whether all the given recordings match the maps
        recordings_maps = [match_info['map_name'] for (_, match_info, _) in recordings]
        result = validate_maps(all_maps, recordings_maps)
        if type(result) == str:
            log_upload_fail_and_raise(db, user.id, result)

    def update_dict(original_dict, **kwargs):
        return {**original_dict, **kwargs}

    db_match = models.Match(**update_dict(
        new_match.dict(),
        date=int(datetime.strptime(new_match.date, '%Y-%m-%d').timestamp()),
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
        order = i

        if match_info:
            teams = match_info['teams']
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
        else:
            db_recording = models.Recording(
                filename=new_filename,
                original_filename=file.filename,
                mod_time=mod_time,
            )
        db.add(db_recording)
        db.flush()
        db.refresh(db_recording)
        recording_id = db_recording.id

        db_match_rec_assoc = models.AssocMatchesRecordings(match_id=match_id, recording_id=recording_id, order=order)
        db.add(db_match_rec_assoc)
        db.flush()

        if match_info:
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
        db_activity_log = models.ActivityLog(
            type=models.ActivityLogType.NEW_MATCH_UPLOAD_SUCCESS,
            table=models.Match.__tablename__,
            item_id=match_id,
            user_id=user.id
        )
        db.add(db_activity_log)
        db.commit()
    else:
        db.rollback()
        log_upload_fail_and_raise(db, user.id, 'Nie udało się zapisać wszystkich plików')


@app.patch("/api/match/{match_id}")
def patch_match(match_id: int, patch: schemas.MatchPatch, db: Session = Depends(get_db), user: models.User = Depends(ensure_current_admin_user)):
    crud.patch_match(db, match_id, patch)
    db.commit()


@app.get('/api/matches', response_model=List[schemas.MatchOut])
def get_matches(db: Session = Depends(get_db)):
    matches = crud.get_matches(db)

    # generate fake recordings
    for match in matches:
        n = len(match.recordings)
        restores_count = len(list(filter(lambda r: r.start_time_seconds >
                             START_TIME_SECONDS_TO_MARK_AS_RESTORE, match.recordings)))

        while n > 0 and n < (match.best_of + restores_count):
            prev = match.recordings[n - 1]
            newRec = models.Recording(
                game_version=prev.game_version, id=prev.id + 1)
            match.recordings.append(newRec)
            n += 1

    return matches


@app.get('/api/match/{match_id}/recording/{rec_id}', response_class=FileResponse)
def get_match_recording(match_id: int, rec_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    match: models.Match = db.query(models.Match).filter(models.Match.id == match_id).first()
    recordings = match.recordings
    match_date = datetime.fromtimestamp(match.date).strftime('%Y-%m-%d')

    rec_ = list(filter(lambda r: r.id == rec_id, recordings))[:1]
    if rec_:
        rec = rec_[0]
        number = recordings.index(rec) + 1
        details = f'number: {number}/{match.best_of}, rec_id: {rec.id}'

    else:
        # generate a fake one
        last = max(recordings, key=lambda r: r.id)
        random.seed(match.date)
        rec = random.choice(recordings)
        number = len(recordings) + (rec_id - last.id)
        details = f'number: {number}/{match.best_of}, fake rec_id: {rec.id}'

    path = os.path.join(cfg.RECORDINGS_PATH, rec.filename)
    download_filename = "{} {} - {} vs {} - {} BO{}.aoe2record" \
        .format(match_date, number, match.p0_name, match.p1_name, match.group, match.best_of)

    user_id = None
    if user:
        user_id = user.id

    db_log = models.ActivityLog(
        type=models.ActivityLogType.DOWNLOAD_RECORDING,
        table=models.Match.__tablename__,
        item_id=match_id,
        user_id=user_id,
        details=details
    )
    db.add(db_log)
    db.commit()

    return FileResponse(path=path, filename=download_filename)


@app.get('/api/calendar', response_model=List[schemas.CalendarEntry])
def get_calendar_entries(db: Session = Depends(get_db)):
    return crud.get_calendar_entries(db)


@app.patch("/api/calendar/{entry_id}")
def patch_calendar_entry(entry_id: int, patch: schemas.CalendarEntryPatch, db: Session = Depends(get_db), user: models.User = Depends(ensure_current_admin_user)):
    crud.patch_calendar_entry(db, entry_id, patch)
    db.commit()


@app.get('/', response_class=FileResponse)
@app.get('/admin', response_class=FileResponse)
@app.get('/logout', response_class=FileResponse)
def index():
    return FileResponse(os.path.join(cfg.STATICS_PATH, 'index.html'))


app.mount("/", StaticFiles(directory=cfg.STATICS_PATH), name="static")
