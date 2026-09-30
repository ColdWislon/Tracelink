import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';

import { StatusDot } from '@/components/StatusBadge';
import { cn } from '@/lib/cn';

export interface MentionItem {
  id: string;
  human_id: string;
  title: string;
  base_kind: 'requirement' | 'verification_item' | 'other';
  status: string | null;
}

export interface MentionListRef {
  onKeyDown: (props: { event: KeyboardEvent }) => boolean;
}

interface Props {
  items: MentionItem[];
  command: (item: MentionItem) => void;
}

export const MentionList = forwardRef<MentionListRef, Props>(function MentionList(
  { items, command },
  ref,
) {
  const [selected, setSelected] = useState(0);

  useEffect(() => setSelected(0), [items]);

  useImperativeHandle(ref, () => ({
    onKeyDown: ({ event }) => {
      if (event.key === 'ArrowDown') {
        setSelected((s) => (s + 1) % Math.max(items.length, 1));
        return true;
      }
      if (event.key === 'ArrowUp') {
        setSelected((s) => (s - 1 + items.length) % Math.max(items.length, 1));
        return true;
      }
      if (event.key === 'Enter') {
        if (items[selected]) command(items[selected]);
        return true;
      }
      return false;
    },
  }));

  return (
    <div
      className="border-line bg-canvas w-[340px] border p-1"
      style={{ boxShadow: 'var(--shadow-lg)' }}
    >
      <div className="text-mut-700 px-2 pt-1.5 pb-1 text-[10.5px] tracking-wider uppercase">
        Link an item
      </div>
      {items.length === 0 && <div className="text-mut-700 px-2 py-1.5 text-[13px]">No matches</div>}
      {items.map((item, i) => (
        <button
          key={item.id}
          type="button"
          onMouseDown={(e) => {
            e.preventDefault();
            command(item);
          }}
          className={cn(
            'grid w-full items-center gap-2 px-2 py-1.5 text-left',
            i === selected ? 'bg-mut-200/70' : 'hover:bg-mut-200/40',
          )}
          style={{ gridTemplateColumns: '10px 96px minmax(0,1fr)' }}
        >
          <StatusDot status={item.status as never} />
          <span className="text-brand-700 font-mono text-[12px]">{item.human_id}</span>
          <span className="truncate text-[12.5px]">{item.title}</span>
        </button>
      ))}
    </div>
  );
});
