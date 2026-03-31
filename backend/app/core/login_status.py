from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.platform_credential import PlatformCredential


async def set_logged_in(db: AsyncSession, platform: str, logged_in: bool):
    result = await db.execute(
        select(PlatformCredential).where(PlatformCredential.platform == platform)
    )
    cred = result.scalar_one_or_none()
    if cred:
        cred.logged_in = logged_in
    else:
        cred = PlatformCredential(platform=platform, credentials="{}", logged_in=logged_in)
        db.add(cred)
    await db.commit()


async def is_logged_in(db: AsyncSession, platform: str) -> bool:
    result = await db.execute(
        select(PlatformCredential).where(PlatformCredential.platform == platform)
    )
    cred = result.scalar_one_or_none()
    return cred.logged_in if cred else False
