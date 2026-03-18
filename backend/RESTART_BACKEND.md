# Restart Backend to Use SerpAPI

## The Issue
Your backend is still using mock data because it was started before the SERP_API_KEY was added to the .env file.

## The Fix
**You need to restart your backend server** to pick up the new environment variable.

## How to Restart

### Step 1: Stop the Current Backend
In the terminal where the backend is running, press:
```
Ctrl + C
```

### Step 2: Start the Backend Again
```bash
cd backend
uvicorn app.main:app --reload
```

### Step 3: Verify It's Working
You should see this in the terminal when you use the ranking check:
```
✅ SerpAPI initialized with key: d6c81446749d65a6a1c6...
🔍 Searching Google via SerpAPI for: your-keyword
✅ Got response from SerpAPI
✅ Successfully retrieved 10 results from SerpAPI
```

If you see this instead, the API key is NOT loaded:
```
⚠️  No SERP_API_KEY found - using mock data
🎭 Using MOCK data for keyword: your-keyword
```

## Quick Test

After restarting, run this to verify the environment is loaded:
```bash
python backend/check_env.py
```

Should show:
```
✅ SERP_API_KEY: d6c81446749d65a6a1c6a1089817...
🎉 SerpAPI key is loaded correctly!
```

## Alternative: Use --reload Flag

If you started the backend with `--reload` flag, it should auto-reload when you save files, but environment variables require a full restart.

## Still Seeing Mock Data?

1. **Check the .env file location**: Must be at `backend/.env`
2. **Check the API key**: Open `backend/.env` and verify SERP_API_KEY is set
3. **Check working directory**: Make sure you're running uvicorn from the `backend` folder
4. **Check terminal output**: Look for the "✅ SerpAPI initialized" message

## After Restart

1. Go to your frontend
2. Navigate to Keywords page
3. Click "Check Ranking" on any keyword
4. You should now see REAL Google results instead of mock data!

---

**Remember**: Any time you change environment variables in .env, you need to restart the backend!
