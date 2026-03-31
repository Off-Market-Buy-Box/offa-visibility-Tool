import { api } from '@/lib/api';

export interface FacebookPost {
    id: number;
    post_id: string;
    title: string;
    snippet: string | null;
    content: string | null;
    url: string;
    author: string | null;
    source: string;
    keywords_matched: string | null;
    is_relevant: boolean;
    created_at: string;
    posted_at: string | null;
}

export interface MonitorFacebookResponse {
    message: string;
    queries_searched: number;
    total_found: number;
    new_saved: number;
}

export const facebookService = {
    monitor: async (keywords?: string[]): Promise<MonitorFacebookResponse> => {
        const params = keywords ? `?${keywords.map(k => `keywords=${k}`).join('&')}` : '';
        return api.post<MonitorFacebookResponse>(`/facebook/monitor${params}`, {});
    },

    getPosts: async (): Promise<FacebookPost[]> => {
        return api.get<FacebookPost[]>('/facebook/posts');
    },

    getById: async (id: number): Promise<FacebookPost> => {
        return api.get<FacebookPost>(`/facebook/posts/${id}`);
    },

    delete: async (id: number): Promise<void> => {
        return api.delete(`/facebook/posts/${id}`);
    },

    fetchContent: async (id: number): Promise<{ content: string | null; success: boolean; message?: string }> => {
        return api.post(`/facebook/posts/${id}/fetch-content`, {});
    },

    postComment: async (postId: number, text: string): Promise<{ message: string; comment_url: string; posted: boolean }> => {
        return api.post(`/facebook/post-comment`, { post_id: postId, text });
    },

    getAuthStatus: async (): Promise<{ authenticated: boolean; email?: string; error?: string }> => {
        return api.get(`/facebook/auth-status`);
    },

    browserLogin: async (): Promise<{ message: string; logged_in: boolean }> => {
        return api.post(`/facebook/browser-login`, {});
    },

    runAgentStream: (
        maxPosts: number,
        delaySec: number,
        dryRun: boolean,
        onEvent: (event: any) => void,
        onDone: () => void,
        onError: (err: string) => void,
    ): (() => void) => {
        const params = new URLSearchParams({
            max_posts: String(maxPosts),
            delay_seconds: String(delaySec),
            dry_run: String(dryRun),
        });
        const url = `http://localhost:8000/api/v1/facebook/agent/stream?${params}`;
        const eventSource = new EventSource(url);

        eventSource.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                onEvent(data);
            } catch { /* ignore */ }
        };

        eventSource.onerror = () => {
            eventSource.close();
            onDone();
        };

        return () => { eventSource.close(); };
    },

    getPendingCount: async (): Promise<{ pending_count: number }> => {
        return api.get(`/facebook/agent/pending`);
    },
};
