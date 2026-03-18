# Simplified Keywords - Only Real Data

## What Changed

Removed search volume and difficulty fields. Now we only track:
- **Keyword**: What you're searching for
- **Domain**: Your website (e.g., offa.com)
- **Best Rank**: Actual position from Google (via SerpAPI)

## Why?

Search volume and difficulty require separate APIs and aren't real-time data. We focus on what matters: **where does your domain actually rank on Google right now?**

## New Keyword Form

**Before** (5 fields):
- Keyword
- Domain
- Search Volume ❌ (removed)
- Difficulty ❌ (removed)
- Status

**After** (2 fields):
- Keyword
- Domain

That's it! Everything else comes from real Google searches.

## Keywords Table

**Columns**:
1. **Keyword** - What you're tracking
2. **Domain** - Your website
3. **Status** - Active/Inactive
4. **Created** - When you added it
5. **Actions** - "Check Ranking" button
6. **Best Rank** - Real position from Google

## Stats Cards

**Before** (3 cards):
- Total Keywords
- Active Keywords
- Avg. Search Volume ❌ (removed)

**After** (2 cards):
- Total Keywords
- Active Keywords

## How to Update

### 1. Update Database (Optional)

If you have existing keywords with search_volume/difficulty data:

```bash
cd backend
python scripts/remove_unused_columns.py
```

This removes the unused columns from the database.

### 2. Restart Backend

```bash
cd backend
uvicorn app.main:app --reload
```

### 3. Test It

1. Go to Keywords page
2. Click "Add Keyword"
3. Enter only:
   - Keyword: "off market real estate deals"
   - Domain: "offa.com"
4. Click "Create Keyword"
5. Click "Check Ranking"
6. See real rank from Google!

## What You Get

✅ Simple 2-field form  
✅ Only real data from SerpAPI  
✅ Actual Google rankings  
✅ No manual data entry  
✅ Focus on what matters  

## Example Workflow

1. **Add keyword**: "off market real estate deals" + "offa.com"
2. **Click "Check Ranking"**: System searches Google via SerpAPI
3. **See result**: "#3" (offa.com is at position 3)
4. **Click rank badge**: See all 10 search results
5. **Track over time**: Check again later to see if rank improved

---

**Clean, simple, real data only!**
