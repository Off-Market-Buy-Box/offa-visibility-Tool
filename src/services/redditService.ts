import { api } from '@/lib/api';

export interface RedditMention {
  id: number;
  post_id: string;
  subreddit: string;
  title: string;
  author: string | null;
  content: string | null;
  url: string | null;
  score: number;
  num_comments: number;
  sentiment_score: number;
  keywords_matched: string | null;
  is_relevant: boolean;
  created_at: string;
  posted_at: string | null;
}

export interface MonitorSubredditResponse {
  subreddit: string;
  mentions_found: number;
  new_mentions_saved: number;
}

export interface RedditComment {
  id: string;
  author: string;
  body: string;
  score: number;
  depth: number;
  created_at: string;
}

export interface MonitorRealEstateResponse {
  message: string;
  subreddits_checked: number;
  total_mentions_found: number;
  new_mentions_saved: number;
  offa_mentions: number;
}

export const redditService = {
  // Monitor a subreddit
  monitor: async (subreddit: string, keywords: string[]): Promise<MonitorSubredditResponse> => {
    return api.post<MonitorSubredditResponse>(
      `/reddit/monitor?subreddit=${subreddit}&${keywords.map(k => `keywords=${k}`).join('&')}`,
      {}
    );
  },

  // Monitor all real estate subreddits for offa.com mentions
  monitorRealEstate: async (): Promise<MonitorRealEstateResponse> => {
    return api.post<MonitorRealEstateResponse>('/reddit/monitor-real-estate', {});
  },

  // Get all mentions
  getMentions: async (subreddit?: string): Promise<RedditMention[]> => {
    const query = subreddit ? `?subreddit=${subreddit}` : '';
    return api.get<RedditMention[]>(`/reddit/mentions${query}`);
  },

  // Get single mention
  getById: async (id: number): Promise<RedditMention> => {
    return api.get<RedditMention>(`/reddit/mentions/${id}`);
  },

  // Get comments for a post
  getComments: async (mentionId: number): Promise<{ post_id: string; comments: RedditComment[] }> => {
    return api.get<{ post_id: string; comments: RedditComment[] }>(`/reddit/mentions/${mentionId}/comments`);
  },

  // Post a comment to Reddit (mode: "api", "browser", or "auto")
  postComment: async (mentionId: number, text: string, mode: string = "auto"): Promise<{ message: string; comment_id?: string; comment_url: string; posted: boolean; method?: string }> => {
    return api.post(`/reddit/post-comment`, { mention_id: mentionId, text, mode });
  },

  // Check Reddit auth status
  getAuthStatus: async (): Promise<{ authenticated: boolean; username?: string; error?: string }> => {
    return api.get(`/reddit/auth-status`);
  },

  // Run the posting agent (mode: "api", "browser", or "auto")
  runAgent: async (maxPosts: number = 5, delaySeconds: number = 120, dryRun: boolean = false, mode: string = "auto"): Promise<{
    message: string;
    threads_found: number;
    responses_generated: number;
    comments_posted: number;
    errors: string[];
    mode: string;
    posts: Array<{ id: number; title: string; subreddit: string; status: string; response_preview?: string; comment_url?: string; error?: string }>;
  }> => {
    return api.post(`/reddit/agent/run`, { max_posts: maxPosts, delay_seconds: delaySeconds, dry_run: dryRun, mode });
  },

  // Run agent with live SSE streaming
  runAgentStream: (
    maxPosts: number,
    delaySeconds: number,
    dryRun: boolean,
    mode: string,
    onLog: (event: any) => void,
    onDone: () => void,
    onError: (err: string) => void,
  ): (() => void) => {
    const params = new URLSearchParams({
      max_posts: String(maxPosts),
      delay_seconds: String(delaySeconds),
      dry_run: String(dryRun),
      mode,
    });
    const url = `http://localhost:8000/api/v1/reddit/agent/stream?${params}`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        onLog(data);
        if (data.type === "result" || data.type === "error") {
          eventSource.close();
          onDone();
        }
      } catch {
        // ignore parse errors
      }
    };

    eventSource.onerror = () => {
      onError("Connection lost");
      eventSource.close();
      onDone();
    };

    // Return cleanup function
    return () => eventSource.close();
  },

  // Get pending posts count
  getPendingCount: async (): Promise<{ pending_count: number }> => {
    return api.get(`/reddit/agent/pending`);
  },

  // Open browser for manual Reddit login (first-time CAPTCHA solve)
  browserLogin: async (): Promise<{ message: string; logged_in?: boolean }> => {
    return api.post(`/reddit/browser-login`, {});
  },
};
