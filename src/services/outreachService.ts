import { api } from '@/lib/api';

export interface OutreachTarget {
    id: number;
    platform: string;
    name: string;
    url: string;
    enabled: boolean;
    last_posted_at: string | null;
    total_posts: number;
    created_at: string;
}

export interface OutreachPost {
    id: number;
    target_id: number;
    platform: string;
    title: string;
    content: string;
    status: string;
    error: string | null;
    posted_at: string | null;
    created_at: string;
}

export interface OutreachStatus {
    running: boolean;
    last_run_at: string | null;
    next_run_at: string | null;
    total_posted: number;
    total_errors: number;
    current_action: string | null;
    interval_hours: number;
    enabled_targets: number;
}

export const outreachService = {
    getStatus: () => api.get<OutreachStatus>('/outreach/status'),
    start: () => api.post<{ message: string }>('/outreach/start', {}),
    stop: () => api.post<{ message: string }>('/outreach/stop', {}),
    updateSettings: (settings: { interval_hours?: number }) =>
        api.put<OutreachStatus>('/outreach/settings', settings),
    getTargets: () => api.get<OutreachTarget[]>('/outreach/targets'),
    addTarget: (data: { name: string; url: string }) =>
        api.post<OutreachTarget>('/outreach/targets', data),
    addDefaults: () => api.post<{ added: number }>('/outreach/targets/add-defaults', {}),
    updateTarget: (id: number, data: { enabled?: boolean; name?: string }) =>
        api.put(`/outreach/targets/${id}`, data),
    deleteTarget: (id: number) => api.delete(`/outreach/targets/${id}`),
    getPosts: (limit = 50) => api.get<OutreachPost[]>(`/outreach/posts?limit=${limit}`),
    generatePreview: () => api.post<{ title: string; body: string }>('/outreach/generate-preview', {}),
    run: () => api.post<{ message: string }>('/outreach/run', {}),
    testBrowser: () => api.post<{ ok: boolean; error?: string; message?: string }>('/outreach/test-browser', {}),
};
