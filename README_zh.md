# Arduino CLI MCP（受管指令處理器）

Arduino CLI MCP 是一個為 VSCode 和 Claude 提供 Arduino CLI 整合的服務器，可讓您通過 Arduino CLI 編譯和上傳 Arduino 草圖。

## 概述

Arduino CLI MCP 提供 Arduino CLI 的包裝器，通過自動批准重複操作等功能實現流程簡化。對於經常使用 Arduino 項目的開發者和教育者來說，此工具尤為有用。

## 模型上下文協議 (Model Context Protocol, MCP) 介紹

Model Context Protocol (MCP) 是一個開放協議，專門用來讓大型語言模型 (LLM) 無縫整合外部數據來源與工具。無論是開發 AI IDE、強化聊天介面，還是構建自動化 AI 工作流，MCP 都能提供標準化的方式來連接 LLM 與所需的上下文環境。透過 MCP，Arduino CLI MCP 伺服器能夠與各種 AI 模型進行交互，處理 Arduino 相關的操作和命令。

## 安裝

```bash
pip install arduino-cli-mcp
```

安裝後，您可以使用以下命令運行：

```bash
python -m arduino_cli_mcp
```

## 先決條件

- Arduino CLI 已安裝並可在 PATH 中使用
- Python 3.11+
- 工作目錄具有適當的文件權限

## 配置

工具可以使用 JSON 格式進行配置，如下所示：

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

### 配置選項

- `command`：要執行的命令（此例中為 Python）
- `args`：傳遞給命令的參數列表
  - 第一個參數是主腳本的路徑
  - `--workdir` 指定 Arduino CLI 操作的工作目錄
- `disabled`：啟用/禁用工具（設置為 `false` 表示啟用）
- `autoApprove`：無需用户確認即可自動批准的 Arduino CLI 操作列表
  - 支持的操作：`upload`（上傳）、`compile`（編譯）、`install_board`（安裝開發板）

### Claude.app 的配置

將以下內容添加到您的 Claude 設置中：

```json
"mcpServers": {
  "arduino": {
    "command": "python",
    "args": ["-m", "arduino_cli_mcp"]
  }
}
```

### Zed 的配置

將以下內容添加到您的 Zed settings.json 文件中：

```json
"context_servers": {
  "arduino-cli-mcp": {
    "command": "python",
    "args": ["-m", "arduino_cli_mcp"]
  }
},
```

### 自訂配置 - Arduino CLI 路徑

預設情況下，伺服器會在系統 PATH 中尋找 Arduino CLI。您可以通過在設定中的 `args` 列表中添加 `--arduino-cli-path` 參數來指定自定路徑。

範例：

```json
{
  "command": "python",
  "args": ["-m", "arduino_cli_mcp", "--arduino-cli-path=/path/to/arduino-cli"]
}
```

## 使用方法

啟動 MCP 服務器：

```bash
arduino-cli-mcp --workdir /path/to/your/arduino/projects
```

配置完成後，該工具將自動處理 Arduino CLI 命令，並對 `autoApprove` 部分列出的操作進行特殊處理。

## Arduino CLI MCP 伺服器

這是一個提供 Arduino CLI 功能的模型上下文協議伺服器。此伺服器使大型語言模型能夠通過自然語言命令與 Arduino 開發板互動、編譯草圖、上傳韌體，以及管理函式庫。

### 可用工具

- `compile`: 編譯 Arduino 草圖

  - **參數:**
    - `sketch_path` (字串, 必要): .ino 檔案的路徑
    - `fqbn` (字串, 必要, 預設: 'arduino:avr:uno'): 完整開發板名稱 (例如 'arduino:avr:uno')

- `upload`: 上傳 Arduino 草圖或 hex 檔案到開發板

  - **參數:**
    - `sketch_path` (字串): .ino 檔案的路徑
    - `hex_path` (字串): hex 檔案的絕對路徑（可選，若提供則直接上傳）
    - `port` (字串, 必要): 開發板的串口
    - `fqbn` (字串, 必要, 預設: 'arduino:avr:uno'): 完整開發板名稱

- `install_board`: 安裝開發板平台

  - **參數:**
    - `platform_id` (字串, 必要): 平台 ID（例如 arduino:avr, esp32:esp32）

- `check`: 檢查 Arduino CLI 版本

  - 不需要參數

- `list`: 列出所有可用的開發板和平台

  - 不需要參數

- `install_library`: 安裝 Arduino 函式庫

  - **參數:**
    - `library_name` (字串, 必要): 要安裝的函式庫名稱

- `search_library`: 搜尋 Arduino 函式庫

  - **參數:**
    - `query` (字串, 必要): 搜尋關鍵字

- `list_libraries`: 列出所有已安裝的 Arduino 函式庫

  - 不需要參數

- `uninstall_library`: 移除 Arduino 函式庫

  - **參數:**
    - `library_name` (字串, 必要): 要移除的函式庫名稱

- `library_examples`: 獲取已安裝函式庫的範例

  - **參數:**
    - `library_name` (字串, 必要): 函式庫名稱

- `load_example`: 載入函式庫範例到工作區

  - **參數:**
    - `library_name` (字串, 必要): 函式庫名稱
    - `example_name` (字串, 必要): 範例名稱

- `diagnose_error`: 診斷編譯錯誤

  - **參數:**
    - `error_output` (字串, 必要): 編譯錯誤輸出

- `auto_install_libs`: 自動安裝草圖中使用的函式庫

  - **參數:**
    - `sketch_path` (字串, 必要): .ino 檔案的路徑

- `monitor`: 啟動串行監視器

  - **參數:**
    - `port` (字串, 必要): 串行端口
    - `baud_rate` (整數, 預設: 9600): 波特率

- `board_options`: 設定開發板選項
  - **參數:**
    - `fqbn` (字串, 必要): 完整開發板名稱
    - `options` (物件, 必要): 開發板選項 (鍵值對)

## 互動範例

1. 列出可用的開發板和平台：

```json
{
  "name": "list",
  "arguments": {}
}
```

回應 (範例):

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

2. 編譯草圖：

```json
{
  "name": "compile",
  "arguments": {
    "sketch_path": "/path/to/Blink/Blink.ino",
    "fqbn": "arduino:avr:uno"
  }
}
```

回應 (範例):

```json
{
  "success": true,
  "build_dir": "/path/to/Blink/build",
  "hex_path": "/path/to/Blink/build/Blink.ino.hex",
  "error": "",
  "error_code": 0
}
```

3. 上傳草圖：

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

回應 (範例):

```json
{
  "success": true,
  "command": "arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno /path/to/Blink",
  "error": ""
}
```

4. 安裝函式庫：

```json
{
  "name": "install_library",
  "arguments": {
    "library_name": "Servo"
  }
}
```

回應 (範例):

```json
{
  "success": true,
  "message": "Successfully installed Servo@1.2.1",
  "command": "arduino-cli lib install \"Servo\""
}
```

5. 錯誤回應範例 (編譯)：

```json
{
  "success": false,
  "build_dir": "/path/to/ErrorSketch/build",
  "hex_path": "",
  "error": "Compilation failed: exit status 1\n/path/to/ErrorSketch/ErrorSketch.ino:5:1: error: expected ';' before '}' token\n }",
  "error_code": 1
}
```

## 調試

您可以使用 MCP inspector 工具來除錯伺服器：

```bash
npx @modelcontextprotocol/inspector python -m arduino_cli_mcp
```

## Claude 問題範例

1. "列出所有可用的 Arduino 開發板和平台"
2. "幫我編譯 Blink 草圖，目標是 Arduino Uno"
3. "將我的 LED 專案上傳到連接在 /dev/ttyACM0 的 Arduino Mega"
4. "搜尋關於 OLED 顯示器的函式庫"
5. "安裝 Servo 函式庫"
6. "列出所有已安裝的函式庫"
7. "啟動 /dev/ttyACM0 的串行監視器"

## 功能

- 編譯 Arduino 草圖
- 上傳草圖或 hex 檔案到 Arduino 開發板
- 安裝 Arduino 平台
- 檢查 Arduino CLI 版本
- 列出可用的開發板和平台
- 搜尋、安裝、列出和移除 Arduino 函式庫
- 列出和載入函式庫範例
- 診斷編譯錯誤
- 自動安裝草圖所需的函式庫
- 啟動串行監視器
- 設定開發板選項

## 貢獻

我們鼓勵您為 arduino-cli-mcp 做出貢獻，以幫助擴展和改進它。無論您想要添加新的 Arduino 相關工具、增強現有功能，還是改進文檔，您的投入都很有價值。

有關其他 MCP 伺服器和實現模式的範例，請參閱：
https://github.com/modelcontextprotocol/servers

歡迎提交 pull request！歡迎您貢獻新想法、錯誤修復或改進，使 arduino-cli-mcp 更加強大和實用。

## 相關鏈接

- [Arduino CLI 文檔](https://arduino.github.io/arduino-cli/)

## 授權條款

此項目根據 MIT 授權條款發布的。這意味著您可以在遵守 MIT 授權條款的情況下自由使用、修改和分發該軟體。詳細信息請參見項目版本庫中的 LICENSE 文件。

---

_英文版請參閱 [README.md](README.md)_
