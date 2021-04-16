import threading
from pathlib import Path
import os

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
    # import discord_bot
    pass


if __name__ == "__main__":
    threads = [
        threading.Thread(target=run_website, daemon=True),
        # threading.Thread(target=run_discord_bot, daemon=True)
    ]
    for t in threads:
        t.start()

    for t in threads:
        try:
            t.join()
        except:
            pass
