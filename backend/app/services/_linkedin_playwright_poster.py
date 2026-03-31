"""
Standalone Playwright script for posting LinkedIn comments.
Uses a persistent browser profile so you only need to log in once.

First run: browser opens, you log in manually + solve CAPTCHA, session is saved.
Subsequent runs: reuses saved session, no login needed.

Usage:
  python _linkedin_playwright_poster.py '{"email":"...", "password":"...", "post_url":"...", "text":"..."}'
  python _linkedin_playwright_poster.py '{"email":"...", "password":"...", "login_only": true}'
"""
import sys
import json
import os
import time
import traceback


def get_profile_dir():
    return os.path.join(os.path.dirname(__file__), ".linkedin_browser_profile")


def is_logged_in(page) -> bool:
    """Check if currently logged into LinkedIn"""
    try:
        # If we're on a login page, not logged in
        if "/login" in page.url or "/checkpoint" in page.url:
            return False
        # Look for feed or profile indicators
        user_indicators = page.locator(
            'img.global-nav__me-photo, '
            'button[aria-label*="profile"], '
            '.feed-identity-module, '
            '#global-nav-icon'
        )
        if user_indicators.count() > 0:
            return True
        # Check if we're on the feed
        return "/feed" in page.url or "/in/" in page.url
    except Exception:
        return "/feed" in page.url


def wait_for_login(page, timeout_seconds=180):
    """Poll every 3s to check if we've left the login page."""
    start = time.time()
    while time.time() - start < timeout_seconds:
        url = page.url
        if "/feed" in url or ("/in/" in url and "/login" not in url):
            return True
        if "/login" not in url and "/checkpoint" not in url and "linkedin.com" in url:
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
    """Open browser, go to LinkedIn, let user log in manually. Wait up to 3 min."""
    print("STEP:launching_browser", flush=True)
    browser = launch_browser(pw)
    page = browser.new_page()
    page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )

    try:
        print("STEP:checking_session", flush=True)
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        if is_logged_in(page):
            print("STEP:already_logged_in", flush=True)
            print(json.dumps({
                "logged_in": True, "method": "browser",
                "message": "Already logged in to LinkedIn!"
            }))
            return

        print("STEP:opening_login_page", flush=True)
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        print("STEP:waiting_for_manual_login", flush=True)
        success = wait_for_login(page, timeout_seconds=180)

        if success:
            print("STEP:login_successful", flush=True)
            page.wait_for_timeout(2000)
            print(json.dumps({
                "logged_in": True, "method": "browser",
                "message": "LinkedIn login successful! Session saved."
            }))
        else:
            print(json.dumps({"error": "Login timed out after 3 minutes."}))
            sys.exit(1)

    finally:
        page.close()
        browser.close()


def _find_comment_box(page):
    """
    Find the LinkedIn comment box and click it.
    LinkedIn uses a contenteditable div for comments.
    Returns the bounding box or None.
    """
    box = page.evaluate("""
        () => {
            // LinkedIn comment boxes are contenteditable divs with specific classes
            const selectors = [
                '.ql-editor[contenteditable="true"]',
                'div.comments-comment-box__form-container .ql-editor',
                'div[role="textbox"][contenteditable="true"]',
                '.editor-content[contenteditable="true"]',
                'div.ql-editor',
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
                            tag: el.tagName,
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


def _type_into_comment_box(page, text):
    """Type text into the focused LinkedIn comment box using keyboard."""
    page.keyboard.press("Control+a")
    page.keyboard.press("Backspace")
    page.wait_for_timeout(300)
    page.keyboard.type(text, delay=8)
    page.wait_for_timeout(1000)

    # Verify text was entered
    has_content = page.evaluate("""
        () => {
            const editors = document.querySelectorAll(
                '.ql-editor[contenteditable="true"], div[role="textbox"][contenteditable="true"]'
            );
            for (const el of editors) {
                const text = el.textContent || '';
                if (text.trim().length > 10) return true;
            }
            return false;
        }
    """)
    return has_content


def _click_submit_button(page):
    """Find and click the LinkedIn comment submit button."""
    # Strategy 1: Standard selectors
    for sel in [
        'button.comments-comment-box__submit-button',
        'button[data-control-name="comment_submit"]',
        'button.comments-comment-box__submit-button--cr',
        'form.comments-comment-box__form button[type="submit"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                el.click()
                return True
        except Exception:
            continue

    # Strategy 2: Find by text content
    try:
        clicked = page.evaluate("""
            () => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    const text = (btn.textContent || '').trim().toLowerCase();
                    const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                    if (text === 'post' || text === 'comment' || text === 'submit'
                        || ariaLabel.includes('post comment') || ariaLabel.includes('submit')) {
                        // Make sure it's in the comment area, not the main post composer
                        const form = btn.closest('.comments-comment-box, .comments-comment-box__form, form');
                        if (form) {
                            const rect = btn.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                btn.click();
                                return true;
                            }
                        }
                    }
                }
                // Fallback: any visible "Post" button
                for (const btn of buttons) {
                    const text = (btn.textContent || '').trim().toLowerCase();
                    if (text === 'post' || text === 'comment') {
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
    """Post a comment to a LinkedIn post."""
    print("STEP:launching_browser", flush=True)
    browser = launch_browser(pw)
    page = browser.new_page()
    page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )

    try:
        # === CHECK LOGIN ===
        print("STEP:checking_session", flush=True)
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        if not is_logged_in(page):
            print("STEP:not_logged_in_attempting_login", flush=True)
            page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            try:
                email_field = page.locator('#username').first
                if email_field.count() > 0 and email_field.is_visible():
                    email_field.fill(email)
                pass_field = page.locator('#password').first
                if pass_field.count() > 0 and pass_field.is_visible():
                    pass_field.fill(password)
                submit_btn = page.locator('button[type="submit"]').first
                if submit_btn.count() > 0 and submit_btn.is_visible():
                    submit_btn.click()
                page.wait_for_timeout(6000)
            except Exception as e:
                print(json.dumps({
                    "error": f"Auto-login failed: {e}. Use 'Login to LinkedIn' button first."
                }))
                sys.exit(1)

            if not is_logged_in(page):
                # Maybe there's a verification challenge
                print("STEP:waiting_for_manual_verification", flush=True)
                success = wait_for_login(page, timeout_seconds=120)
                if not success:
                    print(json.dumps({
                        "error": "Login failed. Use 'Login to LinkedIn' button first."
                    }))
                    sys.exit(1)

            print("STEP:logged_in", flush=True)
        else:
            print("STEP:already_logged_in", flush=True)

        # === NAVIGATE TO POST ===
        print("STEP:navigating_to_post", flush=True)
        page.goto(post_url, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        if "/login" in page.url:
            print(json.dumps({
                "error": "Redirected to login — session expired. Use 'Login to LinkedIn' button."
            }))
            sys.exit(1)

        print("STEP:on_post_page", flush=True)

        # === SCROLL TO COMMENT AREA ===
        print("STEP:scrolling_to_comment_area", flush=True)
        page.evaluate("window.scrollTo(0, 400)")
        page.wait_for_timeout(2000)

        # === CLICK "Add a comment" TO EXPAND COMMENT BOX ===
        print("STEP:expanding_comment_box", flush=True)
        expanded = page.evaluate("""
            () => {
                // Try clicking the "Add a comment" placeholder
                const placeholders = document.querySelectorAll(
                    '.comments-comment-box-comment__text-editor, '
                    + 'button.comments-comment-texteditor__content, '
                    + '.comments-comment-box__form-container, '
                    + '[placeholder*="Add a comment"], '
                    + '.comments-comment-texteditor, '
                    + 'div.feed-shared-update-v2__comments-container button'
                );
                for (const el of placeholders) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 50 && rect.height > 0) {
                        el.click();
                        return 'clicked_placeholder';
                    }
                }
                // Try the comment icon/button
                const commentBtns = document.querySelectorAll(
                    'button[aria-label*="Comment"], button[aria-label*="comment"]'
                );
                for (const btn of commentBtns) {
                    const rect = btn.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        btn.click();
                        return 'clicked_comment_button';
                    }
                }
                return null;
            }
        """)
        print(f"STEP:expand_result:{expanded}", flush=True)
        page.wait_for_timeout(2000)

        # === FIND AND ACTIVATE COMMENT BOX ===
        print("STEP:finding_comment_box", flush=True)
        box = _find_comment_box(page)

        if not box:
            # Retry after scrolling more
            print("STEP:retrying_after_scroll", flush=True)
            page.evaluate("window.scrollTo(0, 600)")
            page.wait_for_timeout(3000)

            # Try clicking comment button again
            page.evaluate("""
                () => {
                    const btns = document.querySelectorAll(
                        'button[aria-label*="Comment"], button[aria-label*="comment"]'
                    );
                    for (const btn of btns) {
                        btn.click();
                        return;
                    }
                }
            """)
            page.wait_for_timeout(2000)
            box = _find_comment_box(page)

        if not box:
            title = page.title()
            print(json.dumps({
                "error": f"Cannot find comment box on LinkedIn. Title: {title}, URL: {page.url}"
            }))
            sys.exit(1)

        print("STEP:comment_box_found", flush=True)

        # === TYPE THE COMMENT ===
        print("STEP:typing_comment", flush=True)
        page.wait_for_timeout(500)
        page.mouse.click(box["x"], box["y"])
        page.wait_for_timeout(500)

        typed = _type_into_comment_box(page, text)
        if not typed:
            print("STEP:typing_failed_retrying", flush=True)
            page.mouse.click(box["x"] + 5, box["y"] + 5)
            page.wait_for_timeout(500)
            typed = _type_into_comment_box(page, text)

        if not typed:
            print(json.dumps({
                "error": "Found comment box but text verification failed. "
                         "The editor may not be accepting keyboard input."
            }))
            sys.exit(1)

        page.wait_for_timeout(1500)
        print("STEP:comment_typed", flush=True)

        # === SUBMIT ===
        print("STEP:finding_submit_button", flush=True)
        page.wait_for_timeout(500)
        submitted = _click_submit_button(page)

        if not submitted:
            print(json.dumps({
                "error": f"Cannot find submit button. URL: {page.url}"
            }))
            sys.exit(1)

        print("STEP:clicking_submit", flush=True)
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
    """Post comments to multiple LinkedIn posts in one browser session."""
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
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        if not is_logged_in(page):
            print("STEP:not_logged_in_attempting_login", flush=True)
            page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            try:
                email_field = page.locator('#username').first
                if email_field.count() > 0 and email_field.is_visible():
                    email_field.fill(email)
                pass_field = page.locator('#password').first
                if pass_field.count() > 0 and pass_field.is_visible():
                    pass_field.fill(password)
                submit_btn = page.locator('button[type="submit"]').first
                if submit_btn.count() > 0 and submit_btn.is_visible():
                    submit_btn.click()
                page.wait_for_timeout(6000)
            except Exception as e:
                print(json.dumps({"error": f"Auto-login failed: {e}. Use 'Login to LinkedIn' button first."}))
                sys.exit(1)

            if not is_logged_in(page):
                print("STEP:waiting_for_manual_verification", flush=True)
                success = wait_for_login(page, timeout_seconds=120)
                if not success:
                    print(json.dumps({"error": "Login failed. Use 'Login to LinkedIn' button first."}))
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

                if "/login" in page.url:
                    results.append({"id": post_id, "error": "Redirected to login — session expired."})
                    continue

                # Scroll & expand comment box
                page.evaluate("window.scrollTo(0, 400)")
                page.wait_for_timeout(2000)

                page.evaluate("""
                    () => {
                        const placeholders = document.querySelectorAll(
                            '.comments-comment-box-comment__text-editor, '
                            + 'button.comments-comment-texteditor__content, '
                            + '.comments-comment-box__form-container, '
                            + '[placeholder*="Add a comment"], '
                            + '.comments-comment-texteditor, '
                            + 'div.feed-shared-update-v2__comments-container button'
                        );
                        for (const el of placeholders) {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 50 && rect.height > 0) { el.click(); return; }
                        }
                        const commentBtns = document.querySelectorAll(
                            'button[aria-label*="Comment"], button[aria-label*="comment"]'
                        );
                        for (const btn of commentBtns) {
                            const rect = btn.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) { btn.click(); return; }
                        }
                    }
                """)
                page.wait_for_timeout(2000)

                box = _find_comment_box(page)
                if not box:
                    page.evaluate("window.scrollTo(0, 600)")
                    page.wait_for_timeout(3000)
                    page.evaluate("""
                        () => {
                            const btns = document.querySelectorAll(
                                'button[aria-label*="Comment"], button[aria-label*="comment"]'
                            );
                            for (const btn of btns) { btn.click(); return; }
                        }
                    """)
                    page.wait_for_timeout(2000)
                    box = _find_comment_box(page)

                if not box:
                    results.append({"id": post_id, "error": "Cannot find comment box"})
                    continue

                # Type
                page.mouse.click(box["x"], box["y"])
                page.wait_for_timeout(500)
                typed = _type_into_comment_box(page, text)
                if not typed:
                    page.mouse.click(box["x"] + 5, box["y"] + 5)
                    page.wait_for_timeout(500)
                    typed = _type_into_comment_box(page, text)

                if not typed:
                    results.append({"id": post_id, "error": "Text verification failed"})
                    continue

                page.wait_for_timeout(1500)

                # Submit
                submitted = _click_submit_button(page)
                if not submitted:
                    results.append({"id": post_id, "error": "Cannot find submit button"})
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
