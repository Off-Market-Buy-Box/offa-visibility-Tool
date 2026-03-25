import { api } from '@/lib/api';

export interface LinkedInPost {
  id: number;
  result_id: string;
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

export interface MonitorLinkedInResponse {
  message: string;
  queries_searched: number;
  total_found: number;
  new_saved: number;
}

export const linkedinService = {
  monitor: async (keywords?: string[]): Promise<MonitorLinkedInResponse> => {
    const params = keywords ? `?${keywords.map(k => `keywords=${k}`).join('&')}` : '';
    return api.post<MonitorLinkedInResponse>(`/linkedin/monitor${params}`, {});
  },

  getPosts: async (): Promise<LinkedInPost[]> => {
    return api.get<LinkedInPost[]>('/linkedin/posts');
  },

  getById: async (id: number): Promise<LinkedInPost> => {
    return api.get<LinkedInPost>(`/linkedin/posts/${id}`);
  },

  delete: async (id: number): Promise<void> => {
    return api.delete(`/linkedin/posts/${id}`);
  },

  fetchContent: async (id: number): Promise<{ content: string | null; success: boolean; message?: string }> => {
    return api.post(`/linkedin/posts/${id}/fetch-content`, {});
  },

  // Post a comment to LinkedIn (browser mode)
  postComment: async (postId: number, text: string): Promise<{ message: string; comment_url: string; posted: boolean }> => {
    return api.post(`/linkedin/post-comment`, { post_id: postId, text });
  },

  // Check LinkedIn auth status
  getAuthStatus: async (): Promise<{ authenticated: boolean; email?: string; error?: string }> => {
    return api.get(`/linkedin/auth-status`);
  },

  // Open browser for manual LinkedIn login
  browserLogin: async (): Promise<{ message: string; logged_in: boolean }> => {
    return api.post(`/linkedin/browser-login`, {});
  },

  // Run agent (non-streaming)
  runAgent: async (maxPosts: number = 5, delaySec: number = 120, dryRun: boolean = false) => {
    return api.post(`/linkedin/agent/run`, { max_posts: maxPosts, delay_seconds: delaySec, dry_run: dryRun });
  },

  // Run agent with SSE streaming
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
    const url = `http://localhost:8000/api/v1/linkedin/agent/stream?${params}`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        onEvent(data);
      } catch { /* ignore parse errors */ }
    };

    eventSource.onerror = () => {
      eventSource.close();
      onDone();
    };

    return () => { eventSource.close(); };
  },

  // Get pending post count
  getPendingCount: async (): Promise<{ pending_count: number }> => {
    return api.get(`/linkedin/agent/pending`);
  },
};
