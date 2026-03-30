"""
Standalone Playwright script for posting Twitter/X replies.
Uses a persistent browser profile so you only need to log in once.

Usage:
  python _twitter_playwright_poster.py '{"email":"...", "password":"...", "post_url":"...", "text":"..."}'
  python _twitter_playwright_poster.py '{"email":"...", "password":"...", "login_only": true}'
"""
import sys
import json
import os
import time
import traceback


def get_profile_dir():
    return os.path.join(os.path.dirname(__file__), ".twitter_browser_profile")


def is_logged_in(page) -> bool:
    """Check if currently logged into Twitter/X"""
    try:
        if "/login" in page.url or "/i/flow/login" in page.url:
            return False
        user_indicators = page.locator(
            'a[aria-label="Profile"], '
            'a[data-testid="AppTabBar_Profile_Link"], '
            'nav[aria-label="Primary"]'
        )
        if user_indicators.count() > 0:
            return True
        return "/home" in page.url or "/compose" in page.url
    except Exception:
        return "/home" in page.url


def wait_for_login(page, timeout_seconds=180):
    """Poll every 3s to check if we've left the login page."""
    start = time.time()
    while time.time() - start < timeout_seconds:
        url = page.url
        if "/home" in url or ("/status/" in url and "/login" not in url):
            return True
        if "/login" not in url and "/i/flow" not in url and "x.com" in url:
            return True
        page.wait_for_timeout(3000)
    return False


def launch_browser(pw):
    profile_dir = get_profile_dir()
    os.makedirs(profile_dir, exist_ok=True)
    return pw.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 900},
        ignore_default_args=["--enable-automation"],
    )


def do_login_only(pw, email, password):
    """Open browser, go to X, let user log in manually."""
    print("STEP:launching_browser", flush=True)
    browser = launch_browser(pw)
    page = browser.new_page()
    page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )

    try:
        print("STEP:checking_session", flush=True)
        page.goto("https://x.com/home", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        if is_logged_in(page):
            print("STEP:already_logged_in", flush=True)
            print(json.dumps({
                "logged_in": True, "method": "browser",
                "message": "Already logged in to X!"
            }))
            return

        print("STEP:opening_login_page", flush=True)
        page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Try to fill email
        print("STEP:filling_credentials", flush=True)
        try:
            email_field = page.locator('input[autocomplete="username"]').first
            if email_field.count() > 0 and email_field.is_visible():
                email_field.fill(email)
                # Click Next
                next_btn = page.locator('button:has-text("Next")').first
                if next_btn.count() > 0 and next_btn.is_visible():
                    next_btn.click()
                    page.wait_for_timeout(2000)
                # Fill password
                pass_field = page.locator('input[type="password"]').first
                if pass_field.count() > 0 and pass_field.is_visible():
                    pass_field.fill(password)
                    login_btn = page.locator('button[data-testid="LoginForm_Login_Button"]').first
                    if login_btn.count() > 0 and login_btn.is_visible():
                        login_btn.click()
                        page.wait_for_timeout(3000)
        except Exception:
            pass

        print("STEP:waiting_for_manual_login", flush=True)
        success = wait_for_login(page, timeout_seconds=180)

        if success:
            print("STEP:login_successful", flush=True)
            page.wait_for_timeout(2000)
            print(json.dumps({
                "logged_in": True, "method": "browser",
                "message": "X login successful! Session saved."
            }))
        else:
            print(json.dumps({"error": "Login timed out after 3 minutes."}))
            sys.exit(1)

    finally:
        page.close()
        browser.close()


def _find_reply_box(page):
    """Find the Twitter reply box and click it."""
    box = page.evaluate("""
        () => {
            // Twitter uses a contenteditable div with data-testid
            const selectors = [
                'div[data-testid="tweetTextarea_0"][contenteditable="true"]',
                'div[role="textbox"][contenteditable="true"]',
                'div.DraftEditor-editorContainer [contenteditable="true"]',
                'div[data-testid="tweetTextarea_0"]',
            ];
            for (const sel of selectors) {
                const els = document.querySelectorAll(sel);
                for (const el of els) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 50 && rect.height > 10) {
                        return {
                            x: rect.x + rect.width / 2,
                            y: rect.y + rect.height / 2,
                            width: rect.width,
                            height: rect.height,
                        };
                    }
                }
            }
            return null;
        }
    """)
    if not box:
        return None
    page.mouse.click(box["x"], box["y"])
    page.wait_for_timeout(500)
    return box


def _type_into_reply_box(page, text):
    """Type text into the focused Twitter reply box."""
    page.keyboard.press("Control+a")
    page.keyboard.press("Backspace")
    page.wait_for_timeout(300)
    page.keyboard.type(text, delay=8)
    page.wait_for_timeout(1000)

    has_content = page.evaluate("""
        () => {
            const editors = document.querySelectorAll(
                'div[data-testid="tweetTextarea_0"], div[role="textbox"][contenteditable="true"]'
            );
            for (const el of editors) {
                const text = el.textContent || '';
                if (text.trim().length > 10) return true;
            }
            return false;
        }
    """)
    return has_content


def _click_reply_button(page):
    """Find and click the Reply/Post button."""
    for sel in [
        'button[data-testid="tweetButtonInline"]',
        'button[data-testid="tweetButton"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                el.click()
                return True
        except Exception:
            continue

    try:
        clicked = page.evaluate("""
            () => {
                const buttons = document.querySelectorAll('button[role="button"]');
                for (const btn of buttons) {
                    const text = (btn.textContent || '').trim().toLowerCase();
                    if (text === 'reply' || text === 'post') {
                        const rect = btn.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0 && !btn.disabled) {
                            btn.click();
                            return true;
                        }
                    }
                }
                return false;
            }
        """)
        if clicked:
            return True
    except Exception:
        pass

    return False


def do_post_comment(pw, email, password, post_url, text):
    """Post a reply to a tweet."""
    print("STEP:launching_browser", flush=True)
    browser = launch_browser(pw)
    page = browser.new_page()
    page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )

    try:
        # === CHECK LOGIN ===
        print("STEP:checking_session", flush=True)
        page.goto("https://x.com/home", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        if not is_logged_in(page):
            print("STEP:not_logged_in_attempting_login", flush=True)
            page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            try:
                email_field = page.locator('input[autocomplete="username"]').first
                if email_field.count() > 0 and email_field.is_visible():
                    email_field.fill(email)
                    next_btn = page.locator('button:has-text("Next")').first
                    if next_btn.count() > 0:
                        next_btn.click()
                        page.wait_for_timeout(2000)
                    pass_field = page.locator('input[type="password"]').first
                    if pass_field.count() > 0 and pass_field.is_visible():
                        pass_field.fill(password)
                        login_btn = page.locator('button[data-testid="LoginForm_Login_Button"]').first
                        if login_btn.count() > 0:
                            login_btn.click()
                            page.wait_for_timeout(4000)
            except Exception as e:
                print(json.dumps({
                    "error": f"Auto-login failed: {e}. Use 'Login to X' button first."
                }))
                sys.exit(1)

            if not is_logged_in(page):
                print("STEP:waiting_for_manual_verification", flush=True)
                success = wait_for_login(page, timeout_seconds=120)
                if not success:
                    print(json.dumps({
                        "error": "Login failed. Use 'Login to X' button first."
                    }))
                    sys.exit(1)

            print("STEP:logged_in", flush=True)
        else:
            print("STEP:already_logged_in", flush=True)

        # === NAVIGATE TO TWEET ===
        print("STEP:navigating_to_tweet", flush=True)
        page.goto(post_url, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        if "/login" in page.url or "/i/flow" in page.url:
            print(json.dumps({
                "error": "Redirected to login — session expired. Use 'Login to X' button."
            }))
            sys.exit(1)

        print("STEP:on_tweet_page", flush=True)

        # === SCROLL DOWN TO REPLY AREA ===
        print("STEP:scrolling_to_reply_area", flush=True)
        page.evaluate("window.scrollTo(0, 400)")
        page.wait_for_timeout(2000)

        # === CLICK REPLY AREA TO EXPAND ===
        print("STEP:expanding_reply_box", flush=True)
        page.evaluate("""
            () => {
                const replyArea = document.querySelector(
                    'div[data-testid="tweetTextarea_0"], '
                    + 'div[role="textbox"]'
                );
                if (replyArea) { replyArea.click(); return 'clicked'; }
                return null;
            }
        """)
        page.wait_for_timeout(2000)

        # === FIND AND ACTIVATE REPLY BOX ===
        print("STEP:finding_reply_box", flush=True)
        box = _find_reply_box(page)

        if not box:
            print("STEP:retrying_after_scroll", flush=True)
            page.evaluate("window.scrollTo(0, 300)")
            page.wait_for_timeout(3000)
            box = _find_reply_box(page)

        if not box:
            title = page.title()
            print(json.dumps({
                "error": f"Cannot find reply box on X. Title: {title}, URL: {page.url}"
            }))
            sys.exit(1)

        print("STEP:reply_box_found", flush=True)

        # === TYPE THE REPLY ===
        print("STEP:typing_reply", flush=True)
        page.wait_for_timeout(500)
        page.mouse.click(box["x"], box["y"])
        page.wait_for_timeout(500)

        typed = _type_into_reply_box(page, text)
        if not typed:
            print("STEP:typing_failed_retrying", flush=True)
            page.mouse.click(box["x"] + 5, box["y"] + 5)
            page.wait_for_timeout(500)
            typed = _type_into_reply_box(page, text)

        if not typed:
            print(json.dumps({
                "error": "Found reply box but text verification failed."
            }))
            sys.exit(1)

        page.wait_for_timeout(1500)
        print("STEP:reply_typed", flush=True)

        # === SUBMIT ===
        print("STEP:finding_reply_button", flush=True)
        page.wait_for_timeout(500)
        submitted = _click_reply_button(page)

        if not submitted:
            print(json.dumps({
                "error": f"Cannot find reply button. URL: {page.url}"
            }))
            sys.exit(1)

        print("STEP:clicking_reply", flush=True)
        page.wait_for_timeout(6000)

        print("STEP:done", flush=True)
        print(json.dumps({
            "posted": True, "method": "browser",
            "comment_url": page.url,
        }))

    finally:
        page.close()
        browser.close()


def do_batch_post(pw, email, password, posts, delay_seconds=30):
    """Post replies to multiple tweets in one browser session."""
    print("STEP:launching_browser", flush=True)
    browser = launch_browser(pw)
    page = browser.new_page()
    page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )

    results = []

    try:
        # === CHECK LOGIN ONCE ===
        print("STEP:checking_session", flush=True)
        page.goto("https://x.com/home", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        if not is_logged_in(page):
            print("STEP:not_logged_in_attempting_login", flush=True)
            page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            try:
                email_field = page.locator('input[autocomplete="username"]').first
                if email_field.count() > 0 and email_field.is_visible():
                    email_field.fill(email)
                    next_btn = page.locator('button:has-text("Next")').first
                    if next_btn.count() > 0:
                        next_btn.click()
                        page.wait_for_timeout(2000)
                    pass_field = page.locator('input[type="password"]').first
                    if pass_field.count() > 0 and pass_field.is_visible():
                        pass_field.fill(password)
                        login_btn = page.locator('button[data-testid="LoginForm_Login_Button"]').first
                        if login_btn.count() > 0:
                            login_btn.click()
                            page.wait_for_timeout(4000)
            except Exception as e:
                print(json.dumps({"error": f"Auto-login failed: {e}. Use 'Login to X' button first."}))
                sys.exit(1)

            if not is_logged_in(page):
                print("STEP:waiting_for_manual_verification", flush=True)
                success = wait_for_login(page, timeout_seconds=120)
                if not success:
                    print(json.dumps({"error": "Login failed. Use 'Login to X' button first."}))
                    sys.exit(1)

            print("STEP:logged_in", flush=True)
        else:
            print("STEP:already_logged_in", flush=True)

        # === LOOP THROUGH POSTS ===
        for idx, post_data in enumerate(posts):
            post_url = post_data["post_url"]
            text = post_data["text"]
            post_id = post_data.get("id", idx)

            print(f"STEP:batch_post_{idx+1}_of_{len(posts)}", flush=True)

            try:
                page.goto(post_url, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)

                if "/login" in page.url or "/i/flow" in page.url:
                    results.append({"id": post_id, "error": "Redirected to login — session expired."})
                    continue

                # Scroll & expand reply box
                page.evaluate("window.scrollTo(0, 400)")
                page.wait_for_timeout(2000)

                page.evaluate("""
                    () => {
                        const replyArea = document.querySelector(
                            'div[data-testid="tweetTextarea_0"], div[role="textbox"]'
                        );
                        if (replyArea) replyArea.click();
                    }
                """)
                page.wait_for_timeout(2000)

                box = _find_reply_box(page)
                if not box:
                    page.evaluate("window.scrollTo(0, 300)")
                    page.wait_for_timeout(3000)
                    box = _find_reply_box(page)

                if not box:
                    results.append({"id": post_id, "error": "Cannot find reply box"})
                    continue

                # Type
                page.mouse.click(box["x"], box["y"])
                page.wait_for_timeout(500)
                typed = _type_into_reply_box(page, text)
                if not typed:
                    page.mouse.click(box["x"] + 5, box["y"] + 5)
                    page.wait_for_timeout(500)
                    typed = _type_into_reply_box(page, text)

                if not typed:
                    results.append({"id": post_id, "error": "Text verification failed"})
                    continue

                page.wait_for_timeout(1500)

                # Submit
                submitted = _click_reply_button(page)
                if not submitted:
                    results.append({"id": post_id, "error": "Cannot find reply button"})
                    continue

                page.wait_for_timeout(6000)
                results.append({"id": post_id, "posted": True, "method": "browser", "comment_url": page.url})
                print(f"STEP:batch_post_{idx+1}_done", flush=True)

            except Exception as e:
                results.append({"id": post_id, "error": str(e)})

            if idx < len(posts) - 1:
                print(f"STEP:waiting_{delay_seconds}s", flush=True)
                time.sleep(delay_seconds)

    finally:
        page.close()
        browser.close()

    print(json.dumps({"batch_results": results}))


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No arguments provided"}))
        sys.exit(1)

    try:
        args = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON args: {e}"}))
        sys.exit(1)

    email = args.get("email", "")
    password = args.get("password", "")
    post_url = args.get("post_url", "")
    text = args.get("text", "")
    login_only = args.get("login_only", False)
    batch_posts = args.get("batch_posts", None)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(json.dumps({"error": "playwright not installed"}))
        sys.exit(1)

    pw = None
    try:
        print("STEP:starting_playwright", flush=True)
        pw = sync_playwright().start()

        if login_only:
            do_login_only(pw, email, password)
        elif batch_posts:
            delay = args.get("delay_seconds", 30)
            do_batch_post(pw, email, password, batch_posts, delay)
        else:
            if not all([post_url, text]):
                print(json.dumps({"error": "Missing post_url or text"}))
                sys.exit(1)
            do_post_comment(pw, email, password, post_url, text)

    except SystemExit:
        raise
    except Exception as e:
        err_msg = str(e) or repr(e) or "Unknown error"
        print(json.dumps({
            "error": err_msg,
            "traceback": traceback.format_exc(),
        }))
        sys.exit(1)
    finally:
        if pw:
            try:
                pw.stop()
            except Exception:
                pass


if __name__ == "__main__":
    main()
