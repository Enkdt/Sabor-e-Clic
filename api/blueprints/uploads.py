import logging
from flask import Blueprint, jsonify, request, send_from_directory

from decorators import validar
from utils import err_json
import storage

uploads_bp = Blueprint("uploads", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


@uploads_bp.post("/uploads")
@validar
def enviar_imagem():
    """Recebe uma imagem (multipart, campo 'file'), valida e grava. Retorna a URL servível.

    Exige sessão válida (qualquer papel). Quem pode associar a imagem a um restaurante/prato/
    ingrediente/avatar é controlado nos endpoints de atualização de cada entidade.
    """
    file = request.files.get("file")
    if file is None:
        return err_json("VALIDATION_FAILED", "Envie um arquivo no campo 'file'.", status=400)
    try:
        key = storage.save_image(file)
    except storage.UploadError as exc:
        return err_json("VALIDATION_FAILED", str(exc), status=400)
    return jsonify({"success": True, "key": key, "url": storage.url_for_key(key)}), 201


@uploads_bp.get("/uploads/<path:key>")
def servir_imagem(key):
    # send_from_directory faz safe-join: nega path traversal (../) automaticamente.
    return send_from_directory(storage.UPLOAD_DIR, key)
