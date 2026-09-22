"""
Load and validate category YAML files.

Inheritance
-----------
A file may declare ``extends: <other_id>``. The child is deep-merged over the
parent:

* mappings (``subscores``, ``generator``, a signal's ``rule``...) merge key by key;
* ``signals`` and ``eligibility`` merge by ``id`` - a child entry with an existing
  id is merged over the parent's entry, new ids are appended;
* ``remove_signals`` / ``remove_eligibility`` drop inherited entries by id;
* any other list or scalar is replaced.

A file with ``abstract: true`` can be extended but is not offered as a category.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import ValidationError

from .schema import Category

CATEGORIES_DIR = Path(__file__).parent / "categories"
_LOADER_KEYS = ("extends", "abstract", "remove_signals", "remove_eligibility")
_ID_LISTS = ("signals", "eligibility")


class CriteriaError(Exception):
    """A category file is missing, malformed or inconsistent."""


def _deep_merge(base: Any, override: Any) -> Any:
    if isinstance(base, dict) and isinstance(override, dict):
        merged = dict(base)
        for key, value in override.items():
            merged[key] = _deep_merge(base[key], value) if key in base else value
        return merged
    return override


def _merge_by_id(parent: List[dict], child: List[dict], removed: List[str], where: str) -> List[dict]:
    known = {item["id"] for item in parent}
    missing = set(removed) - known
    if missing:
        raise CriteriaError(f"{where}: cannot remove unknown id(s) {sorted(missing)}")
    result = {item["id"]: item for item in parent if item["id"] not in removed}
    for item in child:
        if "id" not in item:
            raise CriteriaError(f"{where}: every entry needs an 'id'")
        result[item["id"]] = _deep_merge(result[item["id"]], item) if item["id"] in result else item
    return list(result.values())


def _read_raw(directory: Path) -> Dict[str, dict]:
    raw: Dict[str, dict] = {}
    for path in sorted(directory.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise CriteriaError(f"{path.name}: invalid YAML: {exc}") from None
        if not isinstance(data, dict):
            raise CriteriaError(f"{path.name}: top level must be a mapping")
        if data.get("id") != path.stem:
            raise CriteriaError(f"{path.name}: 'id' must match the file name ('{path.stem}'), got {data.get('id')!r}")
        raw[path.stem] = data
    if not raw:
        raise CriteriaError(f"no category files found in {directory}")
    return raw


def _resolve(cat_id: str, raw: Dict[str, dict], cache: Dict[str, dict], chain: tuple = ()) -> dict:
    if cat_id in cache:
        return cache[cat_id]
    if cat_id in chain:
        raise CriteriaError(f"circular 'extends': {' -> '.join(chain + (cat_id,))}")
    data = raw[cat_id]
    parent_id = data.get("extends")
    if parent_id is None:
        resolved = dict(data)
    else:
        if parent_id not in raw:
            raise CriteriaError(f"{cat_id}.yaml: extends unknown category '{parent_id}'")
        parent = _resolve(parent_id, raw, cache, chain + (cat_id,))
        resolved = _deep_merge({k: v for k, v in parent.items() if k not in _ID_LISTS and k != "abstract"},
                               {k: v for k, v in data.items() if k not in _ID_LISTS})
        for key in _ID_LISTS:
            resolved[key] = _merge_by_id(parent.get(key, []), data.get(key, []),
                                         data.get(f"remove_{key}", []), f"{cat_id}.yaml {key}")
    cache[cat_id] = resolved
    return resolved


def load_categories(directory: Optional[Path] = None) -> Dict[str, Category]:
    """Load every non-abstract category in ``directory``; raise CriteriaError on any problem."""
    directory = Path(directory or CATEGORIES_DIR)
    raw = _read_raw(directory)
    cache: Dict[str, dict] = {}
    categories: Dict[str, Category] = {}

    def depth(cat_id: str, seen: tuple = ()) -> int:
        parent = raw[cat_id].get("extends")
        if parent not in raw or cat_id in seen:
            return 0            # unknown parent / cycle: reported by _resolve
        return 1 + depth(parent, seen + (cat_id,))

    # Validate parents before children so an error is reported against the file that contains it.
    for cat_id in sorted(raw, key=lambda c: (depth(c), c)):
        data = raw[cat_id]
        resolved = _resolve(cat_id, raw, cache)
        if data.get("abstract"):
            continue
        clean = {k: v for k, v in resolved.items() if k not in _LOADER_KEYS}
        try:
            categories[cat_id] = Category.model_validate(clean)
        except ValidationError as exc:
            problems = "\n".join(
                f"  - {'.'.join(str(p) for p in err['loc']) or '(root)'}: {err['msg']}" for err in exc.errors())
            raise CriteriaError(f"{cat_id}.yaml is invalid:\n{problems}") from None
    return categories


_registry: Optional[Dict[str, Category]] = None


def get_registry() -> Dict[str, Category]:
    """Process-wide cached registry of the bundled categories."""
    global _registry
    if _registry is None:
        _registry = load_categories()
    return _registry


def get_category(cat_id: str) -> Category:
    registry = get_registry()
    if cat_id not in registry:
        raise KeyError(f"unknown category '{cat_id}'. Available: {', '.join(sorted(registry))}")
    return registry[cat_id]
