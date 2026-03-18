# Quick Setup Guide for Beginners

## Step 1: Install Python Dependencies

Open terminal in the `backend` folder and run:

```bash
pip install -r requirements.txt
```

## Step 2: Create Database in pgAdmin

1. Open pgAdmin 4 (you already have it!)
2. Expand "Servers" → "PostgreSQL"
3. Right-click "Databases" → "Create" → "Database"
4. Name: `seo_monitor`
5. Click "Save"

## Step 3: Configure Environment Variables

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` file with your details:
```
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/seo_monitor
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-change-this-in-production
```

Replace `YOUR_PASSWORD` with your PostgreSQL password.

## Step 4: Create Database Tables

Run this command to create all tables:

```bash
python scripts/init_db.py
```

## Step 5: Start the Backend Server

```bash
uvicorn app.main:app --reload
```

The API will be available at: http://localhost:8000

Visit http://localhost:8000/docs to see all available endpoints!

## Optional: Redis & Background Jobs

For now, you can skip Redis and Celery. They're only needed for:
- Automated daily ranking checks
- Hourly Reddit monitoring

You can trigger these manually through the API instead.

## Testing the API

Once running, try:
1. Go to http://localhost:8000/docs
2. Click on "POST /api/v1/keywords/"
3. Click "Try it out"
4. Enter test data:
```json
{
  "keyword": "best seo tools",
  "domain": "yoursite.com",
  "search_volume": 1000
}
```
5. Click "Execute"

You should see your keyword created!
