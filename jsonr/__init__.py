"""JSONr – JSON Recursive Resolver.

Resolve ``$ref`` references across multiple JSON files with lazy loading,
caching, and circular-reference detection.
"""

from .resolver import CircularReferenceError, JSONr

__all__ = ["JSONr", "CircularReferenceError"]
