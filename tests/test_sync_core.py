import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

import markdown


spec = importlib.util.spec_from_file_location("sync_core", Path(__file__).resolve().parents[1] / "scripts/sync_core.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class SchemaReferenceTests(unittest.TestCase):
    def test_nested_array_constraints_and_writability_are_preserved(self):
        schema = {"type": "object", "properties": {
            "addresses": {"type": "array", "x-netfyr-writable": True, "items": {
                "type": "object", "required": ["ip"], "properties": {
                    "ip": {"type": "string", "format": "ipv4-cidr", "x-netfyr-writable": True},
                    "lifetime": {"type": "integer", "minimum": 0, "maximum": 3600},
                }}}}}
        sync.validate_schema(schema, "ipv4")
        result = sync.render({"ipv4": schema}, "a" * 40)
        self.assertIn("`ipv4.addresses[].ip` | string | Yes |", result)
        self.assertIn("Required; Format: ipv4-cidr", markdown.markdown(result, extensions=["tables"]))
        self.assertIn("`ipv4.addresses[].lifetime` | integer | No | Minimum: 0; Maximum: 3600", result)

    def test_new_constraints_cannot_silently_disappear(self):
        schema = {"type": "object", "properties": {"name": {"type": "string", "pattern": "^eth"}}}
        with self.assertRaisesRegex(ValueError, "unsupported schema keywords: pattern"):
            sync.validate_schema(schema, "base")

    def test_nested_array_items_keep_their_constraints(self):
        schema = {"type": "object", "properties": {"matrix": {
            "type": "array", "items": {"type": "array", "items": {
                "type": "integer", "minimum": 7}}}}}
        sync.validate_schema(schema, "base")
        self.assertIn("`matrix[][]` | integer | No | Minimum: 7", sync.render({"base": schema}, "a" * 40))

    def test_array_object_items_keep_their_constraints(self):
        schema = {"type": "object", "properties": {"items": {
            "type": "array", "x-netfyr-writable": True, "items": {
                "type": "object", "additionalProperties": False, "properties": {}}}}}
        sync.validate_schema(schema, "base")
        self.assertIn("`items[]` | object | Yes | No additional fields", sync.render({"base": schema}, "a" * 40))

    def test_required_fields_must_exist(self):
        with self.assertRaisesRegex(ValueError, "required fields"):
            sync.validate_schema({"type": "object", "required": ["missing"]}, "base")

    def test_schema_descriptions_cannot_inject_table_cells_or_html(self):
        schema = {"type": "object", "properties": {"name": {
            "type": "string", "description": "one | two\n<script>bad</script>"}}}
        rendered = sync.render({"base": schema}, "a" * 40)
        self.assertIn("one &#124; two &lt;script&gt;bad&lt;/script&gt;", rendered)
        self.assertNotIn("<script>", rendered)

    def test_enum_and_closed_object_constraints_are_visible(self):
        schema = {"type": "object", "additionalProperties": False, "properties": {
            "duplex": {"type": "string", "enum": ["full", "half"]}}}
        result = sync.render({"ethernet": schema}, "a" * 40)
        self.assertIn("Unlisted fields are rejected", result)
        self.assertIn('One of: "full", "half"', result)

    def test_schema_text_stays_literal_after_markdown_rendering(self):
        for text in [
            '[example](javascript:alert%281%29){ onclick="alert(1)" }',
            '![example](x){ onerror="alert(1)" }',
            '`code` **bold** [link](https://example.com) | <b>HTML</b>',
            '--8<-- "office.yaml"',
        ]:
            with self.subTest(text=text):
                schema = {"type": "object", "description": text, "properties": {
                    "name": {"type": "string", "description": text}}}
                reference = sync.render({"base": schema}, "a" * 40)
                rendered = markdown.markdown(reference, extensions=[
                    "tables", "attr_list", "pymdownx.snippets", "pymdownx.superfences"])
                document = ET.fromstring(f"<section>{rendered}</section>")
                self.assertFalse(list(document.iter("img")))
                self.assertFalse(any(name.startswith("on") for element in document.iter()
                                     for name in element.attrib))
                self.assertFalse(any(element.get("href", "").startswith("javascript:")
                                     for element in document.iter("a")))
                self.assertEqual("".join(document.itertext()).count(text), 2)
                self.assertIn("<code>name</code>", rendered)

    def test_objects_are_closed_by_default_in_core(self):
        for setting, closed in [({}, True), ({"additionalProperties": False}, True),
                                ({"additionalProperties": True}, False)]:
            with self.subTest(setting=setting):
                schema = {"type": "object", **setting, "properties": {
                    "nested": {"type": "object", **setting, "properties": {}}}}
                result = sync.render({"base": schema}, "a" * 40)
                self.assertEqual("Unlisted fields are rejected" in result, closed)
                self.assertEqual("No additional fields" in result, closed)

    def test_enums_outside_core_string_dialect_are_rejected(self):
        for schema in [
            {"type": "object", "enum": [{"name": "eth0"}], "properties": {}},
            {"type": "string", "enum": [1]},
            {"type": "string", "enum": "ethernet"},
        ]:
            with self.subTest(schema=schema), self.assertRaises(ValueError):
                sync.validate_schema(schema, "base")

    def test_mutable_refs_and_revision_expressions_are_rejected(self):
        for value in ["main", "HEAD", "a" * 39, "a" * 40 + "^{tree}", None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                sync.revision(value)


if __name__ == "__main__":
    unittest.main()
