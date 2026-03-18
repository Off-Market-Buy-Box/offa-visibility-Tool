# Visibility Feature Explained

## What is "Visibility"?

Visibility shows **how many times your domain appears** in the Google search results for a specific keyword.

## Example

If you search for "off market real estate deals" and your domain `offa.com` appears in:
- Position 3
- Position 7
- Position 12

Then your **visibility count = 3** (your domain appears 3 times in the results)

## How It Works

### 1. When You Click "Check Ranking"
- Backend searches Google for the keyword (e.g., "off market real estate deals")
- Gets back 10 search results
- Checks each result to see if your domain appears in the URL
- Saves each occurrence to the database

### 2. Visibility Count
- Counts how many times your domain was found in the search results
- Shows this number in the "Visibility" column
- Badge colors:
  - **Blue badge**: Domain found (1+ results)
  - **Gray badge**: Domain not found (0 results)
  - **"Not checked"**: Never ran a ranking check

## What You'll See

### In the Keywords Table:

| Keyword | Domain | Visibility |
|---------|--------|------------|
| off market real estate deals | offa.com | **3 results** |
| real estate investing | offa.com | **1 result** |
| property deals | offa.com | **0 results** |
| new keyword | offa.com | Not checked |

## Why This Matters

- **Higher visibility = Better SEO**: More appearances means better brand presence
- **Track improvements**: See if your SEO efforts increase visibility over time
- **Compare keywords**: See which keywords give you the most visibility
- **Identify opportunities**: Keywords with 0 visibility need more SEO work

## Technical Details

### Backend (`/api/v1/rankings/check/{keyword_id}`):
1. Searches Google via SerpAPI
2. Filters results where your domain appears
3. Saves each matching result to the `rankings` table
4. Returns count of total results found

### Frontend (Keywords Page):
- Displays the visibility count from the latest check
- Updates automatically after each ranking check
- Shows "Not checked" if never checked before

## Next Steps

1. **Restart your backend** to use real SerpAPI results
2. **Add keywords** you want to track
3. **Click "Check Ranking"** to see visibility
4. **Monitor over time** to track SEO improvements

---

**Remember**: Visibility is about brand presence, not just ranking position. Multiple appearances = stronger brand visibility!
