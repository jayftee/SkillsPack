"""Install the newest wheel from dist/ into a clean environment and run the project's commands from another folder.

This is the test a recipient's machine would give: nothing from the development environment (the editable
install, the dev tools, neighbouring projects, the working directory) is available. A command that works here
works after `pip install <wheel>`.

Usage:
    python scripts/smoke.py [--python PATH]

Without --python, a throwaway venv is created from the current interpreter and deleted afterwards.
With --python, the wheel is installed into that existing environment (for example a clean ArcGIS Pro clone
kept for runtime testing, which can see arcpy) and uninstalled again afterwards.
The arguments given to each command come from ``[tool.smoke] arguments`` in pyproject.toml.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Project:
    """What the smoke test needs to know about the project."""

    name: str
    commands: list[str]
    arguments: list[str]


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    """Parse the command line.

    Args:
        argv: The arguments after the script name.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--python", type=Path, help="python.exe of an existing environment to install the wheel into")
    return parser.parse_args(argv)


def read_project(pyproject_path: Path) -> Project:
    """Read the project's name, its commands and the smoke-test arguments.

    Args:
        pyproject_path: The project's pyproject.toml.

    Returns:
        The project description.
    """
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return Project(
        name=data["project"]["name"],
        commands=list(data["project"].get("scripts", {})),
        arguments=list(data.get("tool", {}).get("smoke", {}).get("arguments", [])),
    )


def newest_wheel(dist_folder: Path) -> Path:
    """Find the most recently built wheel.

    Args:
        dist_folder: Where `poe package` writes wheels.

    Returns:
        The newest wheel.

    Raises:
        SystemExit: If there is no wheel.
    """
    wheels = sorted(dist_folder.glob("*.whl"), key=lambda wheel: wheel.stat().st_mtime)
    if not wheels:
        message = f"no wheel in {dist_folder}; run `poe package` first"
        raise SystemExit(message)
    return wheels[-1]


def run(*command: str | Path, working_folder: Path | None = None) -> str:
    """Run a command and return its output.

    Args:
        *command: The program and its arguments.
        working_folder: Where to run it; the current folder if omitted.

    Returns:
        What the command printed on stdout.

    Raises:
        SystemExit: If the command exits with a non-zero code.
    """
    result = subprocess.run(
        command, cwd=working_folder, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )
    if result.returncode != 0:
        message = f"{' '.join(map(str, command))}\nexit code {result.returncode}\n{result.stdout}{result.stderr}"
        raise SystemExit(message)
    return result.stdout


def check_commands(python: Path, project: Project, working_folder: Path) -> None:
    """Run every command the project installs, from a folder that has nothing to do with the project.

    Args:
        python: The environment's interpreter, which finds the folder the launchers were installed into.
        project: The project description.
        working_folder: A neutral folder to run from.

    Raises:
        SystemExit: If a launcher is missing or a command fails.
    """
    scripts_folder = run(python, "-c", "import sysconfig; print(sysconfig.get_path('scripts'))").strip()
    for command in project.commands:
        launcher = shutil.which(command, path=scripts_folder)
        if launcher is None:
            message = f"{command}: not installed into {scripts_folder}"
            raise SystemExit(message)
        output = run(launcher, *project.arguments, working_folder=working_folder)
        print(f"{command}: exit 0\n{output}")


def smoke_test(python: Path, wheel: Path, project: Project, working_folder: Path) -> None:
    """Install the wheel with the given interpreter, check the commands, then uninstall it again.

    Args:
        python: The interpreter of the environment to install into.
        wheel: The wheel to install.
        project: The project description.
        working_folder: A neutral folder to run the commands from.
    """
    run(
        python, "-m", "pip", "uninstall", "--yes", project.name
    )  # a copy from an earlier run would make pip skip the install
    try:
        run(python, "-m", "pip", "install", "--quiet", wheel)
        check_commands(python, project, working_folder)
    finally:
        run(python, "-m", "pip", "uninstall", "--yes", project.name)


def venv_python(venv_folder: Path) -> Path:
    """Locate the interpreter inside a venv.

    Args:
        venv_folder: The venv's folder.

    Returns:
        Path of its python executable.
    """
    return venv_folder / "Scripts" / "python.exe" if sys.platform == "win32" else venv_folder / "bin" / "python"


def main(argv: list[str]) -> int:
    """Run the smoke test.

    Args:
        argv: The arguments after the script name.

    Returns:
        The process exit code.
    """
    arguments = parse_arguments(argv)
    project = read_project(PROJECT_ROOT / "pyproject.toml")
    wheel = newest_wheel(PROJECT_ROOT / "dist")
    print(f"wheel: {wheel.name}")
    with tempfile.TemporaryDirectory() as temporary_name:
        working_folder = Path(temporary_name) / "elsewhere"
        working_folder.mkdir()
        if arguments.python is not None:
            smoke_test(arguments.python, wheel, project, working_folder)
        else:
            venv_folder = Path(temporary_name) / "venv"
            run(sys.executable, "-m", "venv", venv_folder)
            smoke_test(venv_python(venv_folder), wheel, project, working_folder)
    print("smoke test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
