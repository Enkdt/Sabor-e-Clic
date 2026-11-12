"""Armazenamento de imagens enviadas pelos usuários (STOR-001).

Camada única e trocável: todos os blueprints passam por aqui, então mudar o backend
não exige tocar em rotas.

Backend escolhido por STORAGE_BACKEND:
  - "local" (padrão): grava em api/uploads/ e serve por /api/uploads/<key>. Dev apenas.
  - "blob": Vercel Blob (produção). Gratuito no plano Hobby (1 GB armazenamento +
    10 GB de transferência/mês). Requer BLOB_READ_WRITE_TOKEN no ambiente.

ATENÇÃO (Vercel): o sistema de arquivos é somente-leitura (exceto /tmp, efêmero), então
uploads em disco NÃO persistem entre invocações. Em produção use STORAGE_BACKEND="blob".

Chaves vs URLs:
  - Backend local: a "key" é o nome do arquivo; url_for_key -> /api/uploads/<key>.
  - Backend blob: a "key" guardada é a própria URL pública absoluta do blob; url_for_key
    devolve a URL como está. Assim registros antigos (nome local) e novos (URL blob)
    coexistem sem migração forçada.
"""
import io
import json
import os
import secrets
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, UnidentifiedImageError

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
BACKEND = os.environ.get("STORAGE_BACKEND", "local").lower()

# Tipos aceitos → (extensão canônica, content-type, formato Pillow).
_ALLOWED = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
}
MAX_BYTES = 2 * 1024 * 1024  # 2 MB
MAX_DIMENSION = 4096  # px por lado; barra "image bombs" com dimensões absurdas

_BLOB_API = "https://blob.vercel-storage.com"


class UploadError(ValueError):
    """Arquivo enviado inválido (tipo não permitido, vazio, grande demais ou corrompido)."""


class StorageConfigError(RuntimeError):
    """Backend de armazenamento mal configurado (ex.: token ausente em produção)."""


def _decode_and_reencode(data: bytes):
    """Decodifica a imagem de verdade (API-002) e a re-encoda em um formato seguro.

    Rejeita arquivos que não decodificam (polyglots/corrompidos) ou com dimensões
    absurdas. Remove metadados ao re-encodar. Retorna (bytes, ext, content_type).
    """
    try:
        with Image.open(io.BytesIO(data)) as img:
            fmt = (img.format or "").upper()
            if fmt not in _ALLOWED:
                raise UploadError("Formato inválido. Envie JPEG, PNG ou WebP.")
            img.load()
            if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
                raise UploadError(f"Imagem excede {MAX_DIMENSION}px por lado.")
            ext, content_type = _ALLOWED[fmt]
            saved = img
            if fmt == "JPEG" and img.mode not in ("RGB", "L"):
                saved = img.convert("RGB")
            buffer = io.BytesIO()
            # Re-encoda sem metadados (não repassa EXIF/ICC do original).
            saved.save(buffer, format=fmt)
            return buffer.getvalue(), ext, content_type
    except UploadError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise UploadError("Arquivo de imagem inválido ou corrompido.") from exc


def ensure_configured() -> None:
    """Falha cedo (no boot) se o backend de produção não estiver configurado."""
    if BACKEND == "blob" and not os.environ.get("BLOB_READ_WRITE_TOKEN"):
        raise StorageConfigError(
            "STORAGE_BACKEND=blob requer BLOB_READ_WRITE_TOKEN no ambiente."
        )


def save_image(file_storage) -> str:
    """Valida, re-encoda e grava a imagem. Retorna a chave. Nunca usa o nome do cliente."""
    data = file_storage.read(MAX_BYTES + 1)
    if not data:
        raise UploadError("Arquivo vazio.")
    if len(data) > MAX_BYTES:
        raise UploadError("Imagem acima de 2 MB.")
    clean, ext, content_type = _decode_and_reencode(data)
    key = f"{secrets.token_hex(16)}.{ext}"
    if BACKEND == "blob":
        return _blob_save(key, clean, content_type)
    UPLOAD_DIR.mkdir(exist_ok=True)
    (UPLOAD_DIR / key).write_bytes(clean)
    return key


def url_for_key(key: str) -> str:
    # Backend blob guarda a URL absoluta como key; devolve-a direto.
    if key.startswith("http://") or key.startswith("https://"):
        return key
    return f"/api/uploads/{key}"


def key_exists(key: str) -> bool:
    """API-002: confirma que a chave foi produzida por este armazenamento antes de
    associá-la a um modelo (impede referenciar uma imagem arbitrária)."""
    if not isinstance(key, str) or not key.strip():
        return False
    key = key.strip()
    if key.startswith("https://") or key.startswith("http://"):
        # Chave de blob: deve ser uma URL do nosso domínio de blob.
        return key.startswith(_BLOB_API + "/") or ".blob.vercel-storage.com/" in key
    # Chave local: nome de arquivo simples existente em uploads/ (sem path traversal).
    if "/" in key or "\\" in key or ".." in key:
        return False
    return (UPLOAD_DIR / key).is_file()


def _blob_save(key: str, data: bytes, content_type: str) -> str:
    """Faz PUT no Vercel Blob e devolve a URL pública. Usa só a stdlib (sem SDK)."""
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if not token:
        raise StorageConfigError("BLOB_READ_WRITE_TOKEN ausente.")
    # API do Vercel Blob: PUT https://blob.vercel-storage.com/<pathname>
    request = urllib.request.Request(
        f"{_BLOB_API}/{key}",
        data=data,
        method="PUT",
        headers={
            "authorization": f"Bearer {token}",
            "x-content-type": content_type,
            "x-api-version": "7",
            "x-add-random-suffix": "0",
            "content-type": content_type,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise UploadError("Falha ao enviar a imagem ao armazenamento.") from exc
    url = payload.get("url")
    if not url:
        raise UploadError("Resposta inválida do armazenamento de imagens.")
    return url  # a URL absoluta vira a "key" persistida
