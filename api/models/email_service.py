"""Serviço de envio de e-mail via outbox durável (MAIL-001).

- `enqueue_email(...)`: grava o e-mail na outbox (dentro da transação do chamador
  quando commit=False). Não envia nada por si só.
- `process_outbox(...)`: drena pendentes, envia por SMTP (Flask-Mail) e marca o
  resultado, com contagem de tentativas e limite de retentativas. Idempotente:
  e-mails já 'enviado' são ignorados.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from .email_outbox import EmailOutbox

logger = logging.getLogger(__name__)

MAX_TENTATIVAS = 5


def enqueue_email(destinatario, assunto, corpo_texto, corpo_html=None, *, commit=True):
    """Insere um e-mail na outbox. Com commit=False, participa da transação externa."""
    registro = EmailOutbox(
        destinatario=destinatario,
        assunto=assunto,
        corpo_texto=corpo_texto,
        corpo_html=corpo_html,
        status="pendente",
    )
    db.session.add(registro)
    if commit:
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception("Falha ao enfileirar e-mail na outbox.")
            raise
    else:
        db.session.flush()
    return registro


def process_outbox(*, limite=20):
    """Envia e-mails pendentes. Retorna (enviados, falhos). Best-effort e idempotente."""
    from utils import sendEmail  # import tardio evita ciclo
    pendentes = (
        db.session.execute(
            db.select(EmailOutbox)
            .where(EmailOutbox.status == "pendente", EmailOutbox.tentativas < MAX_TENTATIVAS)
            .order_by(EmailOutbox.id)
            .limit(limite)
        )
        .scalars()
        .all()
    )
    enviados = 0
    falhos = 0
    for item in pendentes:
        item.tentativas += 1
        try:
            sendEmail(item.assunto, item.destinatario, item.corpo_texto, item.corpo_html or "")
            item.status = "enviado"
            item.enviado_em = datetime.now(timezone.utc)
            item.ultimo_erro = None
            enviados += 1
        except Exception as exc:  # noqa: BLE001 — registra e continua
            item.ultimo_erro = str(exc)[:300]
            if item.tentativas >= MAX_TENTATIVAS:
                item.status = "falha"
            falhos += 1
            logger.warning("Falha ao enviar e-mail %s (tentativa %s).", item.id, item.tentativas)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception("Falha ao gravar estado da outbox para o e-mail %s.", item.id)
    return enviados, falhos
