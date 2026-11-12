# API Sabor&Clic — Documentação

## Propósito

API REST (Flask) que conecta o frontend React ao backend Python. Inclui logging
estruturado, rate limiting, CSRF, hashing de senha com Argon2, sessões por cookie
assinado e decorators de autorização por papel.

## Organização dos arquivos

```
api/
├── app.py              # application factory (create_app); sem efeitos de I/O na importação
├── config.py           # configuração por ambiente (fail-closed em produção)
├── migrations.py       # ciclo de vida das migrações (CLI; não roda no boot do app)
├── extensions.py       # db, limiter, csrf compartilhados
├── blueprints/         # rotas por domínio (auth, cardapio, pedidos, ...)
├── models/             # modelos SQLAlchemy e CRUD
├── alembic/            # migrações (baseline 8c5ce5754122)
├── tests/              # suíte unittest
├── e2e_server.py       # servidor E2E com banco SQLite descartável e isolado
├── seed_demo.py        # seed de demonstração (bloqueado em produção)
└── requirements.txt
```

## Tecnologias

- Python 3.11+ (desenvolvido/testado em 3.14)
- Flask 3, Flask-SQLAlchemy, Alembic
- SQLite (dev/teste) · PostgreSQL/Neon (produção, via `DATABASE_URL`)

## Configuração de ambiente

Copie `.env.example` para `.env` e preencha os valores. **Nunca** faça commit do
`.env` (já está no `.gitignore`). Gere segredos fortes localmente, por exemplo:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Variáveis principais:

| Variável | Obrigatória | Observação |
|---|---|---|
| `APP_ENV` | sim | `development`, `test` ou `production` (valores inválidos falham) |
| `SECRET_KEY` | em produção | mínimo 32 caracteres; em dev é gerada automaticamente se ausente |
| `JWT_SECRET_KEY` | em produção | mínimo 32 caracteres |
| `FRONTEND_BASE_URL` | em produção | origem **HTTPS** |
| `DATABASE_URL` | em produção | URL do banco gerenciado (não SQLite) |
| `SESSION_COOKIE_SECURE` | — | `1` em produção |
| `RATELIMIT_STORAGE_URI` | — | store compartilhado em produção (ver SEC-003) |

## Setup local (desenvolvimento)

```bash
# na raiz do projeto
npm install

# na pasta api/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# aplique o esquema ao banco local (SQLite) — NÃO roda no boot do app
python migrations.py upgrade

# (opcional) popular dados de demonstração — bloqueado em produção
python seed_demo.py

# rodar a API
python app.py
```

Na raiz, rode o frontend: `npm run dev` e acesse `http://localhost:5173`.

> Não há credenciais de teste publicadas. Use `seed_demo.py` em ambiente de
> desenvolvimento para gerar contas de demonstração descartáveis, ou crie um
> usuário pelo fluxo de cadastro.

## Testes

```bash
# backend (na pasta api/, com a venv ativa)
python -m unittest discover -s tests -p "test_*.py"

# E2E (banco SQLite descartável e isolado; ver TEST-001)
python e2e_server.py
```

## Migrações

As migrações **não** rodam na criação do app (evita I/O em cold starts
serverless e corridas de migração). Aplique-as explicitamente por release:

```bash
python migrations.py upgrade     # aplica até head
python migrations.py current     # revisão atual do banco
python migrations.py stamp-head  # marca head sem rodar DDL
```
