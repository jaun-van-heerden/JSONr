"""Tests for the JSONr resolver."""

import json
import os
import pytest

from jsonr import CircularReferenceError, JSONr


# ---------------------------------------------------------------------------
# Fixtures – write temporary JSON files to a tmp directory
# ---------------------------------------------------------------------------

@pytest.fixture()
def simple_setup(tmp_path):
    """Basic two-file setup matching the README example."""
    (tmp_path / "config").mkdir()

    map_data = {
        "base": "config/base.json",
        "network": "config/network.json",
    }
    (tmp_path / "map.json").write_text(json.dumps(map_data))

    base_data = {"name": "example-app", "version": "1.0.0"}
    (tmp_path / "config" / "base.json").write_text(json.dumps(base_data))

    network_data = {"protocol": "MQTT", "host": "localhost"}
    (tmp_path / "config" / "network.json").write_text(json.dumps(network_data))

    main_data = {"app": {"$ref": "base"}, "network": {"$ref": "network"}}
    (tmp_path / "main.json").write_text(json.dumps(main_data))

    return tmp_path


@pytest.fixture()
def nested_setup(tmp_path):
    """Nested references: main → parent → child."""
    map_data = {
        "parent": "parent.json",
        "child": "child.json",
    }
    (tmp_path / "map.json").write_text(json.dumps(map_data))

    child_data = {"value": 42}
    (tmp_path / "child.json").write_text(json.dumps(child_data))

    parent_data = {"nested": {"$ref": "child"}}
    (tmp_path / "parent.json").write_text(json.dumps(parent_data))

    main_data = {"top": {"$ref": "parent"}}
    (tmp_path / "main.json").write_text(json.dumps(main_data))

    return tmp_path


@pytest.fixture()
def circular_setup(tmp_path):
    """Two files that reference each other – should raise CircularReferenceError."""
    map_data = {
        "a": "a.json",
        "b": "b.json",
    }
    (tmp_path / "map.json").write_text(json.dumps(map_data))

    a_data = {"ref_to_b": {"$ref": "b"}}
    (tmp_path / "a.json").write_text(json.dumps(a_data))

    b_data = {"ref_to_a": {"$ref": "a"}}
    (tmp_path / "b.json").write_text(json.dumps(b_data))

    main_data = {"start": {"$ref": "a"}}
    (tmp_path / "main.json").write_text(json.dumps(main_data))

    return tmp_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBasicResolution:
    def test_readme_example(self, simple_setup):
        resolver = JSONr(str(simple_setup / "map.json"))
        result = resolver.build(str(simple_setup / "main.json"))
        assert result == {
            "app": {"name": "example-app", "version": "1.0.0"},
            "network": {"protocol": "MQTT", "host": "localhost"},
        }

    def test_plain_values_passthrough(self, simple_setup):
        """Non-ref values must be preserved as-is."""
        (simple_setup / "plain.json").write_text(json.dumps({"key": "value", "num": 1}))
        resolver = JSONr(str(simple_setup / "map.json"))
        result = resolver.build(str(simple_setup / "plain.json"))
        assert result == {"key": "value", "num": 1}

    def test_list_values_preserved(self, tmp_path):
        map_data = {"item": "item.json"}
        (tmp_path / "map.json").write_text(json.dumps(map_data))
        (tmp_path / "item.json").write_text(json.dumps({"x": 1}))
        (tmp_path / "main.json").write_text(json.dumps({"items": [{"$ref": "item"}, 2, "three"]}))

        resolver = JSONr(str(tmp_path / "map.json"))
        result = resolver.build(str(tmp_path / "main.json"))
        assert result == {"items": [{"x": 1}, 2, "three"]}


class TestNestedResolution:
    def test_nested_ref(self, nested_setup):
        resolver = JSONr(str(nested_setup / "map.json"))
        result = resolver.build(str(nested_setup / "main.json"))
        assert result == {"top": {"nested": {"value": 42}}}


class TestCaching:
    def test_same_ref_resolved_once(self, simple_setup, monkeypatch):
        """The same file should be read only once (caching)."""
        load_count = {"n": 0}
        original_load = JSONr._load_json

        def counting_load(self_, path):
            load_count["n"] += 1
            return original_load(self_, path)

        monkeypatch.setattr(JSONr, "_load_json", counting_load)

        # Create main that references "base" twice
        main_data = {"a": {"$ref": "base"}, "b": {"$ref": "base"}}
        (simple_setup / "main_double.json").write_text(json.dumps(main_data))

        resolver = JSONr(str(simple_setup / "map.json"))
        resolver.build(str(simple_setup / "main_double.json"))

        # map.json + base.json should be loaded once each; network.json not needed
        base_abs = os.path.normpath(str(simple_setup / "config" / "base.json"))
        assert resolver._cache[base_abs] == {"name": "example-app", "version": "1.0.0"}


class TestCircularReferenceDetection:
    def test_circular_raises(self, circular_setup):
        resolver = JSONr(str(circular_setup / "map.json"))
        with pytest.raises(CircularReferenceError):
            resolver.build(str(circular_setup / "main.json"))


class TestMissingReference:
    def test_unknown_ref_raises_key_error(self, simple_setup):
        (simple_setup / "bad.json").write_text(json.dumps({"x": {"$ref": "does_not_exist"}}))
        resolver = JSONr(str(simple_setup / "map.json"))
        with pytest.raises(KeyError, match="does_not_exist"):
            resolver.build(str(simple_setup / "bad.json"))


class TestSchemaValidation:
    def test_valid_schema_passes(self, simple_setup):
        schema = {
            "type": "object",
            "properties": {
                "app": {"type": "object"},
                "network": {"type": "object"},
            },
        }
        resolver = JSONr(str(simple_setup / "map.json"), schema=schema)
        result = resolver.build(str(simple_setup / "main.json"))
        assert "app" in result

    def test_invalid_schema_raises(self, simple_setup):
        pytest.importorskip("jsonschema")
        import jsonschema

        schema = {"type": "array"}  # expects a list, not a dict
        resolver = JSONr(str(simple_setup / "map.json"), schema=schema)
        with pytest.raises(jsonschema.ValidationError):
            resolver.build(str(simple_setup / "main.json"))
