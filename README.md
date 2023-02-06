## 1. What?

1. Website for sharing AoE2 DE recordings of matches.
2. Discord Bot gathering events from chat and putting those on the website.

Both currently adjusted for the [AoEII ANThology: Ant League 2023 Winter Edition](https://play.toornament.com/pl/tournaments/6434801951906512896/).

![Matches](/docs/matches.png "Matches uploaded by the players")

![Calendar](/docs/calendar.png "Calendar of the league based on Discord messages")


## 2. Development

Tech stack:
* website backend: Python 3.9
* website frontend: [Mint](https://mint-lang.com) 16.0
* Discord bot: .NET 6.0

### 2.1. Backend

0. `cd backend`

#### Setup

1. `python -m venv .`
2. `./Scripts/activate` (Windows) OR `./bin/activate` (Mac/Linux)
3. `python -m pip install -r ./requirements.txt`
4. `cp ./.env.template ./.env`
5. edit `.env`: `CORS_ALLOW_ORIGIN=*`

#### Develop the backend

1. `./Scripts/activate` (Windows) OR `./bin/activate` (Mac/Linux)

2. Run the backend WITH the database migrations:
`python -m main.py`

3. Run the backend and get the auto-restart experience when backend files are modified:
    `python uvicorn src.website:app --reload --port 8080`

    Note: this does not migrate the database (see `migration.py`)!

Either way will serve the frontend files from the `frontend/dist` if you open http://localhost:8080.

#### Backend tests

There are just a few tests. Previously the tricky parts were part of this section but now they are moved to the separate Dicsord `bot` process.
- `python -m pytest tests/`


### 2.2. Frontend

0. `cd frontend`

#### Setup

1. [install Mint](https://www.mint-lang.com/install)
2. `cp ./.env.development.template ./.env` and adjust the file

#### Develop

1. `mint start --auto-format --env .env`


### 2.3. Discord Bot

0. `cd bot`

#### Setup

1. `dotnet restore`
2. prepare the `bot/Bot/.env` file based on the `bot/Bot/.env.template`


#### Develop

Run the bot with:
1. `dotnet run`


## 3. Deploy

### 3.1. Run the whole thing on your server

We can avoid all of the development instructions when only the production deployment is needed. For this, just configure few .env files and use docker to start all components:

1. `git submodule update --init --recursive`
2. `cp ./frontend/.env.production.template ./frontend/.env` and adjust
3. `cp ./backend/.env.template ./backend/.env` and adjust
4. `cp ./bot/Bot/.env.template ./bot/Bot/.env` and adjust
5. `docker-compose up --build -d`

### 3.2. Update the deployed build

1. `git pull origin master && git submodule update --recursive`
2. `docker-compose down && docker-compose up --build -d`
