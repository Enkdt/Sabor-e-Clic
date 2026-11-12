# Testes da configuração de logging (PROD-001): stdout estruturado, sem arquivo.
# Rodar: .venv/bin/python -m unittest tests.test_logging

import io
import logging
import unittest

import app as app_module


class LoggingConfigTests(unittest.TestCase):
    def setUp(self):
        root = logging.getLogger()
        self._saved_handlers = list(root.handlers)
        self._saved_level = root.level
        # Parte de um estado limpo quanto ao nosso handler.
        root.handlers = [h for h in root.handlers if getattr(h, "name", None) != "sabor-stream"]

    def tearDown(self):
        root = logging.getLogger()
        for h in root.handlers:
            if getattr(h, "name", None) == "sabor-stream":
                root.removeHandler(h)
        root.handlers = self._saved_handlers
        root.setLevel(self._saved_level)

    def _stream_handler(self):
        return next(
            (h for h in logging.getLogger().handlers if getattr(h, "name", None) == "sabor-stream"),
            None,
        )

    def _make_app(self):
        # Não-testing para que _configure_logging rode; SQLite temporário isolado.
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".db")
        return app_module.create_app({
            "TESTING": False,
            "ENVIRONMENT": "development",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        })

    def test_configures_a_single_stream_handler_not_a_file(self):
        app = self._make_app()
        app_module._configure_logging(app)
        handler = self._stream_handler()
        self.assertIsNotNone(handler, "deveria existir um StreamHandler 'sabor-stream'")
        self.assertIsInstance(handler, logging.StreamHandler)
        self.assertNotIsInstance(handler, logging.FileHandler)

    def test_no_duplicate_handlers_on_repeated_configuration(self):
        app = self._make_app()
        app_module._configure_logging(app)
        app_module._configure_logging(app)
        count = sum(
            1 for h in logging.getLogger().handlers if getattr(h, "name", None) == "sabor-stream"
        )
        self.assertEqual(count, 1, "handler de stream não pode ser duplicado")

    def test_connection_strings_are_redacted(self):
        formatter = app_module._RedactingFormatter("%(message)s")
        record = logging.LogRecord(
            "t", logging.INFO, __file__, 1,
            "conectando em postgresql://user:supersecret@host:5432/db agora",
            None, None,
        )
        out = formatter.format(record)
        self.assertNotIn("supersecret", out)
        self.assertIn("[redacted]", out)

    def test_public_urls_are_not_mangled(self):
        formatter = app_module._RedactingFormatter("%(message)s")
        record = logging.LogRecord(
            "t", logging.INFO, __file__, 1,
            "carregando https://vlibras.gov.br/app",
            None, None,
        )
        out = formatter.format(record)
        self.assertIn("https://vlibras.gov.br/app", out)

    def test_info_record_reaches_stdout_stream(self):
        app = self._make_app()
        app_module._configure_logging(app)
        handler = self._stream_handler()
        self.assertIsNotNone(handler)
        buffer = io.StringIO()
        handler.setStream(buffer)
        # Outro módulo de teste pode ter chamado logging.disable(); reabilita aqui.
        self.addCleanup(logging.disable, logging.CRITICAL)
        logging.disable(logging.NOTSET)
        logging.getLogger().setLevel(logging.INFO)
        marker = "TEST_LOGGING_MARKER_42"
        logging.getLogger("test_logging").info(marker)
        handler.flush()
        self.assertIn(marker, buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
