# Google Custom Search API Setup Guide

## Why Use Google Custom Search API?

- ✅ **Official & Legal** - Direct from Google, no scraping violations
- ✅ **Reliable** - No blocking or captchas
- ✅ **100 Free Queries/Day** - Perfect for testing and small projects
- ✅ **Real-Time Data** - Actual Google search results

## Setup Steps (5 minutes)

### Step 1: Get API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable "Custom Search API":
   - Go to "APIs & Services" → "Library"
   - Search for "Custom Search API"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy your API key

### Step 2: Create Custom Search Engine

1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" or "Create"
3. Configure:
   - **Sites to search**: `www.google.com` (or leave empty for entire web)
   - **Name**: "SEO Monitor Search"
   - **Search the entire web**: Toggle ON
4. Click "Create"
5. Copy your **Search Engine ID** (looks like: `a1b2c3d4e5f6g7h8i`)

### Step 3: Add to Backend .env

Edit `backend/.env` and add:

```env
GOOGLE_API_KEY=your-api-key-here
GOOGLE_CSE_ID=your-search-engine-id-here
```

### Step 4: Restart Backend

```bash
# The backend will auto-reload and detect the API keys
# You'll see: "🔍 Searching Google API for: python"
```

## Testing

1. Add a keyword in your app
2. Click "Check Ranking"
3. Check backend logs - you should see:
   ```
   🔍 Searching Google API for: python
   ✅ Got response from Google API
     #1: https://www.python.org...
     #2: https://en.wikipedia.org...
   ✅ Successfully retrieved 10 results from Google API
   ```

## Free Tier Limits

- **100 queries/day** - Free
- **Additional queries** - $5 per 1,000 queries
- **Max 10 results per query**

## Without API Keys

If you don't add API keys, the system automatically uses mock data so you can still test the full application flow.

## Troubleshooting

**"API key not valid"**
- Make sure Custom Search API is enabled in Google Cloud Console
- Check that API key is copied correctly

**"Invalid CSE ID"**
- Verify Search Engine ID from Programmable Search Engine console
- Make sure "Search the entire web" is enabled

**"Quota exceeded"**
- You've used your 100 free queries for today
- Wait until tomorrow or upgrade to paid tier
