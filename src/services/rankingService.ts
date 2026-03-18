import { api } from '@/lib/api';

export interface Ranking {
  id: number;
  keyword_id: number;
  position: number;
  url: string | null;
  title: string | null;
  snippet: string | null;
  extra_data: Record<string, unknown>;
  checked_at: string;
}

export interface CheckRankingResponse {
  message: string;
  total_results: number;
  domain_found_count: number;
}

export const rankingService = {
  // Check ranking for a keyword
  checkRanking: async (keywordId: number): Promise<CheckRankingResponse> => {
    return api.post<CheckRankingResponse>(`/rankings/check/${keywordId}`, {});
  },

  // Get latest search results for a keyword
  getKeywordResults: async (keywordId: number): Promise<Ranking[]> => {
    return api.get<Ranking[]>(`/rankings/${keywordId}/results`);
  },

  // Get rankings for a keyword
  getByKeyword: async (keywordId: number): Promise<Ranking[]> => {
    return api.get<Ranking[]>(`/rankings/?keyword_id=${keywordId}`);
  },
};
