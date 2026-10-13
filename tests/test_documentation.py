"""Check feature documentation ownership, distribution, and shared link validation.

These package tests do not run Prefine's manual semantic evaluation cases.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SKILL = Path("agents/skills/prefine")
PLUGIN = Path("agents/plugins/prefine")
GUIDE = Path("docs/evaluation.md")
CASES = Path("tests/fixtures/prefine-behavior.json")


class DocumentationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="feature-docs-")
        self.addCleanup(self.temporary.cleanup)
        self.outside = Path(self.temporary.name)
        self.repo = self.outside / "repo"
        self.repo.mkdir()
        shutil.copytree(ROOT / "scripts", self.repo / "scripts",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    def run_script(self, script, *args, succeeds=True):
        result = subprocess.run(
            ["python3", "-B", str(self.repo / "scripts" / script), *args],
            cwd=self.outside, capture_output=True, text=True, timeout=10,
        )
        output = result.stdout + result.stderr
        if succeeds:
            self.assertEqual(result.returncode, 0, output)
        else:
            self.assertNotEqual(result.returncode, 0, output)
        return output

    def copy_repository_resources(self):
        for name in ("agents", "docs", ".github", "tests"):
            shutil.copytree(ROOT / name, self.repo / name)
        for name in ("README.md", "repo-build.json", "AGENTS.md"):
            shutil.copy2(ROOT / name, self.repo / name)

    def assert_evaluation_links(self, skill):
        guide = skill / GUIDE
        text = guide.read_text()
        for label, destination in (
            ("case matrix", "../tests/fixtures/prefine-behavior.json"),
            ("skill", "../SKILL.md"),
        ):
            self.assertIn(f"[{label}]({destination})", text)
            target = (guide.parent / destination).resolve()
            self.assertTrue(target.is_relative_to(skill.resolve()))
            self.assertTrue(target.is_file(), target)

    def test_prefine_contract_regenerates_without_development_resources(self):
        self.assertFalse((ROOT / "docs/skills/prefine/evaluation.md").exists())
        self.assertFalse((ROOT / "docs/prefine-evaluation.md").exists())
        self.assertFalse((ROOT / CASES).exists())
        self.assert_evaluation_links(ROOT / SKILL)
        self.copy_repository_resources()
        generated = self.repo / PLUGIN / "skills/prefine"
        (generated / "SKILL.md").unlink()
        self.run_script("repo.py", "sync", "--check", succeeds=False)
        self.run_script("repo.py", "sync")
        self.run_script("repo.py", "sync", "--check")
        for resource in (Path("SKILL.md"),):
            self.assertEqual((generated / resource).read_bytes(),
                             (ROOT / SKILL / resource).read_bytes())
        before = {p.relative_to(self.repo): p.read_bytes()
                  for p in self.repo.rglob("*") if p.is_file()}
        self.run_script("repo.py", "sync")
        after = {p.relative_to(self.repo): p.read_bytes()
                 for p in self.repo.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.run_script("repo.py", "sync", "--check")
        self.run_script("repo.py", "validate")
        self.run_script("check_docs.py")
        portable = self.outside / "portable"
        shutil.copytree(self.repo / PLUGIN, portable)
        shutil.rmtree(self.repo / "agents")
        self.assertEqual({p.name for p in (portable / "skills/prefine").iterdir()}, {"SKILL.md"})
        for resource in (Path("SKILL.md"),):
            self.assertEqual((portable / "skills/prefine" / resource).read_bytes(),
                             (ROOT / SKILL / resource).read_bytes())

    def test_checker_checks_canonical_guides(self):
        self.copy_repository_resources()
        self.run_script("check_docs.py")
        for relative in (SKILL / GUIDE,):
            guide = self.repo / relative
            original = guide.read_text()
            with self.subTest(guide=relative):
                guide.write_text(original.replace("../SKILL.md", "../missing.md"))
                output = self.run_script("check_docs.py", succeeds=False)
                self.assertIn(f"{relative}: missing ../missing.md", output)
                guide.write_text(original)
                self.run_script("check_docs.py")

    def test_checker_discovers_arbitrary_nested_feature_markdown_and_anchors(self):
        (self.repo / "README.md").write_text("# Repository\n")
        for collection in ("skills", "plugins", "configs"):
            relative = Path("agents") / collection / "example/docs/nested/guide.md"
            guide = self.repo / relative
            guide.parent.mkdir(parents=True)
            target = guide.with_name("target.md")
            target.write_text("# Valid heading\n")
            guide.write_text("[target](target.md#valid-heading)\n"
                             "[web](https://example.invalid/missing)\n"
                             "[mail](mailto:example@example.invalid)\n")
            self.run_script("check_docs.py")
            for link, diagnostic in (("missing.md", "missing"),
                                     ("target.md#absent", "missing anchor")):
                with self.subTest(collection=collection, link=link):
                    guide.write_text(f"[broken]({link})\n")
                    output = self.run_script("check_docs.py", succeeds=False)
                    self.assertIn(f"{relative}: {diagnostic} {link}", output)
            guide.write_text("[target](target.md#valid-heading)\n")
