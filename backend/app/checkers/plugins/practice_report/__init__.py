from __future__ import annotations

import importlib
import pkgutil

_pkg_path = __path__
_pkg_name = __name__

for _importer, _modname, _ispkg in pkgutil.iter_modules(_pkg_path):
    importlib.import_module(f"{_pkg_name}.{_modname}")  # nosemgrep
