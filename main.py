#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
from pathlib import Path

from _version import __version__


APP_NAME = "keyd_manager"
APP_ROOT = Path(__file__).resolve().parent
ASSET_CONFIG = APP_ROOT / "assets" / "keyd.config"
SYSTEM_CONFIG = Path("/etc/keyd/sticky_keys.conf")
INSTALL_SCRIPT = Path(os.environ.get("KEYD_MANAGER_INSTALL_SCRIPT", APP_ROOT / "install.sh"))

HELP_TEXT = """keyd_manager
edit, install, and inspect the managed keyd sticky-keys config

flags:
  keyd_manager -h
    show this help
  keyd_manager -v
    print the installed version
  keyd_manager -u
    upgrade to the latest release

features:
  open the managed keyd config in your editor
  # keyd_manager conf
  keyd_manager conf

  install the managed config into /etc/keyd and reload the service
  # keyd_manager apply
  keyd_manager apply

  inspect the current keyd service status
  # keyd_manager status
  keyd_manager status
"""


def config_dir() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / APP_NAME


def config_path() -> Path:
    return config_dir() / "keyd.config"


def resolve_editor() -> str:
    return os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vim"


def ensure_config_file() -> Path:
    target = config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(ASSET_CONFIG, target)
    return target


def run_root(command: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = list(command)
    if os.geteuid() != 0:
        cmd.insert(0, "sudo")
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        capture_output=capture_output,
    )


def print_help() -> None:
    print(HELP_TEXT.rstrip())


def edit_config() -> int:
    editor = resolve_editor()
    target = ensure_config_file()
    return subprocess.call([editor, str(target)])


def install_self() -> int:
    return subprocess.call([str(INSTALL_SCRIPT), "-u"])


def ensure_keyd_installed() -> int:
    if shutil.which("pacman") is None:
        print("This flow expects Arch Linux with pacman.", file=sys.stderr)
        return 1

    probe = subprocess.run(
        ["pacman", "-Q", "keyd"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if probe.returncode == 0:
        return 0

    install = run_root(["pacman", "-S", "--needed", "--noconfirm", "keyd"])
    return install.returncode


def apply_config() -> int:
    source = ensure_config_file()

    rc = ensure_keyd_installed()
    if rc != 0:
        return rc

    install = run_root(["install", "-Dm644", str(source), str(SYSTEM_CONFIG)])
    if install.returncode != 0:
        return install.returncode

    enable = run_root(["systemctl", "enable", "--now", "keyd.service"])
    if enable.returncode != 0:
        return enable.returncode

    reload_cmd = ["keyd", "reload"]
    reload_result = run_root(reload_cmd)
    if reload_result.returncode != 0:
        restart = run_root(["systemctl", "restart", "keyd.service"])
        if restart.returncode != 0:
            return restart.returncode

    print(f"Installed {source} -> {SYSTEM_CONFIG}")
    print("keyd config applied.")
    return 0


def show_status() -> int:
    result = subprocess.run(
        ["systemctl", "status", "keyd.service", "--no-pager", "--lines=20"],
        check=False,
    )
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv == ["-h"]:
        print_help()
        return 0

    if argv == ["-v"]:
        print(__version__)
        return 0

    if argv == ["-u"]:
        return install_self()

    if argv == ["conf"]:
        return edit_config()

    if argv == ["apply"]:
        return apply_config()

    if argv == ["status"]:
        return show_status()

    print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
