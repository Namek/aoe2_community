from sqlalchemy import update
from sqlalchemy.orm import Session
from typing import (List, Optional)

from . import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_password(db: Session, password: str) -> models.User:
    return db.query(models.User).filter(models.User.password == password).first()


def create_match(db: Session, match: schemas.MatchIn, upload_user_id: int):
    db_match = models.Match(**match.dict(), upload_user_id=upload_user_id)
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match


def get_matches(db: Session) -> List[schemas.MatchOut]:
    matches = db.query(models.Match).all()

    for match in matches:
        match.recordings
        match.p0_maps = match.p0_maps.split('||')
        match.p1_maps = match.p1_maps.split('||')
        match.p0_civ_bans = match.p0_civ_bans.split('||') if match.p0_civ_bans else []
        match.p1_civ_bans = match.p1_civ_bans.split('||') if match.p1_civ_bans else []

    return matches


def get_match(db: Session, id: int) -> models.Match:
    return db.query(models.Match).filter(models.Match.id == id).first()


def patch_match(db: Session, match_id: int, values: schemas.MatchPatch):
    patch = values.dict(exclude_unset=True)
    db.execute(
        update(models.Match).
        where(models.Match.id == match_id).
        values(**patch)
    )
    db.commit()
