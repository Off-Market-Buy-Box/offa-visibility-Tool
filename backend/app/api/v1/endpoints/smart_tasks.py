from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.schemas.smart_task import SmartTaskCreate, SmartTaskUpdate, SmartTaskResponse
from app.services.smart_task_service import SmartTaskService
from app.models.smart_task import TaskStatus

router = APIRouter()

@router.post("/", response_model=SmartTaskResponse)
async def create_task(
    task: SmartTaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new smart task"""
    return await SmartTaskService.create_task(db, task)

@router.get("/", response_model=List[SmartTaskResponse])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all tasks, optionally filtered by status"""
    return await SmartTaskService.get_tasks(db, status, skip, limit)

@router.get("/{task_id}", response_model=SmartTaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific task"""
    task = await SmartTaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}", response_model=SmartTaskResponse)
async def update_task(
    task_id: int,
    task_update: SmartTaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a task"""
    task = await SmartTaskService.update_task(db, task_id, task_update)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/auto-generate")
async def auto_generate_tasks(db: AsyncSession = Depends(get_db)):
    """Auto-generate tasks based on SEO insights"""
    tasks = await SmartTaskService.auto_generate_tasks(db)
    return {"tasks_generated": len(tasks), "tasks": tasks}
