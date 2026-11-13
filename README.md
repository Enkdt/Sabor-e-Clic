<p align="center">
  <img src="https://i.postimg.cc/k56nndjc/Logo-S-C.png" alt="https://postimg.cc/McwkDgJM"/>
</p>

<div align="center">
  <details closed>
    <summary style="list-style: none; outline: none;">
      <h1>Sabor & Clic</h1>
    </summary>
  </details>
</div>

---

---

<div align="center">
  <details closed>
    <summary style="list-style: none; outline: none;">
      <h2>Introdução</h2>
    </summary>
  </details>
</div>

<p align="center"> 
Sabor & Clic é um projeto baseado nas dark kitchens que reúne microempreededores, redes de delivery e outros focados em culinária vegana.
O fim deste projeto é facilitar e melhorar a experiência de gerência para os cozinheiros a se encontrarem com o seu devido cliente.
</p>

---

<div align="center">
  <details closed>
    <summary style="list-style: none; outline: none;">
      <h2>Tecnologias utilizadas</h2>
    </summary>
  </details>
</div>

<p align="center">
  <img src="https://skillicons.dev/icons?i=py,flask,html" alt="https://skillicons.dev"/><br>
  <img src="https://skillicons.dev/icons?i=css,javascript,react" alt="https://skillicons.dev"/><br>
  <img src="https://skillicons.dev/icons?i=figma,mysql,git" alt="https://skillicons.dev"/>

</p>

---

---

<div align="center">
  <details closed>
    <summary style="list-style: none; outline: none;">
      <h2>Créditos</h2>
    </summary>
  </details>
</div>

<p align="center">
  <a href="https://github.com/mate-nos">Matheus de Sousa</a><br>
  <a href="https://github.com/miguelzf22">Miguel Fernandes</a><br>
  <a href="https://github.com/NickollllokciN">Nicholas Alcantara</a><br>
  <a href="https://github.com/Enkdt">Thales Endo</a>
</p>

---

## Desenvolvimento

Stack: React + Vite (frontend) · Flask + SQLAlchemy + Alembic (API) · SQLite em
dev/teste, PostgreSQL (Neon) em produção · deploy na Vercel.

### Setup local

```bash
# frontend (raiz)
npm install
npm run dev            # http://localhost:5173

# API (pasta api/)
cd api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha os valores; gere segredos fortes
python migrations.py upgrade   # aplica o esquema (NÃO roda no boot do app)
python app.py          # API em http://127.0.0.1:5000
```

Gere segredos com `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
Variáveis e detalhes da API: veja [`api/README.md`](api/README.md) e
[`api/.env.example`](api/.env.example). Nunca faça commit do `.env`.

### Testes

```bash
# backend (pasta api/, venv ativa)
python -m unittest discover -s tests -p "test_*.py"

# frontend (raiz)
npm run lint
npm run build

# E2E Playwright (banco SQLite descartável e isolado)
cd api && python e2e_server.py     # sobe a API de teste
npm run test:e2e                   # noutro terminal, na raiz
```

### Migrações

As migrações não rodam na inicialização do app. Aplique por release:
`cd api && python migrations.py upgrade` (`current` mostra a revisão,
`stamp-head` adota a baseline sem rodar DDL).

### Deploy (Vercel)

Defina no ambiente da Vercel: `APP_ENV=production`, `SECRET_KEY`, `JWT_SECRET_KEY`,
`FRONTEND_BASE_URL` (HTTPS), `DATABASE_URL` (Neon), `STORAGE_BACKEND=blob` +
`BLOB_READ_WRITE_TOKEN` (Vercel Blob), `RATELIMIT_STORAGE_URI` (Upstash Redis).
Rode `python migrations.py upgrade` uma vez por release. Funcionalidades de
pagamento são simuladas (sem gateway real).

