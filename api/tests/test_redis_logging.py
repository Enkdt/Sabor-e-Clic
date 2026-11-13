# Testes do envio de logs ao Redis (Upstash REST).
# O stdout continua sendo o log primário; o Redis é best-effort e opcional.
# Rodar: .venv/bin/python -m unittest tests.test_redis_logging

import json
import logging
import unittest
from unittest import mock

import app as app_module


class _RedisHandlerSetupTests(unittest.TestCase):
    """_configure_redis_logging só anexa o handler quando configurado."""

    def setUp(self):
        self._root = logging.getLogger()
        self._saved = list(self._root.handlers)

    def tearDown(self):
        self._root.handlers = self._saved

    def _fresh_root(self):
        self._root.handlers = [
            h for h in self._root.handlers
            if getattr(h, "name", None) not in ("sabor-redis",)
        ]
        return self._root

    def _app(self, **overrides):
        cfg = {
            "DEBUG": False,
            "UPSTASH_REDIS_REST_URL": None,
            "UPSTASH_REDIS_REST_TOKEN": None,
            "LOG_REDIS_KEY": "logs:app",
            "LOG_REDIS_MAX_ENTRIES": 5000,
            "LOG_REDIS_TIMEOUT": 1.5,
        }
        cfg.update(overrides)
        fake = mock.Mock()
        fake.config = cfg
        return fake

    def _redis_handler(self):
        return next(
            (h for h in self._root.handlers if getattr(h, "name", None) == "sabor-redis"),
            None,
        )

    def test_not_attached_when_unconfigured(self):
        root = self._fresh_root()
        app_module._configure_redis_logging(self._app(), root)
        self.assertIsNone(self._redis_handler())

    def test_not_attached_with_only_url(self):
        root = self._fresh_root()
        app_module._configure_redis_logging(
            self._app(UPSTASH_REDIS_REST_URL="https://x.upstash.io"), root
        )
        self.assertIsNone(self._redis_handler())

    def test_attached_when_configured(self):
        root = self._fresh_root()
        app_module._configure_redis_logging(
            self._app(
                UPSTASH_REDIS_REST_URL="https://x.upstash.io",
                UPSTASH_REDIS_REST_TOKEN="tok",
            ),
            root,
        )
        handler = self._redis_handler()
        self.assertIsNotNone(handler)
        self.assertIsInstance(handler, app_module.UpstashLogHandler)

    def test_not_duplicated_on_repeat(self):
        root = self._fresh_root()
        for _ in range(2):
            app_module._configure_redis_logging(
                self._app(
                    UPSTASH_REDIS_REST_URL="https://x.upstash.io",
                    UPSTASH_REDIS_REST_TOKEN="tok",
                ),
                root,
            )
        count = sum(
            1 for h in root.handlers if getattr(h, "name", None) == "sabor-redis"
        )
        self.assertEqual(count, 1)


class _RedisHandlerEmitTests(unittest.TestCase):
    """Comportamento do emit: payload REST, redação e falha silenciosa."""

    def _handler(self, **kwargs):
        defaults = dict(
            base_url="https://x.upstash.io/",
            token="supersecrettoken",
            key="logs:app",
            max_entries=10,
            timeout=1.5,
        )
        defaults.update(kwargs)
        h = app_module.UpstashLogHandler(**defaults)
        h.setFormatter(app_module._RedactingFormatter("%(message)s"))
        return h

    def _record(self, msg):
        return logging.LogRecord("t", logging.INFO, __file__, 1, msg, None, None)

    def _ok_response(self):
        """Mock de resposta de sucesso do /pipeline: status 200 + array JSON."""
        resp = mock.MagicMock()
        resp.status = 200
        resp.read.return_value = b'[{"result":1},{"result":"OK"}]'
        resp.__enter__ = lambda s: s
        resp.__exit__ = lambda *a: False
        return resp

    def test_emit_sends_lpush_and_ltrim_pipeline(self):
        handler = self._handler()
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["method"] = req.get_method()
            captured["auth"] = req.get_header("Authorization")
            captured["body"] = json.loads(req.data.decode("utf-8"))
            captured["timeout"] = timeout
            return self._ok_response()

        with mock.patch.object(app_module._urllib_request, "urlopen", fake_urlopen):
            handler.emit(self._record("ola mundo"))

        # Endpoint do pipeline, sem barra dupla.
        self.assertEqual(captured["url"], "https://x.upstash.io/pipeline")
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["auth"], "Bearer supersecrettoken")
        self.assertEqual(captured["timeout"], 1.5)
        commands = captured["body"]
        self.assertEqual(commands[0][0], "LPUSH")
        self.assertEqual(commands[0][1], "logs:app")
        self.assertEqual(commands[1], ["LTRIM", "logs:app", "0", "9"])
        # A mensagem vai no payload JSON do LPUSH.
        payload = json.loads(commands[0][2])
        self.assertEqual(payload["message"], "ola mundo")
        self.assertEqual(payload["level"], "INFO")

    def test_token_is_not_in_the_pushed_payload(self):
        handler = self._handler()
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["body_raw"] = req.data.decode("utf-8")
            return self._ok_response()

        with mock.patch.object(app_module._urllib_request, "urlopen", fake_urlopen):
            handler.emit(self._record("nada secreto aqui"))

        # O token só aparece no header, nunca no corpo empurrado ao Redis.
        self.assertNotIn("supersecrettoken", captured["body_raw"])

    def test_connection_strings_are_redacted_in_payload(self):
        handler = self._handler()
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return self._ok_response()

        with mock.patch.object(app_module._urllib_request, "urlopen", fake_urlopen):
            handler.emit(self._record("db postgresql://user:p4ss@host:5432/db"))

        payload = json.loads(captured["body"][0][2])
        self.assertNotIn("p4ss", payload["message"])
        self.assertIn("[redacted]", payload["message"])

    def test_emit_never_raises_on_network_failure(self):
        handler = self._handler()

        def boom(req, timeout=None):
            raise OSError("rede fora")

        with mock.patch.object(app_module._urllib_request, "urlopen", boom), \
                mock.patch.object(handler, "handleError") as handle_error:
            # Não deve propagar: telemetria best-effort nunca derruba o request.
            handler.emit(self._record("qualquer coisa"))
            handle_error.assert_called_once()

    def test_pipeline_error_in_body_is_surfaced(self):
        # Regressão do bug "nenhum log chega": o Upstash pode responder 200 com
        # {"error": ...} por comando. Antes, isso era engolido em silêncio.
        # Agora emit deve detectar e chamar handleError (observável), sem propagar.
        handler = self._handler()

        def error_body(req, timeout=None):
            resp = mock.MagicMock()
            resp.status = 200
            resp.read.return_value = b'[{"error":"WRONGPASS invalid password"}]'
            resp.__enter__ = lambda s: s
            resp.__exit__ = lambda *a: False
            return resp

        with mock.patch.object(app_module._urllib_request, "urlopen", error_body), \
                mock.patch.object(handler, "handleError") as handle_error:
            handler.emit(self._record("qualquer coisa"))
            handle_error.assert_called_once()

    def test_http_error_is_surfaced(self):
        # Um 401/400 (token/URL errados) deve ser detectado, não silenciado.
        handler = self._handler()

        def http_err(req, timeout=None):
            raise app_module._urllib_error.HTTPError(
                req.full_url, 401, "Unauthorized", {}, None)

        with mock.patch.object(app_module._urllib_request, "urlopen", http_err), \
                mock.patch.object(handler, "handleError") as handle_error:
            handler.emit(self._record("qualquer coisa"))
            handle_error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
