# -*- coding: utf-8 -*-
"""Command line entry point (same behaviour as the upstream `sherlock` CLI)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sherlock_project.sherlock import main  # noqa: E402

if __name__ == "__main__":
    main()
