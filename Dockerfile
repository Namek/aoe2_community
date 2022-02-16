FROM alpine:latest AS build-frontend

ADD https://github.com/mint-lang/mint/releases/download/0.15.2/mint-0.15.2-linux /bin/mint
RUN chmod +x /bin/mint

WORKDIR /app
COPY frontend/mint.json .
COPY frontend/assets/ ./assets
COPY frontend/tests/ ./tests
COPY frontend/source/ ./source
COPY frontend/.env ./.env
RUN mint build --env .env --skip-service-worker

FROM python:3.8-slim AS server
WORKDIR /app/backend
COPY backend/.env ./.env
COPY backend/requirements.txt .
COPY backend/mgz ./mgz
RUN pip install -r requirements.txt --no-cache-dir
COPY --from=build-frontend /app/dist ../frontend/dist/
COPY backend/database/app.template.db ./database/app.template.db
# RUN false | cp -i ./database/app.template.db ./database/app.db
COPY backend/*.py ./
COPY backend/src/*.py ./src/
COPY backend/src/discord_bot/*.py ./src/discord_bot/

EXPOSE 8080
STOPSIGNAL SIGTERM
WORKDIR "/app/backend"
ENTRYPOINT [ "python3", "-m", "main.py" ]
