// @ts-check
// TEST-002: jornadas de autenticação e autorização por papel.
// O servidor Flask (e2e_server.py) sobe com banco SQLite isolado e seed demo.
// Credenciais do seed (api/seed_demo.py): senha única DEMO_PASSWORD.
import { test, expect } from '@playwright/test';

const PASSWORD = 'SaborDemo123!';
const CUSTOMER = 'ana.demo@sabor.test';
const COOK = 'rafael.cozinha@sabor.test';
const ADMIN = 'admin.demo@sabor.test';

// Faz login pela UI de /login usando os placeholders dos campos (não há htmlFor
// associando label->input no componente Input, então mirar por placeholder é estável).
async function login(page, email, password = PASSWORD) {
  await page.goto('/login');
  await page.getByPlaceholder('exemplo@email.com').fill(email);
  await page.getByPlaceholder('Insira a sua senha').fill(password);
  await page.getByRole('button', { name: 'Continuar' }).click();
}

// Login bem-sucedido: aguarda a resposta do /api/login e o header autenticado antes
// de prosseguir, evitando corrida entre a navegação pós-login e um goto subsequente.
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

test.describe('Autenticação', () => {
  test('cliente faz login e chega à home autenticado', async ({ page }) => {
    await loginAndWait(page, CUSTOMER);
    // Após login o app navega para '/' (ou para a rota de origem).
    // loginAndWait já confirmou a saudação ("Olá,") no header autenticado.
    await expect(page).toHaveURL('/')
  });

  test('credenciais inválidas mostram erro e não autenticam', async ({ page }) => {
    await login(page, CUSTOMER, 'senha-errada-123');
    // Continua em /login; mensagem de erro visível.
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.locator('.loginError').first()).toBeVisible();
  });
});

test.describe('Autorização por papel', () => {
  test('admin acessa a Gerência', async ({ page }) => {
    await loginAndWait(page, ADMIN);
    await page.goto('/gerente');
    await expect(page.getByRole('heading', { name: 'Gerência' })).toBeVisible();
  });

  test('cliente é barrado na área de Gerência (admin-only)', async ({ page }) => {
    await loginAndWait(page, CUSTOMER);
    await page.goto('/gerente');
    // ProtectedRoute renderiza "Acesso restrito" para papel sem permissão.
    await expect(page.getByText('Acesso restrito')).toBeVisible();
  });

  test('cozinheiro acessa a Cozinha', async ({ page }) => {
    await loginAndWait(page, COOK);
    await page.goto('/cozinha');
    // A rota é cook+admin; não deve mostrar "Acesso restrito".
    await expect(page.getByText('Acesso restrito')).toHaveCount(0);
  });

  test('visitante sem sessão é redirecionado ao login em rota protegida', async ({ page }) => {
    await page.goto('/perfil');
    await expect(page).toHaveURL(/\/login$/);
  });
});
