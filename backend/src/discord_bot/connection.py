import asyncio
import logging

import discord

from .. import cfg
from ..database import get_db
from . import calendar

if not cfg.DISCORD_BOT_TOKEN or not cfg.DISCORD_SERVER_ID:
    print("no Discord configuration (token, guild id)")
    exit(1)

asyncio.set_event_loop(asyncio.new_event_loop())
client = discord.Client()


@client.event
async def on_ready():
    server = discord.utils.find(lambda s: s.id == cfg.DISCORD_SERVER_ID, client.guilds)
    if not server:
        print(f'Guild `{cfg.DISCORD_SERVER_ID}` not found')
        return

    channels = [discord.utils.get(client.get_all_channels(), guild__id=cfg.DISCORD_SERVER_ID, name=name)
                for name in cfg.DISCORD_SERVER_CHANNEL_NAMES]
    channels = list(filter(None, channels))
    guilds_str = '\n'.join([f' - {g.name}' for g in client.guilds])
    print(f'User {client.user} is connected to the following guilds:\n{guilds_str}')
    print(f'...but using only the \'{server.name}\' (id: {server.id})')
    channels_str = '\n'.join(f' - {ch.name}' for ch in channels)
    print(f'Channels:\n{channels_str}\n')

    for channel in channels:
        async for message in channel.history(limit=200):
            with get_db() as db:
                await calendar.process_message(client, db, message, message.channel)


@client.event
async def on_message(message: discord.Message):
    channel = message.channel
    if channel.type == discord.ChannelType.text and channel.name in cfg.DISCORD_SERVER_CHANNEL_NAMES:
        with get_db() as db:
            await calendar.process_message(client, db, message, channel)


@client.event
async def on_message_edit(before, after):
    channel = after.channel

    if after.channel.type == discord.ChannelType.text and channel.name in cfg.DISCORD_SERVER_CHANNEL_NAMES:
        with get_db() as db:
            await calendar.process_message(client, db, after, channel)


@client.event
async def on_message_delete(message):
    channel = message.channel

    if channel.type == discord.ChannelType.text and channel.name in cfg.DISCORD_SERVER_CHANNEL_NAMES:
        with get_db() as db:
            calendar.delete_message(client, db, message, channel)


async def start_server():
    print('Set up Discord logger')
    logger = logging.getLogger('discord')
    logger.setLevel(logging.WARNING)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    try:
        print('Starting bot')
        await client.start(cfg.DISCORD_BOT_TOKEN)
    finally:
        if not client.is_closed():
            await client.close()
