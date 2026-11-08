"""Migration steps, one module each (internal), each defining ``migrate(root, changes)``.

- ``from_next.py``: from the development head down to the newest released spec version.
- ``to_next.py``: from the newest released spec version up to the development head.
- ``v<MAJOR>_<MINOR>_to_<MAJOR>_<MINOR>.py``: released steps, down or up (``from_next.py`` and ``to_next.py`` renamed
  at release).
"""
