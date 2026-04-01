"""
Standalone Playwright script for Facebook login and comment posting.
Runs in a subprocess — no asyncio, pure sync Playwright.
"""
import json
import os
import sys
import traceback

PROFILE_DIR = os.path.join(os.path.expanduser("~"), ".offa_facebook_browser")


def get_profile_dir():
    os.makedirs(PROFILE_DIR, exist_ok=True)
    return PROFILE_DIR


def is_logged_in(page) -> bool:
    try:
        page.wait_for_timeout(1500)
        url = page.url.lower()
        if "/login" in url or "/recover" in url:
            return False
        # Check for logged-in indicators
        for sel in ['[aria-label="Your profile"]', '[aria-label="Account"]', 'div[role="navigation"]']:
            try:
                el = page.locator(sel).first
                if el.count() > 0 and el.is_visible():
                    return True
            except Exception:
                continue
        body = page.inner_text("body")[:2000].lower()
        if "log in" in body and "create new account" in body:
            return False
        if "what\'s on your mind" in body or "write something" in body:
            return True
        return "/login" not in url
    except Exception:
        return False


def wait_for_login(page, timeout_seconds=180):
    import time
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if is_logged_in(page):
            return True
        page.wait_for_timeout(2000)
    return False


def launch_browser(pw):
    return pw.chromium.launch_persistent_context(
        get_profile_dir(),
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )


def do_login_only(pw, email, password):
    """Open browser, go to Facebook login. User logs in manually. Browser stays open until user closes it."""
    print("STEP:launching_browser", flush=True)
    browser = launch_browser(pw)
    page = browser.new_page()
    page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )

    print("STEP:checking_session", flush=True)
    page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    if is_logged_in(page):
        print("STEP:already_logged_in", flush=True)
        print(json.dumps({
            "logged_in": True, "method": "browser",
            "message": "Already logged in to Facebook!"
        }))
        # Keep browser open so user can verify
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass
        browser.close()
        return

    print("STEP:opening_login_page", flush=True)
    page.goto("https://www.facebook.com/login/", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    print("STEP:waiting_for_manual_login", flush=True)
    # Wait up to 10 minutes — user handles verification, captcha, etc.
    success = wait_for_login(page, timeout_seconds=600)

    if success:
        print("STEP:login_successful", flush=True)
        page.wait_for_timeout(2000)
        print(json.dumps({
            "logged_in": True, "method": "browser",
            "message": "Facebook login successful! Session saved."
        }))
    else:
        # Even on timeout, don't close — let user keep trying
        print(json.dumps({
            "logged_in": False, "method": "browser",
            "message": "Login not detected yet. Close the browser when done."
        }))

    # Wait for user to close the browser themselves
    try:
        page.wait_for_event("close", timeout=0)
    except Exception:
        pass
    browser.close()


def do_post_comment(pw, email, password, post_url, text):
    """Navigate to a Facebook post and post a comment."""
    print("STEP:launching_browser", flush=True)
    browser = launch_browser(pw)
    page = browser.new_page()
    page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )

    try:
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        if not is_logged_in(page):
            print("STEP:not_logged_in_attempting_login", flush=True)
            page.goto("https://www.facebook.com/login/", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            try:
                page.locator('#email').first.fill(email)
                page.locator('#pass').first.fill(password)
                page.locator('button[name="login"]').first.click()
                page.wait_for_timeout(3000)
            except Exception:
                pass
            if not wait_for_login(page, timeout_seconds=60):
                print(json.dumps({"error": "Could not log in to Facebook", "posted": False}))
                sys.exit(1)

        print(f"STEP:navigating_to_post", flush=True)
        page.goto(post_url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        print("STEP:looking_for_comment_box", flush=True)
        comment_box = None
        for sel in [
            'div[contenteditable="true"][aria-label*="comment"]',
            'div[contenteditable="true"][aria-label*="Comment"]',
            'div[contenteditable="true"][role="textbox"]',
        ]:
            try:
                el = page.locator(sel).first
                if el.count() > 0 and el.is_visible():
                    comment_box = el
                    break
            except Exception:
                continue

        if not comment_box:
            # Try clicking "Write a comment" to open the box
            try:
                write_comment = page.locator('div:has-text("Write a comment")').first
                if write_comment.count() > 0:
                    write_comment.click()
                    page.wait_for_timeout(1500)
                    for sel in ['div[contenteditable="true"][role="textbox"]']:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible():
                            comment_box = el
                            break
            except Exception:
                pass

        if not comment_box:
            print(json.dumps({"error": "Could not find comment box", "posted": False}))
            sys.exit(1)

        print("STEP:typing_comment", flush=True)
        comment_box.click()
        page.wait_for_timeout(500)
        comment_box.type(text, delay=30)
        page.wait_for_timeout(1000)

        print("STEP:submitting_comment", flush=True)
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)

        print(json.dumps({
            "posted": True,
            "comment_url": page.url,
            "message": "Comment posted on Facebook",
        }))

    finally:
        page.close()
        browser.close()


def do_batch_post(pw, email, password, posts, delay_seconds=30):
    """Post comments to multiple Facebook posts in one browser session."""
    import time
    print("STEP:launching_browser", flush=True)
    browser = launch_browser(pw)
    page = browser.new_page()
    page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )
    results = []

    try:
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        if not is_logged_in(page):
            print("STEP:logging_in", flush=True)
            page.goto("https://www.facebook.com/login/", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            try:
                page.locator('#email').first.fill(email)
                page.locator('#pass').first.fill(password)
                page.locator('button[name="login"]').first.click()
                page.wait_for_timeout(3000)
            except Exception:
                pass
            if not wait_for_login(page, timeout_seconds=60):
                for p in posts:
                    results.append({"id": p["id"], "posted": False, "error": "Login failed"})
                print(json.dumps({"batch_results": results}))
                return

        for i, post in enumerate(posts):
            post_id = post["id"]
            post_url = post["post_url"]
            text = post["text"]
            try:
                print(f"STEP:posting_{i+1}_of_{len(posts)}", flush=True)
                page.goto(post_url, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)

                comment_box = None
                for sel in [
                    'div[contenteditable="true"][aria-label*="comment"]',
                    'div[contenteditable="true"][aria-label*="Comment"]',
                    'div[contenteditable="true"][role="textbox"]',
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible():
                            comment_box = el
                            break
                    except Exception:
                        continue

                if not comment_box:
                    try:
                        write_comment = page.locator('div:has-text("Write a comment")').first
                        if write_comment.count() > 0:
                            write_comment.click()
                            page.wait_for_timeout(1500)
                            for sel in ['div[contenteditable="true"][role="textbox"]']:
                                el = page.locator(sel).first
                                if el.count() > 0 and el.is_visible():
                                    comment_box = el
                                    break
                    except Exception:
                        pass

                if not comment_box:
                    results.append({"id": post_id, "posted": False, "error": "Comment box not found"})
                    continue

                comment_box.click()
                page.wait_for_timeout(500)
                comment_box.type(text, delay=30)
                page.wait_for_timeout(1000)
                page.keyboard.press("Enter")
                page.wait_for_timeout(3000)

                results.append({"id": post_id, "posted": True, "comment_url": page.url})

                if i < len(posts) - 1:
                    print(f"STEP:waiting_{delay_seconds}s_before_next", flush=True)
                    time.sleep(delay_seconds)

            except Exception as e:
                results.append({"id": post_id, "posted": False, "error": str(e)})

        print(json.dumps({"batch_results": results}))

    finally:
        page.close()
        browser.close()


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No arguments provided"}))
        sys.exit(1)

    try:
        args = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON arguments"}))
        sys.exit(1)

    email = args.get("email", "")
    password = args.get("password", "")
    post_url = args.get("post_url", "")
    text = args.get("text", "")
    login_only = args.get("login_only", False)
    batch_posts = args.get("batch_posts", None)
    delay_seconds = args.get("delay_seconds", 30)

    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as pw:
            if login_only:
                do_login_only(pw, email, password)
            elif batch_posts:
                do_batch_post(pw, email, password, batch_posts, delay_seconds)
            elif post_url and text:
                do_post_comment(pw, email, password, post_url, text)
            else:
                print(json.dumps({"error": "Missing post_url or text"}))
                sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e), "traceback": traceback.format_exc()}))
        sys.exit(1)


if __name__ == "__main__":
    main()
