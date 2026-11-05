""" Sherlock Module

This module contains the main logic to search for usernames at social
networks.

"""

from importlib.metadata import version as pkg_version, PackageNotFoundError
import importlib
import pathlib
import sys


def _toml_load(fh):
    """Use stdlib tomllib (3.11+); fall back to the pure-python tomli on 3.10.

    The dynamic import keeps PyInstaller from collecting tomli's mypyc
    compiled extension, which cannot be loaded from a onefile bundle.
    """
    try:
        import tomllib
    except ImportError:
        tomllib = importlib.import_module("tomli")
    return tomllib.load(fh)


def get_version() -> str:
    """Fetch the version number of the installed package.

    PyInstaller relocates __file__, so probe several plausible locations and
    fall back to the bundled version string instead of crashing at import time.
    """
    try:
        return pkg_version("sherlock_project")
    except PackageNotFoundError:
        here = pathlib.Path(__file__).resolve()
        roots = [here.parent, here.parent.parent,
                 pathlib.Path(getattr(sys, "_MEIPASS", here.parent))]
        for root in roots:
            candidate = root / "pyproject.toml"
            if candidate.is_file():
                try:
                    with candidate.open("rb") as f:
                        return _toml_load(f)["tool"]["poetry"]["version"]
                except Exception:
                    continue
        return "0.16.2"

# This variable is only used to check for ImportErrors induced by users running as script rather than as module or package
import_error_test_var = None

__shortname__   = "Sherlock"
__longname__    = "Sherlock: Find Usernames Across Social Networks"
__version__     = get_version()

forge_api_latest_release = "https://api.github.com/repos/sherlock-project/sherlock/releases/latest"
