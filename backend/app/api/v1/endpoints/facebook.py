import asyncio
import json
import sys
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db, AsyncSessionLocal
from app.schemas.facebook import FacebookPostResponse
from app.services.facebook_service import FacebookService
from app.models.facebook_post import FacebookPost
from app.core.config import settings
from sqlalchemy import select

router = APIRouter()


@router.post("/monitor")
async def monitor_facebook(
    keywords: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Search Facebook for real estate posts via Google/SerpAPI"""
    service = FacebookService()
    stats = await service.monitor_facebook(db, keywords)
    return {"message": "Facebook monitoring completed", **stats}


@router.get("/posts", response_model=List[FacebookPostResponse])
async def get_posts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(FacebookPost)
        .offset(skip).limit(limit)
        .order_by(FacebookPost.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/posts/{post_id}", response_model=FacebookPostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FacebookPost).where(FacebookPost.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.delete("/posts/{post_id}")
async def delete_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FacebookPost).where(FacebookPost.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await db.delete(post)
    await db.commit()
    return {"message": "Post deleted"}


@router.post("/posts/{post_id}/fetch-content")
async def fetch_post_content(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FacebookPost).where(FacebookPost.id == post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    service = FacebookService()
    content = await service.fetch_post_content(post.url)

    if content:
        post.content = content
        await db.commit()
        return {"content": content, "success": True}
    else:
        return {"content": None, "success": False, "message": "Could not extract content. The post may require login."}


class PostCommentRequest(BaseModel):
    post_id: int
    text: str


@router.post("/post-comment")
async def post_comment(req: PostCommentRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FacebookPost).where(FacebookPost.id == req.post_id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    try:
        from app.services.facebook_poster_browser import FacebookPosterBrowser
        poster = FacebookPosterBrowser()
        try:
            comment = await poster.post_comment(post.url, req.text)
        finally:
            await poster.close()
        return {"message": "Comment posted successfully", **comment}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to post comment: {str(e)}")


@router.get("/auth-status")
async def facebook_auth_status(db: AsyncSession = Depends(get_db)):
    from app.core.login_status import is_logged_in
    logged_in = await is_logged_in(db, "facebook")
    if logged_in:
        return {"authenticated": True, "method": "browser", "note": "Logged in."}
    return {"authenticated": False, "error": "Not logged in. Go to Profile and click Login."}


@router.post("/browser-login")
async def browser_login(db: AsyncSession = Depends(get_db)):
    """Open browser for manual Facebook login — user fills credentials themselves."""
    import subprocess as sp
    from app.services.facebook_poster_browser import _SCRIPT_PATH

    args_json = json.dumps({
        "email": "",
        "password": "",
        "post_url": "", "text": "", "login_only": True,
    })

    loop = asyncio.get_running_loop()
    from concurrent.futures import ThreadPoolExecutor
    executor = ThreadPoolExecutor(max_workers=1)

    def _run():
        proc = sp.Popen(
            [sys.executable, _SCRIPT_PATH, args_json],
            stdout=sp.PIPE, stderr=sp.PIPE,
        )
        stdout, stderr = proc.communicate(timeout=900)
        return proc.returncode, stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")

    try:
        returncode, stdout, stderr = await loop.run_in_executor(executor, _run)
        json_line = None
        for line in reversed(stdout.strip().split("\n")):
            if line.strip().startswith("{"):
                json_line = line.strip()
                break

        if returncode == 0 and json_line:
            data = json.loads(json_line)
            from app.core.login_status import set_logged_in
            await set_logged_in(db, "facebook", True)
            return {"message": "Login successful! Session saved.", **data}
        elif json_line:
            data = json.loads(json_line)
            raise HTTPException(status_code=400, detail=data.get("error", "Login failed"))
        else:
            raise HTTPException(status_code=500, detail=f"Login failed: {stderr[:300] or stdout[:300]}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RunAgentRequest(BaseModel):
    max_posts: int = 5
    delay_seconds: int = 120
    dry_run: bool = False


@router.post("/agent/run")
async def run_agent(req: RunAgentRequest, db: AsyncSession = Depends(get_db)):
    from app.services.facebook_agent import FacebookAgent
    try:
        agent = FacebookAgent(delay_between_posts=req.delay_seconds)
        stats = await agent.run(db, max_posts=req.max_posts, dry_run=req.dry_run)
        return {"message": "Agent run completed", **stats}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")


@router.get("/agent/stream")
async def run_agent_stream(
    request: Request,
    max_posts: int = 5,
    delay_seconds: int = 120,
    dry_run: bool = True,
):
    from app.services.facebook_agent import FacebookAgent

    async def event_generator():
        log_queue: asyncio.Queue = asyncio.Queue()

        async def on_event(event: dict):
            await log_queue.put(event)

        async def run_agent_task():
            async with AsyncSessionLocal() as db:
                try:
                    agent = FacebookAgent(delay_between_posts=delay_seconds)
                    stats = await agent.run(
                        db, max_posts=max_posts, dry_run=dry_run, on_event=on_event
                    )
                    await log_queue.put({"type": "result", "stats": stats})
                except Exception as e:
                    await log_queue.put({"type": "error", "message": str(e)})
                finally:
                    await log_queue.put(None)

        task = asyncio.create_task(run_agent_task())

        try:
            while True:
                if await request.is_disconnected():
                    task.cancel()
                    break
                try:
                    event = await asyncio.wait_for(log_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/agent/pending")
async def get_pending_posts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FacebookPost)
        .where(FacebookPost.agent_posted == False)
        .where(FacebookPost.is_relevant == True)
    )
    threads = result.scalars().all()
    return {"pending_count": len(threads)}
