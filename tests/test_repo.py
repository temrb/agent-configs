"""Exercise the CLI in isolated repositories using only the standard library."""

from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parent.parent


class RepoTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="prefine-test-")
        self.addCleanup(self.temporary.cleanup)
        self.outside = Path(self.temporary.name)
        self.repo = self.outside / "repo"
        self.script = self.repo / "scripts/repo.py"
        native = self.repo / "agents/configs/codex/.codex"
        native.mkdir(parents=True)
        (native / "config.toml").write_text('sandbox_mode = "workspace-write"\n')
        shutil.copytree(REPO_ROOT / "scripts", self.script.parent,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.write_json(self.repo / "repo-build.json", {"version": 1, "collections": ["agents/plugins"]})
        self.source = self.repo / "agents/skills/prefine"
        self.destination = self.repo / "agents/plugins/prefine/skills/prefine"
        self.source.mkdir(parents=True)
        self.destination.parent.mkdir(parents=True)
        self.recipe = self.repo / "agents/plugins/prefine/build.json"
        self.write_json(self.recipe, {"version": 1, "steps": [{"generator": "copy-tree", "source": "../../skills/prefine", "output": "skills/prefine"}]})
        (self.source / "SKILL.md").write_bytes(b"---\nname: prefine\n---\n")
        (self.source / "references/nested").mkdir(parents=True)
        (self.source / "references/nested/data.bin").write_bytes(bytes(range(256)))
        (self.source / "scripts/empty").mkdir(parents=True)
        (self.source / "scripts/empty/.gitkeep").touch()
        (self.source / "scripts/helper.py").write_text("print('helper')\n")
        self.sibling = self.destination.parent / "other/SKILL.md"
        self.sibling.parent.mkdir()
        self.sibling.write_bytes(b"sibling skill")

    def write_json(self, path, value):
        import json
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def run_cli(self, *, check=False, succeeds=True):
        result = subprocess.run(
            ["python3", "-B", str(self.script), "sync"] + (["--check"] if check else []),
            cwd=self.outside,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout + result.stderr
        if succeeds:
            self.assertEqual(result.returncode, 0, output)
        else:
            self.assertNotEqual(result.returncode, 0, output)
        self.assertNotIn("Traceback", output)
        return output

    def snapshot(self, root):
        entries = {}
        for path in root.rglob("*"):
            if path.is_symlink():
                value = ("symlink", os.readlink(path))
            elif path.is_file():
                value = ("file", path.read_bytes())
            elif path.is_dir():
                value = ("directory",)
            else:
                value = ("special", path.lstat().st_mode)
            entries[path.relative_to(root).as_posix()] = value
        return entries

    def assert_equal_trees(self):
        self.assertEqual(self.snapshot(self.source), self.snapshot(self.destination))
        self.assertEqual(self.sibling.read_bytes(), b"sibling skill")

    def assert_rejected_without_writes(self):
        before = self.snapshot(self.repo)
        self.run_cli(check=True, succeeds=False)
        self.run_cli(succeeds=False)
        self.assertEqual(self.snapshot(self.repo), before)

    def test_sync_does_not_require_configuration_validator(self):
        shutil.rmtree(self.script.parent / "configs")
        self.run_cli()
        self.run_cli(check=True)

    def test_sync_from_outside_repository_copies_complete_tree(self):
        self.run_cli(check=True, succeeds=False)
        self.assertFalse(self.destination.exists())
        self.run_cli()
        self.run_cli(check=True)
        self.assert_equal_trees()

    def test_check_detects_drift_without_writes_and_sync_repairs_it(self):
        self.run_cli()
        for difference in ("changed", "missing", "extra", "missing directory", "extra directory"):
            with self.subTest(difference=difference):
                target = self.destination / "SKILL.md"
                if difference == "changed":
                    target.write_bytes(b"changed")
                elif difference == "missing":
                    target.unlink()
                elif difference == "extra":
                    (self.destination / "extra.txt").write_bytes(b"extra")
                elif difference == "missing directory":
                    shutil.rmtree(self.destination / "scripts/empty")
                else:
                    (self.destination / "extra-empty").mkdir()
                before = self.snapshot(self.repo)
                output = self.run_cli(check=True, succeeds=False)
                self.assertIn(difference.split()[0], output)
                self.assertEqual(self.snapshot(self.repo), before)
                self.run_cli()
                self.run_cli(check=True)
                self.assert_equal_trees()

    def test_check_detects_file_directory_type_changes(self):
        self.run_cli()
        target = self.destination / "SKILL.md"
        target.unlink()
        target.mkdir()
        self.run_cli(check=True, succeeds=False)
        self.run_cli()
        self.assert_equal_trees()

    def test_rejects_file_directory_and_dangling_symlinks_in_both_trees(self):
        self.run_cli()
        for tree in (self.source, self.destination):
            for target in (self.sibling, self.outside, self.outside / "missing"):
                with self.subTest(tree=tree, target=target):
                    link = tree / "link"
                    link.symlink_to(target, target_is_directory=target.is_dir())
                    try:
                        self.assert_rejected_without_writes()
                    finally:
                        link.unlink()

    def test_rejects_symlinked_tree_roots_and_parent_paths(self):
        self.run_cli()
        for path in (
            self.source, self.source.parent, self.destination,
            self.destination.parent, self.destination.parent.parent,
            self.destination.parent.parent.parent,
        ):
            with self.subTest(path=path):
                saved = path.with_name(path.name + "-saved")
                path.rename(saved)
                path.symlink_to(saved, target_is_directory=True)
                try:
                    self.assert_rejected_without_writes()
                finally:
                    path.unlink()
                    saved.rename(path)

    def test_missing_source_preserves_existing_destination(self):
        self.run_cli()
        shutil.rmtree(self.source)
        self.assert_rejected_without_writes()

    def test_missing_destination_parent_is_created(self):
        shutil.rmtree(self.destination.parent)
        self.run_cli()
        self.assertTrue(self.destination.is_dir())

    def test_destination_type_change_is_repaired(self):
        self.run_cli()
        shutil.rmtree(self.destination)
        self.destination.write_bytes(b"not a directory")
        self.run_cli()
        self.assert_equal_trees()

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation unavailable")
    def test_rejects_special_files_in_both_trees(self):
        self.run_cli()
        for tree in (self.source, self.destination):
            with self.subTest(tree=tree):
                fifo = tree / "fifo"
                os.mkfifo(fifo)
                try:
                    self.assert_rejected_without_writes()
                finally:
                    fifo.unlink()

    def test_multiple_collections_shared_sources_and_multiple_skills(self):
        self.write_json(self.repo / "repo-build.json", {"version": 1, "collections": ["agents/plugins", "agents/bundles"]})
        self.write_json(self.repo / "agents/bundles/second/build.json", {"version": 1, "steps": [
            {"generator": "copy-tree", "source": "../../skills/prefine", "output": "skills/one"},
            {"generator": "copy-tree", "source": "../../skills/prefine", "output": "skills/two"},
        ]})
        self.run_cli()
        before = self.snapshot(self.repo)
        self.run_cli()
        self.assertEqual(before, self.snapshot(self.repo))
        self.run_cli(check=True)
        for name in ("one", "two"):
            self.assertEqual(self.snapshot(self.source), self.snapshot(self.repo / "agents/bundles/second/skills" / name))

    def test_manifest_defaults_and_metadata_propagation(self):
        import json
        manifest = self.recipe.parent / "plugin.json"
        self.write_json(manifest, {"name": "sample", "version": "1.0.0", "description": "first", "author": {"name": "Owner"}})
        self.write_json(self.recipe, {"version": 1, "steps": [{"generator": "codex-manifest", "source": "plugin.json", "output": ".codex-plugin/plugin.json"}]})
        self.run_cli()
        output = self.recipe.parent / ".codex-plugin/plugin.json"
        result = json.loads(output.read_text())
        self.assertEqual(result["keywords"], [])
        self.assertEqual(result["skills"], "./skills")
        self.write_json(manifest, {"name": "updated", "version": "1.0.1", "description": "updated", "author": {"name": "Owner"}, "extensions": {"com.openai": {"interface": {"displayName": "Updated"}}}})
        self.run_cli(check=True, succeeds=False)
        self.run_cli()
        self.assertEqual(json.loads(output.read_text())["interface"], {"displayName": "Updated"})

    def test_current_prefine_manifest_is_reproduced(self):
        import sys
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from generators import codex_manifest
        content = codex_manifest(REPO_ROOT / "agents/plugins/prefine/plugin.json", None)
        self.assertEqual(content[""][0], (REPO_ROOT / "agents/plugins/prefine/.codex-plugin/plugin.json").read_bytes())

    def test_removed_step_or_recipe_cleans_only_owned_output(self):
        self.run_cli()
        self.write_json(self.recipe, {"version": 1, "steps": []})
        self.assertIn("obsolete", self.run_cli(check=True, succeeds=False))
        self.run_cli()
        self.assertFalse(self.destination.exists())
        self.assertEqual(self.sibling.read_bytes(), b"sibling skill")
        self.write_json(self.recipe, {"version": 1, "steps": [{"generator": "copy-tree", "source": "../../skills/prefine", "output": "skills/prefine"}]})
        self.run_cli()
        self.recipe.unlink()
        self.run_cli()
        self.assertFalse(self.destination.exists())
        self.run_cli(check=True)

    def test_invalid_recipes_fail_before_any_entry_writes(self):
        valid = {"generator": "copy-tree", "source": "../../skills/prefine", "output": "skills/prefine"}
        invalid = [
            {"version": 2, "steps": [valid]},
            {"version": 1, "steps": [dict(valid, generator="unknown")]},
            {"version": 1, "steps": [dict(valid, source="../../../../outside")]},
            {"version": 1, "steps": [dict(valid, output="../escape")]},
            {"version": 1, "steps": [valid, dict(valid, output="skills/prefine/nested")]},
            {"version": 1, "steps": [dict(valid, source="skills/prefine")]},
            {"version": 1, "steps": [dict(valid, output="build.json")]},
        ]
        self.destination.mkdir()
        for recipe in invalid:
            with self.subTest(recipe=recipe):
                self.write_json(self.repo / "agents/plugins/z-invalid/build.json", recipe)
                self.assert_rejected_without_writes()

    def test_executable_permissions_are_copied_and_checked(self):
        helper = self.source / "scripts/helper.py"
        helper.chmod(0o755)
        self.run_cli()
        generated = self.destination / "scripts/helper.py"
        self.assertEqual(generated.stat().st_mode & 0o777, 0o755)
        generated.chmod(0o644)
        self.run_cli(check=True, succeeds=False)
        self.run_cli()
        self.assertEqual(generated.stat().st_mode & 0o777, 0o755)

    def test_install_failure_restores_previous_outputs(self):
        import sys
        from unittest.mock import patch
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import repo as engine
        first = self.repo / "first"
        second = self.repo / "second"
        first.write_bytes(b"original one")
        second.write_bytes(b"original two")
        original_rename = Path.rename

        def fail_second_install(path, target):
            if path.name == "1" and Path(target) == second:
                raise OSError("simulated installation failure")
            return original_rename(path, target)

        before = self.snapshot(self.repo)
        with patch.object(engine, "ROOT", self.repo), patch.object(Path, "rename", fail_second_install):
            with self.assertRaisesRegex(OSError, "simulated"):
                engine.install([(first, {"": (b"new one", 0o644)}), (second, {"": (b"new two", 0o644)})])
        self.assertEqual(before, self.snapshot(self.repo))

    def test_first_ownership_rejects_handwritten_content_and_adoption_previews(self):
        self.destination.mkdir()
        personal = self.destination / "personal.txt"
        personal.write_text("keep me")
        self.assert_rejected_without_writes()
        before = self.snapshot(self.repo)
        preview = subprocess.run(["python3", str(self.script), "sync", "--check", "--adopt"], capture_output=True, text=True)
        self.assertIn("personal.txt", preview.stdout)
        self.assertEqual(before, self.snapshot(self.repo))
        result = subprocess.run(["python3", str(self.script), "sync", "--adopt"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(personal.exists())
        self.run_cli(check=True)

    def test_ownership_expansion_protects_unowned_sibling(self):
        self.run_cli()
        self.write_json(self.recipe, {"version": 1, "steps": [{"generator": "copy-tree", "source": "../../skills/prefine", "output": "skills"}]})
        self.assert_rejected_without_writes()
        self.assertEqual(self.sibling.read_bytes(), b"sibling skill")

    def test_identical_existing_tree_can_be_adopted_without_loss(self):
        shutil.copytree(self.source, self.destination)
        self.run_cli()
        self.run_cli(check=True)

    def test_empty_source_directory_requires_placeholder(self):
        (self.source / "empty").mkdir()
        self.assert_rejected_without_writes()

    def test_non_executable_permissions_do_not_cause_drift(self):
        self.run_cli()
        (self.destination / "SKILL.md").chmod(0o600)
        self.run_cli(check=True)

    def test_git_checkout_round_trip(self):
        (self.source / "scripts/helper.py").chmod(0o751)
        self.run_cli()
        def git(*args, cwd=self.repo):
            result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        git("init", "-q")
        git("add", ".")
        git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")
        checkout = self.outside / "checkout"
        git("clone", "-q", str(self.repo), str(checkout))
        result = subprocess.run(["python3", str(checkout / "scripts/repo.py"), "sync", "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((checkout / "agents/plugins/prefine/skills/prefine/scripts/empty/.gitkeep").exists())

    def test_deregistered_inventory_is_rejected(self):
        self.run_cli()
        self.write_json(self.repo / "repo-build.json", {"version": 1, "collections": []})
        self.assert_rejected_without_writes()

    def test_orphan_codex_directory_is_rejected(self):
        self.write_json(self.recipe.parent / ".codex-plugin/plugin.json", {})
        self.recipe.unlink()
        self.assertIn("generated manifest without ownership inventory", self.run_cli(check=True, succeeds=False))

    def test_reserved_manifest_rejects_unowned_extra_content(self):
        self.write_json(self.recipe, {"version": 1, "steps": [
            {"generator": "codex-manifest", "source": "plugin.json", "output": ".codex-plugin/plugin.json"},
        ]})
        self.write_json(self.recipe.parent / "plugin.json", {
            "name": "prefine", "version": "1.0.0", "description": "Refine",
            "author": {"name": "Owner"},
        })
        self.run_cli()
        (self.recipe.parent / ".codex-plugin/extra.txt").write_text("unowned")
        self.assertIn("unexpected generated content without ownership", self.run_cli(check=True, succeeds=False))

    def test_source_boundary_remains_repository_root(self):
        (self.repo / "shared").mkdir()
        (self.repo / "shared/data.txt").write_text("repository source")
        self.write_json(self.recipe, {"version": 1, "steps": [
            {"generator": "copy-tree", "source": "../../../shared", "output": "shared"},
        ]})
        self.run_cli()
        self.run_cli(check=True)
        self.assertEqual((self.recipe.parent / "shared/data.txt").read_text(), "repository source")
        (self.outside / "outside").mkdir()
        (self.outside / "outside/data.txt").write_text("outside source")
        self.write_json(self.recipe, {"version": 1, "steps": [
            {"generator": "copy-tree", "source": "../../../../outside", "output": "shared"},
        ]})
        self.assert_rejected_without_writes()

    def test_validation_discovers_canonical_and_bundled_skills_without_recipe(self):
        self.recipe.unlink()
        self.sibling.unlink()
        self.sibling.parent.rmdir()
        valid = "---\nname: prefine\ndescription: Refine prompts\n---\nInstructions.\n"
        (self.source / "SKILL.md").write_text(valid)
        shutil.copytree(self.source, self.destination)
        (self.recipe.parent / "README.md").write_text("Plugin documentation")
        self.write_json(self.recipe.parent / "plugin.json", {
            "name": "prefine", "version": "1.0.0", "description": "Refine",
            "author": {"name": "Owner"},
        })
        def validate():
            return subprocess.run(["python3", "-B", str(self.script), "validate"],
                                  cwd=self.outside, capture_output=True, text=True)
        result = validate()
        self.assertEqual(result.returncode, 0, result.stderr)
        for directory in (self.source, self.destination):
            with self.subTest(directory=directory):
                (directory / "SKILL.md").write_text("invalid")
                result = validate()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(str(directory / "SKILL.md"), result.stderr)
                (directory / "SKILL.md").write_text(valid)
        self.assertFalse((self.recipe.parent / ".generated.json").exists())

    def test_inventory_input_is_rejected(self):
        self.run_cli()
        self.write_json(self.recipe, {"version": 1, "steps": [{"generator": "copy-tree", "source": ".", "output": "copy"}]})
        self.assert_rejected_without_writes()

    def test_renderer_contract_rejects_unsafe_paths_and_nodes(self):
        import sys
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import repo as engine
        invalid = [
            {"": None, "../escape": (b"x", 0o644)},
            {"": None, "/absolute": (b"x", 0o644)},
            {"": None, "a//b": (b"x", 0o644)},
            {"": None, "a": (b"x", 0o644), "a/b": (b"x", 0o644)},
            {"": ("text", 0o644)}, {"": (b"x", 0o600)},
            {"": None}, {"x": (b"x", 0o644)},
        ]
        for tree in invalid:
            with self.subTest(tree=tree), self.assertRaises(ValueError):
                engine.validate_tree(tree)

    def test_failed_restoration_retains_backup(self):
        import sys
        from unittest.mock import patch
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import repo as engine
        first = self.repo / "first"
        first.write_bytes(b"original")
        original_rename = Path.rename
        def fail(path, target):
            if path.name in ("0", "backup-0"):
                raise OSError("simulated failure")
            return original_rename(path, target)
        with patch.object(engine, "ROOT", self.repo), patch.object(Path, "rename", fail):
            with self.assertRaises(OSError):
                engine.install([(first, {"": (b"new", 0o644)})])
        backups = list(self.repo.glob(".repo-stage-*/backup-0"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), b"original")

    def test_concurrent_sync_is_rejected(self):
        import fcntl
        descriptor = os.open(self.repo, os.O_RDONLY)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertIn("another synchronization", self.run_cli(succeeds=False))
        finally:
            os.close(descriptor)

    def test_asset_validation_is_independent_of_recipes(self):
        self.recipe.unlink()
        self.write_json(self.recipe.parent / "plugin.json", {})
        result = subprocess.run(["python3", str(self.script), "validate"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.recipe.parent / ".generated.json").exists())

    def test_skill_validation_checks_frontmatter_and_resources(self):
        import sys
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import repo as engine
        from validation import skill
        from unittest.mock import patch
        path = self.source / "SKILL.md"
        valid = "---\nname: prefine\ndescription: Refine prompts\n---\nInstructions.\n"
        with patch.object(engine, "ROOT", self.repo):
            path.write_text(valid)
            skill(self.source, self.repo, engine.safe)
            for text in ("no frontmatter", valid.replace("description: Refine prompts\n", ""), valid.replace("name: prefine", "name: other"), valid + "[missing](references/missing.md)"):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    skill(self.source, self.repo, engine.safe)

    def test_interruption_rolls_back_and_pending_stage_blocks_sync(self):
        import sys
        from unittest.mock import patch
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import repo as engine
        first = self.repo / "first"
        first.write_bytes(b"original")
        original_rename = Path.rename
        def interrupt(path, target):
            if path.name == "0":
                raise KeyboardInterrupt()
            return original_rename(path, target)
        with patch.object(engine, "ROOT", self.repo), patch.object(Path, "rename", interrupt):
            with self.assertRaises(KeyboardInterrupt):
                engine.install([(first, {"": (b"new", 0o644)})])
        self.assertEqual(first.read_bytes(), b"original")
        (self.repo / ".repo-stage-interrupted").mkdir()
        self.assertIn("unfinished synchronization", self.run_cli(succeeds=False))

    def test_manifest_rejects_missing_fields_and_wrong_types(self):
        import sys
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from validation import manifest
        valid = {"name": "sample", "version": "1.0.0", "description": "sample", "author": {"name": "Owner"}}
        for value in ({}, dict(valid, keywords="wrong"), dict(valid, skills=[]), dict(valid, extensions=[]), dict(valid, version="1")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                manifest(value)

    def test_plugin_copy_is_portable_without_canonical_source(self):
        portable = self.outside / "portable"
        shutil.copytree(REPO_ROOT / "agents/plugins/prefine", portable)
        self.assertFalse((portable / "skills").is_symlink())
        self.assertFalse(any(path.is_symlink() for path in portable.rglob("*")))
        self.assertEqual(
            (portable / "skills/prefine/SKILL.md").read_bytes(),
            (REPO_ROOT / "agents/skills/prefine/SKILL.md").read_bytes(),
        )
        self.assertTrue((portable / "plugin.json").is_file())
        self.assertTrue((portable / ".codex-plugin/plugin.json").is_file())


if __name__ == "__main__":
    unittest.main()
