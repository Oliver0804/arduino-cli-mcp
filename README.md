# Arduino CLI MCP (Managed Command Processor)

A Python-based utility for managing Arduino CLI commands with support for auto-approval of common operations.

## Overview

Arduino CLI MCP provides a wrapper around the Arduino CLI, enabling streamlined workflows with features like automatic approval for repetitive operations. This tool is particularly useful for developers and educators who work frequently with Arduino projects.

## Configuration

The tool can be configured in JSON format as follows:

```json
"github.com/arduino-cli-mcp": {
  "command": "python",
  "args": [
    "/Users/oliver/code/mcp/arduino-cli-mcp/main.py",
    "--workdir",
    "/Users/oliver/Documents/Cline/MCP/arduino-cli-mcp"
  ],
  "disabled": false,
  "autoApprove": [
    "upload",
    "compile",
    "install_board"
  ]
}
```

### Configuration Options

- `command`: The command to execute (Python in this case)
- `args`: List of arguments to pass to the command
  - The first argument is the path to the main script
  - `--workdir` specifies the working directory for Arduino CLI operations
- `disabled`: Enable/disable the tool (set to `false` to enable)
- `autoApprove`: List of Arduino CLI operations that will be automatically approved without user confirmation
  - Supported operations: `upload`, `compile`, `install_board`

## Usage

Once configured, the tool will automatically process Arduino CLI commands, with special handling for the operations listed in the `autoApprove` section.

## Requirements

- Python 3.6+
- Arduino CLI
- Proper file permissions for the working directory

## Related Links

- [Arduino CLI Documentation](https://arduino.github.io/arduino-cli/)

---

_For Chinese version, see [README_zh.md](README_zh.md)_

# Arduino CLI MCP Server

A Model Context Protocol server that provides Arduino CLI capabilities. This server enables LLMs to interact with Arduino boards, compile sketches, upload firmware, and manage libraries directly through natural language commands.

### Available Tools

- `list_boards` - List all connected Arduino boards.

  - No required arguments

- `compile_sketch` - Compile an Arduino sketch.

  - Required arguments:
    - `sketch_path` (string): Path to the sketch file
    - `board_fqbn` (string): Fully Qualified Board Name (e.g., 'arduino:avr:uno')

- `upload_sketch` - Upload a compiled sketch to a board.

  - Required arguments:
    - `sketch_path` (string): Path to the sketch file
    - `board_fqbn` (string): Fully Qualified Board Name
    - `port` (string): Port to use for upload (e.g., '/dev/ttyACM0', 'COM3')

- `search_library` - Search for Arduino libraries.

  - Required arguments:
    - `query` (string): Search term

- `install_library` - Install an Arduino library.
  - Required arguments:
    - `library_name` (string): Name of the library to install

## Installation

### Using uv (recommended)

When using [`uv`](https://docs.astral.sh/uv/) no specific installation is needed. We will
use [`uvx`](https://docs.astral.sh/uv/guides/tools/) to directly run _arduino-cli-mcp_.

### Using PIP

Alternatively you can install `arduino-cli-mcp` via pip:

```bash
pip install arduino-cli-mcp
```

After installation, you can run it as a script using:

```bash
python -m arduino_cli_mcp
```

## Configuration

### Configure for Claude.app

Add to your Claude settings:

<details>
<summary>Using uvx</summary>

```json
"mcpServers": {
  "arduino": {
    "command": "uvx",
    "args": ["arduino-cli-mcp"]
  }
}
```

</details>

<details>
<summary>Using pip installation</summary>

```json
"mcpServers": {
  "arduino": {
    "command": "python",
    "args": ["-m", "arduino_cli_mcp"]
  }
}
```

</details>

### Configure for Zed

Add to your Zed settings.json:

<details>
<summary>Using uvx</summary>

```json
"context_servers": [
  "arduino-cli-mcp": {
    "command": "uvx",
    "args": ["arduino-cli-mcp"]
  }
],
```

</details>

<details>
<summary>Using pip installation</summary>

```json
"context_servers": {
  "arduino-cli-mcp": {
    "command": "python",
    "args": ["-m", "arduino_cli_mcp"]
  }
},
```

</details>

### Customization - Arduino CLI Path

By default, the server looks for the Arduino CLI in the system PATH. You can specify a custom path by adding the argument `--arduino-cli-path` to the `args` list in the configuration.

Example:

```json
{
  "command": "python",
  "args": ["-m", "arduino_cli_mcp", "--arduino-cli-path=/path/to/arduino-cli"]
}
```

## Example Interactions

1. List connected boards:

```json
{
  "name": "list_boards",
  "arguments": {}
}
```

Response:

```json
{
  "boards": [
    {
      "port": "COM3",
      "fqbn": "arduino:avr:uno",
      "name": "Arduino Uno"
    },
    {
      "port": "COM4",
      "fqbn": "arduino:avr:nano",
      "name": "Arduino Nano"
    }
  ]
}
```

2. Compile a sketch:

```json
{
  "name": "compile_sketch",
  "arguments": {
    "sketch_path": "/path/to/Blink.ino",
    "board_fqbn": "arduino:avr:uno"
  }
}
```

Response:

```json
{
  "success": true,
  "output": "Sketch uses 924 bytes (2%) of program storage space. Maximum is 32256 bytes.",
  "binary_path": "/path/to/build/arduino.avr.uno/Blink.ino.hex"
}
```

## Debugging

You can use the MCP inspector to debug the server. For uvx installations:

```bash
npx @modelcontextprotocol/inspector uvx arduino-cli-mcp
```

Or if you've installed the package in a specific directory or are developing on it:

```bash
cd path/to/servers/src/arduino-cli
npx @modelcontextprotocol/inspector uv run arduino-cli-mcp
```

## Examples of Questions for Claude

1. "What Arduino boards are currently connected to my computer?"
2. "Compile my Blink sketch for Arduino Uno"
3. "Upload my LED project to my Arduino Mega on port COM5"
4. "Can you search for libraries related to OLED displays?"
5. "Install the Servo library for Arduino"

## Contributing

We encourage contributions to help expand and improve arduino-cli-mcp. Whether you want to add new Arduino-related tools, enhance existing functionality, or improve documentation, your input is valuable.

For examples of other MCP servers and implementation patterns, see:
https://github.com/modelcontextprotocol/servers

Pull requests are welcome! Feel free to contribute new ideas, bug fixes, or enhancements to make arduino-cli-mcp even more powerful and useful.

## License

arduino-cli-mcp is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
