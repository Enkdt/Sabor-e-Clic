"""Imagens de placeholder (stock) para entidades sem foto própria.

Contexto:
  - Em serverless (Vercel) não há `magick` nem disco gravável durável, e a pasta
    `uploads/` é ignorada pelo git. Então o placeholder PADRÃO é um PNG estático
    versionado em `api/static_assets/placeholder.png`, gerado com Pillow (já é
    dependência) — funciona em dev, CI e produção sem depender de ImageMagick.
  - O seed (`seed_demo.py`) ainda pode gerar placeholders coloridos e rotulados com
    `magick` quando disponível (ambiente de desenvolvimento gravável); quando não,
    cai para o placeholder padrão estático.

Uso:
  - `placeholder_url()` -> URL servível do placeholder padrão (para quando um
    restaurante/prato/etc não tem imagem própria).
  - `generate_labeled_placeholder(texto, cor)` -> gera um PNG rotulado em uploads/
    (via magick) e devolve a chave, ou None se o magick não existir.
"""
import logging
import secrets
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).resolve().parent
_STATIC_DIR = _BASE_DIR / "static_assets"
_UPLOAD_DIR = _BASE_DIR / "uploads"
_DEFAULT_NAME = "placeholder.png"

# URL estável servida por blueprints/uploads.py (rota dedicada).
PLACEHOLDER_URL = "/api/placeholder"


def default_placeholder_path() -> Path:
    """Caminho do PNG estático padrão, gerando-o com Pillow se ainda não existir.

    Idempotente. Usa Pillow (sempre disponível) — nada de ImageMagick/rede.
    """
    _STATIC_DIR.mkdir(exist_ok=True)
    destino = _STATIC_DIR / _DEFAULT_NAME
    if destino.is_file():
        return destino
    _render_default_with_pillow(destino)
    return destino


def _render_default_with_pillow(destino: Path) -> None:
    """Desenha um placeholder neutro (fundo + ícone de prato simples) com Pillow."""
    from PIL import Image, ImageDraw

    largura, altura = 600, 400
    fundo = (236, 239, 233)   # verde-acinzentado bem claro (combina com a paleta)
    traco = (122, 138, 110)   # verde oliva suave
    img = Image.new("RGB", (largura, altura), fundo)
    draw = ImageDraw.Draw(img)

    # Ícone simples de "prato" (dois círculos concêntricos) centralizado.
    cx, cy = largura // 2, altura // 2 - 10
    r_externo, r_interno = 90, 60
    draw.ellipse([cx - r_externo, cy - r_externo, cx + r_externo, cy + r_externo],
                 outline=traco, width=8)
    draw.ellipse([cx - r_interno, cy - r_interno, cx + r_interno, cy + r_interno],
                 outline=traco, width=5)
    # Legenda textual (fonte padrão do Pillow; sem depender de fontes do sistema).
    legenda = "Sem imagem"
    try:
        bbox = draw.textbbox((0, 0), legenda)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        tw, th = (len(legenda) * 6, 11)
    draw.text(((largura - tw) / 2, cy + r_externo + 20), legenda, fill=traco)
    img.save(destino, format="PNG")


def placeholder_url() -> str:
    """URL do placeholder padrão. Garante que o arquivo exista antes de referenciá-lo."""
    try:
        default_placeholder_path()
    except Exception:
        # Nunca quebra a serialização por causa do placeholder.
        logger.exception("Falha ao preparar o placeholder padrão.")
    return PLACEHOLDER_URL


def image_url_or_placeholder(key, url_resolver) -> str:
    """Devolve a URL da imagem própria (se houver chave) ou a do placeholder padrão.

    `url_resolver` é tipicamente `storage.url_for_key`.
    """
    if key:
        return url_resolver(key)
    return placeholder_url()


def generate_labeled_placeholder(texto, cor):
    """Gera um PNG rotulado em uploads/ e devolve a chave.

    Tenta ImageMagick (gradiente bonito) e, se indisponível (ex.: Vercel/CI/Windows
    sem `magick`), cai para o Pillow (sempre disponível). Assim o seed SEMPRE produz
    uma foto padrão real para cada restaurante/prato, nunca None.
    """
    _UPLOAD_DIR.mkdir(exist_ok=True)
    key = f"seed_{secrets.token_hex(8)}.png"
    destino = _UPLOAD_DIR / key
    rotulo = (str(texto)[:22]).replace(":", " ")
    try:
        subprocess.run(
            [
                "magick", "-size", "600x400",
                f"gradient:{cor}-#1b1b1b",
                "-gravity", "center",
                "-pointsize", "34", "-fill", "white",
                "-annotate", "0", rotulo,
                str(destino),
            ],
            check=True, capture_output=True, timeout=30,
        )
        return key
    except (subprocess.SubprocessError, FileNotFoundError):
        # magick ausente: gera com Pillow.
        pass
    try:
        _render_labeled_with_pillow(destino, str(texto), cor)
        return key
    except Exception:
        logger.exception("Falha ao gerar placeholder rotulado com Pillow.")
        return None


def _render_labeled_with_pillow(destino: Path, texto: str, cor: str) -> None:
    """Placeholder rotulado via Pillow: fundo na cor da entidade + rótulo centralizado."""
    from PIL import Image, ImageDraw

    largura, altura = 600, 400
    fundo = _hex_to_rgb(cor, (66, 103, 0))
    img = Image.new("RGB", (largura, altura), fundo)
    draw = ImageDraw.Draw(img)
    rotulo = (texto[:24]).strip() or "Sabor & Clic"
    try:
        bbox = draw.textbbox((0, 0), rotulo)
        tw = bbox[2] - bbox[0]
    except Exception:
        tw = len(rotulo) * 6
    draw.text(((largura - tw) / 2, altura / 2 - 6), rotulo, fill=(255, 255, 255))
    img.save(destino, format="PNG")


def _hex_to_rgb(valor, padrao):
    """Converte '#rrggbb' em tupla RGB; devolve `padrao` se inválido."""
    try:
        s = str(valor).lstrip("#")
        if len(s) == 6:
            return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except (ValueError, TypeError):
        pass
    return padrao
