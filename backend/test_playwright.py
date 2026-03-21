"""
Quick test to see if Playwright works on this machine.
Run from backend folder: python test_playwright.py
"""
import traceback

print("=" * 60)
print("TEST 1: Import playwright sync_api")
print("=" * 60)
try:
    from playwright.sync_api import sync_playwright
    print("✅ Import OK")
except Exception as e:
    print(f"❌ Import failed: {e}")
    traceback.print_exc()
    exit(1)

print()
print("=" * 60)
print("TEST 2: Launch Chromium (sync)")
print("=" * 60)
try:
    with sync_playwright() as pw:
        print("  Starting Chromium...")
        browser = pw.chromium.launch(headless=True)
        print("  ✅ Browser launched")
        page = browser.new_page()
        page.goto("https://example.com")
        title = page.title()
        print(f"  ✅ Page loaded, title: {title}")
        browser.close()
        print("  ✅ Browser closed")
    print("✅ Sync Playwright works!")
except Exception as e:
    print(f"❌ Sync test failed: {e}")
    traceback.print_exc()

print()
print("=" * 60)
print("TEST 3: Launch Chromium (async)")
print("=" * 60)
try:
    import asyncio
    from playwright.async_api import async_playwright

    async def test_async():
        async with async_playwright() as pw:
            print("  Starting Chromium (async)...")
            browser = await pw.chromium.launch(headless=True)
            print("  ✅ Browser launched")
            page = await browser.new_page()
            await page.goto("https://example.com")
            title = await page.title()
            print(f"  ✅ Page loaded, title: {title}")
            await browser.close()
            print("  ✅ Browser closed")
        print("✅ Async Playwright works!")

    asyncio.run(test_async())
except Exception as e:
    print(f"❌ Async test failed: {e}")
    traceback.print_exc()

print()
print("=" * 60)
print("TEST 4: Sync in thread (like our poster does)")
print("=" * 60)
try:
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    def sync_in_thread():
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://example.com")
            title = page.title()
            browser.close()
            return title

    async def test_thread():
        loop = asyncio.get_event_loop()
        title = await loop.run_in_executor(None, sync_in_thread)
        print(f"  ✅ Got title from thread: {title}")

    asyncio.run(test_thread())
    print("✅ Thread approach works!")
except Exception as e:
    print(f"❌ Thread test failed: {e}")
    traceback.print_exc()

print()
print("=" * 60)
print("TEST 5: Subprocess approach")
print("=" * 60)
try:
    import subprocess
    import sys
    
    script = '''
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    print(page.title())
    browser.close()
'''
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        print(f"  ✅ Subprocess output: {result.stdout.strip()}")
        print("✅ Subprocess approach works!")
    else:
        print(f"  ❌ Subprocess stderr: {result.stderr}")
except Exception as e:
    print(f"❌ Subprocess test failed: {e}")
    traceback.print_exc()

print()
print("Done! Check which tests passed above.")
