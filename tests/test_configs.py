"""Native configuration contracts, independent of generated plugin assets."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from configs.muse import muse_configs
from configs.opencode import opencode_configs
from repo import safe


class NativeConfigTests(unittest.TestCase):
    clients = (("muse", ".config/muse/settings.json", muse_configs),
               ("opencode", ".config/opencode/opencode.json", opencode_configs))

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "repo"
        for client, _, _ in self.clients:
            shutil.copytree(ROOT / "agents/configs" / client,
                            self.root / "agents/configs" / client)

    def test_canonical_sources_and_optional_json(self):
        for client, _, validate in self.clients:
            directory = self.root / "agents/configs" / client
            (directory / "assets").mkdir()
            (directory / "assets/optional.json").write_text('{"enabled": true}')
            validate(self.root, safe)

    def test_missing_required_files(self):
        for client, filename, validate in self.clients:
            with self.subTest(client=client):
                (self.root / "agents/configs" / client / filename).unlink()
                with self.assertRaisesRegex(ValueError, "missing canonical"):
                    validate(self.root, safe)

    def test_invalid_syntax_object_and_encoding(self):
        for client, filename, validate in self.clients:
            for content in (b'{', b'[]', b'null', b'\xff'):
                with self.subTest(client=client, content=content):
                    (self.root / "agents/configs" / client / filename).write_bytes(content)
                    with self.assertRaisesRegex(ValueError, "invalid configuration"):
                        validate(self.root, safe)

    def test_invalid_companion_json(self):
        for client, _, validate in self.clients:
            (self.root / "agents/configs" / client / "extra.json").write_text('{')
            with self.assertRaisesRegex(ValueError, "invalid configuration"):
                validate(self.root, safe)

    def test_runtime_artifacts_at_any_depth(self):
        for client, _, validate in self.clients:
            nested = self.root / "agents/configs" / client / "assets"
            nested.mkdir()
            for name in ("auth.json", "credentials.json", "history.jsonl", "sessions",
                         "logs", "cache", "node_modules", ".env.local", "state.db",
                         "state.sqlite-wal", "trace.log"):
                with self.subTest(client=client, name=name):
                    path = nested / name
                    path.mkdir() if name in ("sessions", "cache") else path.write_text('{}')
                    with self.assertRaisesRegex(ValueError, "private runtime"):
                        validate(self.root, safe)
                    path.rmdir() if path.is_dir() else path.unlink()

    def test_unsafe_symlinks_including_required_file(self):
        outside = self.root.parent / "outside.json"
        outside.write_text('{}')
        for client, filename, validate in self.clients:
            directory = self.root / "agents/configs" / client
            for name in ("asset.json", filename):
                path = directory / name
                if path.exists():
                    path.unlink()
                path.symlink_to(outside)
                with self.assertRaisesRegex(ValueError, "symlink"):
                    validate(self.root, safe)
                path.unlink()

    def test_unsafe_special_files(self):
        import os
        for client, _, validate in self.clients:
            path = self.root / "agents/configs" / client / "pipe"
            os.mkfifo(path)
            with self.assertRaisesRegex(ValueError, "special file"):
                validate(self.root, safe)

    def test_validation_cli_requires_both_clients_without_build_recipes(self):
        shutil.copytree(ROOT / "scripts", self.root / "scripts")
        for client, filename, _ in self.clients:
            path = self.root / "agents/configs" / client / filename
            original = path.read_bytes()
            path.unlink()
            # Codex runs first; provide its minimum native tree.
            codex = self.root / "agents/configs/codex/.codex"
            codex.mkdir(parents=True, exist_ok=True)
            (codex / "config.toml").write_text('')
            result = subprocess.run([sys.executable, '-B', str(self.root / 'scripts/repo.py'),
                                     'validate'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(f'missing canonical {client}', result.stdout + result.stderr)
            path.write_bytes(original)
