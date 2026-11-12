# STOR-001: adaptador de armazenamento de imagens (local + Vercel Blob).
# Rodar: .venv/bin/python -m unittest tests.test_storage

import importlib
import io
import os
import unittest
from unittest import mock

from PIL import Image


class _FakeFile:
    def __init__(self, data):
        self._data = data

    def read(self, n=-1):
        return self._data[:n] if n and n > 0 else self._data


def _real_image(fmt, size=(8, 8)):
    buf = io.BytesIO()
    Image.new("RGB", size, (120, 80, 40)).save(buf, format=fmt)
    return buf.getvalue()


_PNG = _real_image("PNG")
_JPEG = _real_image("JPEG")
_GARBAGE = b"not an image at all" + b"\x00" * 64


def _reload_storage(env):
    with mock.patch.dict(os.environ, env, clear=False):
        import storage
        return importlib.reload(storage)


class LocalBackendTests(unittest.TestCase):
    def tearDown(self):
        import storage
        importlib.reload(storage)

    def test_rejects_non_image(self):
        storage = _reload_storage({"STORAGE_BACKEND": "local"})
        with self.assertRaises(storage.UploadError):
            storage.save_image(_FakeFile(_GARBAGE))

    def test_rejects_empty(self):
        storage = _reload_storage({"STORAGE_BACKEND": "local"})
        with self.assertRaises(storage.UploadError):
            storage.save_image(_FakeFile(b""))

    def test_local_round_trip(self):
        storage = _reload_storage({"STORAGE_BACKEND": "local"})
        key = storage.save_image(_FakeFile(_PNG))
        self.assertTrue(key.endswith(".png"))
        self.assertEqual(storage.url_for_key(key), f"/api/uploads/{key}")
        self.assertTrue((storage.UPLOAD_DIR / key).exists())
        (storage.UPLOAD_DIR / key).unlink()

    def test_url_for_absolute_url_is_passthrough(self):
        storage = _reload_storage({"STORAGE_BACKEND": "local"})
        url = "https://blob.vercel-storage.com/abc.png"
        self.assertEqual(storage.url_for_key(url), url)

    def test_rejects_oversized_dimensions(self):
        storage = _reload_storage({"STORAGE_BACKEND": "local"})
        big = _real_image("PNG", size=(storage.MAX_DIMENSION + 1, 4))
        with self.assertRaises(storage.UploadError):
            storage.save_image(_FakeFile(big))

    def test_reencodes_strips_to_clean_image(self):
        # API-002: a saída é uma imagem decodificável (re-encodada), não os bytes crus.
        storage = _reload_storage({"STORAGE_BACKEND": "local"})
        key = storage.save_image(_FakeFile(_JPEG))
        saved = (storage.UPLOAD_DIR / key).read_bytes()
        from PIL import Image as _Img
        with _Img.open(io.BytesIO(saved)) as img:
            self.assertEqual(img.format, "JPEG")
        (storage.UPLOAD_DIR / key).unlink()


class BlobBackendTests(unittest.TestCase):
    def tearDown(self):
        import storage
        importlib.reload(storage)

    def test_blob_requires_token(self):
        env = {"STORAGE_BACKEND": "blob", "BLOB_READ_WRITE_TOKEN": ""}
        with mock.patch.dict(os.environ, env, clear=False):
            import storage
            storage = importlib.reload(storage)
            with self.assertRaises(storage.StorageConfigError):
                storage.ensure_configured()

    def test_blob_save_returns_remote_url(self):
        env = {"STORAGE_BACKEND": "blob", "BLOB_READ_WRITE_TOKEN": "tok_test"}
        with mock.patch.dict(os.environ, env, clear=False):
            import storage
            storage = importlib.reload(storage)
            fake_resp = io.BytesIO(b'{"url": "https://blob.vercel-storage.com/x.jpg"}')
            fake_resp.__enter__ = lambda s: s
            fake_resp.__exit__ = lambda s, *a: False
            with mock.patch("urllib.request.urlopen", return_value=fake_resp):
                key = storage.save_image(_FakeFile(_JPEG))
        self.assertEqual(key, "https://blob.vercel-storage.com/x.jpg")
        self.assertEqual(storage.url_for_key(key), key)


if __name__ == "__main__":
    unittest.main()
