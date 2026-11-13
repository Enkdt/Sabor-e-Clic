// @ts-check
// TEST-002: jornada de compra do cliente — navegar → carrinho → pedido → pagamento.
// Usa o seed demo (api/seed_demo.py): há restaurantes com pratos disponíveis.
// Navega clicando nos links reais (não hardcode de slug) para resistir a mudanças de seed.
import { test, expect } from '@playwright/test';

const PASSWORD = 'SaborDemo123!';
const CUSTOMER = 'ana.demo@sabor.test';

async function loginAndWait(page, email = CUSTOMER, password = PASSWORD) {
  await page.goto('/login');
  await page.getByPlaceholder('exemplo@email.com').fill(email);
  await page.getByPlaceholder('Insira a sua senha').fill(password);
  // Aguarda a resposta do login para evitar corrida com a navegação do SPA.
  const [resp] = await Promise.all([
    page.waitForResponse((r) => r.url().includes('/api/login') && r.request().method() === 'POST'),
    page.getByRole('button', { name: 'Continuar' }).click(),
  ]);
  expect(resp.ok(), `login deveria retornar 2xx, veio ${resp.status()}`).toBeTruthy();
  await expect(page.getByText(/Olá,/)).toBeVisible({ timeout: 10000 });
}

test.describe('Jornada de compra', () => {
  test('cliente navega, adiciona ao carrinho, finaliza e paga um pedido', async ({ page }) => {
    await loginAndWait(page);

    // 1) Catálogo lista restaurantes do seed.
    await page.goto('/catalogo');
    await expect(page.getByRole('heading', { name: 'Todos os restaurantes' })).toBeVisible();
    const primeiroRestaurante = page.locator('a[href^="/restaurante/"]').first();
    await expect(primeiroRestaurante).toBeVisible();
    await primeiroRestaurante.click();

    // 2) Página do restaurante → abre o primeiro prato (link para /prato/).
    const primeiroPrato = page.locator('a[href*="/prato/"]').first();
    await expect(primeiroPrato).toBeVisible();
    await primeiroPrato.click();

    // 3) Página do prato → adicionar ao carrinho.
    await expect(page.getByRole('heading').first()).toBeVisible();
    await page.getByRole('button', { name: 'Adicionar ao carrinho' }).click();
    // Feedback acessível confirma a adição.
    await expect(page.getByText(/adicionado ao carrinho/)).toBeVisible();

    // 4) Abre o carrinho pelo header e segue para o pedido.
    await page.getByRole('button', { name: 'Abrir carrinho' }).click();
    const drawer = page.getByRole('dialog', { name: 'Carrinho' });
    await expect(drawer).toBeVisible();
    await drawer.getByRole('button', { name: 'Continuar' }).click();

    // 5) Página do pedido → finaliza.
    await expect(page).toHaveURL(/\/pedido$/);
    await expect(page.getByRole('heading', { name: 'Meu carrinho' })).toBeVisible();
    await page.getByRole('button', { name: 'Continuar' }).click();

    // 6) Pedido confirmado (o backend é a fonte da verdade do total/estado).
    await expect(page.getByRole('heading', { name: 'Pedido confirmado!' })).toBeVisible();
    await expect(page.getByText(/Pedido #\d+ criado/)).toBeVisible();

    // 7) Pagamento → registra o pagamento.
    await page.getByRole('button', { name: 'Pagar' }).click();
    await expect(page.getByText(/Pagamento registrado/)).toBeVisible();
  });

  test('carrinho vazio ao entrar no pedido mostra estado vazio', async ({ page }) => {
    await loginAndWait(page);
    await page.goto('/pedido');
    // O texto também existe (oculto) no CartDrawer; mira o da lista do pedido.
    await expect(page.locator('.orderList').getByText('Seu carrinho está vazio')).toBeVisible();
  });

  test('botão esvaziar carrinho remove todos os itens', async ({ page }) => {
    await loginAndWait(page);
    // Adiciona um item.
    await page.goto('/catalogo');
    await page.locator('a[href^="/restaurante/"]').first().click();
    await page.locator('a[href*="/prato/"]').first().click();
    await page.getByRole('button', { name: 'Adicionar ao carrinho' }).click();
    await expect(page.getByText(/adicionado ao carrinho/)).toBeVisible();

    // Abre o carrinho; o item e o botão de esvaziar devem aparecer.
    await page.getByRole('button', { name: 'Abrir carrinho' }).click();
    const drawer = page.getByRole('dialog', { name: 'Carrinho' });
    await expect(drawer).toBeVisible();
    const esvaziar = drawer.getByRole('button', { name: 'Esvaziar carrinho' });
    await expect(esvaziar).toBeVisible();
    await esvaziar.click();

    // Carrinho fica vazio: botão some e aparece o estado vazio.
    await expect(drawer.getByText('Seu carrinho está vazio')).toBeVisible();
    await expect(drawer.getByRole('button', { name: 'Esvaziar carrinho' })).toHaveCount(0);
  });
});
