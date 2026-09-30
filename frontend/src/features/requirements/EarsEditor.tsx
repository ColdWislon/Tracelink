import Mention from '@tiptap/extension-mention';
import Placeholder from '@tiptap/extension-placeholder';
import Table from '@tiptap/extension-table';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import TableRow from '@tiptap/extension-table-row';
import { EditorContent, ReactRenderer, useEditor, type Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import type { SuggestionKeyDownProps, SuggestionProps } from '@tiptap/suggestion';
import { List, ListOrdered, Table2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import { checkEars } from '@/api/hooks';
import type { EarsReport } from '@/api/types';
import { cn } from '@/lib/cn';

import { EarsUnderline, docPlainText, earsPluginKey } from './ears-extension';
import { MentionList, type MentionItem, type MentionListRef } from './MentionList';

interface Props {
  body: string;
  onCommit: (html: string) => void;
  onReport?: (report: EarsReport) => void;
  mentionItems?: MentionItem[];
  onMention?: (item: MentionItem) => void;
}

const HTML_RE = /^\s*<(p|ul|ol|table|h[1-6]|blockquote)\b/i;

function toContent(body: string): string {
  if (!body) return '';
  return HTML_RE.test(body) ? body : `<p>${escapeHtml(body)}</p>`;
}

function placePopup(
  popup: HTMLElement,
  clientRect: (() => DOMRect | null) | null | undefined,
): void {
  const rect = clientRect?.();
  if (!rect) return;
  popup.style.left = `${rect.left + window.scrollX}px`;
  popup.style.top = `${rect.bottom + window.scrollY + 4}px`;
}

/** A rich TipTap editor (lists + tables + @mentions) with live EARS underlines. */
export function EarsEditor({ body, onCommit, onReport, mentionItems = [], onMention }: Props) {
  const debounce = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const lastCommitted = useRef(body);
  const [focused, setFocused] = useState(false);

  const mentionItemsRef = useRef(mentionItems);
  mentionItemsRef.current = mentionItems;
  const onMentionRef = useRef(onMention);
  onMentionRef.current = onMention;

  const runCheck = (editor: Editor) => {
    const { text } = docPlainText(editor.state.doc);
    void checkEars(text).then((report) => {
      editor.view.dispatch(editor.state.tr.setMeta(earsPluginKey, { findings: report.findings }));
      onReport?.(report);
    });
  };

  const editor = useEditor({
    extensions: [
      StarterKit.configure({ heading: false, codeBlock: false }),
      Placeholder.configure({ placeholder: 'Write the requirement statement…' }),
      Table.configure({ resizable: false }),
      TableRow,
      TableHeader,
      TableCell,
      EarsUnderline,
      Mention.configure({
        HTMLAttributes: { class: 'mention' },
        suggestion: {
          char: '@',
          items: ({ query }) =>
            mentionItemsRef.current
              .filter((i) => `${i.human_id} ${i.title}`.toLowerCase().includes(query.toLowerCase()))
              .slice(0, 8),
          command: ({ editor: ed, range, props }) => {
            const item = props as unknown as MentionItem;
            ed.chain()
              .focus()
              .insertContentAt(range, [
                { type: 'mention', attrs: { id: item.id, label: item.human_id } },
                { type: 'text', text: ' ' },
              ])
              .run();
            onMentionRef.current?.(item);
          },
          render: () => {
            let component: ReactRenderer<MentionListRef> | null = null;
            let popup: HTMLDivElement | null = null;
            return {
              onStart: (props: SuggestionProps) => {
                component = new ReactRenderer(MentionList, { props, editor: props.editor });
                popup = document.createElement('div');
                popup.style.position = 'absolute';
                popup.style.zIndex = '60';
                document.body.appendChild(popup);
                popup.appendChild(component.element);
                placePopup(popup, props.clientRect);
              },
              onUpdate: (props: SuggestionProps) => {
                component?.updateProps(props);
                placePopup(popup!, props.clientRect);
              },
              onKeyDown: (props: SuggestionKeyDownProps) => {
                if (props.event.key === 'Escape') return true;
                return component?.ref?.onKeyDown(props) ?? false;
              },
              onExit: () => {
                popup?.remove();
                component?.destroy();
                popup = null;
                component = null;
              },
            };
          },
        },
      }),
    ],
    content: toContent(body),
    editorProps: { attributes: { class: 'ears-prose' } },
    onFocus: () => setFocused(true),
    onUpdate: ({ editor: ed }) => {
      clearTimeout(debounce.current);
      debounce.current = setTimeout(() => runCheck(ed), 300);
    },
    onBlur: ({ editor: ed }) => {
      setFocused(false);
      const html = ed.getHTML();
      if (ed.getText().trim() && html !== lastCommitted.current) {
        lastCommitted.current = html;
        onCommit(html);
      }
    },
  });

  useEffect(() => {
    if (editor && body) runCheck(editor);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editor]);

  if (!editor) return null;

  const toolButton = (
    active: boolean,
    onClick: () => void,
    label: string,
    icon: React.ReactNode,
  ) => (
    <button
      type="button"
      title={label}
      aria-label={label}
      onMouseDown={(e) => {
        e.preventDefault();
        onClick();
      }}
      className={cn(
        'border-line flex h-6 w-6 items-center justify-center border',
        active ? 'bg-brand-100 text-brand-800' : 'text-mut-700 hover:bg-panel',
      )}
    >
      {icon}
    </button>
  );

  return (
    <div>
      {focused && (
        <div className="mb-1 flex gap-1">
          {toolButton(
            editor.isActive('bulletList'),
            () => editor.chain().focus().toggleBulletList().run(),
            'Bullet list',
            <List size={13} />,
          )}
          {toolButton(
            editor.isActive('orderedList'),
            () => editor.chain().focus().toggleOrderedList().run(),
            'Numbered list',
            <ListOrdered size={13} />,
          )}
          {toolButton(
            editor.isActive('table'),
            () =>
              editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run(),
            'Insert table',
            <Table2 size={13} />,
          )}
        </div>
      )}
      <EditorContent editor={editor} />
    </div>
  );
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
