# Testes da configuração de logging (Ticket 17 / §7.13).
# Rodar: .venv/bin/python -m unittest test_logging
#

import logging
import os
import unittest
from pathlib import Path

import app as app_module


class LoggingConfigTests(unittest.TestCase):
    def setUp(self):
        self._saved_handlers = list(logging.getLogger().handlers)
        self._saved_level = logging.getLogger().level
        self._saved_env = os.environ.get("WERKZEUG_RUN_MAIN")
        self._saved_cwd = os.getcwd()
        # Remove qualquer handler "sabor-file" para partir de um estado limpo.
        logging.getLogger().handlers = [
            h for h in logging.getLogger().handlers if getattr(h, "name", None) != "sabor-file"
        ]

    def tearDown(self):
        root = logging.getLogger()
        for h in root.handlers:
            if getattr(h, "name", None) == "sabor-file":
                h.close()
        root.handlers = self._saved_handlers
        root.setLevel(self._saved_level)
        os.chdir(self._saved_cwd)
        if self._saved_env is None:
            os.environ.pop("WERKZEUG_RUN_MAIN", None)
        else:
            os.environ["WERKZEUG_RUN_MAIN"] = self._saved_env

    def _file_handler(self):
        return next(
            (h for h in logging.getLogger().handlers if getattr(h, "name", None) == "sabor-file"),
            None,
        )

    def test_log_path_is_anchored_to_api_dir_not_cwd(self):
        os.environ.pop("WERKZEUG_RUN_MAIN", None)
        os.chdir("/tmp")  # CWD diferente de api/
        app_module._configure_logging()
        handler = self._file_handler()
        self.assertIsNotNone(handler, "handler de arquivo deveria ter sido configurado")
        expected = Path(app_module.__file__).resolve().parent / "logs" / "logSabor&Clic.log"
        self.assertEqual(Path(handler.baseFilename), expected)

    def test_reloader_monitor_process_does_not_open_file(self):
        os.environ["WERKZEUG_RUN_MAIN"] = "false"  # processo monitor do reloader
        app_module._configure_logging()
        self.assertIsNone(
            self._file_handler(),
            "o processo monitor não deve abrir o arquivo de log (evita corrupção no rollover)",
        )

    def test_info_record_reaches_the_file(self):
        os.environ.pop("WERKZEUG_RUN_MAIN", None)
        app_module._configure_logging()
        handler = self._file_handler()
        self.assertIsNotNone(handler)
        marker = "TEST_LOGGING_MARKER_42"
        logging.getLogger("test_logging").info(marker)
        handler.flush()
        content = Path(handler.baseFilename).read_bytes().decode("utf-8", "replace")
        self.assertIn(marker, content)


if __name__ == "__main__":
    unittest.main()
