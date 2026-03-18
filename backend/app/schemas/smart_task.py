from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.smart_task import TaskStatus, TaskPriority

class SmartTaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: Optional[str] = None
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM

class SmartTaskCreate(SmartTaskBase):
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None

class SmartTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None

class SmartTaskResponse(SmartTaskBase):
    id: int
    status: TaskStatus
    assigned_to: Optional[str]
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
