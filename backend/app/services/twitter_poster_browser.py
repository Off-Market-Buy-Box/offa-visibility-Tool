import asyncio
import json
import os
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor
from app.core.config import settings

_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "_twitter_playwright_poster.py")
_executor = ThreadPoolExecutor(max_workers=2)


def _run_poster_subprocess(python_exe: str, script_path: str, args_json: str) -> dict:
    proc = subprocess.Popen(
        [python_exe, script_path, args_json],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout_bytes, stderr_bytes = proc.communicate(timeout=180)
    stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
    stderr = stderr_bytes.decode("utf-8", errors="replace").strip()

    for line in stdout.split("\n"):
        if line.startswith("STEP:"):
            print(f"  🔄 Twitter Browser: {line.replace('STEP:', '')}")

    json_line = None
    for line in reversed(stdout.split("\n")):
        line = line.strip()
        if line.startswith("{"):
            json_line = line
            break

    if proc.returncode != 0:
        if json_line:
            try:
                data = json.loads(json_line)
                error = data.get("error", "Unknown error")
                tb = data.get("traceback", "")
                if tb:
                    print(f"  📋 Subprocess traceback:\n{tb}")
                raise RuntimeError(error)
            except (json.JSONDecodeError, RuntimeError):
                if isinstance(sys.exc_info()[1], RuntimeError):
                    raise
        detail = stderr or stdout or "No output"
        raise RuntimeError(f"Browser process failed (exit {proc.returncode}): {detail[:800]}")

    if json_line:
        try:
            data = json.loads(json_line)
            if "error" in data:
                raise RuntimeError(data["error"])
            return data
        except json.JSONDecodeError:
            pass

    raise RuntimeError(f"No valid JSON from browser. stdout: {stdout[:500]}")


class TwitterPosterBrowser:
    def __init__(self):
        self.email = settings.TWITTER_EMAIL
        self.password = settings.TWITTER_PASSWORD

    async def post_comment(self, post_url: str, text: str) -> dict:
        if not self.email or not self.password:
            raise RuntimeError("TWITTER_EMAIL and TWITTER_PASSWORD must be set in .env")

        args_json = json.dumps({
            "email": self.email,
            "password": self.password,
            "post_url": post_url,
            "text": text,
        })

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            _executor,
            _run_poster_subprocess,
            sys.executable,
            _SCRIPT_PATH,
            args_json,
        )
        return result

    async def close(self):
        pass

    async def verify_credentials(self) -> dict:
        if not self.email or not self.password:
            return {
                "authenticated": False,
                "method": "browser",
                "error": "TWITTER_EMAIL and TWITTER_PASSWORD not set in .env",
            }
        return {
            "authenticated": True,
            "method": "browser",
            "email": self.email,
            "note": "Browser mode — opens Chromium in a subprocess",
        }
