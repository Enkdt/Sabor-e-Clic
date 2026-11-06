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
    const error = new Error(data.error?.message || 'Não foi possível entrar.');
    error.code = data.error?.code;
    throw error;
  }

  return data;
}

export async function resendValidationEmail(email, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request('/api/cadastro/reenviar-validacao', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ email }),
  });
  const data = await response.json();

  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível reenviar o email de validação.');
    error.code = data.error?.code;
    throw error;
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

export async function placeOrder(items, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request('/api/pedidos', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({
      itens: items.map((item) => ({ id_prato: item.id_prato, quantidade: item.quantity })),
    }),
  });
  const data = await response.json();

  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível finalizar o pedido.');
    error.code = data.error?.code;
    throw error;
  }

  return data.pedido;
}

export async function payOrder(pedidoId, metodo, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/pedidos/${pedidoId}/pagamento`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ metodo }),
  });
  const data = await response.json();

  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível registrar o pagamento.');
    error.code = data.error?.code;
    throw error;
  }

  return data.pedido;
}

export async function fetchAddresses({ request = fetch } = {}) {
  const response = await request('/api/enderecos', { credentials: 'include' });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const error = new Error(data.error?.message || 'Não foi possível carregar seus endereços.');
    error.code = data.error?.code;
    throw error;
  }
  const data = await response.json();
  return data.enderecos || [];
}

export async function fetchOrders({ request = fetch } = {}) {
  const response = await request('/api/pedidos', { credentials: 'include' });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const error = new Error(data.error?.message || 'Não foi possível carregar seus pedidos.');
    error.code = data.error?.code;
    throw error;
  }
  const data = await response.json();
  return data.pedidos || [];
}

export async function fetchIngredients({ request = fetch } = {}) {
  const response = await request('/api/ingredientes', { credentials: 'include' });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const error = new Error(data.error?.message || 'Não foi possível carregar o estoque.');
    error.code = data.error?.code;
    throw error;
  }
  const data = await response.json();
  return data.ingredientes || [];
}

export async function createIngredient(payload, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request('/api/ingredientes', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível salvar o item.');
    error.code = data.error?.code;
    error.fields = data.error?.fields;
    throw error;
  }
  return data.ingrediente;
}

export async function updateIngredient(id, payload, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/ingredientes/${id}`, {
    method: 'PATCH',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível atualizar o item.');
    error.code = data.error?.code;
    error.fields = data.error?.fields;
    throw error;
  }
  return data.ingrediente;
}

export async function fetchDashboard(periodo = '30', { request = fetch } = {}) {
  const response = await request(`/api/dashboard?periodo=${encodeURIComponent(periodo)}`, { credentials: 'include' });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const error = new Error(data.error?.message || 'Não foi possível carregar o painel.');
    error.code = data.error?.code;
    throw error;
  }
  return response.json();
}

export async function createStaff(payload, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request('/api/usuarios/staff', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível criar a conta.');
    error.code = data.error?.code;
    error.fields = data.error?.fields;
    throw error;
  }
  return data.usuario;
}

export async function fetchKitchenOrders({ request = fetch } = {}) {
  const response = await request('/api/cozinha/pedidos', { credentials: 'include' });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const error = new Error(data.error?.message || 'Não foi possível carregar os pedidos.');
    error.code = data.error?.code;
    throw error;
  }
  const data = await response.json();
  return data.itens || [];
}

export async function confirmKitchenItem(idPedido, idPrato, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/cozinha/itens/${idPedido}/${idPrato}/confirmar`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'X-CSRFToken': csrfToken },
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível confirmar o item.');
    error.code = data.error?.code;
    throw error;
  }
  return data.item;
}

export async function denyKitchenItem(idPedido, idPrato, motivo, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/cozinha/itens/${idPedido}/${idPrato}/negar`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ motivo }),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível negar o item.');
    error.code = data.error?.code;
    throw error;
  }
  return data.item;
}

export async function fetchReviews(pedidoId, { request = fetch } = {}) {
  const response = await request(`/api/pedidos/${pedidoId}/avaliacao`, { credentials: 'include' });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const error = new Error(data.error?.message || 'Não foi possível carregar as avaliações.');
    error.code = data.error?.code;
    throw error;
  }
  const data = await response.json();
  return data.avaliacoes || []; // uma avaliação por prato do pedido
}

export async function submitReview(pedidoId, { id_prato, nota, comentario }, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/pedidos/${pedidoId}/avaliacao`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ id_prato, nota, comentario }),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível enviar a avaliação.');
    error.code = data.error?.code;
    throw error;
  }
  return data.avaliacao;
}

export async function fetchFavorites({ request = fetch } = {}) {
  const response = await request('/api/favoritos', { credentials: 'include' });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const error = new Error(data.error?.message || 'Não foi possível carregar os favoritos.');
    error.code = data.error?.code;
    throw error;
  }
  const data = await response.json();
  return data.favoritos || [];
}

export async function addFavorite(idRestaurante, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request('/api/favoritos', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ id_restaurante: idRestaurante }),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const error = new Error(data.error?.message || 'Não foi possível favoritar.');
    error.code = data.error?.code;
    throw error;
  }
  return true;
}

export async function removeFavorite(idRestaurante, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/favoritos/${idRestaurante}`, {
    method: 'DELETE',
    credentials: 'include',
    headers: { 'X-CSRFToken': csrfToken },
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const error = new Error(data.error?.message || 'Não foi possível remover o favorito.');
    error.code = data.error?.code;
    throw error;
  }
  return true;
}

export async function uploadImage(file, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const form = new FormData();
  form.append('file', file);
  // Sem Content-Type manual: o browser define o boundary do multipart.
  const response = await request('/api/uploads', {
    method: 'POST',
    credentials: 'include',
    headers: { 'X-CSRFToken': csrfToken },
    body: form,
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível enviar a imagem.');
    error.code = data.error?.code;
    throw error;
  }
  return data; // { key, url }
}

export async function setRestaurantImage(id, key, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/restaurantes/${id}/imagem`, {
    method: 'PATCH',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ imagem: key }),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível salvar a imagem.');
    error.code = data.error?.code;
    throw error;
  }
  return data.restaurante;
}

export async function setDishImage(id, key, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/pratos/${id}/imagem`, {
    method: 'PATCH',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ imagem: key }),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível salvar a imagem.');
    error.code = data.error?.code;
    throw error;
  }
  return data.prato;
}

export async function fetchAvatar({ request = fetch } = {}) {
  const response = await request('/api/perfil/foto', { credentials: 'include' });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const error = new Error(data.error?.message || 'Não foi possível carregar o avatar.');
    error.code = data.error?.code;
    throw error;
  }
  const data = await response.json();
  return data.avatar; // URL ou null
}

export async function setAvatar(key, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request('/api/perfil/foto', {
    method: 'PATCH',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ avatar: key }),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível salvar o avatar.');
    error.code = data.error?.code;
    throw error;
  }
  return data.avatar;
}


export async function createRestaurant(nome, { imagem } = {}, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request('/api/restaurantes', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ nome, imagem }),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível criar o restaurante.');
    error.code = data.error?.code;
    throw error;
  }
  return data.restaurante;
}

export async function fetchRestaurant(slugOrId, { request = fetch } = {}) {
  const response = await request(`/api/restaurantes/${encodeURIComponent(slugOrId)}`, { credentials: 'include' });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Restaurante não encontrado.');
    error.code = data.error?.code;
    throw error;
  }
  return data.restaurante;
}

export async function createDish(idRestaurante, payload, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/restaurantes/${idRestaurante}/pratos`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível criar o prato.');
    error.code = data.error?.code;
    error.fields = data.error?.fields;
    throw error;
  }
  return data.prato;
}

export async function updateDish(id, payload, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/pratos/${id}`, {
    method: 'PATCH',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível atualizar o prato.');
    error.code = data.error?.code;
    error.fields = data.error?.fields;
    throw error;
  }
  return data.prato;
}

export async function deleteDish(id, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/pratos/${id}`, {
    method: 'DELETE',
    credentials: 'include',
    headers: { 'X-CSRFToken': csrfToken },
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const error = new Error(data.error?.message || 'Não foi possível remover o prato.');
    error.code = data.error?.code;
    throw error;
  }
  return true;
}

export async function fetchCooks({ request = fetch } = {}) {
  const response = await request('/api/usuarios/cozinheiros', { credentials: 'include' });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível carregar os cozinheiros.');
    error.code = data.error?.code;
    throw error;
  }
  return data.cozinheiros || [];
}

export async function affiliateCook(idUsuario, idRestaurante, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/usuarios/cozinheiros/${idUsuario}/restaurantes`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ id_restaurante: idRestaurante }),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível filiar o cozinheiro.');
    error.code = data.error?.code;
    throw error;
  }
  return data.cozinheiro;
}

export async function unaffiliateCook(idUsuario, idRestaurante, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/usuarios/cozinheiros/${idUsuario}/restaurantes/${idRestaurante}`, {
    method: 'DELETE',
    credentials: 'include',
    headers: { 'X-CSRFToken': csrfToken },
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível desfiliar o cozinheiro.');
    error.code = data.error?.code;
    throw error;
  }
  return data.cozinheiro;
}


export async function fetchRestaurants({ request = fetch } = {}) {
  const response = await request('/api/restaurantes', { credentials: 'include' });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível carregar os restaurantes.');
    error.code = data.error?.code;
    throw error;
  }
  return data.restaurantes || [];
}


export async function fetchDishReviews(id, { request = fetch } = {}) {
  const response = await request(`/api/pratos/${id}/avaliacoes`, { credentials: 'include' });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível carregar as avaliações.');
    error.code = data.error?.code;
    throw error;
  }
  return data; // { media, total, avaliacoes: [...] }
}


export async function requestBooking(bancadaId, { inicio, fim }, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/bancadas/${bancadaId}/agendamentos`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ inicio, fim }),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível solicitar a bancada.');
    error.code = data.error?.code;
    throw error;
  }
  return data.agendamento;
}

export async function fetchMyBookings({ request = fetch } = {}) {
  const response = await request('/api/bancadas/meus-agendamentos', { credentials: 'include' });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível carregar seus agendamentos.');
    error.code = data.error?.code;
    throw error;
  }
  return data.agendamentos || [];
}

export async function fetchPendingBookings({ request = fetch } = {}) {
  const response = await request('/api/bancadas/agendamentos/pendentes', { credentials: 'include' });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível carregar os pedidos de bancada.');
    error.code = data.error?.code;
    throw error;
  }
  return data.agendamentos || [];
}

export async function acceptBooking(agId, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/bancadas/agendamentos/${agId}/aceitar`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'X-CSRFToken': csrfToken },
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível aceitar o agendamento.');
    error.code = data.error?.code;
    throw error;
  }
  return data.agendamento;
}

export async function denyBooking(agId, motivo, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request(`/api/bancadas/agendamentos/${agId}/negar`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ motivo }),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível negar o agendamento.');
    error.code = data.error?.code;
    throw error;
  }
  return data.agendamento;
}


export async function fetchBalance({ request = fetch } = {}) {
  const response = await request('/api/perfil/saldo', { credentials: 'include' });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível carregar o saldo.');
    error.code = data.error?.code;
    throw error;
  }
  return data.saldo;
}

export async function addBalance(valor, { request = fetch } = {}) {
  const csrfToken = await getCsrfToken(request);
  const response = await request('/api/perfil/saldo', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ valor }),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Não foi possível adicionar saldo.');
    error.code = data.error?.code;
    throw error;
  }
  return data.saldo;
}
