# Arduino CLI MCP（受管指令處理器）

基於 Python 的 Arduino CLI 指令管理工具，支援常用操作的自動批准功能。

## 概述

Arduino CLI MCP 提供 Arduino CLI 的包裝器，通過自動批准重複操作等功能實現流程簡化。對於經常使用 Arduino 項目的開發者和教育者來說，此工具尤為有用。

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

## 使用方法

配置完成後，該工具將自動處理 Arduino CLI 命令，並對 `autoApprove` 部分列出的操作進行特殊處理。

## 系統要求

- Python 3.6+
- Arduino CLI
- 工作目錄的正確文件權限

## 相關連結

- [Arduino CLI 文檔](https://arduino.github.io/arduino-cli/)

---

_英文版請參閱 [README.md](README.md)_

# Arduino CLI MCP 伺服器

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

## 安裝方法

### 使用 uv（推薦）

當使用 [`uv`](https://docs.astral.sh/uv/) 時，不需要特別安裝。我們將使用 [`uvx`](https://docs.astral.sh/uv/guides/tools/) 直接執行 _arduino-cli-mcp_。

### 使用 PIP

或者您可以通過 pip 安裝 `arduino-cli-mcp`：

```bash
pip install arduino-cli-mcp
```

安裝後，您可以使用以下指令執行：

```bash
python -m arduino_cli_mcp
```

## 設定方式

### 為 Claude.app 設定

在您的 Claude 設定中新增：

<details>
<summary>使用 uvx</summary>

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
<summary>使用 pip 安裝</summary>

```json
"mcpServers": {
  "arduino": {
    "command": "python",
    "args": ["-m", "arduino_cli_mcp"]
  }
}
```

</details>

### 為 Zed 設定

在您的 Zed settings.json 檔案中新增：

<details>
<summary>使用 uvx</summary>

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
<summary>使用 pip 安裝</summary>

```json
"context_servers": {
  "arduino-cli-mcp": {
    "command": "python",
    "args": ["-m", "arduino_cli_mcp"]
  }
},
```

</details>

### 自訂設定 - Arduino CLI 路徑

預設情況下，伺服器會在系統 PATH 中尋找 Arduino CLI。您可以通過在設定中的 `args` 列表中添加 `--arduino-cli-path` 參數來指定自定路徑。

範例：

```json
{
  "command": "python",
  "args": ["-m", "arduino_cli_mcp", "--arduino-cli-path=/path/to/arduino-cli"]
}
```

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

## 除錯

您可以使用 MCP 檢查工具來除錯伺服器。對於 uvx 安裝：

```bash
npx @modelcontextprotocol/inspector uvx arduino-cli-mcp
```

或者，如果您在特定目錄安裝了套件或正在開發：

```bash
cd path/to/servers/src/arduino-cli
npx @modelcontextprotocol/inspector uv run arduino-cli-mcp
```

## Claude 問題範例

1. "哪些 Arduino 開發板目前連接到我的電腦？"
2. "為 Arduino Uno 編譯我的 Blink 草圖"
3. "將我的 LED 專案上傳到 COM5 埠上的 Arduino Mega"
4. "你能搜尋與 OLED 顯示器相關的函式庫嗎？"
5. "為 Arduino 安裝 Servo 函式庫"

## 貢獻

我們鼓勵您為 arduino-cli-mcp 做出貢獻，以幫助擴展和改進它。無論您想要添加新的 Arduino 相關工具、增強現有功能，還是改進文檔，您的投入都很有價值。

有關其他 MCP 伺服器和實現模式的範例，請參閱：
https://github.com/modelcontextprotocol/servers

歡迎提交 pull request！歡迎您貢獻新想法、錯誤修復或改進，使 arduino-cli-mcp 更加強大和實用。

## 授權條款

arduino-cli-mcp 是根據 MIT 授權條款發布的。這意味著您可以在遵守 MIT 授權條款的情況下自由使用、修改和分發該軟體。詳細信息請參見項目版本庫中的 LICENSE 文件。
