# 安裝指南

## 前置需求

使用 arduino-cli-mcp 前，您需要：

1. Python 3.8+ 環境
2. Arduino CLI 已安裝並設定在您的系統路徑中

## Arduino CLI 安裝指南

根據您的操作系統，請按照以下步驟安裝 Arduino CLI：

### Windows

1. 下載最新版 Arduino CLI：https://arduino.github.io/arduino-cli/latest/installation/
2. 解壓縮並將可執行檔案路徑添加到系統環境變數 PATH 中
3. 驗證安裝：`arduino-cli version`

### macOS

使用 Homebrew：

```
brew install arduino-cli
```

或手動安裝：

```
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
```

### Linux

使用以下命令：

```
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
```

或從官方網站下載預編譯二進制文件。

## 驗證安裝

安裝完成後，請在終端機/命令提示字元中執行：

```
arduino-cli version
```

如果顯示版本資訊，則表示安裝成功。
