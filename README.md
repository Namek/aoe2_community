Website for sharing AoE2 DE recordings of matches. Currently adjusted for the [AoEII ANThology: Ant League 2021 Summer Edition](https://play.toornament.com/pl/tournaments/4777579001523625984/).

## Development

### Backend

0. `cd backend`

#### Setup

1. `python -m venv .`
2. `./Scripts/activate`
3. `python -m pip install -r ./requirements.txt`
4. `cp ./.env.template ./.env`
5. edit `.env`: `CORS_ALLOW_ORIGIN=http://127.0.0.1:3000`

#### Develop

1. `./Scripts/activate`
2. `uvicorn src.website:app --reload --port 8080` OR `python -m main.py`

#### Tests

`python -m pytest tests/`


### Frontend

0. `cd frontend`

#### Setup

1. [install Mint](https://www.mint-lang.com/install)
2. `cp ./.env.development.template ./.env` and ajdust the file

#### Develop

1. `mint start --auto-format --env .env`


## Deploy

1. `git submodule update --init`
2. `cp ./frontend/.env.production.template ./frontend/.env` and adjust
3. `cp ./backend/.env.template ./backend/.env` and adjust
4. `docker-compose up --build -d`

