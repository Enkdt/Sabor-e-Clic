from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

# Recursos compartilhados; adicionar outros conforme necessário.
db = SQLAlchemy()
# SEC-003: o storage vem de RATELIMIT_STORAGE_URI (memory:// em dev; redis://... de
# um serviço gerenciado em produção, ex.: Upstash). `in_memory_fallback_enabled`
# mantém o serviço no ar (fail-open) se o store compartilhado ficar indisponível,
# em vez de bloquear todas as requisições.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=None,  # resolvido por init_app a partir de RATELIMIT_STORAGE_URI
    in_memory_fallback_enabled=True,
)
csrf = CSRFProtect()

