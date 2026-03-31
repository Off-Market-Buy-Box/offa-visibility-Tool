#!/bin/bash
# Offa Flow — one-command start for Mac Mini
# Prerequisites: Docker, Python 3.11+, Node.js 18+
set -e

echo "🚀 Starting Offa Flow..."

# 1. Start database and redis via Docker
echo "📦 Starting PostgreSQL and Redis..."
docker compose up -d
sleep 3

# 2. Create .env if missing
if [ ! -f backend/.env ]; then
    cat > backend/.env << 'EOF'
DATABASE_URL=postgresql+asyncpg://offa:offa_secret@localhost:5432/seo_monitor
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production
SERP_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
GOOGLE_CSE_ID=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USERNAME=
REDDIT_PASSWORD=
LINKEDIN_EMAIL=
LINKEDIN_PASSWORD=
TWITTER_EMAIL=
TWITTER_PASSWORD=
FACEBOOK_EMAIL=
FACEBOOK_PASSWORD=
EOF
    echo "📝 Created backend/.env — add your API keys there"
fi

# 3. Setup Python backend
echo "🐍 Setting up backend..."
if [ ! -d backend/venv ]; then
    python3 -m venv backend/venv
fi
source backend/venv/bin/activate
pip install -q -r backend/requirements.txt
playwright install chromium

# 4. Build frontend
echo "🎨 Building frontend..."
if [ ! -d node_modules ]; then
    npm ci
fi
npm run build

# 5. Start backend
echo "🔧 Starting backend..."
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# 6. Serve frontend
echo "🌐 Starting frontend..."
npx serve -s dist -l 3000 &
FRONTEND_PID=$!

echo ""
echo "✅ Offa Flow is running!"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker compose down; exit" INT TERM
wait
