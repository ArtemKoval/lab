#!/usr/bin/env python
import os
import subprocess
import sys
from pathlib import Path


def create_environment(project_path, python_version):
    """Create a new Python environment with pyenv and virtualenv on Windows."""
    project_path = Path(project_path).absolute()
    venv_path = project_path / "venv"

    print(f"Setting up Python {python_version} environment in {project_path}")

    # Check if pyenv has the requested Python version
    try:
        installed_versions = subprocess.check_output(
            ["pyenv", "versions"],
            shell=True,
            text=True
        ).splitlines()
    except subprocess.CalledProcessError as e:
        print(f"pyenv not found or error checking versions: {e}")
        print("Ensure pyenv-win is installed and in your PATH")
        return False

    # Check if version is available
    version_installed = any(python_version in v for v in installed_versions)

    if not version_installed:
        print(f"Python {python_version} not installed. Installing with pyenv...")
        try:
            subprocess.run(
                ["pyenv", "install", python_version],
                shell=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Failed to install Python {python_version}: {e}")
            return False

    # Create project directory if it doesn't exist
    project_path.mkdir(parents=True, exist_ok=True)

    # Set local Python version
    try:
        subprocess.run(
            ["pyenv", "local", python_version],
            cwd=project_path,
            shell=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to set local Python version: {e}")
        return False

    # Create virtual environment
    try:
        # On Windows, we need to use the full path to the Python executable
        python_exe = Path(
            os.environ['USERPROFILE']) / '.pyenv' / 'pyenv-win' / 'versions' / python_version / 'python.exe'

        subprocess.run(
            [str(python_exe), "-m", "venv", str(venv_path)],
            cwd=project_path,
            shell=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e}")
        return False

    print(f"\nSuccessfully created environment!")
    print(f"To activate, run:")
    print(f"  cd {project_path} && .\\venv\\Scripts\\activate")

    return True


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python setup_env.py <project_path> <python_version>")
        print("Example: python setup_env.py ./my_project 3.9.7")
        sys.exit(1)

    project_path = sys.argv[1]
    python_version = sys.argv[2]

    if not create_environment(project_path, python_version):
        sys.exit(1)