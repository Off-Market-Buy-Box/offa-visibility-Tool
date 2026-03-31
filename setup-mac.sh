#!/bin/bash
# One-time setup for Mac Mini
# Run this once after copying the project
set -e

echo "🍎 Offa Flow — Mac Mini Setup"
echo ""

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Install Docker Desktop first: https://docker.com/products/docker-desktop"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 not found. Install: brew install python@3.11"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js not found. Install: brew install node"; exit 1; }

echo "✅ Prerequisites found"

# Start DB
echo "📦 Starting PostgreSQL and Redis..."
docker compose up -d
sleep 3

# Python setup
echo "🐍 Creating Python virtual environment..."
python3 -m venv backend/venv
source backend/venv/bin/activate
echo "📦 Installing Python dependencies..."
pip install -q -r backend/requirements.txt
echo "🎭 Installing Playwright browser..."
playwright install chromium

# Create .env
if [ ! -f backend/.env ]; then
    cat > backend/.env << 'EOF'
DATABASE_URL=postgresql+asyncpg://offa:offa_secret@localhost:5432/seo_monitor
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production
SERP_API_KEY=
OPENAI_API_KEY=
EOF
    echo "📝 Created backend/.env"
fi

# Node setup
echo "🎨 Installing frontend dependencies..."
npm ci

# Build frontend
echo "🔨 Building frontend..."
npm run build

# Install serve globally for static hosting
npm install -g serve

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env and add your SERP_API_KEY and OPENAI_API_KEY"
echo "  2. Run: ./start.sh"
echo "  3. Open http://localhost:3000"
echo "  4. Go to Profile to login to social media accounts"
