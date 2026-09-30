export interface TextDiff {
  pre: string;
  deleted: string;
  inserted: string;
  post: string;
  changed: boolean;
}

/** Strip HTML tags to compare/display requirement bodies as plain text. */
export function stripHtml(html: string): string {
  return html
    .replace(/<[^>]+>/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Minimal common-prefix/suffix diff, matching the backend's single-span diff. */
export function diffText(oldText: string, newText: string): TextDiff {
  let prefix = 0;
  const maxPrefix = Math.min(oldText.length, newText.length);
  while (prefix < maxPrefix && oldText[prefix] === newText[prefix]) prefix += 1;

  let suffix = 0;
  const maxSuffix = Math.min(oldText.length - prefix, newText.length - prefix);
  while (
    suffix < maxSuffix &&
    oldText[oldText.length - 1 - suffix] === newText[newText.length - 1 - suffix]
  )
    suffix += 1;

  const oldEnd = oldText.length - suffix;
  const newEnd = newText.length - suffix;
  const deleted = oldText.slice(prefix, oldEnd);
  const inserted = newText.slice(prefix, newEnd);
  return {
    pre: oldText.slice(0, prefix),
    deleted,
    inserted,
    post: suffix ? oldText.slice(oldEnd) : '',
    changed: Boolean(deleted || inserted),
  };
}
