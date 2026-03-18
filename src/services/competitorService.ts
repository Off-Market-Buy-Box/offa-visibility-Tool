import { api } from '@/lib/api';

export interface Competitor {
  id: number;
  domain: string;
  name: string | null;
  visibility_score: number;
  avg_position: number;
  total_keywords: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateCompetitorData {
  domain: string;
  name?: string;
}

export const competitorService = {
  // Get all competitors
  getAll: async (): Promise<Competitor[]> => {
    return api.get<Competitor[]>('/competitors/');
  },

  // Create new competitor
  create: async (data: CreateCompetitorData): Promise<Competitor> => {
    return api.post<Competitor>('/competitors/', data);
  },

  // Update competitor
  update: async (id: number, data: Partial<CreateCompetitorData>): Promise<Competitor> => {
    return api.patch<Competitor>(`/competitors/${id}`, data);
  },
};
