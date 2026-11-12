import { createContext, useContext } from 'react';

export const FavoritesContext = createContext(null);

export function useFavorites() {
  const context = useContext(FavoritesContext);
  if (!context) throw new Error('useFavorites precisa ser usado dentro de FavoritesProvider.');
  return context;
}
