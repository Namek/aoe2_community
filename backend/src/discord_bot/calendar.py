from typing import cast

import discord

from .. import cfg, crud, models
from ..database import DbSession
from .calendar_messages import analyze_message_content, cleanup_message


async def process_message(client: discord.Client, db: DbSession, message: discord.Message, channel: discord.TextChannel):
    text = cleanup_message(cast(str, message.clean_content))

    if message.author == client.user:
        print('ignoring message by bot')
        return

    if message.pinned:
        print('ignoring pinned message')
        return

    db_msg = crud.get_message_by_original_id(db, message.id)
    is_content_new = not db_msg or db_msg.content != text

    if not is_content_new and (db_msg and db_msg.is_parsed == 1):
        return

    parsed = analyze_message_content(text, message.created_at)
    is_parsed = parsed is not None and parsed.datetime is not None and parsed.content is not None

    db_channel = crud.get_or_create_message_source(db, channel.guild.id, channel.id, channel.name)

    if not db_msg:
        db_msg = models.Message(original_id=message.id, source_id=db_channel.id, content=text, is_parsed=is_parsed)
        db.add(db_msg)
        db.flush()
        db.refresh(db_msg)
    else:
        db_msg = crud.update_message_content(db, db_msg.id, text, is_parsed)

    db_calendar = crud.get_calendar_entry_by_message_id(db, db_msg.id)

    if parsed and parsed.datetime and parsed.content:
        calendar_entry_text = parsed.group.strip() + " Ants\n" + " vs ".join([v.strip() for v in parsed.vs]) \
            if parsed.vs and parsed.group else parsed.content

        await message.add_reaction('📅')

        if not db_calendar:
            db_calendar = models.CalendarEntry(
                message_id=db_msg.id, datetime=parsed.datetime, description=calendar_entry_text)
            db.add(db_calendar)
        else:
            crud.update_calendar_entry(db, db_calendar.id, parsed.datetime, calendar_entry_text)
    else:
        if db_calendar:
            db.delete(db_calendar)

        author_name = message.author.display_name
        print(f'I cannot parse this one by {author_name}:\n{text}\n')
        print(parsed)
        print('\n')

        # when the message can't be parsed then ask user to edit it
        if cfg.DISCORD_BOT_BUGGING_PEOPLE and is_content_new:
            url_text = f' {cfg.WEBSITE_URL}' if cfg.WEBSITE_URL else ''
            fix_request_message = f'Chcę umieścić wydarzenie do kalendarza{url_text},' +\
                ' ale nie widzę w tej wiadomości poprawnej daty i godziny.' +\
                f' Zedytuj proszę swoją wiadomość na kanale #{channel.name}:\n{message.content}\n\n' +\
                'Przykład:\n\n10.08.2021 wtorek, godzina 20:00\nGreen Ants\n@Namek vs @Golik\n\n'

            author = cast(discord.User, message.author)
            dm_channel: discord.DMChannel = author.dm_channel or await author.create_dm()
            await dm_channel.send(content=fix_request_message)

        await message.remove_reaction('📅', client.user)

    db.commit()


def delete_message(client: discord.Client, db: DbSession, message: discord.Message, channel: discord.TextChannel):
    print(f'deleting a message: {message.clean_content}')

    db_msg = crud.get_message_by_original_id(db, message.id)

    if db_msg:
        crud.delete_message_with_calendar_entries(db, db_msg.id)
        db.commit()
