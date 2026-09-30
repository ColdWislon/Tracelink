import { Extension } from '@tiptap/core';
import type { Node as PMNode } from '@tiptap/pm/model';
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';

import type { EarsFinding } from '@/api/types';

export const earsPluginKey = new PluginKey<EarsState>('ears');

interface EarsState {
  findings: EarsFinding[];
  deco: DecorationSet;
}

/**
 * Flatten the document to plain text plus a map from each text-character index to
 * its ProseMirror position. EARS checks run on this exact text, so finding offsets
 * map back to decorations correctly even across lists/tables/multiple blocks.
 */
export function docPlainText(doc: PMNode): { text: string; map: number[] } {
  let text = '';
  const map: number[] = [];
  doc.descendants((node, pos) => {
    if (node.isText && node.text) {
      for (let i = 0; i < node.text.length; i += 1) {
        text += node.text[i];
        map.push(pos + i);
      }
    }
    return true;
  });
  return { text, map };
}

function buildDecorations(doc: PMNode, findings: EarsFinding[]): DecorationSet {
  const { map } = docPlainText(doc);
  const decos = findings
    .filter((f) => f.end > f.start && f.start < map.length)
    .map((f) => {
      const from = map[f.start];
      const to = (map[f.end - 1] ?? map[map.length - 1]) + 1;
      return Decoration.inline(from, to, {
        class: f.severity === 'error' ? 'ears-err' : 'ears-warn',
        title: `${f.code}: ${f.message}`,
      });
    });
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
