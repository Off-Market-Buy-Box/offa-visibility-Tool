from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from app.models.smart_task import SmartTask, TaskStatus
from app.schemas.smart_task import SmartTaskCreate, SmartTaskUpdate

class SmartTaskService:
    """Service for managing smart tasks"""
    
    @staticmethod
    async def create_task(db: AsyncSession, task_data: SmartTaskCreate) -> SmartTask:
        task = SmartTask(**task_data.model_dump())
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def get_tasks(
        db: AsyncSession, 
        status: Optional[TaskStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[SmartTask]:
        query = select(SmartTask)
        
        if status:
            query = query.where(SmartTask.status == status)
        
        query = query.offset(skip).limit(limit).order_by(SmartTask.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_task(db: AsyncSession, task_id: int) -> Optional[SmartTask]:
        result = await db.execute(select(SmartTask).where(SmartTask.id == task_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_task(
        db: AsyncSession, 
        task_id: int, 
        task_data: SmartTaskUpdate
    ) -> Optional[SmartTask]:
        task = await SmartTaskService.get_task(db, task_id)
        
        if task:
            for key, value in task_data.model_dump(exclude_unset=True).items():
                setattr(task, key, value)
            
            if task_data.status == TaskStatus.COMPLETED and not task.completed_at:
                task.completed_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(task)
        
        return task
    
    @staticmethod
    async def auto_generate_tasks(db: AsyncSession) -> List[SmartTask]:
        """Auto-generate tasks based on SEO data"""
        tasks = []
        
        # Example: Generate task for keywords with declining rankings
        # This would be expanded with actual logic
        
        return tasks
