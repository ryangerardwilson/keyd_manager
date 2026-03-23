import os
import subprocess
import tempfile
from pathlib import Path


INSTALLER = Path(__file__).resolve().parents[1] / "install.sh"


def test_local_install_removes_legacy_footprint_and_keeps_existing_bashrc() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        bin_dir = tmp_path / "bin"
        home_dir = tmp_path / "home"
        bashrc = home_dir / ".bashrc"
        source_binary = tmp_path / "source-binary"
        legacy_home = home_dir / ".keyd_manager"
        legacy_launcher = home_dir / ".local" / "bin" / "keyd_manager"
        public_launcher = home_dir / ".local" / "bin" / "km"
        bin_dir.mkdir()
        home_dir.mkdir()
        bashrc.write_text(
            f"export PATH={home_dir}/.keyd_manager/bin:$PATH\n",
            encoding="utf-8",
        )
        legacy_home.mkdir()
        legacy_launcher.parent.mkdir(parents=True)
        legacy_launcher.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        legacy_launcher.chmod(0o755)
        public_launcher.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"\"{home_dir / '.km' / 'bin' / 'km'}\" \"$@\"\n",
            encoding="utf-8",
        )
        public_launcher.chmod(0o755)
        source_binary.write_text(
            "#!/usr/bin/env bash\n"
            "if [[ \"${1:-}\" == \"-v\" ]]; then\n"
            "  printf '0.0.0\\n'\n"
            "  exit 0\n"
            "fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        source_binary.chmod(0o755)

        result = subprocess.run(
            ["/usr/bin/bash", str(INSTALLER), "-b", str(source_binary), "-n"],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": str(home_dir), "PATH": f"{bin_dir}:{os.environ['PATH']}"},
            check=True,
        )

        assert ".keyd_manager/bin" in bashrc.read_text(encoding="utf-8")
        assert not legacy_home.exists()
        assert not legacy_launcher.exists()
        assert public_launcher.exists()
        public_text = public_launcher.read_text(encoding="utf-8")
        assert "# Managed by rgw_cli_contract local-bin launcher" in public_text
        assert f'exec "{home_dir / ".km" / "bin" / "km"}" "$@"' in public_text
        assert "Legacy cleanup:" in result.stdout
