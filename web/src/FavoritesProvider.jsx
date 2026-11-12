import { useEffect, useMemo, useState } from 'react';
import { useAuth } from './authContext';
import { addFavorite, fetchFavorites, removeFavorite } from './authSession';
import { FavoritesContext } from './favoritesContext';

export function FavoritesProvider({ children }) {
  const { user } = useAuth();
  const enabled = user?.role === 'customer';
  const [ids, setIds] = useState([]);
  const [loadedFor, setLoadedFor] = useState(null);
  const [error, setError] = useState(null); // mensagem transitória de falha ao favoritar

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
      .catch(() => { if (active) setError('Não foi possível carregar seus favoritos.'); });
    return () => { active = false; };
  }, [enabled, key]);

  const value = useMemo(() => {
    const isFavorite = (id) => ids.includes(id);
    const clearError = () => setError(null);
    const toggle = async (id) => {
      if (!enabled) return;
      const wasFav = ids.includes(id);
      setError(null);
      setIds((current) => (wasFav ? current.filter((x) => x !== id) : [...current, id]));
      try {
        if (wasFav) await removeFavorite(id);
        else await addFavorite(id);
      } catch {
        // Reverte o otimismo e informa o usuário (UX-002: nada de falha silenciosa).
        setIds((current) => (wasFav ? [...current, id] : current.filter((x) => x !== id)));
        setError(wasFav ? 'Não foi possível remover dos favoritos.' : 'Não foi possível adicionar aos favoritos.');
      }
    };
    return { enabled, isFavorite, toggle, favorites: ids, error, clearError };
  }, [enabled, ids, error]);

  return <FavoritesContext.Provider value={value}>{children}</FavoritesContext.Provider>;
}
