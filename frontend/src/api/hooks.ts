import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from './client';
import type {
  Dashboard,
  EarsReport,
  Evidence,
  EvidenceCreate,
  Item,
  ItemCreate,
  ItemDetail,
  ItemType,
  ItemUpdate,
  LinkCreate,
  LinkCreated,
  ProjectNode,
  RegressionRun,
} from './types';

export const queryKeys = {
  projects: ['projects'] as const,
  items: (projectId: string) => ['items', projectId] as const,
  item: (itemId: string) => ['item', itemId] as const,
  itemTypes: (projectId: string) => ['item-types', projectId] as const,
  evidence: (projectId: string) => ['evidence', projectId] as const,
  dashboard: (projectId: string) => ['dashboard', projectId] as const,
  runs: (projectId: string) => ['runs', projectId] as const,
};

export function useProjects() {
  return useQuery({
    queryKey: queryKeys.projects,
    queryFn: () => api.get<ProjectNode[]>('/api/projects'),
  });
}

export function useItems(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.items(projectId ?? ''),
    queryFn: () => api.get<Item[]>(`/api/projects/${projectId}/items`),
    enabled: Boolean(projectId),
  });
}

export function useItemTypes(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.itemTypes(projectId ?? ''),
    queryFn: () => api.get<ItemType[]>(`/api/projects/${projectId}/item-types`),
    enabled: Boolean(projectId),
  });
}

export function useItem(itemId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.item(itemId ?? ''),
    queryFn: () => api.get<ItemDetail>(`/api/items/${itemId}`),
    enabled: Boolean(itemId),
  });
}

export function useEvidence(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.evidence(projectId ?? ''),
    queryFn: () => api.get<Evidence[]>(`/api/projects/${projectId}/evidence`),
    enabled: Boolean(projectId),
  });
}

export function useCreateEvidence(projectId: string | undefined) {
  const invalidate = useInvalidateProject(projectId);
  return useMutation({
    mutationFn: (payload: EvidenceCreate) =>
      api.post<Evidence>(`/api/projects/${projectId}/evidence`, payload),
    onSuccess: invalidate,
  });
}

function useInvalidateProject(projectId: string | undefined) {
  const client = useQueryClient();
  return () => {
    if (projectId) {
      client.invalidateQueries({ queryKey: queryKeys.items(projectId) });
      client.invalidateQueries({ queryKey: queryKeys.evidence(projectId) });
    }
    if (projectId) {
      client.invalidateQueries({ queryKey: queryKeys.dashboard(projectId) });
      client.invalidateQueries({ queryKey: queryKeys.runs(projectId) });
    }
    client.invalidateQueries({ queryKey: queryKeys.projects });
    // Any open drawer reflects link/status changes.
    client.invalidateQueries({ queryKey: ['item'] });
  };
}

export function useDashboard(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.dashboard(projectId ?? ''),
    queryFn: () => api.get<Dashboard>(`/api/projects/${projectId}/dashboard`),
    enabled: Boolean(projectId),
  });
}

export function useRuns(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.runs(projectId ?? ''),
    queryFn: () => api.get<RegressionRun[]>(`/api/projects/${projectId}/runs`),
    enabled: Boolean(projectId),
  });
}

export function useIngestRun(projectId: string | undefined) {
  const invalidate = useInvalidateProject(projectId);
  return useMutation({
    mutationFn: (payload: unknown) => api.post<unknown>('/api/regression/runs', payload),
    onSuccess: invalidate,
  });
}

export function useCreateItem(projectId: string | undefined) {
  const invalidate = useInvalidateProject(projectId);
  return useMutation({
    mutationFn: (payload: ItemCreate) => api.post<ItemDetail>('/api/items', payload),
    onSuccess: invalidate,
  });
}

export function useUpdateItem(projectId: string | undefined) {
  const invalidate = useInvalidateProject(projectId);
  return useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: ItemUpdate }) =>
      api.patch<ItemDetail>(`/api/items/${id}`, patch),
    onSuccess: invalidate,
  });
}

export function useCreateLink(projectId: string | undefined) {
  const invalidate = useInvalidateProject(projectId);
  return useMutation({
    mutationFn: (payload: LinkCreate) => api.post<LinkCreated>('/api/links', payload),
    onSuccess: invalidate,
  });
}

export function useClearSuspect(projectId: string | undefined) {
  const invalidate = useInvalidateProject(projectId);
  return useMutation({
    mutationFn: (linkId: string) => api.post<LinkCreated>(`/api/links/${linkId}/clear-suspect`, {}),
    onSuccess: invalidate,
  });
}

export function useDeleteLink(projectId: string | undefined) {
  const invalidate = useInvalidateProject(projectId);
  return useMutation({
    mutationFn: (linkId: string) => api.del<void>(`/api/links/${linkId}`),
    onSuccess: invalidate,
  });
}

export async function checkEars(text: string): Promise<EarsReport> {
  return api.post<EarsReport>('/api/ears/check', { text });
}
