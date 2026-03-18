# Quick Start Guide - Ranking Check Feature

## ✅ Setup Complete!

Your SEO monitoring tool is now configured with **SerpAPI** for real Google search results.

## What's Working

1. ✅ Backend API with PostgreSQL database
2. ✅ Keyword tracking system
3. ✅ Ranking check functionality
4. ✅ SerpAPI integration (100 free searches/month)
5. ✅ Automatic fallback to mock data
6. ✅ Frontend connected to backend

## Test It Now

### 1. Start the Backend (if not running)
```bash
cd backend
uvicorn app.main:app --reload
```

Backend will run at: http://127.0.0.1:8000

### 2. Test SerpAPI Integration
```bash
python backend/test_serpapi.py
```

This will search for "off market real estate deals" and show real Google results.

### 3. Use the Frontend
1. Open your frontend (usually http://localhost:5173)
2. Go to "Keywords" page
3. Add a keyword (e.g., "off market real estate deals")
4. Click "Check Ranking" button
5. See real Google search results!

## How It Works

```
User clicks "Check Ranking"
    ↓
Frontend calls: POST /api/v1/rankings/check/{keyword_id}
    ↓
Backend uses GoogleScraper
    ↓
SerpAPI returns real Google results
    ↓
Backend saves ranking to database
    ↓
Frontend displays results
```

## API Limits

**Free Tier (Current)**:
- 100 searches per month
- Perfect for testing and development
- Resets monthly

**Paid Plans** (if needed later):
- $50/month: 5,000 searches
- $125/month: 15,000 searches

## Files Changed

1. `backend/app/services/scraper.py` - Updated to use SerpAPI
2. `backend/.env` - Added SERP_API_KEY
3. `backend/test_serpapi.py` - New test script
4. Documentation files added

## Troubleshooting

### Backend shows "Using MOCK data"
- Check that `SERP_API_KEY` is set in `backend/.env`
- Restart the backend after adding the key

### "Backend Offline" in frontend
- Make sure backend is running: `uvicorn app.main:app --reload`
- Check backend is at http://127.0.0.1:8000
- Verify PostgreSQL is running on port 5433

### No results returned
- Check SerpAPI dashboard for remaining searches
- Verify API key is correct
- System will automatically use mock data if API fails

## Next Steps

1. **Test the ranking check** with real keywords
2. **Add your target keywords** to track
3. **Monitor your rankings** over time
4. **Check competitor positions** in search results

## Support

- SerpAPI Dashboard: https://serpapi.com/dashboard
- SerpAPI Docs: https://serpapi.com/search-api
- Your API Key: Check `backend/.env`

---

**Ready to track your rankings!** 🚀
