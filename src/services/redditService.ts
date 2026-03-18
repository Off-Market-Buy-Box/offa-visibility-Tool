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
};
