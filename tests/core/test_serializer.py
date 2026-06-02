"""Tests for PickleSerializer and JsonSerializer."""

from __future__ import annotations

from omnicache_ai.core.serializer import JsonSerializer, PickleSerializer


class TestPickleSerializer:
    def setup_method(self):
        self.s = PickleSerializer()

    def test_roundtrip_string(self):
        assert self.s.loads(self.s.dumps("hello")) == "hello"

    def test_roundtrip_dict(self):
        obj = {"key": [1, 2, 3], "nested": {"a": True}}
        assert self.s.loads(self.s.dumps(obj)) == obj

    def test_roundtrip_list(self):
        lst = [1, "two", 3.0, None, True]
        assert self.s.loads(self.s.dumps(lst)) == lst

    def test_roundtrip_bytes(self):
        data = b"\x00\xff\xab"
        assert self.s.loads(self.s.dumps(data)) == data

    def test_roundtrip_none(self):
        assert self.s.loads(self.s.dumps(None)) is None

    def test_dumps_returns_bytes(self):
        assert isinstance(self.s.dumps("hello"), bytes)

    def test_roundtrip_nested_structure(self):
        obj = {"key": [1, 2, {"inner": True}], "flag": None}
        assert self.s.loads(self.s.dumps(obj)) == obj


class TestJsonSerializer:
    def setup_method(self):
        self.s = JsonSerializer()

    def test_roundtrip_string(self):
        assert self.s.loads(self.s.dumps("hello")) == "hello"

    def test_roundtrip_dict(self):
        obj = {"key": [1, 2, 3], "flag": True}
        assert self.s.loads(self.s.dumps(obj)) == obj

    def test_roundtrip_list(self):
        assert self.s.loads(self.s.dumps([1, 2, 3])) == [1, 2, 3]

    def test_roundtrip_none(self):
        assert self.s.loads(self.s.dumps(None)) is None

    def test_dumps_returns_bytes(self):
        assert isinstance(self.s.dumps({"a": 1}), bytes)

    def test_non_json_types_stringify(self):
        # default=str handles non-serializable types
        result = self.s.dumps({"key": object()})
        assert isinstance(result, bytes)

    def test_json_is_valid_utf8(self):
        data = self.s.dumps({"hello": "world"})
        assert data.decode("utf-8")
