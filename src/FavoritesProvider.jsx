import { useEffect, useMemo, useState } from 'react';
import { useAuth } from './authContext';
import { addFavorite, fetchFavorites, removeFavorite } from './authSession';
import { FavoritesContext } from './favoritesContext';

export function FavoritesProvider({ children }) {
  const { user } = useAuth();
  const enabled = user?.role === 'customer';
  const [ids, setIds] = useState([]);
  const [loadedFor, setLoadedFor] = useState(null);

  // Carrega os favoritos da conta atual quando um cliente faz login (durante o render).
  const key = enabled ? user.id : null;
  if (key !== loadedFor) {
    setLoadedFor(key);
    if (!enabled) setIds([]);
  }

  useEffect(() => {
    if (!enabled) return;
    let active = true;
    fetchFavorites()
      .then((list) => { if (active) setIds(list); })
      .catch(() => {});
    return () => { active = false; };
  }, [enabled, key]);

  const value = useMemo(() => {
    const isFavorite = (id) => ids.includes(id);
    const toggle = async (id) => {
      if (!enabled) return;
      const wasFav = ids.includes(id);
      setIds((current) => (wasFav ? current.filter((x) => x !== id) : [...current, id]));
      try {
        if (wasFav) await removeFavorite(id);
        else await addFavorite(id);
      } catch {
        setIds((current) => (wasFav ? [...current, id] : current.filter((x) => x !== id)));
      }
    };
    return { enabled, isFavorite, toggle, favorites: ids };
  }, [enabled, ids]);

  return <FavoritesContext.Provider value={value}>{children}</FavoritesContext.Provider>;
}
