"""Validate Prefine evaluator data; this does not run a model evaluation."""
import copy
import json
from pathlib import Path
import unittest


def behavior_cases(value):
    """Validate deterministic case structure, independently of live evaluation."""
    if not isinstance(value, dict) or type(value.get('schema_version')) is not int or value['schema_version'] != 1:
        raise ValueError('unsupported behavior case schema')
    cases = value.get('cases')
    if not isinstance(cases, list) or not cases:
        raise ValueError('behavior cases must be a nonempty list')
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError('behavior case must be an object')
        identifier = case.get('id')
        if not isinstance(identifier, str) or not identifier.strip() or identifier in seen:
            raise ValueError('behavior case IDs must be nonempty and unique')
        seen.add(identifier)
        turns = case.get('turns')
        if not isinstance(turns, list) or not turns or not all(isinstance(t, str) and t.strip() for t in turns):
            raise ValueError('behavior case requires nonempty turns')
        if not isinstance(case.get('expected'), str) or not case['expected'].strip():
            raise ValueError('behavior case requires expectations')


class BehaviorFixtureTests(unittest.TestCase):
    def test_behavior_fixture_structure(self):
        path = Path(__file__).parent / 'fixtures/prefine-behavior.json'
        value = json.loads(path.read_text())
        behavior_cases(value)
        for mutate in (lambda v: v.update(schema_version=True),
                       lambda v: v.update(schema_version=2),
                       lambda v: v['cases'].append(copy.deepcopy(v['cases'][0])),
                       lambda v: v['cases'][0].update(turns=[]),
                       lambda v: v['cases'][0].update(turns=[' ']),
                       lambda v: v['cases'][0].update(expected='')):
            invalid = copy.deepcopy(value)
            mutate(invalid)
            with self.assertRaises(ValueError):
                behavior_cases(invalid)
        neutral = next(c for c in value['cases'] if c['id'] == 'neutral')
        self.assertIn('target: model-neutral/auto\n', neutral['turns'][0])
        self.assertTrue(any(c['id'] == 'unsupported-mixed-target' for c in value['cases']))


if __name__ == "__main__":
    unittest.main()
