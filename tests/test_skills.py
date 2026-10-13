"""Run skill-owned Python suites without feature logic in shared validation.

Each suite runs in its own process so skills may reuse Python module names.
JavaScript suites are dispatched separately by scripts/check.py.
"""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent


class SkillSuiteTests(unittest.TestCase):
    def test_canonical_python_suites(self):
        for directory in sorted((ROOT / 'agents/skills').glob('*/tests')):
            if not any(directory.glob('test_*.py')):
                continue
            with self.subTest(skill=directory.parent.name):
                result = subprocess.run(
                    [sys.executable, '-B', '-m', 'unittest', 'discover',
                     '-s', str(directory)],
                    cwd=ROOT, capture_output=True, text=True, timeout=60,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
