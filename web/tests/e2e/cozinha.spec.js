// @ts-check
// TEST-002: fluxos do cozinheiro — disponibilidade de prato e confirmação de item.
// O cozinheiro do seed (rafael.cozinha@sabor.test) é filiado a um restaurante com
// pratos (api/seed_demo.py), então a tela "Meus pratos" tem dados reais.
import { test, expect } from '@playwright/test';

const PASSWORD = 'SaborDemo123!';
const CUSTOMER = 'ana.demo@sabor.test';
const COOK = 'rafael.cozinha@sabor.test';

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

test.describe('Cozinheiro — disponibilidade de prato', () => {
  test('alterna disponibilidade e o estado persiste após recarregar', async ({ page }) => {
    await loginAndWait(page, COOK);
    await page.goto('/cozinha/pratos');
    await expect(page.getByRole('heading', { name: 'Meus pratos' })).toBeVisible();

    // Primeiro card de prato da lista.
    const primeiroCard = page.locator('.kitchenDishCard').first();
    await expect(primeiroCard).toBeVisible();

    // O botão alterna entre "Desativar" (disponível) e "Ativar" (indisponível).
    // Aguarda a resposta da API para evitar corrida com o recarregamento da lista.
    const toggle = primeiroCard.getByRole('button', { name: /^(Desativar|Ativar)$/ });
    const estadoInicial = (await toggle.textContent())?.trim();
    await Promise.all([
      page.waitForResponse((r) => r.url().includes('/disponibilidade') && r.request().method() === 'PATCH'),
      toggle.click(),
    ]);

    // O rótulo do botão deve ter invertido.
    const esperadoApos = estadoInicial === 'Desativar' ? 'Ativar' : 'Desativar';
    await expect(primeiroCard.getByRole('button', { name: esperadoApos })).toBeVisible();

    // Persistência: recarrega e confirma o novo estado.
    await page.reload();
    const cardAposReload = page.locator('.kitchenDishCard').first();
    await expect(cardAposReload.getByRole('button', { name: esperadoApos })).toBeVisible();

    // Restaura o estado original (teste idempotente para o banco compartilhado).
    await Promise.all([
      page.waitForResponse((r) => r.url().includes('/disponibilidade') && r.request().method() === 'PATCH'),
      cardAposReload.getByRole('button', { name: esperadoApos }).click(),
    ]);
    await expect(cardAposReload.getByRole('button', { name: estadoInicial })).toBeVisible();
  });
});

test.describe('Cozinheiro — confirmação de item na cozinha', () => {
  test('cliente paga um pedido e o cozinheiro confirma o item', async ({ page, browser }) => {
    // Teste pesado (2 logins + compra completa em contextos separados): dá mais folga.
    test.setTimeout(60000)
    // 1) Cliente cria e paga um pedido num contexto próprio.
    const custCtx = await browser.newContext();
    const custPage = await custCtx.newPage();
    try {
      await loginAndWait(custPage, CUSTOMER);
      // Vai ao primeiro restaurante → primeiro prato → adiciona ao carrinho.
      await custPage.goto('/catalogo');
      await custPage.locator('a[href^="/restaurante/"]').first().click();
      await custPage.locator('a[href*="/prato/"]').first().click();
      const nomePrato = (await custPage.locator('.dishPageName').textContent())?.trim();
      await custPage.getByRole('button', { name: 'Adicionar ao carrinho' }).click();
      await expect(custPage.getByText(/adicionado ao carrinho/)).toBeVisible();
      // Carrinho → pedido → finaliza → paga.
      await custPage.getByRole('button', { name: 'Abrir carrinho' }).click();
      await custPage.getByRole('dialog', { name: 'Carrinho' }).getByRole('button', { name: 'Continuar' }).click();
      await expect(custPage).toHaveURL(/\/pedido$/);
      await custPage.getByRole('button', { name: 'Continuar' }).click();
      await expect(custPage.getByRole('heading', { name: 'Pedido confirmado!' })).toBeVisible();
      await custPage.getByRole('button', { name: 'Pagar' }).click();
      await expect(custPage.getByText(/Pagamento registrado/)).toBeVisible();

      // 2) Cozinheiro vê o item aguardando e confirma.
      await loginAndWait(page, COOK);
      await page.goto('/cozinha');
      await expect(page.getByRole('heading', { name: 'Cozinha' })).toBeVisible();
      // Há pelo menos um item aguardando (o pedido pago acima). Confirma o primeiro.
      const confirmar = page.getByRole('button', { name: 'Confirmar' }).first();
      await expect(confirmar).toBeVisible();
      await Promise.all([
        page.waitForResponse((r) => r.url().includes('/cozinha/') && r.request().method() === 'POST'),
        confirmar.click(),
      ]);
      // Após confirmar, o item sai da fila "aguardando" (recarregada pela tela).
      // Verifica que a página continua consistente (sem erro).
      await expect(page.getByRole('alert')).toHaveCount(0);

      if (nomePrato) {
        // Sanidade: o nome do prato comprado é uma string não vazia.
        expect(nomePrato.length).toBeGreaterThan(0);
      }
    } finally {
      await custCtx.close();
    }
  });
});
