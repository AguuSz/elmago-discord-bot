#!/bin/bash
# deploy.sh

IMAGEN="elmago-bot:v2"
CONTAINER="elmago-bot"
ENV_FILE="/home/agus/dockers/elmago-discord-bot/.env"

echo "🛑 Deteniendo container anterior..."
docker stop $CONTAINER 2>/dev/null
docker rm $CONTAINER 2>/dev/null

echo "🏗️  Rebuildeando imagen..."
docker build -t $IMAGEN .

echo "🚀 Iniciando nuevo container..."
docker run -d --env-file $ENV_FILE --name $CONTAINER --restart unless-stopped $IMAGEN

