"""Verificação de ponta a ponta do envio de logs ao Upstash Redis (OBS-001).

Emite um log real pela aplicação e, em seguida, lê o topo da lista no Redis via
REST para confirmar que a entrada chegou. Útil para diagnosticar "nenhum log
chega ao Redis" — distingue entre config ausente, token/URL inválidos e sucesso.

    python verify_redis_logging.py

Sai com código 0 em sucesso; 1 em falha (com motivo). NÃO imprime o token.
"""
import json
import logging
import sys
import time
from urllib import error as urllib_error
from urllib import request as urllib_request


def main() -> int:
    from app import create_app

    app = create_app()  # lê o .env real; configura logging (stdout + Redis se houver)
    base_url = app.config.get("UPSTASH_REDIS_REST_URL")
    token = app.config.get("UPSTASH_REDIS_REST_TOKEN")
    key = app.config.get("LOG_REDIS_KEY", "logs:app")

    if not base_url or not token:
        print("FALHA: UPSTASH_REDIS_REST_URL e/ou UPSTASH_REDIS_REST_TOKEN ausentes. "
              "Sem eles, os logs vão apenas para o stdout.", file=sys.stderr)
        return 1

    base_url = base_url.rstrip("/")
    marker = f"VERIFY_REDIS_LOG_{int(time.time())}"
    # Emite pelo caminho REAL da aplicação (logger de módulo -> root -> handler Redis).
    logging.getLogger("verify_redis_logging").warning(marker)
    # Dá um instante para a escrita síncrona concluir (ela é feita no emit).
    time.sleep(0.5)

    # Lê o item mais recente da lista (LPUSH coloca no índice 0).
    req = urllib_request.Request(
        f"{base_url}/lrange/{key}/0/0",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib_request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
    except urllib_error.HTTPError as err:
        print(f"FALHA: Redis respondeu HTTP {err.code} ao ler de volta. "
              "Verifique a URL/token do Upstash.", file=sys.stderr)
        return 1
    except Exception as err:
        print(f"FALHA: não foi possível ler do Redis: {err!r}", file=sys.stderr)
        return 1

    topo = (data.get("result") or [None])[0] if isinstance(data, dict) else None
    if topo and marker in topo:
        print(f"OK: log real confirmado no Redis (lista '{key}').")
        return 0

    print("FALHA: o log emitido não apareceu no topo da lista. "
          f"Topo atual: {topo!r}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
