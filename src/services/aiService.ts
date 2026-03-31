import { api } from '@/lib/api';

export interface AIMetadata {
  id: number;
  reddit_mention_id: number | null;
  linkedin_post_id: number | null;
  twitter_post_id: number | null;
  facebook_post_id: number | null;
  intent: string | null;
  main_topic: string | null;
  summary: string | null;
  pain_points: string[];
  opportunities: string[];
  keywords: string[];
  sentiment: string | null;
  created_at: string;
}

export interface GeneratedResponse {
  id: number;
  reddit_mention_id: number | null;
  linkedin_post_id: number | null;
  twitter_post_id: number | null;
  facebook_post_id: number | null;
  response_type: string;
  content: string;
  created_at: string;
}

export const aiService = {
  // Reddit AI
  analyze: async (mentionId: number): Promise<AIMetadata> => {
    return api.post<AIMetadata>('/ai/analyze', { mention_id: mentionId });
  },

  getMetadata: async (mentionId: number): Promise<AIMetadata | null> => {
    try {
      const result = await api.get<AIMetadata>(`/ai/metadata/${mentionId}`);
      if (!result || Array.isArray(result) || !result.id) return null;
      return result;
    } catch {
      return null;
    }
  },

  generateResponse: async (mentionId: number): Promise<GeneratedResponse> => {
    return api.post<GeneratedResponse>('/ai/generate-response', { mention_id: mentionId });
  },

  generateBlog: async (mentionIds: number[], topic?: string): Promise<GeneratedResponse> => {
    return api.post<GeneratedResponse>('/ai/generate-blog', { mention_ids: mentionIds, topic });
  },

  getResponses: async (mentionId: number): Promise<GeneratedResponse[]> => {
    return api.get<GeneratedResponse[]>(`/ai/responses/${mentionId}`);
  },

  // LinkedIn AI
  analyzeLinkedIn: async (postId: number): Promise<AIMetadata> => {
    return api.post<AIMetadata>('/ai/linkedin/analyze', { post_id: postId });
  },

  getLinkedInMetadata: async (postId: number): Promise<AIMetadata | null> => {
    try {
      const result = await api.get<AIMetadata>(`/ai/linkedin/metadata/${postId}`);
      if (!result || Array.isArray(result) || !result.id) return null;
      return result;
    } catch {
      return null;
    }
  },

  generateLinkedInResponse: async (postId: number): Promise<GeneratedResponse> => {
    return api.post<GeneratedResponse>('/ai/linkedin/generate-response', { post_id: postId });
  },

  getLinkedInResponses: async (postId: number): Promise<GeneratedResponse[]> => {
    return api.get<GeneratedResponse[]>(`/ai/linkedin/responses/${postId}`);
  },

  // Twitter AI
  analyzeTwitter: async (postId: number): Promise<AIMetadata> => {
    return api.post<AIMetadata>('/ai/twitter/analyze', { post_id: postId });
  },

  getTwitterMetadata: async (postId: number): Promise<AIMetadata | null> => {
    try {
      const result = await api.get<AIMetadata>(`/ai/twitter/metadata/${postId}`);
      if (!result || Array.isArray(result) || !result.id) return null;
      return result;
    } catch {
      return null;
    }
  },

  generateTwitterResponse: async (postId: number): Promise<GeneratedResponse> => {
    return api.post<GeneratedResponse>('/ai/twitter/generate-response', { post_id: postId });
  },

  getTwitterResponses: async (postId: number): Promise<GeneratedResponse[]> => {
    return api.get<GeneratedResponse[]>(`/ai/twitter/responses/${postId}`);
  },

  // Facebook AI
  analyzeFacebook: async (postId: number): Promise<AIMetadata> => {
    return api.post<AIMetadata>('/ai/facebook/analyze', { post_id: postId });
  },

  getFacebookMetadata: async (postId: number): Promise<AIMetadata | null> => {
    try {
      const result = await api.get<AIMetadata>(`/ai/facebook/metadata/${postId}`);
      if (!result || Array.isArray(result) || !result.id) return null;
      return result;
    } catch {
      return null;
    }
  },

  generateFacebookResponse: async (postId: number): Promise<GeneratedResponse> => {
    return api.post<GeneratedResponse>('/ai/facebook/generate-response', { post_id: postId });
  },

  getFacebookResponses: async (postId: number): Promise<GeneratedResponse[]> => {
    return api.get<GeneratedResponse[]>(`/ai/facebook/responses/${postId}`);
  },
};
