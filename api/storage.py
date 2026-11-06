"""Armazenamento de imagens enviadas pelos usuários.

Camada única e trocável: todos os blueprints passam por aqui, então mudar o backend
não exige tocar em rotas.

Backend escolhido por STORAGE_BACKEND:
  - "local" (padrão): grava em api/uploads/ e serve por /api/uploads/<key>. Bom para dev.
  - "blob": destino de produção (Vercel Blob / S3 / R2).

ATENÇÃO (deploy na Vercel): o sistema de arquivos é somente-leitura, exceto /tmp, que é
efêmero — uploads gravados em disco NÃO persistem entre invocações. Em produção na Vercel use
STORAGE_BACKEND="blob" com um bucket. shortcut: o backend "blob" é um stub; ao migrar, implemente
save/open aqui (cliente do bucket) e configure a env — nenhum blueprint muda.
"""
import os
import secrets
from pathlib import Path

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
BACKEND = os.environ.get("STORAGE_BACKEND", "local").lower()

# Tipos aceitos → extensão canônica.
_ALLOWED = {"jpeg": "jpg", "png": "png", "webp": "webp"}
MAX_BYTES = 2 * 1024 * 1024  # 2 MB

class UploadError(ValueError):
    """Arquivo enviado inválido (tipo não permitido, vazio ou grande demais)."""

def _detect(head: bytes) -> str | None:
    """Detecta o tipo pela assinatura (magic bytes), não pela extensão enviada pelo cliente."""
    if head[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None

def save_image(file_storage) -> str:
    """Valida e grava a imagem. Retorna a chave (nome do arquivo). Nunca usa o nome enviado pelo cliente."""
    data = file_storage.read(MAX_BYTES + 1)
    if not data:
        raise UploadError("Arquivo vazio.")
    if len(data) > MAX_BYTES:
        raise UploadError("Imagem acima de 2 MB.")
    kind = _detect(data)
    if kind is None:
        raise UploadError("Formato inválido. Envie JPEG, PNG ou WebP.")
    key = f"{secrets.token_hex(16)}.{_ALLOWED[kind]}"
    if BACKEND == "blob":
        return _blob_save(key, data)
    UPLOAD_DIR.mkdir(exist_ok=True)
    (UPLOAD_DIR / key).write_bytes(data)
    return key

def url_for_key(key: str) -> str:
    return f"/api/uploads/{key}"

def _blob_save(key: str, data: bytes) -> str:  # pragma: no cover - stub de produção
    # shortcut: implementar com o SDK do bucket (Vercel Blob/S3/R2) ao deployar na Vercel.
    raise UploadError("Armazenamento em nuvem ainda não configurado (STORAGE_BACKEND=blob).")
