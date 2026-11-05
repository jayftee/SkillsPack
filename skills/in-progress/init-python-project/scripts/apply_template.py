"""Copy this skill's files/ tree (plus files-arcgis/ with --arcgis) into a target folder, filling in the {{TOKENS}}.

Never overwrites: a file that already exists in the target is reported as "exists" and left alone,
for the person running the skill to merge. Refuses to write anything if the target holds a
tool-specific config file that would silently override pyproject.toml.

Usage:
    python apply_template.py TARGET --project-name NAME --python-version 3.13
                             [--package-name NAME] [--arcgis] [--dry-run]
"""

from __future__ import annotations

import argparse
import keyword
from pathlib import Path
import re
import sys

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_ROOT = SKILL_ROOT / "files"
ARCGIS_TEMPLATE_ROOT = SKILL_ROOT / "files-arcgis"  # overlay for an ArcGIS Pro clone
MINIMUM_PYTHON = (3, 11)  # StrEnum in the sample; every dev tool needs 3.10+

# Each of these takes precedence over its [tool.*] section in pyproject.toml.
STRAY_CONFIG_FILES = (
    "ruff.toml",
    ".ruff.toml",
    "mypy.ini",
    ".mypy.ini",
    "pytest.ini",
    ".pytest.ini",
    ".coveragerc",
    "setup.cfg",
    "tox.ini",
    ".importlinter",
    "pyrightconfig.json",
)

PROJECT_NAME_PATTERN = re.compile(r"[a-z][a-z0-9]*(-[a-z0-9]+)*")
PACKAGE_NAME_PATTERN = re.compile(r"[a-z_][a-z0-9_]*")
PYTHON_VERSION_PATTERN = re.compile(r"3\.(\d+)")
TOKEN_PATTERN = re.compile(r"\{\{[A-Z_]+\}\}")

EXIT_INVALID_ARGUMENTS = 2
EXIT_STRAY_CONFIG = 3


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", type=Path, help="project folder to initialise")
    parser.add_argument("--project-name", required=True, help="distribution name, e.g. my-project")
    parser.add_argument("--package-name", help="import name; default: project name with - replaced by _")
    parser.add_argument("--python-version", required=True, help="the base Python's major.minor, e.g. 3.13")
    parser.add_argument(
        "--arcgis", action="store_true", help="also copy files-arcgis/ (the target environment is an ArcGIS Pro clone)"
    )
    parser.add_argument("--dry-run", action="store_true", help="report what would happen, write nothing")
    return parser.parse_args(argv)


def validation_errors(arguments: argparse.Namespace, package_name: str) -> list[str]:
    """Return a message for every invalid argument."""
    errors = []
    if not PROJECT_NAME_PATTERN.fullmatch(arguments.project_name):
        errors.append(f"project name {arguments.project_name!r}: use lowercase letters, digits and single hyphens")
    if not PACKAGE_NAME_PATTERN.fullmatch(package_name) or keyword.iskeyword(package_name):
        errors.append(f"package name {package_name!r}: must be a lowercase Python identifier and not a keyword")
    version_match = PYTHON_VERSION_PATTERN.fullmatch(arguments.python_version)
    if version_match is None or (3, int(version_match.group(1))) < MINIMUM_PYTHON:
        errors.append(f"python version {arguments.python_version!r}: use 3.N with N >= {MINIMUM_PYTHON[1]}")
    return errors


def build_tokens(arguments: argparse.Namespace, package_name: str) -> dict[str, str]:
    """Map every {{TOKEN}} in the template to its value."""
    return {
        "{{PROJECT_NAME}}": arguments.project_name,
        "{{PACKAGE_NAME}}": package_name,
        "{{PYTHON_VERSION}}": arguments.python_version,
    }


def substitute(text: str, tokens: dict[str, str]) -> str:
    """Replace every known token in the text and fail on any token left over."""
    for token, value in tokens.items():
        text = text.replace(token, value)
    leftover_tokens = TOKEN_PATTERN.findall(text)
    if leftover_tokens:
        message = f"unknown template tokens: {sorted(set(leftover_tokens))}"
        raise ValueError(message)
    return text


def apply(template_roots: list[Path], target: Path, tokens: dict[str, str], *, dry_run: bool) -> list[tuple[str, Path]]:
    """Copy each template tree into the target. Returns (status, relative path) for every template file."""
    results = []
    sources = [(root, source) for root in template_roots for source in sorted(root.rglob("*")) if source.is_file()]
    for root, source in sources:
        relative_path = Path(substitute(source.relative_to(root).as_posix(), tokens))
        destination = target / relative_path
        if destination.exists():
            results.append(("exists", relative_path))
            continue
        content = substitute(source.read_text(encoding="utf-8"), tokens)
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8", newline="\n")
        results.append(("created", relative_path))
    return results


def main(argv: list[str]) -> int:
    """Run the script."""
    arguments = parse_arguments(argv)
    package_name = arguments.package_name or arguments.project_name.replace("-", "_")
    errors = validation_errors(arguments, package_name)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return EXIT_INVALID_ARGUMENTS

    target = arguments.target.resolve()
    stray_files = [name for name in STRAY_CONFIG_FILES if (target / name).exists()]
    if stray_files:
        print(f"stray config files override pyproject.toml, nothing written: {', '.join(stray_files)}")
        return EXIT_STRAY_CONFIG

    tokens = build_tokens(arguments, package_name)
    template_roots = [TEMPLATE_ROOT, ARCGIS_TEMPLATE_ROOT] if arguments.arcgis else [TEMPLATE_ROOT]
    results = apply(template_roots, target, tokens, dry_run=arguments.dry_run)
    verb = "would be" if arguments.dry_run else "were"
    for status, relative_path in results:
        print(f"{status:8} {relative_path.as_posix()}")
    created_count = sum(status == "created" for status, _ in results)
    print(
        f"\n{created_count} files {verb} created; {len(results) - created_count} already existed and {verb} left alone."
    )
    print(f"project: {arguments.project_name}  package: {package_name}  python: {arguments.python_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
