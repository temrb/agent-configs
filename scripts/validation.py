"""Repository asset contracts, independent of generation and synchronization.

This is a deliberately bounded local contract, not a general JSON Schema validator.
"""
import json
import re
from agent_paths import CANONICAL_SKILLS, PLUGIN_COLLECTION


def manifest(value, codex=False):
    if not isinstance(value, dict):
        raise ValueError('manifest must be an object')
    for field in ('name', 'version', 'description'):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError(f'manifest requires nonempty {field}')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value['name']):
        raise ValueError('invalid manifest name')
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?', value['version']):
        raise ValueError('manifest version must be semantic version')
    author = value.get('author')
    if not isinstance(author, dict) or not isinstance(author.get('name'), str) or not author['name'].strip():
        raise ValueError('manifest requires author.name')
    if 'keywords' in value and (not isinstance(value['keywords'], list) or not all(isinstance(k, str) for k in value['keywords'])):
        raise ValueError('keywords must be strings')
    if 'skills' in value and (not isinstance(value['skills'], str) or not value['skills']):
        raise ValueError('skills must be a nonempty path')
    extensions = value.get('extensions', {})
    if not isinstance(extensions, dict) or not isinstance(extensions.get('com.openai', {}), dict):
        raise ValueError('invalid extensions')
    interface = value.get('interface') if codex else extensions.get('com.openai', {}).get('interface')
    if interface is not None:
        if not isinstance(interface, dict):
            raise ValueError('interface must be an object')
        for key, item in interface.items():
            if key in ('capabilities', 'defaultPrompt'):
                if not isinstance(item, list) or not all(isinstance(x, str) for x in item):
                    raise ValueError(f'interface {key} must be strings')
            elif not isinstance(item, str):
                raise ValueError(f'interface {key} must be a string')
    if codex and ('skills' not in value or 'keywords' not in value):
        raise ValueError('Codex manifest requires skills and keywords')
    return value


def skill(directory, root, safe):
    path = safe(directory / 'SKILL.md', root)
    text = path.read_text()
    lines = text.splitlines()
    if not lines or lines[0] != '---' or '---' not in lines[1:]:
        raise ValueError(f'missing skill frontmatter: {path}')
    end = lines.index('---', 1)
    fields = {}
    for line in lines[1:end]:
        match = re.fullmatch(r'([a-z][a-z-]*):\s*(.+)', line)
        if not match or match[1] in fields:
            raise ValueError(f'frontmatter must use unique single-line fields: {path}')
        fields[match[1]] = match[2].strip().strip('\"\'')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', fields.get('name', '')) or not fields.get('description'):
        raise ValueError(f'skill requires name and description: {path}')
    if fields['name'] != directory.name or not '\n'.join(lines[end + 1:]).strip():
        raise ValueError(f'skill name/body invalid: {path}')
    for link in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', text):
        if ':' in link or link.startswith('#'):
            continue
        target = safe(directory / link.split('#')[0], root)
        if not target.exists():
            raise ValueError(f'broken skill resource: {path}: {link}')


def validate_assets(root, safe):
    for directory in sorted((root / CANONICAL_SKILLS).iterdir()):
        safe(directory, root)
        if directory.is_dir():
            skill(directory, root, safe)
    for entry in sorted((root / PLUGIN_COLLECTION).iterdir()):
        safe(entry, root)
        if not entry.is_dir():
            continue
        if not safe(entry / 'README.md', root).is_file():
            raise ValueError(f'plugin requires README: {entry}')
        canonical = manifest(json.loads(safe(entry / 'plugin.json', root).read_text()))
        manifests = [(canonical, entry)]
        generated = entry / '.codex-plugin/plugin.json'
        if generated.exists():
            manifests.append((manifest(json.loads(safe(generated, root).read_text()), codex=True), entry))
        for value, base in manifests:
            interface = value.get('interface', value.get('extensions', {}).get('com.openai', {}).get('interface', {}))
            references = [value[key] for key in ('mcp', 'hooks', 'apps') if key in value]
            references.extend(interface[key] for key in ('iconSmall', 'iconLarge', 'logo') if key in interface)
            for reference in references:
                if not isinstance(reference, str) or not reference:
                    raise ValueError(f'resource reference must be a path string: {entry}')
                target = safe(base / reference, entry)
                if not target.is_file():
                    raise ValueError(f'missing manifest resource: {target}')
            resources = safe(base / value.get('skills', './skills'), entry)
            if not resources.is_dir() or not any(resources.iterdir()):
                raise ValueError(f'missing plugin skills: {resources}')
            for directory in resources.iterdir():
                safe(directory, root)
                if not directory.is_dir():
                    raise ValueError(f'skill entry must be a directory: {directory}')
                skill(directory, root, safe)
