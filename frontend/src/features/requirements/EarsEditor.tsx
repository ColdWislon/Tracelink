import Placeholder from '@tiptap/extension-placeholder';
import Table from '@tiptap/extension-table';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import TableRow from '@tiptap/extension-table-row';
import { EditorContent, useEditor, type Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { List, ListOrdered, Table2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import { checkEars } from '@/api/hooks';
import type { EarsReport } from '@/api/types';
import { cn } from '@/lib/cn';

import { EarsUnderline, docPlainText, earsPluginKey } from './ears-extension';

interface Props {
  body: string;
  onCommit: (html: string) => void;
  onReport?: (report: EarsReport) => void;
}

const HTML_RE = /^\s*<(p|ul|ol|table|h[1-6]|blockquote)\b/i;

function toContent(body: string): string {
  if (!body) return '';
  return HTML_RE.test(body) ? body : `<p>${escapeHtml(body)}</p>`;
}

/** A rich TipTap editor (lists + tables) with live EARS underlines, commit-on-blur. */
export function EarsEditor({ body, onCommit, onReport }: Props) {
  const debounce = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const lastCommitted = useRef(body);
  const [focused, setFocused] = useState(false);

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

  // Initial EARS check so underlines/pattern show without editing.
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
