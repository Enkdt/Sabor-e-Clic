export async function getCsrfToken(request = fetch) {
  const response = await request('/api/csrf-token', { credentials: 'include' });
  const data = await response.json();
  if (!response.ok || !data.csrf_token) {
    throw new Error('Não foi possível iniciar uma sessão segura.');
  }
  return data.csrf_token;
}

export async function login(email, password, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request('/api/login', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error?.message || 'Não foi possível entrar.');
  }

  return data;
}

export async function validateSession({ request = fetch } = {}) {
  const response = await request('/api/session', {
    credentials: 'include',
  });

  if (response.status === 401 || response.status === 403) return null;

  if (!response.ok) {
    throw new Error('Não foi possível validar a sessão.');
  }

  const data = await response.json();
  return data.user || null;
}

export async function clearSession({ request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request('/api/logout', {
    method: 'POST',
    credentials: 'include',
    headers: { 'X-CSRFToken': csrfToken },
  });
  if (!response.ok) throw new Error('Não foi possível encerrar a sessão.');
}
