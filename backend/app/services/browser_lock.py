import asyncio

# Global lock — only one browser operation at a time
# Prevents outreach posting and automation commenting from fighting over the browser
reddit_browser_lock = asyncio.Lock()
