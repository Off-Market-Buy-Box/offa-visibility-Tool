"""
Credential resolver: checks DB first, falls back to .env settings.
Usage:
    creds = await get_platform_credentials("twitter", db)
    email = creds.get("email", "")
"""
import json
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.platform_credential import PlatformCredential
from app.core.config import settings


# Maps platform field names to Settings attribute names
_ENV_MAP = {
    "reddit": {
        "username": "REDDIT_USERNAME",
        "password": "REDDIT_PASSWORD",
    },
    "linkedin": {
        "email": "LINKEDIN_EMAIL",
        "password": "LINKEDIN_PASSWORD",
    },
    "twitter": {
        "email": "TWITTER_EMAIL",
        "password": "TWITTER_PASSWORD",
    },
    "facebook": {
        "email": "FACEBOOK_EMAIL",
        "password": "FACEBOOK_PASSWORD",
    },
}


async def get_platform_credentials(platform: str, db: AsyncSession) -> Dict[str, str]:
    """
    Get credentials for a platform.
    Priority: DB-stored values > .env values
    Returns a dict of field_name -> value.
    """
    result_creds: Dict[str, str] = {}
    env_fields = _ENV_MAP.get(platform, {})

    # Start with .env values
    for field, env_attr in env_fields.items():
        result_creds[field] = getattr(settings, env_attr, "") or ""

    # Override with DB values if present
    try:
        result = await db.execute(
            select(PlatformCredential).where(PlatformCredential.platform == platform)
        )
        cred = result.scalar_one_or_none()
        if cred:
            stored = json.loads(cred.credentials)
            for field in env_fields:
                db_val = stored.get(field, "")
                if db_val:
                    result_creds[field] = db_val
    except Exception:
        pass  # Fall back to .env values

    return result_creds
