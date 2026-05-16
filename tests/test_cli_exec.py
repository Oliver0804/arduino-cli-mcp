"""Test the subprocess wrapper without actually invoking arduino-cli."""

from unittest.mock import patch, MagicMock

import pytest

from arduino_cli_mcp.main import ArduinoCliServer


@pytest.fixture
def server(tmp_path):
    return ArduinoCliServer(workdir=str(tmp_path))


def _fake_run(returncode=0, stdout="ok", stderr=""):
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


def test_execute_cli_command_invokes_arduino_cli(server):
    with patch("arduino_cli_mcp.main.subprocess.run") as run:
        run.return_value = _fake_run(stdout="arduino-cli 1.2.3")
        out = server.execute_cli_command("version")

    assert out.success is True
    assert out.output == "arduino-cli 1.2.3"
    args_passed = run.call_args.args[0]
    assert args_passed[0] == "arduino-cli"
    assert "version" in args_passed


def test_execute_cli_command_reports_failure(server):
    with patch("arduino_cli_mcp.main.subprocess.run") as run:
        run.return_value = _fake_run(returncode=1, stderr="boom")
        out = server.execute_cli_command("bogus")

    assert out.success is False
    assert "boom" in out.error


def test_user_input_does_not_inject_extra_flags(server):
    """A malicious platform_id must not smuggle extra CLI flags through."""
    with patch("arduino_cli_mcp.main.subprocess.run") as run:
        run.return_value = _fake_run()
        server.install_platform("esp32:esp32 --config-file /etc/passwd")

    tokens = run.call_args.args[0]
    assert "--config-file" not in tokens
    assert "/etc/passwd" not in tokens
