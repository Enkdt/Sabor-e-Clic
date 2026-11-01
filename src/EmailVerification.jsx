import { useEffect, useState } from 'react';
import { getCsrfToken } from './authSession';

//depois mudar essa página tá, eu peguei ela pra testar só
export function EmailVerification() {
  const token = new URLSearchParams(window.location.search).get('token');
  const [message, setMessage] = useState(
    token ? 'Validando seu email...' : 'Isso não é um token >:('
  );

  useEffect(() => {
    if (!token) return;
    getCsrfToken().then((csrfToken) => fetch('/api/cadastro/validar', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
      body: JSON.stringify({ token }),
    }))
    .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          throw new Error(
            data.error?.message || 'Não foi possível validar o email'
          );
        }
        setMessage('Email validado, Tá funfando!!! >:) ');
    })
      .catch((error) => setMessage(error.message));
  }, [token]);
  return <p>{message}</p>;
}
