import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from './client';
import type {
  EarsReport,
  Item,
  ItemCreate,
  ItemDetail,
  ItemType,
  ItemUpdate,
  ProjectNode,
} from './types';

export const queryKeys = {
  projects: ['projects'] as const,
  items: (projectId: string) => ['items', projectId] as const,
  item: (itemId: string) => ['item', itemId] as const,
  itemTypes: (projectId: string) => ['item-types', projectId] as const,
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

function useInvalidateProject(projectId: string | undefined) {
  const client = useQueryClient();
  return () => {
    if (projectId) client.invalidateQueries({ queryKey: queryKeys.items(projectId) });
    client.invalidateQueries({ queryKey: queryKeys.projects });
  };
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

export async function checkEars(text: string): Promise<EarsReport> {
  return api.post<EarsReport>('/api/ears/check', { text });
}
