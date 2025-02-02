from pathlib import Path
import os
import sys
import threading

import uvicorn

from . import cfg, migration, utils
from .recordings import retry_recordings_parsing

print(f'current dir: {os.getcwd()}')

if not Path(cfg.DB_PATH).exists():
    print(f'Database file {cfg.DB_PATH} to be copied from {cfg.DB_TEMPLATE_PATH}...')
    with open(cfg.DB_PATH, 'wb') as fp:
        with open(cfg.DB_TEMPLATE_PATH, 'rb') as source:
            utils.copy_file(source, fp)
    print('Database copied.')

if not Path(cfg.DB_PATH).exists():
    print("Database file '{}' does not exist!".format(cfg.DB_PATH))
    exit(1)

migration.migrate(cfg.DB_PATH)
retry_recordings_parsing()

for dir in [cfg.RECORDINGS_PATH]:
    try:
        os.mkdir(dir)
    except:
        pass


class Server(uvicorn.Server):
    def install_signal_handlers(self):
        pass


def run_website():
    def launch():
        if cfg.ENABLE_WEBSITE:
            from .website import app as webapp

            config = uvicorn.Config(webapp, host='0.0.0.0', port=8080)
            server = Server(config=config)
            server.run()

    thread = threading.Thread(target=launch, daemon=True)
    thread.start()
    return thread


def run():
    threads = [
        run_website(),
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
