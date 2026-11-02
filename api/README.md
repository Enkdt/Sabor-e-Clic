# API Sabor&Clic - DOCUMENTAÇÃO 

## Será alterado posteriormente

## Propósito

Para o projeto Sabor&CLic, foi criada uma API REST para 
possibilitar a comunicação entre o backend (Em python) e 
o frontend (em reactJS).

A api conta com funções como logs, proteção contra requisições 
em massa, IDORs e outras vulnerabilidades.

## Organização dos Arquivos

├── app.py

├── blueprints/

│   └── auth.py

├── config.py

├── db.py

├── extensions.py

├── instances/

│   └── app.db

├── logs/

│   └── testeLog.log

├── README.md

├── requirements.txt

├── utils.py

└── validations.py

## Tecnologias 

- Python
- Flask
- SQLite

## Passos

Requirements:

```npm install``` na pasta principal
```python3 -m venv .venv``` na pasta da api
Após ativar o ambiente virtual
```pip install -r requirements.txt```
na pasta da api

Depois, só rodar
```python3 app.py``` na pasta da api
```npm run dev``` na pasta principal

Acessar, enquanto em dev:
```http://localhost:5173```

ADMIN TESTE: admindasilva@email.com
SENHA: Faladorpassamal3!
