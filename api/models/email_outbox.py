"""Caixa de saída de e-mails (MAIL-001).

Em vez de disparar o envio numa daemon thread — que morre quando a função
serverless congela —, cada e-mail é gravado numa tabela de outbox DENTRO da mesma
transação que cria o usuário/token. Um drenador (`process_outbox`) envia os
pendentes e registra tentativas, de forma idempotente e com retry. Pode ser
chamado best-effort após a resposta e/ou por um cron/CLI.
"""
from datetime import datetime, timezone

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from extensions import db


class EmailOutbox(db.Model):
    __tablename__ = 'email_outbox'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    destinatario: Mapped[str] = mapped_column(String(255), nullable=False)
    assunto: Mapped[str] = mapped_column(String(255), nullable=False)
    corpo_texto: Mapped[str] = mapped_column(Text, nullable=False)
    corpo_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='pendente')  # pendente|enviado|falha
    tentativas: Mapped[int] = mapped_column(nullable=False, default=0)
    ultimo_erro: Mapped[str | None] = mapped_column(String(300), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now(timezone.utc))
    enviado_em: Mapped[datetime | None] = mapped_column(nullable=True)
