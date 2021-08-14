import enum
from collections import OrderedDict
from functools import partial
from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    roles = Column(Integer, default=0, nullable=False)


class WatchStatus:
    UNTOUCHED = 0
    COMMENTED = 1
    WATCHED = 2


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
    upload_user_id = Column(Integer, nullable=False)
    best_of = Column(Integer)
    p0_civ_bans = Column(String)
    p1_civ_bans = Column(String)
    watch_status = Column(Integer, default=WatchStatus.UNTOUCHED)

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
    profile_id = Column(ForeignKey('users.id'), primary_key=True)
    name = Column(String, nullable=False)
    civ = Column(String, nullable=False)
    team_index = Column(Integer, nullable=False)
