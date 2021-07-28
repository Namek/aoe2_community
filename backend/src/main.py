from pathlib import Path
import os
import sys
import time
import threading

import uvicorn

from . import cfg, migration, utils

if not Path(cfg.DB_PATH).exists():
    with open(cfg.DB_PATH, 'wb') as fp:
        with open(cfg.DB_TEMPLATE_PATH, 'rb') as source:
            utils.copy_file(source, fp)

if not Path(cfg.DB_PATH).exists():
    print("Database file '{}' does not exist!".format(cfg.DB_PATH))
    exit(1)

migration.migrate(cfg.DB_PATH)

for dir in [cfg.RECORDINGS_PATH]:
    try:
        os.mkdir(dir)
    except:
        pass


class Server(uvicorn.Server):
    def install_signal_handlers(self):
        pass


def run_website():
    from .website import app as webapp

    config = uvicorn.Config(webapp, host='0.0.0.0', port=8080)
    server = Server(config=config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return thread


def run_discord_bot():
    def launch():
        if cfg.ENABLE_DISCORD_BOT:
            from . import discord_bot

    thread = threading.Thread(target=launch, daemon=True)
    thread.start()
    return thread


def run():
    threads = [
        run_website(),
        run_discord_bot()
    ]

    try:
        any_alive = True
        while any_alive:
            any_alive = False
            for t in [t for t in threads if t.is_alive]:
                if t.is_alive():
                    any_alive = True
                    t.join(0.5)
    except KeyboardInterrupt as e:
        sys.exit(e)
