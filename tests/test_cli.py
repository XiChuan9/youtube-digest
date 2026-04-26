import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from youtube_digest.cli import build_parser, main
from youtube_digest.config import load_config


class CliTests(unittest.TestCase):
    def test_generate_accepts_video_url(self):
        args = build_parser().parse_args(
            ["generate", "--video-url", "https://www.youtube.com/watch?v=abc123", "--dry-run"]
        )

        self.assertEqual(args.video_url, "https://www.youtube.com/watch?v=abc123")
        self.assertTrue(args.dry_run)

    def test_channels_add_and_remove(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = str(Path(tmp) / "config.json")

            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--config", config_path, "channels", "add", "@example"]), 0)
            self.assertIn("@example", load_config(config_path).youtube.channels)

            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--config", config_path, "channels", "remove", "@example"]), 0)
            self.assertNotIn("@example", load_config(config_path).youtube.channels)

    def test_json_mode_returns_machine_readable_config_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            config_path.write_text('{\n  "default_mode": "magazine",\n}\n', encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(["--config", str(config_path), "generate", "--dry-run", "--json"])

            self.assertEqual(code, 1)
            self.assertEqual(stderr.getvalue(), "")
            data = json.loads(stdout.getvalue())
            self.assertEqual(data["status"], "failed")
            self.assertIn("Invalid JSON", data["errors"][0])


if __name__ == "__main__":
    unittest.main()
