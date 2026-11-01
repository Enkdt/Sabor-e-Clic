from functools import wraps
import logging

from flask import g, request, session

from extensions import db
from models import Usuario
from utils import err_json

logger = logging.getLogger(__name__)

admin = "admin"
cook = "cook"
customer = client = "customer"

def user_role(user):
    """Retorna o papel do user"""
    return user.role


def validar(view):
    """Requere um cookie Flask válido com sessão onde o useer existe"""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            logger.warning("Acesso sem sessão válida à rota %s.", request.path)
            return err_json("AUTHENTICATION_REQUIRED", "Faça login para continuar.", status=401)

        user = db.session.get(Usuario, user_id)
        if user is None or session.get("auth_version") != user.auth_version:
            session.clear()
            logger.warning("Sessão ausente, expirada ou revogada na rota %s.", request.path)
            return err_json("INVALID_SESSION", "Sessão inválida ou expirada.", status=401)

        g.current_user = user
        g.current_role = user_role(user)
        if g.current_role is None:
            session.clear()
            logger.warning("Conta sem perfil autorizado tentou acessar %s.", request.path)
            return err_json("INVALID_SESSION", "A conta não possui um perfil válido.", status=401)
        return view(*args, **kwargs)
    return wrapped


def permission(roles):
    """Restringe o acesso a determinado grupo de usuários

    Exemplo: @permission(admin), @permission(client), ou @permission((admin, cook))
    IMPORTANTE: Deve-se usar @validar antes desse decorator para validar o papel e evitar erros.
    """
    allowed = {roles} if isinstance(roles, str) else set(roles)

    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            role = getattr(g, "current_role", None)
            if role is None:
                logger.warning("Acesso sem autenticação a recurso restrito: %s.", request.path)
                return err_json("AUTHENTICATION_REQUIRED", "Faça login para continuar.", status=401)
            if role not in allowed:
                logger.warning("Acesso negado por perfil à rota %s.", request.path)
                return err_json("PERMISSION_DENIED", "Você não tem permissão para acessar este recurso.", status=403)
            return view(*args, **kwargs)
        return wrapped
    return decorate
