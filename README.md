Website for sharing AoE2 DE recordings of matches. Currently adjusted for the [AoEII ANThology: Ant League 2022 Spring Edition](https://play.toornament.com/pl/tournaments/5304504147050160128/).

## Development

Tech stack:
* Python 3.9
* [Mint](https://mint-lang.com) 15.2

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


## Deploy

1. `git submodule update --init`
2. `cp ./frontend/.env.production.template ./frontend/.env` and adjust
3. `cp ./backend/.env.template ./backend/.env` and adjust
4. `docker-compose up --build -d`

