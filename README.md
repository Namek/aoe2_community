## What?

1. Website for sharing AoE2 DE recordings of matches.
2. Discord Bot gathering events from chat and putting those on the website.

Both currently adjusted for the [AoEII ANThology: Ant League 2022 Spring Edition](https://play.toornament.com/pl/tournaments/5304504147050160128/).

## Development

Tech stack:
* website backend: Python 3.9
* website frontend: [Mint](https://mint-lang.com) 15.2
* Discord bot: .NET 6.0

### Backend

0. `cd backend`

#### Setup

1. `python3 -m venv .`
2. `./Scripts/activate`
3. `python3 -m pip install -r ./requirements.txt`
4. `cp ./.env.template ./.env`
5. edit `.env`: `CORS_ALLOW_ORIGIN=http://127.0.0.1:3000`

#### Develop

1. `./Scripts/activate` (Windows) OR `./bin/activate` (Mac/Linux)

2.a) To run the website only and get the auto-restart experience when backend files are modified:
`uvicorn src.website:app --reload --port 8080`

2.b) To run database migrations (and the Discord bot):
`python3 -m main.py`


#### Tests

`python3 -m pytest tests/`


### Frontend

0. `cd frontend`

#### Setup

1. [install Mint](https://www.mint-lang.com/install)
2. `cp ./.env.development.template ./.env` and adjust the file

#### Develop

1. `mint start --auto-format --env .env`


### Discord Bot

#### Setup

TODO

#### Develop

TODO


## Deploy

1. `git submodule update --init`
2. `cp ./frontend/.env.production.template ./frontend/.env` and adjust
3. `cp ./backend/.env.template ./backend/.env` and adjust
4. `cp ./bot/Bot/.env.template ./bot/Bot/.env` and adjust
5. `docker-compose up --build -d`

