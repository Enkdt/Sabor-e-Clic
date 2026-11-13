// @ts-check
// TEST-002: exibição de avaliações do prato e ciclo de sessão (login → logout).
// A elegibilidade de avaliação (só após entrega) é coberta no backend
// (api/tests/test_avaliacao.py); aqui validamos a UI de avaliações e a sessão.
import { test, expect } from '@playwright/test';

const PASSWORD = 'SaborDemo123!';
const CUSTOMER = 'ana.demo@sabor.test';

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

test.describe('Avaliações do prato', () => {
  test('a página do prato mostra a seção de avaliações com um estado válido', async ({ page }) => {
    // Público (sem login): navega até um prato pelo catálogo.
    await page.goto('/catalogo');
    await page.locator('a[href^="/restaurante/"]').first().click();
    await page.locator('a[href*="/prato/"]').first().click();

    await expect(page.getByRole('heading', { name: 'Avaliações' })).toBeVisible();
    // A seção resolve para um dos estados possíveis (sem erro perpétuo de carregamento):
    //  - "ainda não tem avaliações" (vazio), OU
    //  - uma lista de avaliações (.dishPageReview).
    const vazio = page.getByText('Este prato ainda não tem avaliações.');
    const lista = page.locator('.dishPageReview');
    await expect(async () => {
      const temVazio = await vazio.isVisible().catch(() => false);
      const temItens = (await lista.count()) > 0;
      expect(temVazio || temItens).toBeTruthy();
    }).toPass({ timeout: 10000 });
  });
});

test.describe('Ciclo de sessão', () => {
  test('login, logout e bloqueio de rota protegida após sair', async ({ page }) => {
    await loginAndWait(page, CUSTOMER);

    // Logout pela tela de Configurações.
    await page.goto('/configuracoes');
    await Promise.all([
      page.waitForResponse((r) => r.url().includes('/api/logout') && r.request().method() === 'POST').catch(() => null),
      page.getByRole('button', { name: 'Sair da conta' }).click(),
    ]);

    // Após sair, o header volta a mostrar "Acessar Conta".
    await expect(page.getByRole('link', { name: 'Acessar Conta' })).toBeVisible();

    // Rota protegida agora redireciona ao login.
    await page.goto('/perfil');
    await expect(page).toHaveURL(/\/login$/);
  });
});
