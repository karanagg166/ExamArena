#!/bin/bash
set -e

echo "🚀 Starting setup for Exam Arena..."

echo "1. Checking if docker is running..."
docker info >/dev/null 2>&1 || { echo >&2 "Docker is not running. Please start Docker and try again."; exit 1; }

echo "2. Starting services..."
docker compose up -d

echo "3. Waiting for backend to be ready..."
for i in {1..60}; do
    RESPONSE=$(curl --silent http://localhost:8000/health 2>/dev/null)
    if echo "$RESPONSE" | grep -q '"healthy"'; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "❌ Backend never became ready. Check logs with 'docker compose logs backend'."
        exit 1
    fi
    echo "   Waiting... ($i/60)"
    sleep 3
done

echo "4. Generating Prisma Client..."
docker compose exec backend prisma generate --generator pyclient

echo "5. Pushing Database Schema..."
docker compose exec backend prisma db push

echo "6. Seeding Database..."
docker compose exec backend python seed.py

echo "🎉 Setup complete! You can now use the seeded credentials to log in."
echo "--------------------------------------------------------"
echo "Admin:     admin@gmail.com          (Pass: admin123)"
echo "Principal: principal@gmail.com      (Pass: principal123)"
echo "Teacher:   teacher@gmail.com        (Pass: karan166)"
echo "Student:   student@gmail.com        (Pass: student123)"
echo "--------------------------------------------------------"
