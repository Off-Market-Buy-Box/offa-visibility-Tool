# Frontend-Backend Connection Guide

## What We Created

### Backend Services (src/services/)
- `keywordService.ts` - Manage keywords
- `rankingService.ts` - Check rankings
- `competitorService.ts` - Track competitors
- `redditService.ts` - Monitor Reddit
- `smartTaskService.ts` - Manage tasks

### API Client (src/lib/api.ts)
- Handles all HTTP requests to backend
- Base URL: http://127.0.0.1:8000/api/v1

## How to Test

1. **Make sure backend is running:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start frontend:**
   ```bash
   npm run dev
   ```

3. **Visit test page:**
   http://localhost:5173/test-api

4. **Click buttons to test:**
   - "Get Keywords" - Fetches all keywords
   - "Create Test Keyword" - Creates a sample keyword
   - "Get Competitors" - Fetches competitors
   - "Get Tasks" - Fetches tasks

## How to Use in Your Pages

### Example: Fetch Keywords
```typescript
import { keywordService } from '@/services/keywordService';

// In your component
const fetchKeywords = async () => {
  try {
    const keywords = await keywordService.getAll();
    console.log(keywords);
  } catch (error) {
    console.error('Error:', error);
  }
};
```

### Example: Create Keyword
```typescript
const createKeyword = async () => {
  const newKeyword = await keywordService.create({
    keyword: "seo tools",
    domain: "mysite.com",
    search_volume: 5000
  });
};
```

### Example: Monitor Reddit
```typescript
import { redditService } from '@/services/redditService';

const monitorReddit = async () => {
  const result = await redditService.monitor('SEO', ['ranking', 'keywords']);
  console.log(`Found ${result.mentions_found} mentions`);
};
```

## API Endpoints Available

### Keywords
- GET /keywords/ - List all
- POST /keywords/ - Create new
- GET /keywords/{id} - Get one

### Rankings
- POST /rankings/check/{keyword_id} - Check ranking

### Competitors
- GET /competitors/ - List all
- POST /competitors/ - Add new

### Reddit
- POST /reddit/monitor - Monitor subreddit
- GET /reddit/mentions - Get mentions

### Smart Tasks
- GET /smart-tasks/ - List all
- POST /smart-tasks/ - Create new
- PATCH /smart-tasks/{id} - Update
