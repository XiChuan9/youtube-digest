import json
import tempfile
import unittest
from pathlib import Path

from youtube_digest.config import DigestConfig, load_config, save_config


class ConfigTests(unittest.TestCase):
    def test_save_and_load_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            config = DigestConfig()
            config.default_mode = "faithful"
            config.youtube.channels = ["@example"]

            save_config(config, str(path))
            loaded = load_config(str(path))

            self.assertEqual(loaded.default_mode, "faithful")
            self.assertEqual(loaded.youtube.channels, ["@example"])

    def test_rejects_invalid_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({"default_mode": "loose"}), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_config(str(path))

    def test_json_parse_error_includes_line_column_and_hint(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text('{\n  "default_mode": "magazine",\n}\n', encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_config(str(path))

            message = str(ctx.exception)
            self.assertIn("Invalid JSON", message)
            self.assertIn("line 3", message)
            self.assertIn("trailing commas", message)


if __name__ == "__main__":
    unittest.main()
