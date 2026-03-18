# Enable Google Custom Search JSON API

## Current Error
```
"This project does not have the access to Custom Search JSON API."
```

## Solution: Enable the API

### Step 1: Go to API Library
Visit this direct link (already has your project selected):
https://console.cloud.google.com/apis/library/customsearch.googleapis.com?project=valued-aquifer-490021-t4

### Step 2: Enable the API
1. You should see "Custom Search API" page
2. Click the blue "ENABLE" button
3. Wait 30-60 seconds for it to activate

### Step 3: Verify API is Enabled
Visit: https://console.cloud.google.com/apis/dashboard?project=valued-aquifer-490021-t4

You should see "Custom Search API" in the list of enabled APIs.

### Step 4: Test Again
Run the test script:
```bash
python backend/test_scraper.py
```

## Alternative: Check if Already Enabled

If you think it's already enabled, verify:
1. Go to: https://console.cloud.google.com/apis/api/customsearch.googleapis.com?project=valued-aquifer-490021-t4
2. Check if it says "API Enabled" at the top
3. If not, click "Enable"

## API Key Restrictions

If the API is enabled but still getting 403, check API key restrictions:
1. Go to: https://console.cloud.google.com/apis/credentials?project=valued-aquifer-490021-t4
2. Click on your API key: `AIzaSyCvlX3aarYDxavEBzbQLIX3iHEpPWiCMZI`
3. Under "API restrictions":
   - Either select "Don't restrict key" (for testing)
   - OR select "Restrict key" and add "Custom Search API" to the allowed list

## Current Configuration
- Project ID: `valued-aquifer-490021-t4`
- API Key: `AIzaSyCvlX3aarYDxavEBzbQLIX3iHEpPWiCMZI`
- Search Engine ID: `c67db2c89a96a4bf7`

## What Happens After Enabling?

Once enabled, your scraper will:
- ✅ Make real Google searches
- ✅ Return actual search results
- ✅ Show real rankings for your keywords
- ✅ Track competitor positions

The mock data fallback will only be used if the API fails.
