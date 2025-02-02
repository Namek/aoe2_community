from datetime import datetime as dt
import enum
from collections import OrderedDict
from functools import partial
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from typing import List

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    roles = Column(Integer, default=0, nullable=False)


class WatchStatus(enum.IntEnum):
    UNTOUCHED = 0
    WATCHED = 1
    COMMENTED = 2
    WATCHED_AND_NOTED = 3
    TO_BE_COMMENTED_SOON = 4

    @classmethod
    def values(cls):
        return [m.value for _, m in cls.__members__.items()]


class ActivityLogType(enum.IntEnum):
    NEW_MATCH_UPLOAD_FAIL = 1
    NEW_MATCH_UPLOAD_SUCCESS = 2
    DOWNLOAD_RECORDING = 3


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    group = Column(String)
    civ_draft = Column(String)
    date = Column(Integer)
    p0_name = Column(String)
    p0_map_ban = Column(String)
    p0_maps = Column(String)
    p1_name = Column(String)
    p1_map_ban = Column(String)
    p1_maps = Column(String)
    upload_user_id = Column(ForeignKey('users.id'), nullable=False)
    best_of = Column(Integer)
    p0_civ_bans = Column(String)
    p1_civ_bans = Column(String)
    watch_status = Column(Integer, nullable=False, default=WatchStatus.UNTOUCHED)

    recordings = relationship("Recording", secondary="matches_recordings",
                              back_populates="match", order_by="asc(AssocMatchesRecordings.order)")


class Recording(Base):
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    mod_time = Column(Integer, nullable=False)
    map_name = Column(String, nullable=False)
    completed = Column(Boolean, nullable=False)
    game_version = Column(String, nullable=False)
    team_count = Column(Integer, nullable=False)
    game_map_type = Column(String, nullable=False)
    start_time_seconds = Column(Integer, nullable=False, default=0)
    duration_seconds = Column(Integer, nullable=False, default=0)

    match = relationship("Match", secondary="matches_recordings", back_populates="recordings")


class AssocMatchesRecordings(Base):
    __tablename__ = 'matches_recordings'

    match_id = Column(ForeignKey('matches.id'), primary_key=True)
    recording_id = Column(ForeignKey('recordings.id'), primary_key=True)
    order = Column(Integer)

    match = relationship(Match, viewonly=True)
    recording = relationship(Recording, viewonly=True)


class AssocRecordingsPlayers(Base):
    __tablename__ = 'recordings_players'

    recording_id = Column(ForeignKey('recordings.id'), primary_key=True)
    profile_id = Column(Integer)
    name = Column(String, nullable=False)
    civ = Column(String, nullable=False)
    team_index = Column(Integer, nullable=False)


class MessageSource(Base):
    __tablename__ = 'message_sources'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    guild_id = Column(Integer, nullable=False)
    channel_id = Column(Integer, nullable=False)
    channel_name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=dt.now)
    modified_at = Column(DateTime, nullable=False, default=dt.now, onupdate=dt.now)


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    original_id = Column(Integer, index=True)
    source_id = Column(ForeignKey('message_sources.id'), nullable=False)
    content = Column(String, nullable=False)
    is_parsed = Column(Integer, nullable=False, default=0)
    is_manually_ignored = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=dt.now)
    modified_at = Column(DateTime, nullable=False, default=dt.now, onupdate=dt.now)


class CalendarEntry(Base):
    __tablename__ = 'calendar'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    message_id = Column(Integer, nullable=False, index=True)
    datetime = Column(DateTime, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=dt.now)
    modified_at = Column(DateTime, nullable=False, default=dt.now, onupdate=dt.now)
    spectate_on = Column(Boolean, nullable=True)
    spectate_link = Column(String, nullable=True)


class ActivityLog(Base):
    __tablename__ = 'activity_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    datetime = Column(DateTime, nullable=False, default=dt.now)
    type = Column(Integer, nullable=False)
    table = Column(String, nullable=True)
    item_id = Column(Integer, nullable=True)
    user_id = Column(ForeignKey('users.id'), nullable=True)
    details = Column(String, nullable=True)
