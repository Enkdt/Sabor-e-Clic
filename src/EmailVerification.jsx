import { useEffect, useState } from 'react';

//depois mudar essa página tá, eu peguei ela pra testar só
export function EmailVerification() {
  const token = new URLSearchParams(window.location.search).get('token');
  const [message, setMessage] = useState(
    token ? 'Validando seu email...' : 'Isso não é um token >:('
  );

  useEffect(() => {
    if (!token) return;
    fetch('/api/cadastro/validar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    })
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
