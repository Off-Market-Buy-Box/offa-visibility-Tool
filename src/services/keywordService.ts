import { api } from '@/lib/api';

export interface Keyword {
  id: number;
  keyword: string;
  domain: string;
  is_active: boolean;
  best_rank?: number | null;  // Best (lowest) position where domain appears
  created_at: string;
  updated_at: string;
}

export interface CreateKeywordData {
  keyword: string;
  domain: string;
}

export const keywordService = {
  // Get all keywords
  getAll: async (): Promise<Keyword[]> => {
    return api.get<Keyword[]>('/keywords/');
  },

  // Get single keyword
  getById: async (id: number): Promise<Keyword> => {
    return api.get<Keyword>(`/keywords/${id}`);
  },

  // Create new keyword
  create: async (data: CreateKeywordData): Promise<Keyword> => {
    return api.post<Keyword>('/keywords/', data);
  },

  // Update keyword
  update: async (id: number, data: Partial<CreateKeywordData>): Promise<Keyword> => {
    return api.patch<Keyword>(`/keywords/${id}`, data);
  },

  // Delete keyword
  delete: async (id: number): Promise<void> => {
    return api.delete(`/keywords/${id}`);
  },
};
