import datetime
from typing import List, Optional

from fastapi import Body, File, Form
from fastapi.datastructures import UploadFile
from pydantic import BaseModel
from typing_extensions import ParamSpecArgs

from .utils import as_form


class RecordingOut(BaseModel):
    id: int
    game_version: str

    class Config:
        orm_mode = True


class MatchBase(BaseModel):
    group: str
    civ_draft: Optional[str] = None
    date: str
    best_of: int
    p0_name: str
    p1_name: str
    p0_maps: List[str]
    p1_maps: List[str]
    p0_map_ban: Optional[str]
    p1_map_ban: Optional[str]
    p0_civ_bans: Optional[List[str]] = None
    p1_civ_bans: Optional[List[str]] = None


@as_form
class MatchIn(MatchBase):
    pass


class MatchOut(MatchBase):
    id: int
    watch_status: int
    recordings: List[RecordingOut]

    class Config:
        orm_mode = True

class MatchPatch(BaseModel):
    watch_status: Optional[int]


class CalendarEntry(BaseModel):
    id: int
    datetime: datetime.datetime
    description: str
    source_id: int

    class Config:
        orm_mode = True
