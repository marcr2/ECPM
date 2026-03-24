#!/bin/bash
# Start ECPM services with Docker Compose

echo "Starting TimescaleDB, Redis, and backend services..."
docker-compose up -d timescaledb redis backend

echo "Waiting for TimescaleDB to be ready..."
sleep 5

echo "Running database migrations..."
docker-compose exec backend alembic upgrade head

echo "Services started! Check status with: docker-compose ps"
echo "View logs with: docker-compose logs -f backend"
