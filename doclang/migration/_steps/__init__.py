"""Migration steps, one module each (internal), each defining ``migrate(root, changes)``.

- ``next.py``: from the development head to the newest released spec version.
- ``v<MAJOR>_<MINOR>_to_<MAJOR>_<MINOR>.py``: released steps (``next.py`` renamed at release).
"""
