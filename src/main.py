"""Self-hosted GitHub Actions runner lifecycle management.

Handles runner registration and unregistration against a GitHub repository
or organization. Terraform provisions the EC2 instance; this module manages
the runner binary on the host.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import subprocess
import sys
import tarfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

LOG = logging.getLogger(__name__)

GITHUB_RUNNER_LATEST = "https://api.github.com/repos/actions/runner/releases/latest"
RUNNER_VERSION_ENV = "RUNNER_VERSION"


@dataclass
class RunnerConfig:
    """Configuration for a self-hosted runner."""

    owner: str  # GitHub org or user
    repo: str
    token: str  # Runner registration token (from GitHub API)
    labels: list[str]
    name: str
    work_dir: Path = Path("/actions-runner")


class DownloadError(RuntimeError):
    """Failed to download the runner binary."""


class RunnerError(RuntimeError):
    """Runner command failed."""


def get_runner_url(version: str | None = None) -> str:
    """Return the download URL for the given runner version.

    Resolves the latest release from GitHub if no version is specified.
    """
    if version is None:
        version = os.environ.get(RUNNER_VERSION_ENV, "")

    if version:
        base = f"https://github.com/actions/runner/releases/download/v{version}"
    else:
        try:
            with urllib.request.urlopen(GITHUB_RUNNER_LATEST, timeout=10) as resp:
                release = json.loads(resp.read())
                version = release["tag_name"].lstrip("v")
                base = release["html_url"].replace("/releases/tag/", "/releases/download/")
        except Exception as exc:  # noqa: BLE001
            raise DownloadError(
                f"Could not resolve latest runner version: {exc}"
            ) from exc

    system = platform.system().lower()
    arch = platform.machine().lower()
    if arch == "x86_64":
        arch = "x64"
    elif arch not in ("x64", "arm64"):
        raise DownloadError(f"Unsupported architecture: {arch}")

    filename = f"actions-runner-{system}-{arch}-{version}.tar.gz"
    return f"{base}/{filename}"


def download_runner(dest: Path, version: str | None = None) -> Path:
    """Download and extract the runner binary to dest.

    Returns the path to the extracted runner directory.
    """
    url = get_runner_url(version)
    dest = dest.expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)

    archive = dest / "runner.tar.gz"
    try:
        LOG.info("Downloading runner from %s", url)
        urllib.request.urlretrieve(url, archive)
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(dest)
        # The extracted directory name varies by version; find it.
        for item in dest.iterdir():
            if item.is_dir() and item.name.startswith("actions-runner-"):
                return item
        raise DownloadError("Runner directory not found after extraction")
    finally:
        archive.unlink(missing_ok=True)


def configure_runner(runner_dir: Path, config: RunnerConfig) -> None:
    """Run the runner config script non-interactively.

    Sets the URL, auth token, runner name, and labels.
    Raises RunnerError if the config script exits non-zero.
    """
    config_sh = runner_dir / "config.sh"
    if not config_sh.exists():
        raise RunnerError(f"config.sh not found in {runner_dir}")

    labels_arg = ",".join(config.labels) if config.labels else ""
    url = f"https://github.com/{config.owner}/{config.repo}"

    cmd = [
        str(config_sh),
        "--url",
        url,
        "--token",
        config.token,
        "--name",
        config.name,
        "--labels",
        labels_arg,
        "--unattended",
        "--replace",
    ]
    LOG.info("Configuring runner %s for %s", config.name, url)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RunnerError(f"config.sh failed: {result.stderr.strip()}")


def unregister_runner(runner_dir: Path, token: str, name: str) -> None:
    """Remove this runner from GitHub using the remove.sh script."""
    remove_sh = runner_dir / "bin" / "remove.sh"
    if not remove_sh.exists():
        raise RunnerError(f"remove.sh not found in {runner_dir}")

    cmd = [
        str(remove_sh),
        "--token",
        token,
        "--name",
        name,
        "--unattended",
    ]
    LOG.info("Unregistering runner %s", name)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Log but do not raise -- runner might already be gone from GitHub.
        LOG.warning("remove.sh exited %d: %s", result.returncode, result.stderr.strip())


def run_runner(runner_dir: Path) -> None:
    """Start the runner in the foreground (blocking)."""
    run_sh = runner_dir / "run.sh"
    if not run_sh.exists():
        raise RunnerError(f"run.sh not found in {runner_dir}")

    LOG.info("Starting runner from %s", runner_dir)
    subprocess.run([str(run_sh)], check=True)


def install_and_register(config: RunnerConfig, version: str | None = None) -> Path:
    """Download, extract, configure, and return the runner directory."""
    work_dir = config.work_dir.expanduser().resolve()
    runner_dir = download_runner(work_dir, version)
    configure_runner(runner_dir, config)
    return runner_dir


def main() -> None:
    """CLI entry point for runner installation.

    Usage:
        python -m src.main install --owner ORG --repo REPO --token TOKEN --name NAME
        python -m src.main run --runner-dir PATH
        python -m src.main remove --runner-dir PATH --token TOKEN --name NAME
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )

    if len(sys.argv) < 2:
        LOG.error("Usage: python -m src.main <install|run|remove> ...")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "install":
        import argparse

        parser = argparse.ArgumentParser(description="Install and register a runner")
        parser.add_argument("--owner", required=True)
        parser.add_argument("--repo", required=True)
        parser.add_argument("--token", required=True)
        parser.add_argument("--name", required=True)
        parser.add_argument("--labels", default="")
        parser.add_argument("--work-dir", default="/actions-runner")
        args = parser.parse_args(sys.argv[2:])

        config = RunnerConfig(
            owner=args.owner,
            repo=args.repo,
            token=args.token,
            labels=args.labels.split(",") if args.labels else [],
            name=args.name,
            work_dir=Path(args.work_dir),
        )
        runner_dir = install_and_register(config)
        LOG.info("Runner installed at %s", runner_dir)

    elif cmd == "run":
        import argparse

        parser = argparse.ArgumentParser(description="Run the runner")
        parser.add_argument("--runner-dir", required=True)
        args = parser.parse_args(sys.argv[2:])
        run_runner(Path(args.runner_dir))

    elif cmd == "remove":
        import argparse

        parser = argparse.ArgumentParser(description="Remove runner from GitHub")
        parser.add_argument("--runner-dir", required=True)
        parser.add_argument("--token", required=True)
        parser.add_argument("--name", required=True)
        args = parser.parse_args(sys.argv[2:])
        unregister_runner(Path(args.runner_dir), args.token, args.name)

    else:
        LOG.error("Unknown command: %s", cmd)
        sys.exit(1)


if __name__ == "__main__":
    main()
