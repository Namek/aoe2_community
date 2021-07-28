import inspect
from typing import Type

from fastapi import Form
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
import pydantic
from pydantic.fields import ModelField

from mgz.model import parse_match
from mgz.summary import Summary


def copy_file(source_file, dest_file, chunk_size=2 ** 16):
    source_file.seek(0)
    read, write, offset = source_file.read, dest_file.write, source_file.tell()
    while 1:
        buf = read(chunk_size)
        if not buf:
            break
        write(buf)
    source_file.seek(offset)


def get_match_info(data):
    try:
        # some files seems broken for this library when using the `Summary`.
        m = parse_match(data)
        players = [dict(name=p.name, user_id=p.profile_id, number=p.number,
                        civilization=p.civilization) for p in m.players]

        return dict(
            map_name=m.map.name,
            game_version=f"{m.version.name} {m.version.value}",
            game_map_type=m.type,
            players=players,
            teams=m.teams,
            completed=False,
            start_time_seconds=int(m.actions[0].timestamp.seconds),
            duration_seconds=m.duration.seconds,
        )
    except RuntimeError:
        # the `parse_match` method doesn't work for restored recordings, thus, let's try with the `Summary`.
        s = Summary(data)

        return dict(
            map_name=s.get_map()['name'],
            game_version=" ".join(str(x) for x in s.get_version()),
            game_map_type=s.get_settings()['type'][1],
            players=s.get_players(),
            teams=s.get_teams(),
            completed=s.get_completed(),
            start_time_seconds=int(s.get_start_time()/1000),
            duration_seconds=int(s.get_duration()/1000),
        )


def as_form(cls: Type[BaseModel]):
    """
    Adds an as_form class method to decorated models. The as_form class method
    can be used with FastAPI endpoints
    """
    new_params = [
        inspect.Parameter(
            field.alias,
            inspect.Parameter.POSITIONAL_ONLY,
            default=(Form(field.default) if not field.required else Form(...)),
            annotation=field.outer_type_
        )
        for field in cls.__fields__.values()
    ]

    async def _as_form(**data):
        try:
            return cls(**data)
        except pydantic.ValidationError as e:
            raise RequestValidationError(e.raw_errors)

    sig = inspect.signature(_as_form)
    sig = sig.replace(parameters=new_params)
    _as_form.__signature__ = sig
    setattr(cls, "as_form", _as_form)
    return cls
