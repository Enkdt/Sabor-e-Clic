// @ts-check
// TEST-002: fluxo de agendamento de bancada com propriedade (SEC-002).
// Um cliente solicita um agendamento (fica 'pendente'); o cozinheiro filiado ao
// restaurante dono da bancada aceita pela UI. O setup do pedido do cliente usa
// fetch same-origin na própria página (reusa sessão + CSRF, como o app faz),
// porque o calendário de seleção de data/hora seria frágil de dirigir pela UI.
import { test, expect } from '@playwright/test';

const PASSWORD = 'SaborDemo123!';
const CUSTOMER = 'ana.demo@sabor.test';
const COOK = 'rafael.cozinha@sabor.test'; // filiado ao restaurante dono da bancada 1 (seed)

async function loginAndWait(page, email, password = PASSWORD) {
  await page.goto('/login');
  await page.getByPlaceholder('exemplo@email.com').fill(email);
  await page.getByPlaceholder('Insira a sua senha').fill(password);
  const [resp] = await Promise.all([
    page.waitForResponse((r) => r.url().includes('/api/login') && r.request().method() === 'POST'),
    page.getByRole('button', { name: 'Continuar' }).click(),
  ]);
  expect(resp.ok(), `login deveria retornar 2xx, veio ${resp.status()}`).toBeTruthy();
  await expect(page.getByText(/Olá,/)).toBeVisible({ timeout: 10000 });
}

// Executa, dentro da página (same-origin, com a sessão do usuário logado), os
// mesmos passos que a UI faria: crédito de saldo + pedido de agendamento.
// Retorna o agendamento criado (ou lança com a mensagem de erro do backend).
async function requestBookingViaApi(page, bancadaId, { inicioISO, fimISO, credito }) {
  return page.evaluate(async ({ bancadaId, inicioISO, fimISO, credito }) => {
    async function csrf() {
      const r = await fetch('/api/csrf-token', { credentials: 'include' });
      const d = await r.json();
      return d.csrf_token;
    }
    // Garante saldo suficiente para o débito do agendamento.
    await fetch('/api/perfil/saldo', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': await csrf() },
      body: JSON.stringify({ valor: credito }),
    });
    const resp = await fetch(`/api/bancadas/${bancadaId}/agendamentos`, {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': await csrf() },
      body: JSON.stringify({ inicio: inicioISO, fim: fimISO }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(`${resp.status} ${data.error?.code || ''} ${data.error?.message || ''}`);
    return data.agendamento;
  }, { bancadaId, inicioISO, fimISO, credito });
}

test.describe('Bancada — cliente agenda e cozinheiro aceita', () => {
  test('cozinheiro filiado aceita um agendamento pendente', async ({ page, browser }) => {
    // O backend espera datetime-local SEM fuso (YYYY-MM-DDTHH:MM), como o
    // <input type="datetime-local"> da UI. Janela no futuro e em horário comercial.
    const d = new Date();
    d.setDate(d.getDate() + 60);
    const ymd = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    const inicioISO = `${ymd}T10:00`;
    const fimISO = `${ymd}T11:00`;

    // 1) Cliente solicita o agendamento na bancada 1 (num contexto próprio).
    const custCtx = await browser.newContext();
    const custPage = await custCtx.newPage();
    let agendamento;
    try {
      await loginAndWait(custPage, CUSTOMER);
      agendamento = await requestBookingViaApi(custPage, 1, { inicioISO, fimISO, credito: '500.00' });
      expect(agendamento?.id, 'agendamento deveria ser criado').toBeTruthy();
      expect(agendamento.status).toBe('pendente');
    } finally {
      await custCtx.close();
    }

    // 2) Cozinheiro filiado vê o pedido na fila e aceita pela UI.
    await loginAndWait(page, COOK);
    await page.goto('/cozinha/bancadas');
    await expect(page.getByRole('heading', { name: 'Pedidos de bancada' })).toBeVisible();

    // O card do agendamento recém-criado deve estar na lista; aceita o primeiro.
    const aceitar = page.getByRole('button', { name: 'Aceitar' }).first();
    await expect(aceitar).toBeVisible();
    await Promise.all([
      page.waitForResponse((r) => r.url().includes('/aceitar') && r.request().method() === 'POST'),
      aceitar.click(),
    ]);

    // Sem erro após aceitar; a lista é recarregada.
    await expect(page.locator('.bookingsError')).toHaveCount(0);
  });

  test('a fila de bancadas carrega para o cozinheiro', async ({ page }) => {
    await loginAndWait(page, COOK);
    await page.goto('/cozinha/bancadas');
    await expect(page.getByRole('heading', { name: 'Pedidos de bancada' })).toBeVisible();
    // Estado válido: carregou sem erro (com itens ou vazio).
    await expect(page.getByRole('alert')).toHaveCount(0);
  });
});
