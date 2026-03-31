#!/bin/bash
# Offa Flow — one-command start for Mac Mini
set -e

echo "🚀 Starting Offa Flow..."

# 1. Start database and redis via Docker
echo "📦 Starting PostgreSQL and Redis..."
docker compose up -d

# 2. Wait for PostgreSQL to accept connections from host
echo "⏳ Waiting for PostgreSQL on localhost:5432..."
for i in $(seq 1 30); do
    # Use docker exec to check inside the container, then verify port is reachable from host
    if docker compose exec -T db pg_isready -U offa -d seo_monitor > /dev/null 2>&1; then
        # Also verify the port is reachable from the host
        if nc -z localhost 5432 2>/dev/null || (echo > /dev/tcp/localhost/5432) 2>/dev/null; then
            echo "✅ PostgreSQL is ready"
            break
        fi
    fi
    if [ "$i" -eq 30 ]; then
        echo "❌ PostgreSQL not reachable on localhost:5432 after 30s"
        echo "Trying to connect directly..."
        docker compose exec -T db psql -U offa -d seo_monitor -c "SELECT 1" 2>&1 || true
        echo ""
        echo "Check if port 5432 is in use by another process:"
        lsof -i :5432 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# 3. Ensure backend/.env has the correct DATABASE_URL for Docker
if [ -f backend/.env ]; then
    if ! grep -q "offa:offa_secret@localhost:5432" backend/.env 2>/dev/null; then
        echo "⚠️  Fixing DATABASE_URL in backend/.env to use Docker PostgreSQL..."
        sed -i '' 's|^DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://offa:offa_secret@localhost:5432/seo_monitor|' backend/.env
    fi
else
    cat > backend/.env << 'EOF'
DATABASE_URL=postgresql+asyncpg://offa:offa_secret@localhost:5432/seo_monitor
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production
SERP_API_KEY=
OPENAI_API_KEY=
EOF
    echo "📝 Created backend/.env"
fi

echo "🔗 $(grep DATABASE_URL backend/.env)"

# 4. Activate venv
source backend/venv/bin/activate

# 5. Quick DB connection test from Python
echo "🔗 Testing DB connection..."
cd backend
python3 -c "
import asyncio, asyncpg
async def test():
    conn = await asyncpg.connect('postgresql://offa:offa_secret@localhost:5432/seo_monitor')
    print('✅ DB connection works')
    await conn.close()
asyncio.run(test())
" || { echo "❌ Cannot connect to DB from Python. Check Docker port mapping."; exit 1; }

# 6. Start backend (run from backend/ dir so pydantic-settings finds .env)
echo "🔧 Starting backend..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# 7. Wait for backend
echo "⏳ Waiting for backend..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "❌ Backend failed to start"
        exit 1
    fi
    sleep 1
done

# 8. Serve frontend
echo "🌐 Starting frontend..."
npx serve -s dist -l 3000 &
FRONTEND_PID=$!

echo ""
echo "✅ Offa Flow is running!"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
