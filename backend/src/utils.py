import inspect
from typing import Type

from fastapi import Form
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
import pydantic


def copy_file(source_file, dest_file, chunk_size=2 ** 16):
    read, write, offset = source_file.read, dest_file.write, source_file.tell()
    source_file.seek(0)
    while 1:
        buf = read(chunk_size)
        if not buf:
            break
        write(buf)
    source_file.seek(offset)


def get_file_size(file):
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    return size


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


def pick_one(elements, predicate):
    new_list = []

    for i, el in enumerate(elements):
        if predicate(el):
            rest = new_list + elements[(i + 1):]
            return el, rest
        else:
            new_list.append(el)

    return None, new_list
