FROM alpine:latest AS build-frontend

ADD https://github.com/mint-lang/mint/releases/download/0.11.0/mint-0.11.0-linux /bin/mint
RUN chmod +x /bin/mint

WORKDIR /app
COPY frontend/mint.json .
COPY frontend/assets/ ./assets
COPY frontend/tests/ ./tests
COPY frontend/source/ ./source
COPY frontend/.env.production.template ./.env
RUN mint build --env .env --skip-service-worker

FROM python:3.8-slim AS server
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY --from=build-frontend /app/dist ./static
COPY backend/database/app.db ./database/
COPY backend/main.py .

EXPOSE 8080
STOPSIGNAL SIGTERM
ENTRYPOINT [ "python3", "/app/main.py" ]
