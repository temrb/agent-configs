"""Exercise the complete check runner without rerunning its child suites."""
import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parent.parent / "scripts/check.py"
spec = importlib.util.spec_from_file_location("repository_check", SCRIPT)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class CheckTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="check with spaces ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.root_patch = patch.object(check, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def suite(self, skill, filename):
        path = self.root / "agents/skills" / skill / "tests" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        return str(path)

    def run_check(self, codes=None, runtime=True):
        output = io.StringIO()
        with patch.object(check.shutil, "which", return_value="runtime" if runtime else None), \
                patch.object(check.subprocess, "run") as run, \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            run.side_effect = [subprocess.CompletedProcess([], code) for code in codes] if codes else None
            run.return_value = subprocess.CompletedProcess([], 0)
            status = check.main()
        return status, run.call_args_list, output.getvalue()

    def test_sorted_skill_groups_and_space_paths(self):
        z = self.suite("zeta", "z.test.mjs")
        b = self.suite("alpha", "b with spaces.test.mjs")
        a = self.suite("alpha", "a.test.mjs")
        self.suite("alpha", "ignored.mjs")
        status, calls, _ = self.run_check()
        self.assertEqual(status, 0)
        self.assertEqual([c.args[0] for c in calls[4:]],
                         [["node", "--test", a, b], ["node", "--test", z]])
        self.assertTrue(all(c.kwargs == {"cwd": self.root} for c in calls))

    def test_no_javascript_requires_no_runtimes_and_python_runs_once(self):
        self.suite("python", "test_example.py")
        status, calls, _ = self.run_check(runtime=False)
        self.assertEqual(status, 0)
        self.assertEqual(len(calls), 4)
        python_tests = [c.args[0] for c in calls if "unittest" in c.args[0]]
        self.assertEqual(python_tests, [[sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"]])

    def test_failure_stops_and_preserves_exit_code(self):
        status, calls, output = self.run_check(codes=[0, 7])
        self.assertEqual(status, 7)
        self.assertEqual(len(calls), 2)
        self.assertIn("Python tests failed (exit 7)", output)

    def test_missing_runtimes(self):
        self.suite("example", "a.test.mjs")
        status, calls, output = self.run_check(runtime=False)
        self.assertEqual(status, 1)
        self.assertFalse(calls)
        self.assertIn("node, bun", output)
        self.assertIn("Node 24.19.0 and Bun 1.4.2", output)

    def test_launch_error(self):
        with patch.object(check.subprocess, "run", side_effect=OSError("unavailable")), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as output:
            self.assertEqual(check.main(), 1)
        self.assertIn("could not run: unavailable", output.getvalue())

    def test_script_location_from_another_directory(self):
        # A copied runner and tiny child scripts exercise real cwd/path resolution.
        scripts = self.root / "scripts"
        scripts.mkdir()
        (scripts / "check.py").write_text(SCRIPT.read_text())
        child = "from pathlib import Path\nassert Path.cwd() == Path(__file__).resolve().parent.parent\n"
        (scripts / "check_docs.py").write_text(child)
        (scripts / "repo.py").write_text(child)
        (self.root / "tests").mkdir()
        (self.root / "tests/test_example.py").write_text(
            "import unittest\nclass Example(unittest.TestCase):\n    def test_ok(self): pass\n")
        result = subprocess.run([sys.executable, "-B", str(scripts / "check.py")],
                                cwd=self.root.parent, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count("==>"), 4)
