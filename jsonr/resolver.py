"""Core JSONr resolver implementation."""

import json
import os
from typing import Any, Optional


class CircularReferenceError(Exception):
    """Raised when a circular reference is detected during resolution."""


class JSONr:
    """Recursively resolves JSON ``$ref`` references across multiple files.

    Parameters
    ----------
    map_file:
        Path to a JSON map file whose values are paths to external JSON files.
        The keys become the reference names used in ``$ref`` lookups.
    schema:
        Optional JSON Schema dict used to validate the fully resolved output of
        :meth:`build`.

    Example
    -------
    >>> resolver = JSONr("map.json")
    >>> result = resolver.build("main.json")
    """

    def __init__(self, map_file: str, schema: Optional[dict] = None) -> None:
        self._map_file = map_file
        abs_map = os.path.abspath(map_file)
        self._base_dir = os.path.dirname(abs_map)
        self._schema = schema
        self._cache: dict[str, Any] = {}
        self._ref_map: dict[str, str] = self._load_json(abs_map)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self, main_file: str) -> dict:
        """Resolve all ``$ref`` references in *main_file* and return the result.

        Parameters
        ----------
        main_file:
            Path to the primary JSON file that may contain ``{"$ref": "key"}``
            entries referencing keys defined in the map file.

        Returns
        -------
        dict
            Fully resolved JSON structure.

        Raises
        ------
        CircularReferenceError
            If a circular reference chain is detected.
        jsonschema.ValidationError
            If a *schema* was supplied and the resolved document is invalid.
        """
        data = self._load_json(os.path.abspath(main_file))
        resolved = self._resolve(data, visiting=set())
        if self._schema is not None:
            self._validate(resolved)
        return resolved

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_json(self, path: str) -> Any:
        """Load *path* relative to the map file's directory, with caching."""
        abs_path = path if os.path.isabs(path) else os.path.join(self._base_dir, path)
        abs_path = os.path.normpath(abs_path)
        if abs_path not in self._cache:
            with open(abs_path, encoding="utf-8") as fh:
                self._cache[abs_path] = json.load(fh)
        return self._cache[abs_path]

    def _resolve(self, node: Any, visiting: set) -> Any:
        """Recursively walk *node* and replace every ``$ref`` encountered."""
        if isinstance(node, dict):
            if "$ref" in node and len(node) == 1:
                return self._resolve_ref(node["$ref"], visiting)
            return {key: self._resolve(value, visiting) for key, value in node.items()}
        if isinstance(node, list):
            return [self._resolve(item, visiting) for item in node]
        return node

    def _resolve_ref(self, ref_key: str, visiting: set) -> Any:
        """Look up *ref_key* in the map and return the resolved content."""
        if ref_key not in self._ref_map:
            raise KeyError(f"Reference '{ref_key}' not found in map file '{self._map_file}'")
        if ref_key in visiting:
            raise CircularReferenceError(
                f"Circular reference detected for key '{ref_key}'"
            )
        target_path = self._ref_map[ref_key]
        data = self._load_json(target_path)
        return self._resolve(data, visiting | {ref_key})

    def _validate(self, data: Any) -> None:
        """Validate *data* against the stored JSON Schema (requires jsonschema)."""
        try:
            import jsonschema  # noqa: PLC0415 – optional dependency
        except ImportError as exc:
            raise ImportError(
                "Schema validation requires the 'jsonschema' package. "
                "Install it with: pip install jsonschema"
            ) from exc
        jsonschema.validate(instance=data, schema=self._schema)
