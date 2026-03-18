# Complete Ranking System Test Guide

## What We're Testing

The system now tracks **Best Rank** - the highest position (lowest number) where your domain appears in Google search results.

## Example

**Keyword**: "off market real estate deals"  
**Domain**: "offa.com"

**If Google shows**:
- Position #1: zillow.com
- Position #2: realtor.com
- Position #3: **offa.com** ← Found here!
- Position #4: redfin.com
- Position #5: trulia.com
- Position #6: **offa.com/blog** ← Found again!
- Position #7-10: other sites

**Result**: Best Rank = #3 (the highest/best position)

## Step-by-Step Test

### 1. Test SerpAPI Connection

```bash
cd backend
python test_real_search.py
```

**What to look for**:
- ✅ "Searching Google via SerpAPI"
- ✅ Shows 10 real search results
- ✅ Identifies if offa.com appears
- ✅ Shows best rank position

**If you see mock data**:
- Check SERP_API_KEY is in backend/.env
- Restart backend

### 2. Start Backend

```bash
cd backend
uvicorn app.main:app --reload
```

**Check terminal for**:
```
✅ SerpAPI initialized with key: d6c81446749d65a6a1c6...
```

### 3. Start Frontend

```bash
npm run dev
```

### 4. Test in Browser

1. **Go to Keywords page** (http://localhost:5173/keywords)

2. **Add a test keyword**:
   - Click "Add Keyword"
   - Keyword: "off market real estate deals"
   - Domain: "offa.com"
   - Search Volume: 8400
   - Difficulty: 45
   - Click "Create Keyword"

3. **Check Ranking**:
   - Click "Check Ranking" button
   - Wait for toast: "Found 10 total results, X contain your domain"
   - Look at "Best Rank" column

4. **View Results**:
   - Click on the rank badge (e.g., "#3")
   - See all 10 search results
   - Your domain results are highlighted

## What You Should See

### Best Rank Column Colors:
- **Green (#1-#3)**: Excellent ranking! Top 3 results
- **Blue (#4-#10)**: Good ranking! First page
- **"Not ranked"**: Domain not in top 10

### Results Dialog:
- All 10 search results listed
- Your domain results have:
  - Green border and background
  - "Your Domain" badge
  - Position number
  - Full URL, title, snippet

## Testing Different Scenarios

### Test 1: Domain Appears Multiple Times
**Keyword**: "python programming"  
**Domain**: "python.org"  
**Expected**: Should appear in top 3, maybe #1 or #2

### Test 2: Domain Doesn't Appear
**Keyword**: "weather forecast"  
**Domain**: "offa.com"  
**Expected**: "Not ranked" (offa.com won't be in weather results)

### Test 3: Your Real Keywords
**Keyword**: "off market real estate deals"  
**Domain**: "offa.com"  
**Expected**: See where offa.com actually ranks on Google

## Troubleshooting

### "Using MOCK data" in terminal
**Problem**: SerpAPI key not loaded  
**Fix**: 
1. Check backend/.env has SERP_API_KEY
2. Restart backend

### "Not ranked" for everything
**Problem**: Domain matching might be too strict  
**Check**: 
- Is domain spelled correctly? (offa.com not www.offa.com)
- Click the rank badge to see all results
- Check if your domain appears with different format

### No results in dialog
**Problem**: Haven't run ranking check yet  
**Fix**: Click "Check Ranking" first

### Backend shows 403 error
**Problem**: SerpAPI issue  
**Check**: 
- API key is correct
- Haven't exceeded 100 searches/month
- Check SerpAPI dashboard

## Expected Output

### Terminal (Backend):
```
✅ SerpAPI initialized with key: d6c81446749d65a6a1c6...
🔍 Searching Google via SerpAPI for: off market real estate deals
✅ Got response from SerpAPI
  #1: https://www.zillow.com/...
  #2: https://www.realtor.com/...
  #3: https://offa.com/...
  ...
✅ Successfully retrieved 10 results from SerpAPI
```

### Browser (Frontend):
```
Keywords Table:
┌─────────────────────────────┬──────────┬─────────┐
│ Keyword                     │ Domain   │ Best Rank│
├─────────────────────────────┼──────────┼─────────┤
│ off market real estate deals│ offa.com │   #3    │ ← Green badge
└─────────────────────────────┴──────────┴─────────┘
```

## Success Criteria

✅ SerpAPI returns real Google results  
✅ System saves all 10 results  
✅ Best rank is calculated correctly  
✅ Rank badge shows correct position  
✅ Clicking badge shows all results  
✅ Your domain results are highlighted  

---

**Ready to test!** Start with `python backend/test_real_search.py`
