import { api } from '@/lib/api';

export interface TwitterPost {
    id: number;
    tweet_id: string;
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

export interface MonitorTwitterResponse {
    message: string;
    queries_searched: number;
    total_found: number;
    new_saved: number;
}

export const twitterService = {
    monitor: async (keywords?: string[]): Promise<MonitorTwitterResponse> => {
        const params = keywords ? `?${keywords.map(k => `keywords=${k}`).join('&')}` : '';
        return api.post<MonitorTwitterResponse>(`/twitter/monitor${params}`, {});
    },

    getPosts: async (): Promise<TwitterPost[]> => {
        return api.get<TwitterPost[]>('/twitter/posts');
    },

    getById: async (id: number): Promise<TwitterPost> => {
        return api.get<TwitterPost>(`/twitter/posts/${id}`);
    },

    delete: async (id: number): Promise<void> => {
        return api.delete(`/twitter/posts/${id}`);
    },

    fetchContent: async (id: number): Promise<{ content: string | null; success: boolean; message?: string }> => {
        return api.post(`/twitter/posts/${id}/fetch-content`, {});
    },

    postComment: async (postId: number, text: string): Promise<{ message: string; comment_url: string; posted: boolean }> => {
        return api.post(`/twitter/post-comment`, { post_id: postId, text });
    },

    getAuthStatus: async (): Promise<{ authenticated: boolean; email?: string; error?: string }> => {
        return api.get(`/twitter/auth-status`);
    },

    browserLogin: async (): Promise<{ message: string; logged_in: boolean }> => {
        return api.post(`/twitter/browser-login`, {});
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
        const url = `http://localhost:8000/api/v1/twitter/agent/stream?${params}`;
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
        return api.get(`/twitter/agent/pending`);
    },
};
