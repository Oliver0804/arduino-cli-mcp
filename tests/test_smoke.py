"""Smoke tests: catch the kind of packaging bug that shipped 0.1.5 broken."""

import arduino_cli_mcp
from arduino_cli_mcp import main as main_module


def test_package_exposes_version():
    assert hasattr(arduino_cli_mcp, "__version__")
    assert isinstance(arduino_cli_mcp.__version__, str)


def test_entry_points_are_callable():
    assert callable(main_module.main)
    assert callable(main_module.serve)


def test_arduino_cli_server_constructs(tmp_path):
    server = main_module.ArduinoCliServer(workdir=str(tmp_path))
    assert server.workdir == str(tmp_path)


def test_models_roundtrip():
    result = main_module.ArduinoCommandResult(
        command="arduino-cli version",
        success=True,
        output="hello",
        error="",
    )
    assert result.success is True
    assert result.output == "hello"
