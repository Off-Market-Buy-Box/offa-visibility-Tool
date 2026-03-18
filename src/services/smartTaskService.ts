import { api } from '@/lib/api';

export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface SmartTask {
  id: number;
  title: string;
  description: string | null;
  task_type: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  assigned_to: string | null;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateTaskData {
  title: string;
  description?: string;
  task_type?: string;
  priority?: TaskPriority;
  assigned_to?: string;
  due_date?: string;
}

export interface UpdateTaskData {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  assigned_to?: string;
  due_date?: string;
}

export const smartTaskService = {
  // Get all tasks
  getAll: async (status?: TaskStatus): Promise<SmartTask[]> => {
    const query = status ? `?status=${status}` : '';
    return api.get<SmartTask[]>(`/smart-tasks/${query}`);
  },

  // Get single task
  getById: async (id: number): Promise<SmartTask> => {
    return api.get<SmartTask>(`/smart-tasks/${id}`);
  },

  // Create new task
  create: async (data: CreateTaskData): Promise<SmartTask> => {
    return api.post<SmartTask>('/smart-tasks/', data);
  },

  // Update task
  update: async (id: number, data: UpdateTaskData): Promise<SmartTask> => {
    return api.patch<SmartTask>(`/smart-tasks/${id}`, data);
  },

  // Auto-generate tasks
  autoGenerate: async (): Promise<{ tasks_generated: number; tasks: SmartTask[] }> => {
    return api.post('/smart-tasks/auto-generate', {});
  },
};
