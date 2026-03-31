import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict
from app.core.database import get_db
from app.models.platform_credential import PlatformCredential

router = APIRouter()

PLATFORM_FIELDS = {
    "reddit": ["username", "password"],
    "linkedin": ["email", "password"],
    "twitter": ["email", "password"],
    "facebook": ["email", "password"],
}


class CredentialUpdate(BaseModel):
    platform: str
    credentials: Dict[str, str]


class CredentialResponse(BaseModel):
    platform: str
    fields: list[str]
    has_values: Dict[str, bool]


@router.get("/", response_model=list[CredentialResponse])
async def get_all_credentials(db: AsyncSession = Depends(get_db)):
    """Get all platform credential status (which fields are set, without exposing values)"""
    results = []
    for platform, fields in PLATFORM_FIELDS.items():
        result = await db.execute(
            select(PlatformCredential).where(PlatformCredential.platform == platform)
        )
        cred = result.scalar_one_or_none()
        has_values = {}
        if cred:
            try:
                stored = json.loads(cred.credentials)
            except json.JSONDecodeError:
                stored = {}
            has_values = {f: bool(stored.get(f, "")) for f in fields}
        else:
            has_values = {f: False for f in fields}
        results.append(CredentialResponse(platform=platform, fields=fields, has_values=has_values))
    return results


@router.get("/{platform}")
async def get_credential(platform: str, db: AsyncSession = Depends(get_db)):
    """Get credential values for a platform (masked)"""
    if platform not in PLATFORM_FIELDS:
        return {"error": f"Unknown platform: {platform}"}
    result = await db.execute(
        select(PlatformCredential).where(PlatformCredential.platform == platform)
    )
    cred = result.scalar_one_or_none()
    if not cred:
        return {"platform": platform, "credentials": {f: "" for f in PLATFORM_FIELDS[platform]}}
    try:
        stored = json.loads(cred.credentials)
    except json.JSONDecodeError:
        stored = {}
    # Mask values: show first 3 chars + *** for non-empty values
    masked = {}
    for f in PLATFORM_FIELDS[platform]:
        val = stored.get(f, "")
        if val and len(val) > 3:
            masked[f] = val[:3] + "•" * min(len(val) - 3, 10)
        elif val:
            masked[f] = "•" * len(val)
        else:
            masked[f] = ""
    return {"platform": platform, "credentials": masked}


@router.put("/{platform}")
async def update_credential(platform: str, req: CredentialUpdate, db: AsyncSession = Depends(get_db)):
    """Save or update credentials for a platform"""
    if platform not in PLATFORM_FIELDS:
        return {"error": f"Unknown platform: {platform}"}

    result = await db.execute(
        select(PlatformCredential).where(PlatformCredential.platform == platform)
    )
    cred = result.scalar_one_or_none()

    # Merge: only update fields that are non-empty in the request
    existing = {}
    if cred:
        try:
            existing = json.loads(cred.credentials)
        except json.JSONDecodeError:
            existing = {}

    for key, val in req.credentials.items():
        if key in PLATFORM_FIELDS[platform] and val.strip():
            existing[key] = val.strip()

    if cred:
        cred.credentials = json.dumps(existing)
    else:
        cred = PlatformCredential(platform=platform, credentials=json.dumps(existing))
        db.add(cred)

    await db.commit()
    return {"message": f"{platform} credentials saved", "platform": platform}


@router.delete("/{platform}")
async def delete_credential(platform: str, db: AsyncSession = Depends(get_db)):
    """Delete all credentials for a platform"""
    result = await db.execute(
        select(PlatformCredential).where(PlatformCredential.platform == platform)
    )
    cred = result.scalar_one_or_none()
    if cred:
        await db.delete(cred)
        await db.commit()
    return {"message": f"{platform} credentials cleared"}
