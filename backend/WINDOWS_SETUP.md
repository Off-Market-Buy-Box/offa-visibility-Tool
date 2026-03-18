# Windows Setup Guide

## Prerequisites Check

You already have:
- ✅ pgAdmin 4 (PostgreSQL)

You need:
- Python 3.10+ ([Download](https://www.python.org/downloads/))

## Quick Start (5 minutes)

### 1. Create Database
In pgAdmin:
- Right-click "Databases" → "Create" → "Database"
- Name: `seo_monitor`
- Save

### 2. Find Your PostgreSQL Password
If you forgot your password:
- Open pgAdmin
- When it asks for password, that's your PostgreSQL password
- Write it down!

### 3. Install Python Packages
Open PowerShell in the `backend` folder:

```powershell
pip install fastapi uvicorn sqlalchemy asyncpg pydantic-settings python-dotenv httpx beautifulsoup4 lxml
```

### 4. Create .env File
Create a file named `.env` in the `backend` folder:

```
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD_HERE@localhost:5432/seo_monitor
SECRET_KEY=my-secret-key-12345
REDIS_URL=redis://localhost:6379/0
```

Replace `YOUR_PASSWORD_HERE` with your actual PostgreSQL password.

### 5. Initialize Database

```powershell
python scripts/init_db.py
```

### 6. Start Server

```powershell
uvicorn app.main:app --reload
```

### 7. Test It!
Open browser: http://localhost:8000/docs

You should see the API documentation!

## Common Issues

**Error: "asyncpg" not found**
```powershell
pip install asyncpg
```

**Error: "Can't connect to database"**
- Check your password in `.env`
- Make sure PostgreSQL is running (check pgAdmin)
- Verify database name is `seo_monitor`

**Error: "Port 8000 already in use"**
```powershell
uvicorn app.main:app --reload --port 8001
```
