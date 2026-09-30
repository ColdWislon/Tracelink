import { Link2, Moon, Sun } from 'lucide-react';
import { useCallback, useState } from 'react';

import { applyTheme, getInitialTheme, type Theme } from './lib/theme';

/**
 * Phase 0 placeholder shell. The full sidebar/header/views land in Phase 1.5.
 */
export default function App() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next: Theme = prev === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      return next;
    });
  }, []);

  return (
    <div className="bg-canvas text-ink flex h-full flex-col items-center justify-center gap-4">
      <div className="flex items-center gap-2">
        <Link2 className="text-brand" size={22} strokeWidth={1.5} />
        <span className="font-head text-3xl font-semibold tracking-tight">Tracelink</span>
      </div>
      <p className="text-mut-700">Requirement tracking for SoC/ASIC verification.</p>
      <button
        type="button"
        onClick={toggleTheme}
        className="border-line text-ink hover:bg-panel flex items-center gap-2 border px-3 py-1.5"
      >
        {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
        <span>Toggle theme</span>
      </button>
    </div>
  );
}
