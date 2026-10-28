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
    source: str | None  # None: the development head
    target: str
    apply: StepFunction


class NoMigrationPath(Exception):
    """There is no chain of steps from the source to the target version."""


def _load_steps(newest_released: str) -> dict[str | None, Step]:
    steps: dict[str | None, Step] = {}
    for module_info in pkgutil.iter_modules(steps_package.__path__):
        name = module_info.name
        apply = importlib.import_module(f"{steps_package.__name__}.{name}").migrate
        if name == "next":
            steps[None] = Step(source=None, target=newest_released, apply=apply)
            continue
        match = _RELEASED_STEP_RE.match(name)
        if match:
            source = f"{match.group(1)}.{match.group(2)}"
            steps[source] = Step(source=source, target=f"{match.group(3)}.{match.group(4)}", apply=apply)
    return steps


def _plan(source: str | None, target: str, steps: dict[str | None, Step]) -> list[Step]:
    """The steps leading from ``source`` (None: the head) down to exactly ``target``.

    A source version without a released step of its own is treated as the development head.
    """
    node = source if source in steps else None
    path: list[Step] = []
    while node != target:
        step = steps.get(node)
        if step is None or _version_key(step.target) < _version_key(target):
            raise NoMigrationPath(f"no migration path from {source or 'the latest version'} to {target}")
        path.append(step)
        node = step.target
    return path
