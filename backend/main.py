import threading
from pathlib import Path
import os
import sys

import cfg
from migrate import migrate
import utils

if not Path(cfg.DB_PATH).exists():
    with open(cfg.DB_PATH, 'wb') as fp:
        with open(cfg.DB_TEMPLATE_PATH, 'rb') as source:
            utils.copy_file(source, fp)

if not Path(cfg.DB_PATH).exists():
    print("Database file '{}' does not exist!".format(cfg.DB_PATH))
    exit(1)

migrate(cfg.DB_PATH)

for dir in [cfg.SESSIONS_DATA_DIR, cfg.SESSIONS_LOCK_DIR, cfg.RECORDINGS_PATH]:
    try:
        os.mkdir(dir)
    except:
        pass


def run_website():
        import website


def run_discord_bot():
    if cfg.ENABLE_DISCORD_BOT:
        import discord_bot


if __name__ == "__main__":    
    threads = [
        threading.Thread(target=run_website, daemon=True),
        # threading.Thread(target=run_discord_bot, daemon=True)
    ]

    try:
        for t in threads:
            t.start()

        alive_threads_count = len(threads)

        while alive_threads_count > 0:
            for t in threads:
                if t.is_alive():
                    t.join(0.5)
                else:
                    alive_threads_count -= 1

    except KeyboardInterrupt as e:
        sys.exit(e)
