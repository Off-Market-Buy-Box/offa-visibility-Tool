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
};
