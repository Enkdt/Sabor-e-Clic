"""Drenador da outbox de e-mails (MAIL-001).

Processa e-mails pendentes e aplica retry. Rode periodicamente (cron / job
agendado) para reenviar o que falhou no envio best-effort durante a requisição:

    python drain_outbox.py
"""
import logging


def main():
    logging.basicConfig(level=logging.INFO)
    from app import create_app
    from models.email_service import process_outbox

    app = create_app()
    with app.app_context():
        enviados, falhos = process_outbox(limite=100)
    print(f"Outbox drenada: {enviados} enviado(s), {falhos} falha(s).")


if __name__ == "__main__":
    main()
