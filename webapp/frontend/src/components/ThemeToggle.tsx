import { Moon, Sun } from 'lucide-react';
import { useEffect, useState } from 'react';

type Theme = 'light' | 'dark';

const STORAGE_KEY = 'liver-mri-ui-theme';

function readTheme(): Theme {
  return document.documentElement.classList.contains('theme-light') ? 'light' : 'dark';
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(readTheme);

  useEffect(() => {
    if (localStorage.getItem(STORAGE_KEY)) return;
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const syncSystemTheme = (event: MediaQueryListEvent) => setTheme(event.matches ? 'dark' : 'light');
    media.addEventListener('change', syncSystemTheme);
    return () => media.removeEventListener('change', syncSystemTheme);
  }, []);

  useEffect(() => {
    document.documentElement.classList.remove('theme-light', 'theme-dark');
    document.documentElement.classList.add(`theme-${theme}`);
  }, [theme]);

  const toggle = () => {
    setTheme((current) => {
      const next = current === 'dark' ? 'light' : 'dark';
      localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  };

  return (
    <button
      type="button"
      className="theme-toggle"
      role="switch"
      aria-checked={theme === 'dark'}
      aria-label={theme === 'dark' ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối'}
      title={theme === 'dark' ? 'Giao diện tối' : 'Giao diện sáng'}
      onClick={toggle}
    >
      <Sun aria-hidden="true" />
      <span className="theme-toggle__track" aria-hidden="true"><span /></span>
      <Moon aria-hidden="true" />
    </button>
  );
}
