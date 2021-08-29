from sqlalchemy import delete, select, update
from sqlalchemy.orm import aliased
from typing import (List, Optional)

from . import schemas
from .models import Match, Recording, WatchStatus, User, Message, MessageSource, CalendarEntry
from .database import DbSession


def get_user(db: DbSession, user_id: int):
    query = select(User).where(User.id == user_id).limit(1)
    return db.execute(query).scalars().one()


def get_user_by_password(db: DbSession, password: str) -> User:
    query = select(User).where(User.password == password).limit(1)
    return db.execute(query).scalars().one()


def create_match(db: DbSession, match: schemas.MatchIn, upload_user_id: int):
    db_match = Match(**match.dict(), upload_user_id=upload_user_id)
    db.add(db_match)
    db.flush()
    db.refresh(db_match)
    return db_match


def get_matches(db: DbSession) -> List[schemas.MatchOut]:
    matches = db.execute(select(Match)).scalars().all()

    for match in matches:
        match.recordings
        match.p0_maps = match.p0_maps.split('||')
        match.p1_maps = match.p1_maps.split('||')
        match.p0_civ_bans = match.p0_civ_bans.split('||') if match.p0_civ_bans else []
        match.p1_civ_bans = match.p1_civ_bans.split('||') if match.p1_civ_bans else []

    return matches


def get_match(db: DbSession, id: int) -> Match:
    query = select(Match).where(Match.id == id).limit(1)
    return db.execute(query).scalars().one()


def patch_match(db: DbSession, match_id: int, values: schemas.MatchPatch):
    if values.watch_status and (values.watch_status not in WatchStatus.values()):
        raise ValueError('invalid watch_status')

    patch = values.dict(exclude_unset=True)
    db.execute(
        update(Match).
        where(Match.id == match_id).
        values(**patch)
    )
    db.flush()


def get_message_by_original_id(db: DbSession, id: str) -> Message:
    query = select(Message).where(Message.original_id == id).limit(1)
    return db.execute(query).scalars().one_or_none()


def update_message_content(db: DbSession, id: int, content: str, is_parsed: bool):
    query = update(Message).where(Message.id == id).values(content=content, is_parsed=is_parsed)
    db.execute(query)
    db.flush()
    return db.execute(select(Message).where(Message.id == id)).scalars().one()


def get_or_create_message_source(db: DbSession, guild_id: int, channel_id: int, channel_name: str) -> MessageSource:
    query = select(MessageSource).\
        where(MessageSource.guild_id == guild_id).\
        where(MessageSource.channel_id == channel_id)
    source = db.execute(query).scalars().one_or_none()

    if not source:
        source = MessageSource(guild_id=guild_id, channel_id=channel_id, channel_name=channel_name)
        db.add(source)
        db.flush()
        db.refresh(source)

    return source


def get_calendar_entries(db: DbSession) -> List[schemas.CalendarEntry]:
    query = select(CalendarEntry, Message.source_id).join(Message, CalendarEntry.message_id == Message.id)
    result = [
        schemas.CalendarEntry(id=entry.id, datetime=entry.datetime, description=entry.description, source_id=source_id)
        for [entry, source_id] in db.execute(query).all()]

    return result


def get_calendar_entry_by_message_id(db: DbSession, msg_id: int) -> CalendarEntry:
    query = select(CalendarEntry).where(CalendarEntry.message_id == msg_id).limit(1)
    return db.execute(query).scalars().one_or_none()


def update_calendar_entry(db: DbSession, id: int, datetime, description: str):
    query = update(CalendarEntry).where(CalendarEntry.id == id).values(datetime=datetime, description=description)
    db.execute(query)


def delete_message_with_calendar_entries(db: DbSession, msg_id: int):
    db.execute(delete(CalendarEntry).where(CalendarEntry.message_id == msg_id))
    db.execute(delete(Message).where(Message.id == msg_id))
