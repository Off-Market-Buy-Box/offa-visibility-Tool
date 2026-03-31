from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.schemas.ai import (
    AIMetadataResponse,
    GeneratedResponseOut,
    AnalyzeRequest,
    AnalyzeLinkedInRequest,
    AnalyzeTwitterRequest,
    AnalyzeFacebookRequest,
    GenerateResponseRequest,
    GenerateLinkedInResponseRequest,
    GenerateTwitterResponseRequest,
    GenerateFacebookResponseRequest,
    GenerateBlogRequest,
)
from app.services.ai_service import AIService

router = APIRouter()


@router.post("/analyze", response_model=AIMetadataResponse)
async def analyze_post(req: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    """Analyze a Reddit post with AI to extract structured metadata"""
    try:
        service = AIService()
        metadata = await service.analyze_post(db, req.mention_id)
        return metadata
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")


@router.get("/metadata/{mention_id}", response_model=AIMetadataResponse)
async def get_metadata(mention_id: int, db: AsyncSession = Depends(get_db)):
    """Get existing AI metadata for a mention"""
    service = AIService()
    metadata = await service.get_metadata(db, mention_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="No AI analysis found for this post")
    return metadata


@router.post("/generate-response", response_model=GeneratedResponseOut)
async def generate_response(req: GenerateResponseRequest, db: AsyncSession = Depends(get_db)):
    """Generate a natural community response for a Reddit post"""
    try:
        service = AIService()
        response = await service.generate_response(db, req.mention_id)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Response generation failed: {str(e)}")


@router.post("/generate-blog", response_model=GeneratedResponseOut)
async def generate_blog(req: GenerateBlogRequest, db: AsyncSession = Depends(get_db)):
    """Generate a blog post from Reddit discussions"""
    try:
        service = AIService()
        blog = await service.generate_blog(db, req.mention_ids, req.topic)
        return blog
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blog generation failed: {str(e)}")


@router.get("/responses/{mention_id}", response_model=List[GeneratedResponseOut])
async def get_responses(mention_id: int, db: AsyncSession = Depends(get_db)):
    """Get all generated responses for a mention"""
    service = AIService()
    return await service.get_responses(db, mention_id)


# ---- LinkedIn AI endpoints ----

@router.post("/linkedin/analyze", response_model=AIMetadataResponse)
async def analyze_linkedin_post(req: AnalyzeLinkedInRequest, db: AsyncSession = Depends(get_db)):
    """Analyze a LinkedIn post with AI"""
    try:
        service = AIService()
        metadata = await service.analyze_linkedin_post(db, req.post_id)
        return metadata
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")


@router.get("/linkedin/metadata/{post_id}", response_model=AIMetadataResponse)
async def get_linkedin_metadata(post_id: int, db: AsyncSession = Depends(get_db)):
    """Get existing AI metadata for a LinkedIn post"""
    service = AIService()
    metadata = await service.get_linkedin_metadata(db, post_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="No AI analysis found")
    return metadata


@router.post("/linkedin/generate-response", response_model=GeneratedResponseOut)
async def generate_linkedin_response(req: GenerateLinkedInResponseRequest, db: AsyncSession = Depends(get_db)):
    """Generate a professional response for a LinkedIn post"""
    try:
        service = AIService()
        response = await service.generate_linkedin_response(db, req.post_id)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Response generation failed: {str(e)}")


@router.get("/linkedin/responses/{post_id}", response_model=List[GeneratedResponseOut])
async def get_linkedin_responses(post_id: int, db: AsyncSession = Depends(get_db)):
    """Get all generated responses for a LinkedIn post"""
    service = AIService()
    return await service.get_linkedin_responses(db, post_id)


# ---- Twitter/X AI endpoints ----

@router.post("/twitter/analyze", response_model=AIMetadataResponse)
async def analyze_twitter_post(req: AnalyzeTwitterRequest, db: AsyncSession = Depends(get_db)):
    try:
        service = AIService()
        metadata = await service.analyze_twitter_post(db, req.post_id)
        return metadata
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")


@router.get("/twitter/metadata/{post_id}", response_model=AIMetadataResponse)
async def get_twitter_metadata(post_id: int, db: AsyncSession = Depends(get_db)):
    service = AIService()
    metadata = await service.get_twitter_metadata(db, post_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="No AI analysis found")
    return metadata


@router.post("/twitter/generate-response", response_model=GeneratedResponseOut)
async def generate_twitter_response(req: GenerateTwitterResponseRequest, db: AsyncSession = Depends(get_db)):
    try:
        service = AIService()
        response = await service.generate_twitter_response(db, req.post_id)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Response generation failed: {str(e)}")


@router.get("/twitter/responses/{post_id}", response_model=List[GeneratedResponseOut])
async def get_twitter_responses(post_id: int, db: AsyncSession = Depends(get_db)):
    service = AIService()
    return await service.get_twitter_responses(db, post_id)


# ---- Facebook AI endpoints ----

@router.post("/facebook/analyze", response_model=AIMetadataResponse)
async def analyze_facebook_post(req: AnalyzeFacebookRequest, db: AsyncSession = Depends(get_db)):
    try:
        service = AIService()
        metadata = await service.analyze_facebook_post(db, req.post_id)
        return metadata
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")


@router.get("/facebook/metadata/{post_id}", response_model=AIMetadataResponse)
async def get_facebook_metadata(post_id: int, db: AsyncSession = Depends(get_db)):
    service = AIService()
    metadata = await service.get_facebook_metadata(db, post_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="No AI analysis found")
    return metadata


@router.post("/facebook/generate-response", response_model=GeneratedResponseOut)
async def generate_facebook_response(req: GenerateFacebookResponseRequest, db: AsyncSession = Depends(get_db)):
    try:
        service = AIService()
        response = await service.generate_facebook_response(db, req.post_id)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Response generation failed: {str(e)}")


@router.get("/facebook/responses/{post_id}", response_model=List[GeneratedResponseOut])
async def get_facebook_responses(post_id: int, db: AsyncSession = Depends(get_db)):
    service = AIService()
    return await service.get_facebook_responses(db, post_id)
