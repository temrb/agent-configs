"""Regression probes for audit findings, using isolated filesystem fixtures."""
import fnmatch
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import repo
from check_docs import local_link_errors
from validation import manifest, skill, validate_assets


class RegressionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_interruptions_before_and_after_each_rename(self):
        rename = Path.rename
        for kind in ('file', 'directory', 'inventory', 'new'):
            for operation in ('backup', 'install'):
                if kind == 'new' and operation == 'backup':
                    continue
                for after in (False, True):
                    with self.subTest(kind=kind, operation=operation, after=after):
                        destination = self.root / ('.generated.json' if kind == 'inventory' else 'output')
                        if kind == 'directory':
                            destination.mkdir()
                            (destination / 'original').write_bytes(b'original')
                        elif kind != 'new':
                            destination.write_bytes(b'original')
                        fired = False
                        def interrupt(path, target):
                            nonlocal fired
                            matches = (Path(target).name == 'backup-0' if operation == 'backup'
                                       else path.name == '0')
                            if matches and not fired:
                                fired = True
                                if after:
                                    rename(path, target)
                                raise KeyboardInterrupt()
                            return rename(path, target)
                        with patch.object(repo, 'ROOT', self.root), patch.object(Path, 'rename', interrupt):
                            with self.assertRaises(KeyboardInterrupt):
                                repo.install([(destination, ({'': None, 'new': (b'new', 0o644)}
                                                           if kind == 'directory' else {'': (b'new', 0o644)}))])
                        if kind == 'new':
                            self.assertFalse(destination.exists())
                        elif kind == 'directory':
                            self.assertEqual((destination / 'original').read_bytes(), b'original')
                            shutil.rmtree(destination)
                        else:
                            self.assertEqual(destination.read_bytes(), b'original')
                            destination.unlink()
                        self.assertFalse(list(self.root.glob('.repo-stage-*')))

    def test_failed_restore_keeps_original_backup(self):
        destination = self.root / 'output'
        destination.write_bytes(b'original')
        rename = Path.rename
        def fail(path, target):
            if path.name == '0':
                raise KeyboardInterrupt()
            if path.name == 'backup-0':
                raise OSError('restore failed')
            return rename(path, target)
        with patch.object(repo, 'ROOT', self.root), patch.object(Path, 'rename', fail):
            with self.assertRaises(KeyboardInterrupt):
                repo.install([(destination, {'': (b'new', 0o644)})])
        stages = list(self.root.glob('.repo-stage-*'))
        self.assertEqual(len(stages), 1)
        self.assertEqual((stages[0] / 'backup-0').read_bytes(), b'original')
        self.assertTrue((stages[0] / 'recovery.json').is_file())

    def test_semver_boundaries(self):
        valid = dict(name='sample', version='1.0.0', description='Sample', author={'name': 'Owner'})
        for version in ('0.0.0', '1.0.0-0', '1.0.0-rc.1+build.1', '1.0.0+001', '1.0.0-x-y.z'):
            manifest(dict(valid, version=version))
        for version in ('01.0.0', '1.00.0', '1.0.01', '1.0.0-01', '1.0.0-..',
                        '1.0.0-', '1.0.0+', '1.0.0+build..1', '١.0.0', 'v1.0.0'):
            with self.subTest(version=version), self.assertRaises(ValueError):
                manifest(dict(valid, version=version))

    def test_frontmatter_scalars_and_same_document_anchors(self):
        directory = self.root / 'sample'
        directory.mkdir()
        path = directory / 'SKILL.md'
        for value in ('Plain description', '"Quoted description"', "'It''s useful'", '"Escaped \\"quote\\""'):
            path.write_text(f'---\nname: sample\ndescription: {value}\n---\n# Body\n[body](#body)\n')
            skill(directory, self.root, repo.safe)
        for value in ('"Unterminated', "'Unterminated", '"   "', "'   '", '"bad" trailing', '|'):
            path.write_text(f'---\nname: sample\ndescription: {value}\n---\n# Body\n')
            with self.subTest(value=value), self.assertRaises(ValueError):
                skill(directory, self.root, repo.safe)
        path.write_text('---\nname: sample\ndescription: Valid\n---\n# Body\n[bad](#missing)')
        with self.assertRaisesRegex(ValueError, 'missing anchor'):
            skill(directory, self.root, repo.safe)

    def test_optional_plugin_components(self):
        shutil.copytree(ROOT / 'agents/configs', self.root / 'agents/configs')
        (self.root / 'agents/skills').mkdir()
        plugin = self.root / 'agents/plugins/sample'
        plugin.mkdir(parents=True)
        (plugin / 'README.md').write_text('# Sample')
        (plugin / 'mcp.json').write_text('{}')
        value = dict(name='sample', version='1.0.0', description='Sample', author={'name':'Owner'}, mcp='./mcp.json')
        path = plugin / 'plugin.json'
        path.write_text(json.dumps(value))
        validate_assets(self.root, repo.safe)
        (plugin / 'skills').symlink_to(plugin / 'absent', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            validate_assets(self.root, repo.safe)
        (plugin / 'skills').unlink()
        path.write_text(json.dumps(dict(value, skills='./missing')))
        with self.assertRaisesRegex(ValueError, 'missing plugin skills'):
            validate_assets(self.root, repo.safe)

    def test_reviewer_denies_mutation_delegation_and_services(self):
        value = json.loads((ROOT / 'agents/configs/opencode/.config/opencode/opencode.json').read_text())
        rules = value['permissions'] + value['agents']['reviewer']['permissions']
        def effect(action, resource):
            result = 'ask'
            for rule in rules:
                if fnmatch.fnmatchcase(action, rule['action']) and fnmatch.fnmatchcase(resource, rule['resource']):
                    result = rule['effect']
            return result
        for action, resource in (('shell', 'git diff --no-index --output=protected.md before after'),
                                 ('shell', 'git diff'), ('edit', 'file'), ('subagent', 'build'),
                                 ('execute', '*'), ('service_write', '*'), ('read', '.env.local')):
            with self.subTest(action=action):
                self.assertEqual(effect(action, resource), 'deny')
        self.assertEqual(effect('read', 'source.py'), 'allow')
        self.assertEqual(effect('read', '.env.example'), 'allow')

    def test_all_detached_plugin_markdown_links(self):
        plugin = self.root / 'plugin'
        shutil.copytree(ROOT / 'agents/plugins/prefine', plugin)
        for source in plugin.rglob('*.md'):
            self.assertEqual(local_link_errors(source, plugin), [], source)
        readme = plugin / 'README.md'
        readme.write_text(readme.read_text() + '\n[broken](#missing-section)\n')
        self.assertTrue(local_link_errors(readme, plugin))

    def test_plugin_validation_enforces_package_link_boundary(self):
        shutil.copytree(ROOT / 'agents', self.root / 'agents')
        plugin = self.root / 'agents/plugins/prefine'
        guide = plugin / 'docs/guide.md'
        guide.parent.mkdir()
        guide.write_text('[contract](../skills/prefine/SKILL.md)\n')
        validate_assets(self.root, repo.safe)
        for relative, destination in (
            ('README.md', '../../skills/prefine/SKILL.md'),
            ('skills/prefine/SKILL.md', '../../../../skills/prefine/SKILL.md'),
            ('docs/guide.md', '../../../skills/prefine/SKILL.md'),
        ):
            with self.subTest(file=relative):
                source = plugin / relative
                original = source.read_text()
                source.write_text(original + f'\n[checkout-only]({destination})\n')
                # The destination exists in the repository, but not in the package.
                self.assertTrue((source.parent / destination).is_file())
                with self.assertRaisesRegex(ValueError, 'path must stay inside'):
                    validate_assets(self.root, repo.safe)
                source.write_text(original)
