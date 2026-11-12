import { useEffect, useMemo, useState } from 'react';
import { ThemeContext, applyThemePreference, readPreference, systemIsDark } from './themeContext';

export function ThemeProvider({ children }) {
  const [preference, setPreferenceState] = useState(readPreference);
  const [systemDark, setSystemDark] = useState(systemIsDark);

  const effective = preference === 'system' ? (systemDark ? 'dark' : 'light') : preference;

  const setPreference = (next) => {
    setPreferenceState(applyThemePreference(next));
  };

  // Aplica a preferência ao documento e acompanha mudanças do SO (usado quando em 'system').
  useEffect(() => {
    applyThemePreference(preference);
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = (event) => setSystemDark(event.matches);
    media.addEventListener('change', onChange);
    return () => media.removeEventListener('change', onChange);
  }, [preference]);

  const value = useMemo(() => ({ preference, setPreference, effective }), [preference, effective]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
