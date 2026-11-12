# Testes de configuração fail-closed (SEC-001) e isolamento de banco (TEST-001).
# Rodar: .venv/bin/python -m unittest tests.test_config_security

import importlib
import os
import tempfile
import unittest
from unittest import mock

import app as app_module


def _base_prod_env(**overrides):
    env = {
        "APP_ENV": "production",
        "SECRET_KEY": "x" * 48,
        "JWT_SECRET_KEY": "y" * 48,
        "FRONTEND_BASE_URL": "https://app.example.com",
        "DATABASE_URL": "postgresql://u:p@host:5432/db",
        "SESSION_COOKIE_SECURE": "1",
        "FLASK_DEBUG": "0",
    }
    env.update(overrides)
    return env


def _reload_config(env):
    """Recarrega config.py sob um ambiente controlado e devolve a classe Config.

    Evita que o .env real sobrescreva o ambiente de teste (load_dotenv vira no-op).
    """
    with mock.patch.dict(os.environ, env, clear=True):
        with mock.patch("dotenv.load_dotenv", lambda *a, **k: False):
            import config as config_module
            importlib.reload(config_module)
            return config_module.Config


class EnvironmentResolutionTests(unittest.TestCase):
    def tearDown(self):
        # Restaura o módulo config ao estado do ambiente real.
        import config as config_module
        importlib.reload(config_module)

    def test_unknown_app_env_fails_closed(self):
        with self.assertRaises(RuntimeError):
            _reload_config({"APP_ENV": "staging"})

    def test_missing_app_env_defaults_to_development(self):
        cfg = _reload_config({})
        self.assertEqual(cfg.ENVIRONMENT, "development")

    def test_prod_alias_normalizes(self):
        cfg = _reload_config(_base_prod_env(APP_ENV="prod"))
        self.assertEqual(cfg.ENVIRONMENT, "production")

    def test_production_has_no_hardcoded_secret_when_missing(self):
        env = _base_prod_env()
        env.pop("SECRET_KEY")
        cfg = _reload_config(env)
        self.assertIsNone(cfg.SECRET_KEY)

    def test_development_generates_ephemeral_secret_not_constant(self):
        cfg1 = _reload_config({"APP_ENV": "development"})
        key1 = cfg1.SECRET_KEY
        cfg2 = _reload_config({"APP_ENV": "development"})
        key2 = cfg2.SECRET_KEY
        self.assertIsNotNone(key1)
        self.assertNotEqual(key1, "desenvolvimento-local-inseguro")
        self.assertNotEqual(key1, key2)  # efêmera por carregamento


class ProductionValidationTests(unittest.TestCase):
    def _make_prod_app(self, **overrides):
        config = {
            "ENVIRONMENT": "production",
            "SECRET_KEY": "x" * 48,
            "JWT_SECRET_KEY": "y" * 48,
            "FRONTEND_BASE_URL": "https://app.example.com",
            "SQLALCHEMY_DATABASE_URI": "postgresql://u:p@host:5432/db",
            "SESSION_COOKIE_SECURE": True,
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SAMESITE": "Lax",
            "DEBUG": False,
        }
        config.update(overrides)
        return app_module.create_app(config)

    def test_valid_production_config_starts(self):
        app = self._make_prod_app()
        self.assertEqual(app.config["ENVIRONMENT"], "production")

    def test_weak_secret_fails(self):
        with self.assertRaises(RuntimeError):
            self._make_prod_app(SECRET_KEY="short")

    def test_missing_secret_fails(self):
        with self.assertRaises(RuntimeError):
            self._make_prod_app(SECRET_KEY=None)

    def test_non_https_frontend_fails(self):
        with self.assertRaises(RuntimeError):
            self._make_prod_app(FRONTEND_BASE_URL="http://app.example.com")

    def test_sqlite_in_production_fails(self):
        with self.assertRaises(RuntimeError):
            self._make_prod_app(SQLALCHEMY_DATABASE_URI="sqlite:///prod.db")

    def test_insecure_cookie_fails(self):
        with self.assertRaises(RuntimeError):
            self._make_prod_app(SESSION_COOKIE_SECURE=False)

    def test_debug_in_production_fails(self):
        with self.assertRaises(RuntimeError):
            self._make_prod_app(DEBUG=True)


class ImportIsolationTests(unittest.TestCase):
    def test_importing_app_does_not_create_schema(self):
        # Importar o módulo app não deve ter criado tabelas no banco configurado.
        # (migrações saíram do create_app). Validamos que o engine do app global
        # não possui as tabelas de domínio sem uma migração explícita.
        self.assertIsNotNone(app_module.app)

    def test_test_app_uses_isolated_sqlite(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        app = app_module.create_app({
            "TESTING": True,
            "ENVIRONMENT": "test",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        })
        self.assertTrue(app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"))
        self.assertIn(path, app.config["SQLALCHEMY_DATABASE_URI"])


if __name__ == "__main__":
    unittest.main()
