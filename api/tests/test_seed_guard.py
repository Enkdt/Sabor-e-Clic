# SEC-004: o seed de demonstração deve recusar produção mesmo chamado como função.
# Rodar: .venv/bin/python -m unittest tests.test_seed_guard

import tempfile
import unittest

import app as app_module
import seed_demo


class SeedGuardTests(unittest.TestCase):
    def _make_app(self, environment):
        fd, path = tempfile.mkstemp(suffix=".db")
        return app_module.create_app({
            "TESTING": True,
            "ENVIRONMENT": environment,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        })

    def test_seed_refuses_production_when_called_directly(self):
        # create_app com ENVIRONMENT=production exigiria validação completa, então
        # montamos um app de teste e forçamos o contexto a reportar produção.
        app = self._make_app("test")
        app.config["ENVIRONMENT"] = "production"
        with app.app_context():
            with self.assertRaises(RuntimeError):
                seed_demo.seed()


if __name__ == "__main__":
    unittest.main()
