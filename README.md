# Arduino CLI MCP

Arduino CLI MCP is a server that provides Arduino CLI integration for VSCode and Claude, allowing you to compile and upload Arduino sketches through the Arduino CLI.

## Overview

Arduino CLI MCP provides a wrapper for Arduino CLI that simplifies workflows through features such as auto-approval of repetitive operations. This tool is particularly useful for developers and educators who frequently work with Arduino projects.

## Introduction to Model Context Protocol (MCP)

Model Context Protocol (MCP) is an open protocol specifically designed to enable Large Language Models (LLMs) to seamlessly integrate with external data sources and tools. Whether you're developing an AI IDE, enhancing chat interfaces, or building automated AI workflows, MCP provides a standardized way to connect LLMs with the context they need. Through MCP, the Arduino CLI MCP server can interact with various AI models, handling Arduino-related operations and commands.

## Installation

```bash
pip install arduino-cli-mcp
```

After installation, you can run it with the following command:

```bash
python -m arduino_cli_mcp
```

## Prerequisites

- Arduino CLI installed and available in PATH
- Python 3.11+
- Working directory with appropriate file permissions

## Configuration

The tool can be configured using JSON format as follows:

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
- `args`: List of arguments passed to the command
  - First argument is the path to the main script
  - `--workdir` specifies the working directory for Arduino CLI operations
- `disabled`: Enable/disable the tool (set to `false` to enable)
- `autoApprove`: List of Arduino CLI operations that can be auto-approved without user confirmation
  - Supported operations: `upload`, `compile`, `install_board`

### Configuration for Claude.app

Add the following to your Claude settings:

```json
"mcpServers": {
  "arduino": {
    "command": "python",
    "args": ["-m", "arduino_cli_mcp"]
  }
}
```

### Configuration for Zed

Add the following to your Zed settings.json file:

```json
"context_servers": {
  "arduino-cli-mcp": {
    "command": "python",
    "args": ["-m", "arduino_cli_mcp"]
  }
},
```

### Custom Configuration - Arduino CLI Path

By default, the server looks for Arduino CLI in the system PATH. You can specify a custom path by adding the `--arduino-cli-path` parameter to the `args` list in your configuration.

Example:

```json
{
  "command": "python",
  "args": ["-m", "arduino_cli_mcp", "--arduino-cli-path=/path/to/arduino-cli"]
}
```

## Usage

Start the MCP server:

```bash
arduino-cli-mcp --workdir /path/to/your/arduino/projects
```

Once configured, the tool will automatically handle Arduino CLI commands, with special handling for operations listed in the `autoApprove` section.

## Arduino CLI MCP Server

This is a Model Context Protocol server that provides Arduino CLI functionality. The server enables large language models to interact with Arduino boards through natural language commands, compile sketches, upload firmware, and manage libraries.

### Available Tools

- `compile`: Compile an Arduino sketch / 編譯 Arduino 草圖

  - **Parameters:**
    - `sketch_path` (string, required): Path to the .ino file / .ino 文件的路徑
    - `fqbn` (string, required, default: 'arduino:avr:uno'): Fully Qualified Board Name (e.g. 'arduino:avr:uno') / 完整開發板名稱

- `upload`: Upload an Arduino sketch or hex file to a board / 上傳 Arduino 草圖或 hex 檔案到開發板

  - **Parameters:**
    - `sketch_path` (string): Path to the .ino file / .ino 文件的路徑
    - `hex_path` (string): Path to the hex file (optional, if provided will upload directly) / hex 檔案的絕對路徑（可選）
    - `port` (string, required): Serial port of the board / 開發板的串口
    - `fqbn` (string, required, default: 'arduino:avr:uno'): Fully Qualified Board Name / 完整開發板名稱

- `install_board`: Install a board platform / 安裝開發板平台

  - **Parameters:**
    - `platform_id` (string, required): Platform ID (e.g. arduino:avr, esp32:esp32) / 平台 ID（如 arduino:avr, esp32:esp32）

- `check`: Check Arduino CLI version / 檢查 Arduino CLI 版本

  - No parameters required

- `list`: List all available boards and platforms / 列出所有可用的開發板和平台

  - No parameters required

- `install_library`: Install an Arduino library / 安裝 Arduino 函式庫

  - **Parameters:**
    - `library_name` (string, required): Name of the library to install / 要安裝的函式庫名稱

- `search_library`: Search for Arduino libraries / 搜尋 Arduino 函式庫

  - **Parameters:**
    - `query` (string, required): Search query / 搜尋關鍵字

- `list_libraries`: List all installed Arduino libraries / 列出所有已安裝的 Arduino 函式庫

  - No parameters required

- `uninstall_library`: Uninstall an Arduino library / 移除 Arduino 函式庫

  - **Parameters:**
    - `library_name` (string, required): Name of the library to uninstall / 要移除的函式庫名稱

- `library_examples`: Get examples from an installed library / 獲取已安裝函式庫的範例

  - **Parameters:**
    - `library_name` (string, required): Name of the library / 函式庫名稱

- `load_example`: Load a library example to the workspace / 載入函式庫範例到工作區

  - **Parameters:**
    - `library_name` (string, required): Name of the library / 函式庫名稱
    - `example_name` (string, required): Name of the example / 範例名稱

- `diagnose_error`: Diagnose compilation errors / 診斷編譯錯誤

  - **Parameters:**
    - `error_output` (string, required): Compilation error output / 編譯錯誤輸出

- `auto_install_libs`: Automatically install libraries used in a sketch / 自動安裝草圖中使用的函式庫

  - **Parameters:**
    - `sketch_path` (string, required): Path to the .ino file / .ino 文件的路徑

- `monitor`: Start serial monitor / 啟動串行監視器

  - **Parameters:**
    - `port` (string, required): Serial port / 串行端口
    - `baud_rate` (integer, default: 9600): Baud rate / 波特率

- `board_options`: Configure board options / 設定開發板選項
  - **Parameters:**
    - `fqbn` (string, required): Fully Qualified Board Name / 完整開發板名稱
    - `options` (object, required): Board options as key-value pairs / 開發板選項

## Interaction Examples

1. Listing available boards and platforms:

```json
{
  "name": "list",
  "arguments": {}
}
```

Response (example):

```json
{
  "connected": [
    {
      "port": "/dev/ttyACM0",
      "fqbn": "arduino:avr:uno",
      "board_name": "Arduino Uno"
    }
  ],
  "platforms": ["arduino:avr", "esp32:esp32"],
  "all_boards": "Board Name              FQBN            Core             \nArduino Uno             arduino:avr:uno arduino:avr      \nArduino Mega or Mega 2560 arduino:avr:mega arduino:avr      \n..."
}
```

2. Compiling a sketch:

```json
{
  "name": "compile",
  "arguments": {
    "sketch_path": "/path/to/Blink/Blink.ino",
    "fqbn": "arduino:avr:uno"
  }
}
```

Response (example):

```json
{
  "success": true,
  "build_dir": "/path/to/Blink/build",
  "hex_path": "/path/to/Blink/build/Blink.ino.hex",
  "error": "",
  "error_code": 0
}
```

3. Uploading a sketch:

```json
{
  "name": "upload",
  "arguments": {
    "sketch_path": "/path/to/Blink/Blink.ino",
    "port": "/dev/ttyACM0",
    "fqbn": "arduino:avr:uno"
  }
}
```

Response (example):

```json
{
  "success": true,
  "command": "arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno /path/to/Blink",
  "error": ""
}
```

4. Installing a library:

```json
{
  "name": "install_library",
  "arguments": {
    "library_name": "Servo"
  }
}
```

Response (example):

```json
{
  "success": true,
  "message": "Successfully installed Servo@1.2.1",
  "command": "arduino-cli lib install \"Servo\""
}
```

5. Error response example (compilation):

```json
{
  "success": false,
  "build_dir": "/path/to/ErrorSketch/build",
  "hex_path": "",
  "error": "Compilation failed: exit status 1\n/path/to/ErrorSketch/ErrorSketch.ino:5:1: error: expected ';' before '}' token\n }",
  "error_code": 1
}
```

## Debugging

You can use the MCP inspector tool to debug the server:

```bash
npx @modelcontextprotocol/inspector python -m arduino_cli_mcp
```

## Example Questions for Claude

1. "列出所有可用的 Arduino 開發板和平台" (List all available Arduino boards and platforms)
2. "幫我編譯 Blink 草圖，目標是 Arduino Uno" (Compile my Blink sketch for Arduino Uno)
3. "將我的 LED 專案上傳到連接在 /dev/ttyACM0 的 Arduino Mega" (Upload my LED project to the Arduino Mega on /dev/ttyACM0)
4. "搜尋關於 OLED 顯示器的函式庫" (Search for libraries related to OLED displays)
5. "安裝 Servo 函式庫" (Install the Servo library)
6. "列出所有已安裝的函式庫" (List all installed libraries)
7. "啟動 /dev/ttyACM0 的串行監視器" (Start the serial monitor for /dev/ttyACM0)

## Features

- Compile Arduino sketches / 編譯 Arduino 草圖
- Upload sketches or hex files to Arduino boards / 上傳草圖或 hex 檔案到 Arduino 開發板
- Install Arduino platforms / 安裝 Arduino 平台
- Check Arduino CLI version / 檢查 Arduino CLI 版本
- List available boards and platforms / 列出可用的開發板和平台
- Search, install, list, and uninstall Arduino libraries / 搜尋、安裝、列出和移除 Arduino 函式庫
- List and load library examples / 列出和載入函式庫範例
- Diagnose compilation errors / 診斷編譯錯誤
- Automatically install missing libraries for a sketch / 自動安裝草圖所需的函式庫
- Start serial monitor / 啟動串行監視器
- Configure board options / 設定開發板選項

## Contributing

We encourage you to contribute to arduino-cli-mcp to help expand and improve it. Whether you want to add new Arduino-related tools, enhance existing functionality, or improve documentation, your input is valuable.

For examples of other MCP servers and implementation patterns, see:
https://github.com/modelcontextprotocol/servers

Pull requests are welcome! Feel free to contribute new ideas, bug fixes, or improvements to make arduino-cli-mcp more powerful and useful.

## Related Links

- [Arduino CLI Documentation](https://arduino.github.io/arduino-cli/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

_For the Chinese version, please refer to [README.zh-tw.md](README.zh-tw.md)_
