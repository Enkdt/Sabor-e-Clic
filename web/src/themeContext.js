import { createContext, useContext } from 'react';

const STORAGE_KEY = 'theme-preference';
const VALID = new Set(['light', 'dark', 'system']);

export const ThemeContext = createContext(null);

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme precisa ser usado dentro de ThemeProvider.');
  return context;
}

export function readPreference() {
  const stored = localStorage.getItem(STORAGE_KEY);
  return VALID.has(stored) ? stored : 'system';
}

export function systemIsDark() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

// Fonte única da verdade: aplica a preferência literal ao documento.
// 'system' permanece 'system' para que o @media do index.css resolva o tema.
export function applyThemePreference(preference) {
  const pref = VALID.has(preference) ? preference : 'system';
  document.documentElement.dataset.theme = pref;
  document.documentElement.style.colorScheme = pref === 'system' ? '' : pref;
  localStorage.setItem(STORAGE_KEY, pref);
  return pref;
}
