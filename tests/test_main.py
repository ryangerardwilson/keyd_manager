import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock
import unittest


APP_ROOT = Path(__file__).resolve().parents[1]
MAIN = APP_ROOT / "main.py"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

import main as km_main


def run_app(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    base_env = os.environ.copy()
    if env:
        base_env.update(env)
    return subprocess.run(
        [sys.executable, str(MAIN), *args],
        capture_output=True,
        text=True,
        check=False,
        env=base_env,
    )


class MainContractTests(unittest.TestCase):
    def test_no_args_matches_dash_h(self):
        no_args = run_app()
        help_args = run_app("-h")
        self.assertEqual(no_args.returncode, 0)
        self.assertEqual(no_args.stdout, help_args.stdout)

    def test_version_is_single_line(self):
        result = run_app("-v")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "0.0.0")

    def test_ensure_config_seeds_xdg_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {"XDG_CONFIG_HOME": temp_dir}
            result = run_app("conf", env={**env, "EDITOR": "/usr/bin/true"})
            self.assertEqual(result.returncode, 0)
            target = Path(temp_dir) / "km" / "keyd.config"
            self.assertTrue(target.exists())

    def test_ensure_config_migrates_legacy_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            legacy_dir = Path(temp_dir) / "keyd_manager"
            legacy_dir.mkdir()
            legacy_config = legacy_dir / "keyd.config"
            legacy_config.write_text("[ids]\n*\n", encoding="utf-8")

            env = {"XDG_CONFIG_HOME": temp_dir}
            result = run_app("conf", env={**env, "EDITOR": "/usr/bin/true"})
            self.assertEqual(result.returncode, 0)

            target = Path(temp_dir) / "km" / "keyd.config"
            self.assertEqual(target.read_text(encoding="utf-8"), "[ids]\n*\n")

    def test_upgrade_invokes_install_script_with_dash_u(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            marker = Path(temp_dir) / "marker.txt"
            install_script = Path(temp_dir) / "install.sh"
            install_script.write_text(
                "#!/usr/bin/env bash\n"
                "printf '%s\\n' \"$*\" > \"$KM_MARKER\"\n",
                encoding="utf-8",
            )
            install_script.chmod(0o755)

            result = run_app(
                "-u",
                env={
                    "KM_INSTALL_SCRIPT": str(install_script),
                    "KM_MARKER": str(marker),
                },
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(marker.read_text(encoding="utf-8").strip(), "-u")

    def test_apply_retries_reload_after_socket_error(self):
        completed = subprocess.CompletedProcess
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        source = Path(temp_dir.name) / "keyd.config"
        source.write_text("[main]\ncontrol = oneshot(control)\n", encoding="utf-8")

        with (
            mock.patch("main.ensure_config_file", return_value=source),
            mock.patch("main.ensure_keyd_installed", return_value=0),
            mock.patch("pathlib.Path.exists", autospec=True, side_effect=lambda path: path == km_main.KEYD_SOCKET),
            mock.patch("main.time.sleep"),
            mock.patch(
                "main.run_root",
                side_effect=[
                    completed(["install"], 0),
                    completed(["systemctl", "enable", "--now", "keyd.service"], 0),
                    completed(["keyd", "reload"], 1, "", "failed to connect to /var/run/keyd.socket"),
                    completed(["systemctl", "restart", "keyd.service"], 0),
                    completed(["keyd", "reload"], 0),
                ],
            ) as run_root,
        ):
            rc = km_main.apply_config()

        self.assertEqual(rc, 0)
        self.assertEqual(
            [call.args[0] for call in run_root.call_args_list],
            [
                ["install", "-Dm644", str(source), str(km_main.SYSTEM_CONFIG)],
                ["systemctl", "enable", "--now", "keyd.service"],
                ["keyd", "reload"],
                ["systemctl", "restart", "keyd.service"],
                ["keyd", "reload"],
            ],
        )


if __name__ == "__main__":
    unittest.main()
