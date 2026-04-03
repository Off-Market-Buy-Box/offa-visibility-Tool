import { api } from '@/lib/api';

export interface PlatformStatus {
    enabled: boolean;
    last_scan: string | null;
    last_comment: string | null;
    total_commented: number;
    total_scanned: number;
    errors: number;
}

export interface RateLimitInfo {
    daily_limit: number | null;
    used_24h: number;
    remaining_24h: number | null;
    delay_between_posts: number;
    in_cooldown: boolean;
    cooldown_until: string | null;
    consecutive_failures: number;
}

export interface AutomationStatus {
    running: boolean;
    current_platform: string | null;
    current_action: string | null;
    cycle_count: number;
    last_cycle_at: string | null;
    platforms: Record<string, PlatformStatus>;
    rate_limits: Record<string, RateLimitInfo>;
    delay_between_platforms: number;
    delay_between_cycles: number;
    max_posts_per_run: number;
}

export interface AutomationLog {
    id: number;
    platform: string;
    action: string;
    posts_found: number;
    posts_commented: number;
    errors: number;
    details: any;
    created_at: string;
}

export interface CommentedPost {
    platform: string;
    id: number;
    title: string;
    url: string;
    author: string | null;
    posted_at: string | null;
}

export const automationService = {
    getStatus: () => api.get<AutomationStatus>('/automation/status'),
    start: () => api.post<{ message: string }>('/automation/start', {}),
    stop: () => api.post<{ message: string }>('/automation/stop', {}),
    updateSettings: (settings: Partial<AutomationStatus>) =>
        api.put<AutomationStatus>('/automation/settings', settings),
    getLogs: (platform?: string, limit = 50) => {
        const params = new URLSearchParams({ limit: String(limit) });
        if (platform) params.set('platform', platform);
        return api.get<AutomationLog[]>(`/automation/logs?${params}`);
    },
    getStats: () => api.get<Record<string, { total_found: number; total_commented: number; total_errors: number; total_runs: number }>>('/automation/stats'),
    getCommentedPosts: (platform?: string, limit = 50) => {
        const params = new URLSearchParams({ limit: String(limit) });
        if (platform) params.set('platform', platform);
        return api.get<CommentedPost[]>(`/automation/commented-posts?${params}`);
    },
    clearAll: () => api.post<{ message: string }>('/automation/clear-all', {}),
};
