import { useCreateItem, useItemTypes, useItems, useUpdateItem } from '@/api/hooks';
import type { ItemCreate, ItemUpdate, ProjectNode } from '@/api/types';
import type { View } from '@/components/layout/types';

import { DocumentView } from './DocumentView';
import { GridView } from './GridView';

export function RequirementsView({
  project,
  view,
  onOpenItem,
}: {
  project: ProjectNode | undefined;
  view: View;
  onOpenItem: (id: string) => void;
}) {
  const projectId = project?.id;
  const { data: items = [], isLoading } = useItems(projectId);
  const { data: itemTypes = [] } = useItemTypes(projectId);
  const updateItem = useUpdateItem(projectId);
  const createItem = useCreateItem(projectId);

  if (!project) return <div className="text-mut-700 p-8">Select an IP from the hierarchy.</div>;
  if (isLoading) return <div className="text-mut-700 p-8">Loading requirements…</div>;

  const requirements = items.filter((i) => i.base_kind === 'requirement');
  const requirementType = itemTypes.find((t) => t.base_kind === 'requirement');

  const onUpdate = (id: string, patch: ItemUpdate) => updateItem.mutate({ id, patch });
  const onCreate = (payload: ItemCreate) => createItem.mutate(payload);

  if (view === 'grid') {
    return <GridView requirements={requirements} onUpdate={onUpdate} onOpenItem={onOpenItem} />;
  }
  return (
    <DocumentView
      projectName={project.name}
      requirements={requirements}
      requirementType={requirementType}
      onUpdate={onUpdate}
      onCreate={onCreate}
      onOpenItem={onOpenItem}
      projectId={project.id}
    />
  );
}
