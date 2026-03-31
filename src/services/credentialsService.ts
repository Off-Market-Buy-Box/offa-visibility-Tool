import { api } from '@/lib/api';

export interface CredentialStatus {
    platform: string;
    fields: string[];
    has_values: Record<string, boolean>;
}

export interface CredentialDetail {
    platform: string;
    credentials: Record<string, string>;
}

export const credentialsService = {
    getAll: async (): Promise<CredentialStatus[]> => {
        return api.get<CredentialStatus[]>('/credentials/');
    },

    get: async (platform: string): Promise<CredentialDetail> => {
        return api.get<CredentialDetail>(`/credentials/${platform}`);
    },

    update: async (platform: string, credentials: Record<string, string>): Promise<{ message: string }> => {
        return api.put<{ message: string }>(`/credentials/${platform}`, { platform, credentials });
    },

    delete: async (platform: string): Promise<{ message: string }> => {
        return api.delete<{ message: string }>(`/credentials/${platform}`);
    },
};
