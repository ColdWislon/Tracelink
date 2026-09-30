import { Extension } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';
import type { Node as PMNode } from '@tiptap/pm/model';

import type { EarsFinding } from '@/api/types';

export const earsPluginKey = new PluginKey<EarsState>('ears');

interface EarsState {
  findings: EarsFinding[];
  deco: DecorationSet;
}

/** Map a plain-text character offset to a ProseMirror document position. */
function offsetToPos(doc: PMNode, offset: number): number {
  let remaining = offset;
  let pos = 0;
  let found = 0;
  doc.descendants((node, nodePos) => {
    if (found) return false;
    if (node.isText) {
      const len = node.text?.length ?? 0;
      if (remaining <= len) {
        pos = nodePos + remaining;
        found = 1;
        return false;
      }
      remaining -= len;
    }
    return true;
  });
  return found ? pos : doc.content.size;
}

function buildDecorations(doc: PMNode, findings: EarsFinding[]): DecorationSet {
  const decos = findings
    .filter((f) => f.end > f.start)
    .map((f) =>
      Decoration.inline(offsetToPos(doc, f.start), offsetToPos(doc, f.end), {
        class: f.severity === 'error' ? 'ears-err' : 'ears-warn',
        title: `${f.code}: ${f.message}`,
      }),
    );
  return DecorationSet.create(doc, decos);
}

export const EarsUnderline = Extension.create({
  name: 'earsUnderline',
  addProseMirrorPlugins() {
    return [
      new Plugin<EarsState>({
        key: earsPluginKey,
        state: {
          init: () => ({ findings: [], deco: DecorationSet.empty }),
          apply(tr, value, _old, newState) {
            const meta = tr.getMeta(earsPluginKey) as { findings: EarsFinding[] } | undefined;
            const findings = meta ? meta.findings : value.findings;
            if (!meta && !tr.docChanged) return value;
            return { findings, deco: buildDecorations(newState.doc, findings) };
          },
        },
        props: {
          decorations(state) {
            return earsPluginKey.getState(state)?.deco;
          },
        },
      }),
    ];
  },
});
