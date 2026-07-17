#!/usr/bin/env python3
"""Non-destructive structural validator for Agent Skills directories.

The validator performs local structural and compatibility checks without
mutating the target skill. It uses PyYAML for complete YAML validation when
available. If PyYAML is unavailable, it falls back to limited top-level
frontmatter parsing and reports reduced validation confidence as a warning.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
XML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
BACKTICK_PATH_RE = re.compile(r"`((?:scripts|references|assets|agents)/[^`\n]+)`")
CLAUDE_ONLY_KEYS = {
    "when_to_use",
    "argument-hint",
    "arguments",
    "disable-model-invocation",
    "user-invocable",
    "disallowed-tools",
    "model",
    "effort",
    "context",
    "agent",
    "hooks",
    "paths",
    "shell",
}
CLAUDE_BOOLEAN_FIELDS = {"disable-model-invocation", "user-invocable"}
CLAUDE_STRING_OR_LIST_FIELDS = {"arguments", "allowed-tools", "disallowed-tools", "paths"}
CLAUDE_STRING_FIELDS = {"when_to_use", "argument-hint", "model", "agent"}
CLAUDE_EFFORT_VALUES = {"low", "medium", "high", "xhigh", "max"}
SUPPORTED_PROFILES = {
    "auto",
    "portable",
    "agentskills",
    "openai",
    "claude-platform",
    "claude-code",
}


@dataclass
class Issue:
    severity: str
    code: str
    message: str
    path: str | None = None


class Reporter:
    def __init__(self) -> None:
        self.issues: list[Issue] = []

    def add(self, severity: str, code: str, message: str, path: Path | None = None) -> None:
        self.issues.append(
            Issue(severity=severity, code=code, message=message, path=str(path) if path else None)
        )

    def error(self, code: str, message: str, path: Path | None = None) -> None:
        self.add("ERROR", code, message, path)

    def warn(self, code: str, message: str, path: Path | None = None) -> None:
        self.add("WARN", code, message, path)

    def info(self, code: str, message: str, path: Path | None = None) -> None:
        self.add("INFO", code, message, path)

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "ERROR" for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(issue.severity == "WARN" for issue in self.issues)

    @property
    def result(self) -> str:
        if self.has_errors:
            return "fail"
        if self.has_warnings:
            return "pass_with_warnings"
        return "pass"


@dataclass
class Frontmatter:
    values: dict[str, Any]
    body: str
    body_line_count: int
    full_yaml_validation: bool


def _decode_scalar(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    if value[0:1] in {"'", '"'} and value[-1:] == value[0:1]:
        try:
            parsed = ast.literal_eval(value)
            return parsed if isinstance(parsed, str) else str(parsed)
        except (SyntaxError, ValueError):
            return value[1:-1]
    # Remove a simple unquoted YAML comment while preserving hashes in words/URLs.
    return re.split(r"\s+#", value, maxsplit=1)[0].rstrip()


def _parse_frontmatter_fallback(fm_lines: list[str], reporter: Reporter, path: Path) -> dict[str, Any]:
    """Parse only top-level scalar/block fields when a YAML library is unavailable."""
    values: dict[str, Any] = {}
    duplicate_keys: list[str] = []

    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line.startswith((" ", "\t")):
            i += 1
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):(?:\s*(.*))?$", line)
        if not match:
            reporter.warn(
                "frontmatter.unparsed-line",
                f"Could not interpret top-level frontmatter line {i + 2}: {line!r}.",
                path,
            )
            i += 1
            continue

        key = match.group(1)
        raw_value = (match.group(2) or "").strip()
        if key in values:
            duplicate_keys.append(key)

        if raw_value in {"|", "|-", "|+", ">", ">-", ">+"}:
            block: list[str] = []
            i += 1
            while i < len(fm_lines):
                candidate = fm_lines[i]
                if candidate and not candidate.startswith((" ", "\t")):
                    break
                block.append(candidate.lstrip())
                i += 1
            if raw_value.startswith(">"):
                values[key] = " ".join(part.strip() for part in block if part.strip())
            else:
                values[key] = "\n".join(block).strip("\n")
            continue

        values[key] = _decode_scalar(raw_value) if raw_value else None
        i += 1

    for key in duplicate_keys:
        reporter.error("frontmatter.duplicate-key", f"Duplicate top-level frontmatter key: {key}.", path)

    return values


def _parse_yaml_mapping(raw_yaml: str, reporter: Reporter, path: Path) -> tuple[dict[str, Any] | None, bool]:
    try:
        import yaml  # type: ignore
        from yaml.constructor import ConstructorError  # type: ignore
    except ImportError:
        reporter.warn(
            "frontmatter.yaml-partial",
            "PyYAML is unavailable; frontmatter received limited top-level checks only, so nested YAML syntax and field types are not fully validated.",
            path,
        )
        return None, False

    class DuplicateKeyError(ConstructorError):
        pass

    class UniqueKeyLoader(yaml.SafeLoader):  # type: ignore[name-defined, misc]
        pass

    def construct_mapping(loader: Any, node: Any, deep: bool = False) -> dict[Any, Any]:
        loader.flatten_mapping(node)
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            try:
                duplicate = key in mapping
            except TypeError as exc:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found an unhashable key",
                    key_node.start_mark,
                ) from exc
            if duplicate:
                raise DuplicateKeyError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key {key!r}",
                    key_node.start_mark,
                )
            mapping[key] = loader.construct_object(value_node, deep=deep)
        return mapping

    UniqueKeyLoader.add_constructor(  # type: ignore[attr-defined]
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping  # type: ignore[name-defined]
    )

    try:
        parsed = yaml.load(raw_yaml, Loader=UniqueKeyLoader)  # type: ignore[name-defined]
    except DuplicateKeyError as exc:
        reporter.error("frontmatter.duplicate-key", f"SKILL.md frontmatter contains a duplicate YAML key: {exc.problem}.", path)
        return None, True
    except yaml.YAMLError as exc:  # type: ignore[name-defined]
        reporter.error("frontmatter.yaml-invalid", f"SKILL.md frontmatter is not valid YAML: {exc}.", path)
        return None, True

    if parsed is None:
        parsed = {}
    if not isinstance(parsed, dict):
        reporter.error("frontmatter.root", "SKILL.md frontmatter must contain a YAML mapping at the root.", path)
        return None, True
    if any(not isinstance(key, str) for key in parsed):
        reporter.error("frontmatter.key-type", "All top-level frontmatter keys must be strings.", path)
        return None, True

    return parsed, True


def parse_frontmatter(text: str, reporter: Reporter, path: Path) -> Frontmatter | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        reporter.error("frontmatter.missing", "SKILL.md must start with YAML frontmatter delimited by ---.", path)
        return None

    closing = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing = index
            break
    if closing is None:
        reporter.error("frontmatter.unclosed", "SKILL.md frontmatter has no closing --- delimiter.", path)
        return None

    fm_lines = lines[1:closing]
    body_lines = lines[closing + 1 :]
    raw_yaml = "\n".join(fm_lines)
    values, full_yaml_validation = _parse_yaml_mapping(raw_yaml, reporter, path)
    if full_yaml_validation and values is None:
        return None
    if values is None:
        values = _parse_frontmatter_fallback(fm_lines, reporter, path)

    return Frontmatter(
        values=values,
        body="\n".join(body_lines),
        body_line_count=len(body_lines),
        full_yaml_validation=full_yaml_validation,
    )


def normalize_anthropic_root(value: str) -> str:
    """Claude API root matching is case- and underscore-insensitive only."""
    return value.strip().lower().replace("_", "-")


def detect_profile(root: Path, fm: Frontmatter) -> str:
    parts = {part.lower() for part in root.parts}
    if (root / "agents" / "openai.yaml").exists() or ".agents" in parts:
        return "openai"
    if ".claude" in parts or CLAUDE_ONLY_KEYS.intersection(fm.values):
        return "claude-code"
    return "portable"


def validate_frontmatter_types(root: Path, fm: Frontmatter, profile: str, reporter: Reporter) -> None:
    values = fm.values
    path = root / "SKILL.md"

    for field in ("license", "compatibility"):
        if field in values and values[field] is not None and not isinstance(values[field], str):
            reporter.error(f"{field}.type", f"{field} must be a string when present.", path)

    if fm.full_yaml_validation and "metadata" in values:
        metadata = values["metadata"]
        if not isinstance(metadata, dict):
            reporter.error("metadata.shape", "metadata must be a YAML mapping when present.", path)
        elif any(not isinstance(key, str) or not isinstance(value, str) for key, value in metadata.items()):
            reporter.error("metadata.value-type", "metadata must map string keys to string values.", path)

    if profile in {"portable", "agentskills", "openai", "claude-platform"}:
        if fm.full_yaml_validation and "allowed-tools" in values and not isinstance(values["allowed-tools"], str):
            reporter.error(
                "allowed-tools.type",
                "The portable Agent Skills allowed-tools field must be a space-separated string.",
                path,
            )


def validate_name_and_description(root: Path, fm: Frontmatter, profile: str, reporter: Reporter) -> None:
    values = fm.values
    strict_required = profile in {"portable", "agentskills", "openai", "claude-platform"}

    name = values.get("name")
    description = values.get("description")

    if strict_required and not isinstance(name, str):
        reporter.error("name.missing", f"Profile {profile} requires a string name field.", root / "SKILL.md")
    if strict_required and not isinstance(description, str):
        reporter.error(
            "description.missing",
            f"Profile {profile} requires a string description field.",
            root / "SKILL.md",
        )

    if profile == "claude-code" and not isinstance(description, str):
        reporter.warn(
            "description.recommended",
            "Claude Code can load skills without a description, but a description is recommended for automatic discovery.",
            root / "SKILL.md",
        )

    if isinstance(name, str):
        if not (1 <= len(name) <= 64):
            reporter.error("name.length", "name must be 1-64 characters.", root / "SKILL.md")
        if profile in {"portable", "agentskills", "openai", "claude-platform"} and not NAME_RE.fullmatch(name):
            reporter.error(
                "name.syntax",
                "name must use lowercase ASCII letters, digits, and single hyphens, without leading/trailing hyphens.",
                root / "SKILL.md",
            )
        if profile in {"portable", "claude-platform"}:
            lowered = name.lower()
            if "anthropic" in lowered or "claude" in lowered:
                reporter.error(
                    "name.anthropic-reserved",
                    "Anthropic-compatible skill names must not contain the reserved words 'anthropic' or 'claude'.",
                    root / "SKILL.md",
                )
            if XML_TAG_RE.search(name):
                reporter.error("name.xml", "Anthropic-compatible name must not contain XML tags.", root / "SKILL.md")

        if profile in {"portable", "agentskills", "openai"} and root.name != name:
            reporter.error(
                "name.directory-mismatch",
                f"Directory name {root.name!r} must exactly match frontmatter name {name!r} for profile {profile}.",
                root,
            )
        elif profile == "claude-platform" and normalize_anthropic_root(root.name) != normalize_anthropic_root(name):
            reporter.error(
                "name.directory-mismatch",
                "Claude Platform upload root must match the frontmatter name, ignoring only case and underscore-vs-hyphen differences.",
                root,
            )

    if isinstance(description, str):
        if not (1 <= len(description) <= 1024):
            reporter.error("description.length", "description must be 1-1024 characters.", root / "SKILL.md")
        if profile in {"portable", "claude-platform"} and XML_TAG_RE.search(description):
            reporter.error(
                "description.xml",
                "Anthropic-compatible description must not contain XML tags.",
                root / "SKILL.md",
            )
        lowered = description.lower()
        trigger_markers = ("use when", "use for", "when ", "asked", "working with", "requests")
        if not any(marker in lowered for marker in trigger_markers):
            reporter.warn(
                "description.activation-scope",
                "Description may not clearly state when the skill should activate.",
                root / "SKILL.md",
            )
        if lowered.startswith("i ") or lowered.startswith("you "):
            reporter.warn(
                "description.point-of-view",
                "Descriptions are generally clearer for discovery when written in third person.",
                root / "SKILL.md",
            )

    compatibility = values.get("compatibility")
    if isinstance(compatibility, str) and not (1 <= len(compatibility) <= 500):
        reporter.error("compatibility.length", "compatibility must be 1-500 characters when present.", root / "SKILL.md")

    if "allowed-tools" in values and profile in {"portable", "agentskills", "openai"}:
        reporter.warn(
            "allowed-tools.portability",
            "allowed-tools support/semantics vary by client; verify it against the intended runtime.",
            root / "SKILL.md",
        )


def validate_claude_code_fields(root: Path, fm: Frontmatter, reporter: Reporter) -> None:
    if not fm.full_yaml_validation:
        return

    values = fm.values
    path = root / "SKILL.md"

    for field in CLAUDE_BOOLEAN_FIELDS:
        if field in values and not isinstance(values[field], bool):
            reporter.error(f"claude.{field}.type", f"{field} must be a boolean when present.", path)

    for field in CLAUDE_STRING_FIELDS:
        if field in values and not isinstance(values[field], str):
            reporter.error(f"claude.{field}.type", f"{field} must be a string when present.", path)

    for field in CLAUDE_STRING_OR_LIST_FIELDS:
        if field not in values:
            continue
        value = values[field]
        if isinstance(value, str):
            continue
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            continue
        reporter.error(
            f"claude.{field}.type",
            f"{field} must be a string or a YAML list of strings when present.",
            path,
        )

    if "context" in values and values["context"] != "fork":
        reporter.error("claude.context.value", "context currently supports the value 'fork' when present.", path)

    if "effort" in values:
        effort = values["effort"]
        if not isinstance(effort, str) or effort not in CLAUDE_EFFORT_VALUES:
            reporter.error(
                "claude.effort.value",
                f"effort must be one of: {', '.join(sorted(CLAUDE_EFFORT_VALUES))}.",
                path,
            )

    if "shell" in values and values["shell"] not in {"bash", "powershell"}:
        reporter.error("claude.shell.value", "shell must be either 'bash' or 'powershell'.", path)

    if "hooks" in values and not isinstance(values["hooks"], dict):
        reporter.error("claude.hooks.type", "hooks must be a YAML mapping when present.", path)

    if values.get("agent") is not None and values.get("context") != "fork":
        reporter.warn(
            "claude.agent-without-fork",
            "agent is only meaningful when context: fork is configured.",
            path,
        )


def _clean_reference(raw: str) -> str | None:
    value = raw.strip().strip("<>")
    if not value or value.startswith(("#", "http://", "https://", "mailto:", "data:")):
        return None
    value = value.split("#", 1)[0].split("?", 1)[0].strip()
    if not value:
        return None
    if any(token in value for token in ("<", ">", "*", "$", "{")):
        return None
    return value


def referenced_paths(skill_md: str) -> Iterable[str]:
    seen: set[str] = set()
    for match in MARKDOWN_LINK_RE.finditer(skill_md):
        ref = _clean_reference(match.group(1))
        if ref and ref not in seen:
            seen.add(ref)
            yield ref
    for match in BACKTICK_PATH_RE.finditer(skill_md):
        ref = _clean_reference(match.group(1).rstrip(".,;:"))
        if ref and ref not in seen:
            seen.add(ref)
            yield ref


def validate_references(root: Path, text: str, reporter: Reporter) -> None:
    for ref in referenced_paths(text):
        if "\\" in ref:
            reporter.warn("reference.backslash", f"Use forward slashes in relative paths: {ref}", root / "SKILL.md")
        target = root / ref
        if not target.exists():
            reporter.error("reference.missing", f"Referenced local path does not exist: {ref}", root / "SKILL.md")
        if ref.count("/") > 1:
            reporter.warn(
                "reference.depth",
                f"Reference is more than one directory level deep from SKILL.md: {ref}",
                root / "SKILL.md",
            )


def _resolve_skill_asset(root: Path, raw: str, reporter: Reporter, path: Path, key: str) -> None:
    value = raw.strip()
    if not value:
        reporter.error("openai.icon-empty", f"{key} must not be empty when configured.", path)
        return
    if value.startswith(("http://", "https://", "data:")):
        reporter.warn(
            "openai.icon-nonlocal",
            f"{key} is not a local skill asset path and cannot be verified by this validator: {value}",
            path,
        )
        return

    candidate = (root / value).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        reporter.error(
            "openai.icon-outside-root",
            f"{key} must resolve inside the skill root for portable packaging: {value}",
            path,
        )
        return

    if not candidate.exists():
        reporter.error("openai.icon-missing", f"{key} path does not exist: {value}", path)


def validate_openai_yaml(root: Path, reporter: Reporter) -> None:
    path = root / "agents" / "openai.yaml"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        reporter.error("openai.empty", "agents/openai.yaml is empty.", path)
        return

    try:
        import yaml  # type: ignore
    except ImportError:
        reporter.warn(
            "openai.yaml-partial",
            "PyYAML is unavailable; agents/openai.yaml received lightweight checks only.",
            path,
        )
        policy_match = re.search(r"(?m)^\s*allow_implicit_invocation:\s*([^#\n]+)", text)
        if policy_match and policy_match.group(1).strip().lower() not in {"true", "false"}:
            reporter.error(
                "openai.policy-type",
                "policy.allow_implicit_invocation must be a boolean when present.",
                path,
            )
        for key in ("icon_small", "icon_large"):
            match = re.search(rf"(?m)^\s*{key}:\s*[\"']?([^\"'\n#]+)", text)
            if match:
                _resolve_skill_asset(root, match.group(1).strip(), reporter, path, key)
        return

    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        reporter.error("openai.yaml-invalid", f"agents/openai.yaml could not be parsed: {exc}", path)
        return
    if not isinstance(parsed, dict):
        reporter.error("openai.yaml-root", "agents/openai.yaml must contain a YAML mapping at the root.", path)
        return

    interface = parsed.get("interface")
    if interface is not None and not isinstance(interface, dict):
        reporter.error("openai.interface-shape", "interface must be a mapping when present.", path)
    if isinstance(interface, dict):
        for key in ("icon_small", "icon_large"):
            if key in interface:
                value = interface[key]
                if not isinstance(value, str):
                    reporter.error("openai.icon-type", f"interface.{key} must be a string path.", path)
                else:
                    _resolve_skill_asset(root, value, reporter, path, key)

    policy = parsed.get("policy")
    if policy is not None and not isinstance(policy, dict):
        reporter.error("openai.policy-shape", "policy must be a mapping when present.", path)
    if isinstance(policy, dict) and "allow_implicit_invocation" in policy and not isinstance(
        policy["allow_implicit_invocation"], bool
    ):
        reporter.error("openai.policy-type", "allow_implicit_invocation must be boolean.", path)

    dependencies = parsed.get("dependencies")
    if dependencies is not None and not isinstance(dependencies, dict):
        reporter.error("openai.dependencies-shape", "dependencies must be a mapping when present.", path)
    if isinstance(dependencies, dict) and "tools" in dependencies and not isinstance(dependencies["tools"], list):
        reporter.error("openai.dependencies-tools-shape", "dependencies.tools must be a YAML list when present.", path)


def scan_runtime_constraints(root: Path, profile: str, reporter: Reporter) -> None:
    if profile not in {"portable", "claude-platform"}:
        return

    compatibility_text = ""
    skill_md = root / "SKILL.md"
    if skill_md.exists():
        compatibility_text = skill_md.read_text(encoding="utf-8", errors="replace").lower()
    if re.search(r"compatibility:.*\b(requires?|needs?)\b.*\b(internet|network)\b", compatibility_text):
        reporter.warn(
            "claude.network-requirement",
            "Declared network requirement is incompatible with Claude API code-execution runtime unless execution occurs elsewhere.",
            skill_md,
        )

    script_dir = root / "scripts"
    if not script_dir.exists():
        return

    install_patterns = [
        re.compile(r"\bpip(?:3)?\s+install\b"),
        re.compile(r"\bnpm\s+install\b"),
        re.compile(r"\bapt(?:-get)?\s+install\b"),
        re.compile(r"\bbrew\s+install\b"),
    ]
    network_patterns = [
        re.compile(r"\brequests\."),
        re.compile(r"\burllib\."),
        re.compile(r"\bcurl\s+"),
        re.compile(r"\bwget\s+"),
        re.compile(r"\bfetch\s*\("),
    ]

    for path in script_dir.rglob("*"):
        if not path.is_file() or path.stat().st_size > 1_000_000:
            continue
        try:
            script_text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(script_text) for pattern in install_patterns):
            reporter.warn(
                "claude.runtime-install",
                "Script appears to install packages at runtime; Claude API containers do not support runtime package installation.",
                path,
            )
        if any(pattern.search(script_text) for pattern in network_patterns):
            reporter.warn(
                "claude.runtime-network",
                "Script appears to use network access; Claude API code-execution containers have no network access.",
                path,
            )


def validate_size(root: Path, profile: str, reporter: Reporter) -> None:
    total = 0
    for path in root.rglob("*"):
        if path.is_file():
            try:
                total += path.stat().st_size
            except OSError:
                pass
    if profile in {"portable", "claude-platform"} and total >= 30 * 1024 * 1024:
        reporter.error(
            "claude.upload-size",
            f"Skill directory is {total / (1024 * 1024):.2f} MiB, which is not under the Claude API 30 MB upload limit.",
            root,
        )
    else:
        reporter.info("size.total", f"Skill directory size: {total / 1024:.1f} KiB.", root)


def validate_skill(root: Path, requested_profile: str) -> tuple[str, Reporter]:
    reporter = Reporter()
    root = root.expanduser().resolve()

    if not root.exists():
        reporter.error("root.missing", "Target skill directory does not exist.", root)
        return requested_profile, reporter
    if not root.is_dir():
        reporter.error("root.not-directory", "Target path must be a skill directory.", root)
        return requested_profile, reporter

    skill_md = root / "SKILL.md"
    if not skill_md.exists():
        reporter.error("skill-md.missing", "SKILL.md is required at the skill root.", skill_md)
        return requested_profile, reporter

    try:
        text = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        reporter.error("skill-md.encoding", "SKILL.md must be readable as UTF-8 text.", skill_md)
        return requested_profile, reporter

    fm = parse_frontmatter(text, reporter, skill_md)
    if fm is None:
        return requested_profile, reporter

    profile = detect_profile(root, fm) if requested_profile == "auto" else requested_profile
    reporter.info("profile.selected", f"Validation profile: {profile}.", root)

    validate_frontmatter_types(root, fm, profile, reporter)
    validate_name_and_description(root, fm, profile, reporter)
    if profile == "claude-code" or CLAUDE_ONLY_KEYS.intersection(fm.values):
        validate_claude_code_fields(root, fm, reporter)

    if fm.body_line_count > 500:
        reporter.warn(
            "skill-md.length",
            f"SKILL.md body has {fm.body_line_count} lines; consider progressive disclosure below 500 lines.",
            skill_md,
        )

    validate_references(root, text, reporter)
    if profile in {"portable", "openai"} or (root / "agents" / "openai.yaml").exists():
        validate_openai_yaml(root, reporter)
    scan_runtime_constraints(root, profile, reporter)
    validate_size(root, profile, reporter)

    if profile != "claude-code" and CLAUDE_ONLY_KEYS.intersection(fm.values):
        fields = ", ".join(sorted(CLAUDE_ONLY_KEYS.intersection(fm.values)))
        reporter.warn(
            "platform.claude-code-fields",
            f"Claude Code-specific frontmatter detected under profile {profile}: {fields}.",
            skill_md,
        )

    return profile, reporter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate an Agent Skills directory without modifying it."
    )
    parser.add_argument("skill_dir", type=Path, help="Path to the skill directory")
    parser.add_argument(
        "--platform",
        default="auto",
        choices=sorted(SUPPORTED_PROFILES),
        help="Validation profile (default: auto)",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    profile, reporter = validate_skill(args.skill_dir, args.platform)

    if args.json:
        payload = {
            "profile": profile,
            "result": reporter.result,
            "issues": [asdict(issue) for issue in reporter.issues],
        }
        print(json.dumps(payload, indent=2))
    else:
        for issue in reporter.issues:
            location = f" [{issue.path}]" if issue.path else ""
            print(f"{issue.severity:<5} {issue.code}: {issue.message}{location}")
        labels = {
            "pass": "PASS",
            "pass_with_warnings": "PASS WITH WARNINGS",
            "fail": "FAIL",
        }
        print(labels[reporter.result])

    return 1 if reporter.has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
