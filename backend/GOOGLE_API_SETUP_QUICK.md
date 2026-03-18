# Quick Setup - You Already Have a Google Cloud Project!

You already have a Google Cloud project: `valued-aquifer-490021-t4`

## Step 1: Enable Custom Search API (2 minutes)

1. Go to: https://console.cloud.google.com/apis/library/customsearch.googleapis.com?project=valued-aquifer-490021-t4
2. Click "ENABLE"

## Step 2: Create API Key (1 minute)

1. Go to: https://console.cloud.google.com/apis/credentials?project=valued-aquifer-490021-t4
2. Click "CREATE CREDENTIALS" → "API key"
3. Copy the API key (looks like: `AIzaSyD...`)

## Step 3: Create Custom Search Engine (2 minutes)

1. Go to: https://programmablesearchengine.google.com/
2. Click "Add" or "Get Started"
3. Settings:
   - **Sites to search**: Leave empty or add `*`
   - **Name**: "Offa SEO Monitor"
   - **Search the entire web**: Toggle ON
4. Click "Create"
5. Copy your **Search Engine ID** (looks like: `a1b2c3d4e5f6g7h8i`)

## Step 4: Add to .env

Edit `backend/.env` and add these two lines:

```env
GOOGLE_API_KEY=AIzaSyD...your-key-here
GOOGLE_CSE_ID=a1b2c3d4e5f6g7h8i...your-id-here
```

## Step 5: Test

Restart backend and click "Check Ranking" - you'll see real Google results!

## Free Tier

- 100 searches/day free
- Perfect for testing and development
