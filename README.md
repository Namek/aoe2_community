## Development

### Backend

0. `cd backend`

Setup:

1. `python -m venv .`
2. `./Scripts/activate`
3. `python -m pip install -r ./requirements.txt`
4. `cp ./.env.template ./.env`
5. edit `.env`: `CORS_ALLOW_ORIGIN=http://127.0.0.1:3000`

Develop:

1. `./Scripts/activate`
2. `uvicorn src.website:app --reload --port 8080`


### Frontend

0. `cd frontend`

Setup:

1. [install Mint](https://www.mint-lang.com/install)

Develop:

1. `mint start --auto-format`


## Deploy

1. `git submodule update --init`
2. `docker-compose up --build -d`

