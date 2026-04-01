import asyncio
import json
import sys
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db, AsyncSessionLocal
from app.schemas.reddit import RedditMentionResponse
from app.services.reddit_service import RedditService
from app.models.reddit_mention import RedditMention
from app.core.config import settings
from sqlalchemy import select

router = APIRouter()

@router.post("/monitor")
async def monitor_subreddit(
    subreddit: str,
    keywords: List[str] = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Monitor a specific subreddit for keyword mentions"""
    reddit_service = RedditService()
    
    mentions = await reddit_service.search_subreddit(subreddit, keywords)
    saved_count = await reddit_service.save_mentions(db, mentions)
    
    return {
        "subreddit": subreddit,
        "mentions_found": len(mentions),
        "new_mentions_saved": saved_count
    }

@router.post("/monitor-real-estate")
async def monitor_real_estate(
    keywords: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Monitor all real estate subreddits for offa.com and related keywords"""
    reddit_service = RedditService()
    
    stats = await reddit_service.monitor_real_estate_mentions(db, keywords)
    
    return {
        "message": "Real estate monitoring completed",
        **stats
    }

@router.get("/mentions", response_model=List[RedditMentionResponse])
async def get_mentions(
    subreddit: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get Reddit mentions"""
    query = select(RedditMention)
    
    if subreddit:
        query = query.where(RedditMention.subreddit == subreddit)
    
    query = query.offset(skip).limit(limit).order_by(RedditMention.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/mentions/{mention_id}", response_model=RedditMentionResponse)
async def get_mention(
    mention_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific Reddit mention"""
    result = await db.execute(select(RedditMention).where(RedditMention.id == mention_id))
    mention = result.scalar_one_or_none()
    
    if not mention:
        raise HTTPException(status_code=404, detail="Mention not found")
    
    return mention

@router.get("/mentions/{mention_id}/comments")
async def get_mention_comments(
    mention_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get comments for a specific Reddit post"""
    result = await db.execute(select(RedditMention).where(RedditMention.id == mention_id))
    mention = result.scalar_one_or_none()
    
    if not mention:
        raise HTTPException(status_code=404, detail="Mention not found")
    
    reddit_service = RedditService()
    comments = await reddit_service.get_post_comments(mention.url)
    
    return {"post_id": mention.post_id, "comments": comments}

@router.delete("/mentions/{mention_id}")
async def delete_mention(
    mention_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a Reddit mention"""
    result = await db.execute(select(RedditMention).where(RedditMention.id == mention_id))
    mention = result.scalar_one_or_none()
    
    if not mention:
        raise HTTPException(status_code=404, detail="Mention not found")
    
    await db.delete(mention)
    await db.commit()
    return {"message": "Mention deleted"}


class PostCommentRequest(BaseModel):
    mention_id: int
    text: str
    mode: str = "auto"  # "api", "browser", or "auto"


def _has_api_credentials() -> bool:
    return all([
        settings.REDDIT_CLIENT_ID,
        settings.REDDIT_CLIENT_SECRET,
        settings.REDDIT_USERNAME,
        settings.REDDIT_PASSWORD,
    ])


@router.post("/post-comment")
async def post_comment(
    req: PostCommentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Post a comment to a Reddit thread (API or browser mode)"""
    result = await db.execute(
        select(RedditMention).where(RedditMention.id == req.mention_id)
    )
    mention = result.scalar_one_or_none()
    if not mention:
        raise HTTPException(status_code=404, detail="Mention not found")

    try:
        use_api = req.mode == "api" or (req.mode == "auto" and _has_api_credentials())

        if use_api:
            from app.services.reddit_poster import RedditPoster
            poster = RedditPoster()
            comment = await poster.post_comment(mention.post_id, req.text)
        else:
            from app.services.reddit_poster_browser import RedditPosterBrowser
            poster = RedditPosterBrowser()
            try:
                comment = await poster.post_comment(mention.url, req.text)
            finally:
                await poster.close()

        return {"message": "Comment posted successfully", **comment}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to post comment: {str(e)}")


@router.get("/auth-status")
async def reddit_auth_status(db: AsyncSession = Depends(get_db)):
    from app.core.login_status import is_logged_in
    logged_in = await is_logged_in(db, "reddit")
    if logged_in:
        return {"authenticated": True, "method": "browser", "note": "Logged in."}
    return {"authenticated": False, "error": "Not logged in. Go to Profile and click Login."}


@router.post("/browser-login")
async def browser_login(db: AsyncSession = Depends(get_db)):
    """Open browser for manual Reddit login — user fills credentials themselves."""
    import subprocess as sp

    from app.services.reddit_poster_browser import _SCRIPT_PATH
    script_path = _SCRIPT_PATH
    args_json = json.dumps({
        "username": "",
        "password": "",
        "post_url": "",
        "text": "",
        "login_only": True,
    })

    loop = asyncio.get_running_loop()
    from concurrent.futures import ThreadPoolExecutor
    executor = ThreadPoolExecutor(max_workers=1)

    def _run():
        proc = sp.Popen(
            [sys.executable, script_path, args_json],
            stdout=sp.PIPE, stderr=sp.PIPE,
        )
        stdout, stderr = proc.communicate(timeout=900)
        return proc.returncode, stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")

    try:
        returncode, stdout, stderr = await loop.run_in_executor(executor, _run)

        # Find JSON result
        json_line = None
        for line in reversed(stdout.strip().split("\n")):
            if line.strip().startswith("{"):
                json_line = line.strip()
                break

        if returncode == 0 and json_line:
            data = json.loads(json_line)
            from app.core.login_status import set_logged_in
            await set_logged_in(db, "reddit", True)
            return {"message": "Login successful! Session saved.", **data}
        elif json_line:
            data = json.loads(json_line)
            raise HTTPException(status_code=400, detail=data.get("error", "Login failed"))
        else:
            raise HTTPException(status_code=500, detail=f"Login process failed: {stderr[:300] or stdout[:300]}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RunAgentRequest(BaseModel):
    max_posts: int = 5
    delay_seconds: int = 120
    dry_run: bool = False
    mode: str = "auto"  # "api", "browser", or "auto"


@router.post("/agent/run")
async def run_agent(
    req: RunAgentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Run the Reddit posting agent — generates responses and posts them"""
    from app.services.reddit_agent import RedditAgent

    try:
        agent = RedditAgent(delay_between_posts=req.delay_seconds, mode=req.mode)
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
    mode: str = "auto",
):
    """Run the agent with live SSE log streaming"""
    from app.services.reddit_agent import RedditAgent

    async def event_generator():
        log_queue: asyncio.Queue = asyncio.Queue()

        async def on_event(event: dict):
            await log_queue.put(event)

        async def run_agent_task():
            async with AsyncSessionLocal() as db:
                try:
                    agent = RedditAgent(delay_between_posts=delay_seconds, mode=mode)
                    stats = await agent.run(
                        db, max_posts=max_posts, dry_run=dry_run, on_event=on_event
                    )
                    await log_queue.put({"type": "result", "stats": stats})
                except Exception as e:
                    await log_queue.put({"type": "error", "message": str(e)})
                finally:
                    await log_queue.put(None)  # Signal done

        # Start agent in background
        task = asyncio.create_task(run_agent_task())

        try:
            while True:
                if await request.is_disconnected():
                    task.cancel()
                    break

                try:
                    event = await asyncio.wait_for(log_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    # Send keepalive
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
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/agent/pending")
async def get_pending_posts(db: AsyncSession = Depends(get_db)):
    """Get count of threads not yet processed by the agent"""
    result = await db.execute(
        select(RedditMention)
        .where(RedditMention.agent_posted == False)
        .where(RedditMention.is_relevant == True)
    )
    threads = result.scalars().all()
    return {"pending_count": len(threads)}
