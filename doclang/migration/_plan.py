"""Loading the migration steps and planning the chain from a source to a target version (internal).

The steps live in the ``_steps`` package (see there); ``_tree`` holds helpers shared by the steps.
"""

from __future__ import annotations

import importlib
import pkgutil
import re
from collections.abc import Callable
from dataclasses import dataclass

from lxml import etree

from doclang._schemas import _version_key
from doclang.migration import _steps as steps_package
from doclang.migration._tree import Changes

_RELEASED_STEP_RE = re.compile(r"^v(\d+)_(\d+)_to_(\d+)_(\d+)$")

StepFunction = Callable[[etree._Element, Changes], None]


@dataclass(frozen=True)
class Step:
    source: str
    target: str
    apply: StepFunction

    @property
    def down(self) -> bool:
        return _version_key(self.target) < _version_key(self.source)


class NoMigrationPath(Exception):
    """There is no chain of steps from the source to the target version."""


def _load_steps(newest_released: str, head: str | None) -> list[Step]:
    """All steps, down and up.

    ``head`` is the version of the development head, or None if it has no changes of its own (then
    ``from_next.py`` and ``to_next.py`` do not apply).
    """
    steps: list[Step] = []
    for info in pkgutil.iter_modules(steps_package.__path__):
        apply = importlib.import_module(f"{steps_package.__name__}.{info.name}").migrate
        if info.name in ("from_next", "to_next"):
            if head is not None:
                ends = (head, newest_released) if info.name == "from_next" else (newest_released, head)
                steps.append(Step(*ends, apply=apply))
            continue
        match = _RELEASED_STEP_RE.match(info.name)
        if match:
            steps.append(Step(f"{match.group(1)}.{match.group(2)}", f"{match.group(3)}.{match.group(4)}", apply))
    return steps


def _plan(source: str, target: str, steps: list[Step]) -> list[Step]:
    """The steps leading from ``source`` to ``target``.

    Down, every version on the way needs its step, as an older version cannot express everything. Up, steps are
    optional: between two versions without one, a document keeps its meaning and only its version changes.
    """
    if _version_key(source) <= _version_key(target):
        return sorted(
            (
                s
                for s in steps
                if not s.down
                and _version_key(source) <= _version_key(s.source)
                and _version_key(s.target) <= _version_key(target)
            ),
            key=lambda s: _version_key(s.source),
        )
    down = {s.source: s for s in steps if s.down}
    node = source
    path: list[Step] = []
    while node != target:
        step = down.get(node)
        if step is None or _version_key(step.target) < _version_key(target):
            raise NoMigrationPath(f"no migration path from {source} to {target}")
        path.append(step)
        node = step.target
    return path
