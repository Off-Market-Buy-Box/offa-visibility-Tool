"""
Standalone Playwright script for posting Reddit comments.
Uses a persistent browser profile so you only need to log in once.

First run: browser opens, you log in manually + solve CAPTCHA, session is saved.
Subsequent runs: reuses saved session, no login needed.

Usage:
  python _playwright_poster.py '{"username":"...", "password":"...", "post_url":"...", "text":"..."}'
  python _playwright_poster.py '{"username":"...", "password":"...", "login_only": true}'
"""
import sys
import json
import os
import time
import traceback


def get_profile_dir():
    return os.path.join(os.path.dirname(__file__), ".reddit_browser_profile")


def is_logged_in(page) -> bool:
    """Check if currently logged into Reddit"""
    try:
        login_indicators = page.locator(
            'a[href*="/login"], button:has-text("Log In"), a:has-text("Log In")'
        )
        if login_indicators.count() > 0:
            return False
        user_indicators = page.locator(
            '[id*="USER"], button[aria-label*="profile"], #expand-user-drawer-button'
        )
        return user_indicators.count() > 0 or "/login" not in page.url
    except Exception:
        return "/login" not in page.url


def wait_for_login(page, timeout_seconds=180):
    """Poll every 3s to check if we've left the login page."""
    start = time.time()
    while time.time() - start < timeout_seconds:
        if "/login" not in page.url and "reddit.com" in page.url:
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


def do_login_only(pw, username, password):
    """Open browser, go to Reddit, let user log in manually. Wait up to 3 min."""
    print("STEP:launching_browser", flush=True)
    browser = launch_browser(pw)
    page = browser.new_page()
    page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )

    try:
        print("STEP:checking_session", flush=True)
        page.goto("https://www.reddit.com/", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        if is_logged_in(page):
            print("STEP:already_logged_in", flush=True)
            print(json.dumps({
                "logged_in": True, "method": "browser",
                "message": "Already logged in!"
            }))
            return

        print("STEP:opening_login_page", flush=True)
        page.goto("https://www.reddit.com/login/", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        body_text = page.inner_text("body")
        has_captcha = (
            "Prove your humanity" in body_text
            or "not a robot" in body_text.lower()
        )

        if has_captcha:
            print("STEP:captcha_detected_solve_manually", flush=True)
            print("STEP:waiting_up_to_3_min_for_login", flush=True)
        else:
            print("STEP:filling_credentials", flush=True)
            try:
                for sel in ['#login-username', 'input[name="username"]']:
                    el = page.locator(sel).first
                    if el.count() > 0 and el.is_visible():
                        el.fill(username)
                        break
                for sel in ['#login-password', 'input[name="password"]']:
                    el = page.locator(sel).first
                    if el.count() > 0 and el.is_visible():
                        el.fill(password)
                        break
            except Exception:
                pass
            print("STEP:waiting_for_manual_login", flush=True)

        success = wait_for_login(page, timeout_seconds=180)

        if success:
            print("STEP:login_successful", flush=True)
            page.goto("https://www.reddit.com/", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            print(json.dumps({
                "logged_in": True, "method": "browser",
                "message": "Login successful! Session saved."
            }))
        else:
            print(json.dumps({"error": "Login timed out after 3 minutes."}))
            sys.exit(1)

    finally:
        page.close()
        browser.close()


def _find_and_activate_comment_box(page):
    """
    Find the Reddit comment box (inside shadow DOM) and click it
    using Playwright's mouse so keyboard events will go to it.
    Returns the bounding box {x, y, width, height} or None.
    """
    # Use JS to find the editable element and return its coordinates
    box = page.evaluate("""
        () => {
            function findEditable(root) {
                const editables = root.querySelectorAll(
                    '[contenteditable="true"], textarea, div[role="textbox"]'
                );
                for (const el of editables) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 50 && rect.height > 10) {
                        return {
                            x: rect.x + rect.width / 2,
                            y: rect.y + rect.height / 2,
                            width: rect.width,
                            height: rect.height,
                            tag: el.tagName,
                            editable: el.contentEditable
                        };
                    }
                }
                const allEls = root.querySelectorAll('*');
                for (const el of allEls) {
                    if (el.shadowRoot) {
                        const result = findEditable(el.shadowRoot);
                        if (result) return result;
                    }
                }
                return null;
            }
            return findEditable(document);
        }
    """)
    if not box:
        return None

    # Click at the center of the found element using Playwright's mouse
    # This ensures Playwright's keyboard events will target this element
    page.mouse.click(box["x"], box["y"])
    page.wait_for_timeout(500)
    return box


def _type_into_comment_box(page, text):
    """
    Type text into the focused comment box using keyboard.
    Reddit's Lexical editor in shadow DOM doesn't respond to .fill() or
    execCommand — we MUST use keyboard.type() after clicking the element.
    """
    # Select all existing text (if any) and delete it first
    page.keyboard.press("Control+a")
    page.keyboard.press("Backspace")
    page.wait_for_timeout(300)

    # Type the text character by character via keyboard
    # This is the ONLY reliable way to input text into Lexical editors
    page.keyboard.type(text, delay=8)
    page.wait_for_timeout(1000)

    # Verify text was actually entered by checking the editor content
    has_content = page.evaluate("""
        () => {
            function checkContent(root) {
                const editables = root.querySelectorAll(
                    '[contenteditable="true"], textarea, div[role="textbox"]'
                );
                for (const el of editables) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 50 && rect.height > 10) {
                        const text = el.textContent || el.value || '';
                        if (text.trim().length > 10) return true;
                    }
                }
                const allEls = root.querySelectorAll('*');
                for (const el of allEls) {
                    if (el.shadowRoot) {
                        if (checkContent(el.shadowRoot)) return true;
                    }
                }
                return false;
            }
            return checkContent(document);
        }
    """)
    return has_content


def _click_submit_button(page):
    """
    Find and click the submit/Comment button.
    Searches through shadow DOM as well.
    """
    # Strategy 1: Try standard Playwright selectors
    for sel in [
        'button[slot="submit-button"]',
        'button:has-text("Comment"):visible',
        'button[type="submit"]:has-text("Comment")',
        'button[data-testid="comment-submit-button"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                el.click()
                return True
        except Exception:
            continue

    # Strategy 2: Use JS to find submit button in shadow DOM
    try:
        clicked = page.evaluate("""
            () => {
                function findSubmit(root) {
                    // Look for buttons with "Comment" text or submit type
                    const buttons = root.querySelectorAll(
                        'button[type="submit"], button[slot="submit-button"], button'
                    );
                    for (const btn of buttons) {
                        const text = btn.textContent || '';
                        if (text.trim().toLowerCase() === 'comment' 
                            || btn.getAttribute('slot') === 'submit-button') {
                            const rect = btn.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                btn.click();
                                return true;
                            }
                        }
                    }
                    // Recurse into shadow roots
                    const allEls = root.querySelectorAll('*');
                    for (const el of allEls) {
                        if (el.shadowRoot) {
                            const result = findSubmit(el.shadowRoot);
                            if (result) return true;
                        }
                    }
                    return false;
                }
                return findSubmit(document);
            }
        """)
        if clicked:
            return True
    except Exception:
        pass

    return False


def do_post_comment(pw, username, password, post_url, text):
    """Post a comment to a Reddit thread."""
    print("STEP:launching_browser", flush=True)
    browser = launch_browser(pw)
    page = browser.new_page()
    page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )

    try:
        # === CHECK LOGIN ===
        print("STEP:checking_session", flush=True)
        page.goto("https://www.reddit.com/", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        if not is_logged_in(page):
            print("STEP:not_logged_in_attempting_login", flush=True)
            page.goto("https://www.reddit.com/login/", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            body_text = page.inner_text("body")
            has_captcha = (
                "Prove your humanity" in body_text
                or "not a robot" in body_text.lower()
            )

            if has_captcha:
                print("STEP:captcha_detected_waiting", flush=True)
                success = wait_for_login(page, timeout_seconds=120)
                if not success:
                    print(json.dumps({
                        "error": "Not logged in and CAPTCHA detected. "
                                 "Use 'Login to Reddit' button first."
                    }))
                    sys.exit(1)
            else:
                try:
                    for sel in ['#login-username', 'input[name="username"]']:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible():
                            el.fill(username)
                            break
                    for sel in ['#login-password', 'input[name="password"]']:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible():
                            el.fill(password)
                            break
                    for sel in ['button[type="submit"]', 'button:has-text("Log In")']:
                        el = page.locator(sel).first
                        if el.count() > 0 and el.is_visible():
                            el.click()
                            break
                    page.wait_for_timeout(6000)
                except Exception as e:
                    print(json.dumps({
                        "error": f"Auto-login failed: {e}. "
                                 "Use 'Login to Reddit' button first."
                    }))
                    sys.exit(1)

                if "/login" in page.url:
                    print(json.dumps({
                        "error": "Login failed. Use 'Login to Reddit' button first."
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
                "error": "Redirected to login — session expired. "
                         "Use 'Login to Reddit' button."
            }))
            sys.exit(1)

        print("STEP:on_post_page", flush=True)

        # === SCROLL TO COMMENT AREA ===
        print("STEP:scrolling_to_comment_area", flush=True)
        page.evaluate("window.scrollTo(0, 300)")
        page.wait_for_timeout(2000)

        # === FIND AND ACTIVATE COMMENT BOX ===
        print("STEP:finding_comment_box", flush=True)

        # First, try clicking on the shreddit-composer or any "Add a comment" area
        # to activate/expand the comment editor
        activated = page.evaluate("""
            () => {
                // Try clicking the composer element itself
                const composer = document.querySelector('shreddit-composer');
                if (composer) {
                    composer.click();
                    // Also try clicking inside its shadow root
                    if (composer.shadowRoot) {
                        const placeholder = composer.shadowRoot.querySelector(
                            '[placeholder], [data-placeholder], .placeholder, p'
                        );
                        if (placeholder) {
                            placeholder.click();
                            return 'clicked_shadow_placeholder';
                        }
                        // Click any div that looks like an editor area
                        const editorArea = composer.shadowRoot.querySelector(
                            '[contenteditable], [role="textbox"], .DraftEditor-root, '
                            + '.public-DraftEditor-content, .notranslate, .ql-editor'
                        );
                        if (editorArea) {
                            editorArea.click();
                            return 'clicked_shadow_editor';
                        }
                    }
                    return 'clicked_composer';
                }
                // Try other common selectors
                const addComment = document.querySelector(
                    '[placeholder="Add a comment"], '
                    + '[data-testid="comment-composer"], '
                    + '.comment-composer'
                );
                if (addComment) {
                    addComment.click();
                    return 'clicked_add_comment';
                }
                return null;
            }
        """)
        print(f"STEP:activation_result:{activated}", flush=True)
        page.wait_for_timeout(2000)

        # Now try to find the actual editable element and click it
        box = _find_and_activate_comment_box(page)

        if not box:
            # Maybe the composer needs a second click or the page needs more time
            print("STEP:retrying_after_extra_wait", flush=True)
            page.wait_for_timeout(3000)

            # Try clicking the composer area again via JS
            page.evaluate("""
                () => {
                    const composer = document.querySelector('shreddit-composer');
                    if (composer) {
                        composer.click();
                        if (composer.shadowRoot) {
                            const divs = composer.shadowRoot.querySelectorAll('div');
                            for (const d of divs) {
                                const rect = d.getBoundingClientRect();
                                if (rect.height > 30 && rect.width > 200) {
                                    d.click();
                                    break;
                                }
                            }
                        }
                    }
                }
            """)
            page.wait_for_timeout(2000)
            box = _find_and_activate_comment_box(page)

        if not box:
            # Last resort: use old Reddit URL which has a simple textarea
            print("STEP:trying_old_reddit", flush=True)
            old_url = post_url.replace("www.reddit.com", "old.reddit.com")
            page.goto(old_url, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            # old.reddit.com uses a simple textarea
            textarea = page.locator('textarea[name="text"], .usertext-edit textarea').first
            if textarea.count() > 0 and textarea.is_visible():
                print("STEP:found_old_reddit_textarea", flush=True)
                textarea.click()
                textarea.fill(text)
                page.wait_for_timeout(1000)

                # Submit on old reddit
                submit = page.locator(
                    'button[type="submit"]:has-text("save"), '
                    + '.save-button button, '
                    + 'button:has-text("save")'
                ).first
                if submit.count() > 0 and submit.is_visible():
                    print("STEP:submitting_old_reddit", flush=True)
                    submit.click()
                    page.wait_for_timeout(5000)
                    print("STEP:done", flush=True)
                    print(json.dumps({
                        "posted": True, "method": "browser-old-reddit",
                        "comment_url": page.url,
                    }))
                    return
                else:
                    print(json.dumps({
                        "error": f"Found textarea on old Reddit but can't find submit. URL: {page.url}"
                    }))
                    sys.exit(1)

            # If old reddit also fails, give up
            title = page.title()
            print(json.dumps({
                "error": f"Cannot find comment box on new or old Reddit. "
                         f"Title: {title}, URL: {page.url}"
            }))
            sys.exit(1)

        print("STEP:comment_box_found", flush=True)
        print(f"STEP:box_info:tag={box.get('tag')},w={box.get('width')},h={box.get('height')}", flush=True)

        # === TYPE THE COMMENT ===
        print("STEP:typing_comment", flush=True)
        page.wait_for_timeout(500)

        # Click the box again to make sure it's focused
        page.mouse.click(box["x"], box["y"])
        page.wait_for_timeout(500)

        typed = _type_into_comment_box(page, text)
        if not typed:
            # Retry: click slightly different position and try again
            print("STEP:typing_failed_retrying", flush=True)
            page.mouse.click(box["x"] + 5, box["y"] + 5)
            page.wait_for_timeout(500)
            typed = _type_into_comment_box(page, text)

        if not typed:
            print(json.dumps({
                "error": "Found comment box and typed text, but verification "
                         "shows the editor is still empty. The Lexical editor "
                         "may not be accepting keyboard input."
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

        # Check for errors after submit — "this field is required", rate limits, etc.
        has_error = page.evaluate("""
            () => {
                function findErrors(root) {
                    // Check for error text patterns
                    const allText = root.textContent || '';
                    if (/this field is required/i.test(allText)
                        || /field is required/i.test(allText)) {
                        return 'field_required';
                    }
                    // Check inside shadow roots
                    const allEls = root.querySelectorAll('*');
                    for (const el of allEls) {
                        if (el.shadowRoot) {
                            const err = findErrors(el.shadowRoot);
                            if (err) return err;
                        }
                    }
                    return null;
                }
                // Check the composer area specifically
                const composer = document.querySelector('shreddit-composer');
                if (composer && composer.shadowRoot) {
                    const err = findErrors(composer.shadowRoot);
                    if (err) return err;
                }
                return findErrors(document);
            }
        """)

        if has_error:
            print(json.dumps({
                "error": f"Reddit validation error: {has_error}. "
                         "Text was not entered into the comment box properly."
            }))
            sys.exit(1)

        print("STEP:done", flush=True)
        print(json.dumps({
            "posted": True, "method": "browser",
            "comment_url": page.url,
        }))

    finally:
        page.close()
        browser.close()


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No arguments provided"}))
        sys.exit(1)

    try:
        args = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON args: {e}"}))
        sys.exit(1)

    username = args.get("username", "")
    password = args.get("password", "")
    post_url = args.get("post_url", "")
    text = args.get("text", "")
    login_only = args.get("login_only", False)

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
            do_login_only(pw, username, password)
        else:
            if not all([post_url, text]):
                print(json.dumps({"error": "Missing post_url or text"}))
                sys.exit(1)
            do_post_comment(pw, username, password, post_url, text)

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
