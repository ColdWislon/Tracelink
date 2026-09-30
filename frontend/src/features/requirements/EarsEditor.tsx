import Placeholder from '@tiptap/extension-placeholder';
import { EditorContent, useEditor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { useEffect, useRef } from 'react';

import { checkEars } from '@/api/hooks';
import type { EarsReport } from '@/api/types';

import { EarsUnderline, earsPluginKey } from './ears-extension';

interface Props {
  body: string;
  onCommit: (text: string) => void;
  onReport?: (report: EarsReport) => void;
}

/** A single-paragraph TipTap editor with live EARS underlines and a commit-on-blur. */
export function EarsEditor({ body, onCommit, onReport }: Props) {
  const debounce = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const lastCommitted = useRef(body);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: false,
        bulletList: false,
        orderedList: false,
        blockquote: false,
        codeBlock: false,
      }),
      Placeholder.configure({ placeholder: 'Write the requirement statement…' }),
      EarsUnderline,
    ],
    content: body ? `<p>${escapeHtml(body)}</p>` : '',
    editorProps: { attributes: { class: 'ears-prose' } },
    onUpdate: ({ editor: ed }) => {
      const text = ed.getText();
      clearTimeout(debounce.current);
      debounce.current = setTimeout(() => {
        void checkEars(text).then((report) => {
          ed.view.dispatch(ed.state.tr.setMeta(earsPluginKey, { findings: report.findings }));
          onReport?.(report);
        });
      }, 300);
    },
    onBlur: ({ editor: ed }) => {
      const text = ed.getText().trim();
      if (text && text !== lastCommitted.current) {
        lastCommitted.current = text;
        onCommit(text);
      }
    },
  });

  // Run an initial EARS check so underlines/pattern show without editing.
  useEffect(() => {
    if (!editor || !body) return;
    void checkEars(body).then((report) => {
      editor.view.dispatch(editor.state.tr.setMeta(earsPluginKey, { findings: report.findings }));
      onReport?.(report);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editor]);

  return <EditorContent editor={editor} />;
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
