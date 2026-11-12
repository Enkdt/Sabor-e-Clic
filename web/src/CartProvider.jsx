import { useEffect, useMemo, useState } from 'react';
import { useAuth } from './authContext';
import { CartContext } from './cartContext';

// Carrinho é escopado por conta para que, num navegador compartilhado, o carrinho
// de um usuário não vaze para outro ao trocar de login.
const storageKeyFor = (user) => `cart-items:${user?.id ?? 'guest'}`;

// localStorage não é confiável: valida a forma de cada item antes de usar.
function isValidItem(entry) {
  return (
    entry &&
    typeof entry === 'object' &&
    Number.isInteger(entry.id_prato) &&
    typeof entry.nome === 'string' &&
    Number.isFinite(entry.preco) &&
    entry.preco >= 0 &&
    Number.isInteger(entry.quantity) &&
    entry.quantity > 0
  );
}

function loadItems(key) {
  try {
    const stored = JSON.parse(localStorage.getItem(key));
    return Array.isArray(stored) ? stored.filter(isValidItem) : [];
  } catch {
    return [];
  }
}

export function CartProvider({ children }) {
  const { user } = useAuth();
  const storageKey = storageKeyFor(user);
  const [items, setItems] = useState(() => loadItems(storageKey));
  const [loadedKey, setLoadedKey] = useState(storageKey);

  // Ao trocar de conta (login/logout/troca de usuário), recarrega o carrinho da conta
  // atual durante o render — padrão React para ajustar estado quando uma prop muda.
  if (storageKey !== loadedKey) {
    setLoadedKey(storageKey);
    setItems(loadItems(storageKey));
  }

  useEffect(() => {
    localStorage.setItem(storageKey, JSON.stringify(items));
  }, [items, storageKey]);

  const addItem = (item) => {
    const normalized = {
      id_prato: item.id_prato,
      nome: item.nome,
      preco: Number(item.preco),
      quantity: Math.max(1, Math.trunc(item.quantity) || 1),
      imagem: typeof item.imagem === 'string' ? item.imagem : null,
    };
    if (!isValidItem(normalized)) return;
    setItems((current) => {
      const existing = current.find((entry) => entry.id_prato === normalized.id_prato);
      if (existing) {
        return current.map((entry) =>
          entry.id_prato === normalized.id_prato
            ? { ...entry, quantity: entry.quantity + normalized.quantity }
            : entry
        );
      }
      return [...current, normalized];
    });
  };

  const removeItem = (id_prato) => {
    setItems((current) => current.filter((entry) => entry.id_prato !== id_prato));
  };

  const setQuantity = (id_prato, quantity) => {
    setItems((current) =>
      current.map((entry) =>
        entry.id_prato === id_prato ? { ...entry, quantity: Math.max(1, Math.trunc(quantity) || 1) } : entry
      )
    );
  };

  const clear = () => setItems([]);

  const subtotal = useMemo(
    () => items.reduce((sum, entry) => sum + entry.preco * entry.quantity, 0),
    [items]
  );

  return (
    <CartContext.Provider value={{ items, subtotal, addItem, removeItem, setQuantity, clear }}>
      {children}
    </CartContext.Provider>
  );
}
