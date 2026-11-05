"""Pacote de testes do backend.

Garante que o diretório `api/` (pai deste pacote) esteja no sys.path, para que
os testes possam importar `app`, `models`, etc. como módulos de topo —
independentemente de onde o `unittest` seja executado.
"""
import os
import sys

_API_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _API_DIR not in sys.path:
    sys.path.insert(0, _API_DIR)
