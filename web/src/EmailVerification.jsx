import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getCsrfToken } from './authSession';

export function EmailVerification() {
  const token = new URLSearchParams(window.location.search).get('token');
  const [status, setStatus] = useState(token ? 'loading' : 'error'); // loading | success | error
  const [message, setMessage] = useState(
    token ? 'Validando seu email…' : 'Link inválido: nenhum token de validação foi informado.'
  );

  useEffect(() => {
    if (!token) return;
    let active = true;
    getCsrfToken()
      .then((csrfToken) => fetch('/api/cadastro/validar', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ token }),
      }))
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error?.message || 'Não foi possível validar o email.');
        }
        if (active) {
          setStatus('success');
          setMessage('Email validado com sucesso! Sua conta está autenticada.');
        }
      })
      .catch((error) => {
        if (active) {
          setStatus('error');
          setMessage(error.message || 'Não foi possível validar o email.');
        }
      });
    return () => { active = false; };
  }, [token]);

  return (
    <main className="auth-flow" aria-live="polite">
      <h1>Validação de email</h1>
      {status === 'loading' && <p role="status">{message}</p>}
      {status === 'success' && (
        <>
          <p role="status">✓ {message}</p>
          <Link to="/login">Ir para o login</Link>
        </>
      )}
      {status === 'error' && (
        <>
          <p role="alert">{message}</p>
          <Link to="/login">Voltar ao login</Link>
        </>
      )}
    </main>
  );
}
