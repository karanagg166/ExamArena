import os
import site
import subprocess
import sys
import sysconfig
from pathlib import Path


def run_command(cmd, env=None):
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def ensure_prisma():
    # Install through uv only when the current environment can be modified safely.
    try:
        import prisma

        print("Prisma Python package is already installed.")
    except ImportError:
        # Never modify a host's system Python. CI and containers are disposable;
        # local development must use the explicitly selected virtual environment.
        disposable = Path("/.dockerenv").exists() or os.environ.get("CI") == "true"
        if sys.prefix == sys.base_prefix and not disposable:
            sys.exit(
                "Prisma is missing. Create a virtual environment with "
                "'uv venv --python 3.11 venv', then install Prisma with "
                "'uv pip install --python venv/bin/python prisma' and rerun "
                "this script with venv/bin/python."
            )
        print("Prisma Python package not found. Installing with uv...")
        command = ["uv", "pip", "install", "--python", sys.executable]
        if sys.prefix == sys.base_prefix:
            command.append("--system")
        subprocess.run([*command, "prisma"], check=True)


def main():
    ensure_prisma()
    # Collect potential script directories where prisma-client-py could be installed
    potential_dirs = []

    # Virtualenv / system prefix
    potential_dirs.append(os.path.join(sys.prefix, "bin"))

    # User-base bin
    try:
        user_base = site.getuserbase()
        if user_base:
            potential_dirs.append(os.path.join(user_base, "bin"))
    except Exception:
        pass

    # Sysconfig scripts paths
    try:
        potential_dirs.append(sysconfig.get_path("scripts"))
    except Exception:
        pass

    try:
        potential_dirs.append(sysconfig.get_path("scripts", "posix_user"))
    except Exception:
        pass

    # Default ~/.local/bin
    potential_dirs.append(os.path.expanduser("~/.local/bin"))

    # Filter unique and existing directories
    unique_dirs = []
    for d in potential_dirs:
        d = os.path.abspath(d)
        if os.path.isdir(d) and d not in unique_dirs:
            unique_dirs.append(d)

    print(f"Discovered potential script directories: {unique_dirs}")

    # Find which directory actually contains prisma-client-py
    found_bin_dir = None
    for d in unique_dirs:
        if os.path.exists(os.path.join(d, "prisma-client-py")) or os.path.exists(
            os.path.join(d, "prisma-client-py.exe")
        ):
            found_bin_dir = d
            print(f"Found prisma-client-py in: {d}")
            break

    # Prepare the environment with updated PATH
    env = os.environ.copy()
    env["PRISMA_PY_DEBUG_GENERATOR"] = "1"

    # Add discovered paths to PATH
    current_path = env.get("PATH", "")
    all_paths = unique_dirs + current_path.split(os.pathsep)
    env["PATH"] = os.pathsep.join(all_paths)

    print(f"Updated PATH for generator execution: {env['PATH']}")

    # 3. Run the generator
    schema_path = os.path.join("backend", "prisma", "schema.prisma")
    cmd = [sys.executable, "-m", "prisma", "py", "generate", f"--schema={schema_path}"]
    run_command(cmd, env=env)

    print("Prisma Python client generated successfully!")


if __name__ == "__main__":
    main()
