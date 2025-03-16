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

- `list_boards` - 列出所有已連接的 Arduino 開發板。

  - 不需要參數

- `compile_sketch` - 編譯 Arduino 草圖。

  - 必要參數：
    - `sketch_path` (字串)：草圖檔案路徑
    - `board_fqbn` (字串)：完整合格板名稱（例如 'arduino:avr:uno'）

- `upload_sketch` - 上傳已編譯的草圖到開發板。

  - 必要參數：
    - `sketch_path` (字串)：草圖檔案路徑
    - `board_fqbn` (字串)：完整合格板名稱
    - `port` (字串)：用於上傳的埠（例如 '/dev/ttyACM0'、'COM3'）

- `search_library` - 搜尋 Arduino 函式庫。

  - 必要參數：
    - `query` (字串)：搜尋詞彙

- `install_library` - 安裝 Arduino 函式庫。
  - 必要參數：
    - `library_name` (字串)：要安裝的函式庫名稱

## 互動範例

1. 列出已連接的開發板：

```json
{
  "name": "list_boards",
  "arguments": {}
}
```

回應：

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

2. 編譯草圖：

```json
{
  "name": "compile_sketch",
  "arguments": {
    "sketch_path": "/path/to/Blink.ino",
    "board_fqbn": "arduino:avr:uno"
  }
}
```

回應：

```json
{
  "success": true,
  "output": "Sketch uses 924 bytes (2%) of program storage space. Maximum is 32256 bytes.",
  "binary_path": "/path/to/build/arduino.avr.uno/Blink.ino.hex"
}
```

3. 錯誤回應範例：

```json
{
  "error": true,
  "message": "編譯失敗：第5行有語法錯誤",
  "details": "語句結尾缺少分號"
}
```

## 調試

您可以使用 MCP inspector 工具來除錯伺服器：

```bash
npx @modelcontextprotocol/inspector python -m arduino_cli_mcp
```

## Claude 問題範例

1. "哪些 Arduino 開發板目前連接到我的電腦？"
2. "為 Arduino Uno 編譯我的 Blink 草圖"
3. "將我的 LED 專案上傳到 COM5 埠上的 Arduino Mega"
4. "你能搜尋與 OLED 顯示器相關的函式庫嗎？"
5. "為 Arduino 安裝 Servo 函式庫"

## 功能

- 編譯 Arduino 草圖
- 上傳草圖到 Arduino 板
- 安裝 Arduino 平台
- 列出可用的板和平台
- 創建和管理 Arduino 項目
- 搜索和安裝庫

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
