import { useEffect, useState } from 'react';

//depois mudar essa página tá, eu peguei ela pra testar só
export function EmailVerification() {
  const [message, setMessage] = useState('Validando seu email...');

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get('token');

    if (!token) {
      setMessage('Isso não é um token!');
      return;
    }
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
        setMessage('Email validado! Tá funfando!!! >:) ');
    })
      .catch((error) => setMessage(error.message));
  }, []);
  return <p>{message}</p>;
}
