# 發版流程

本專案透過 GitHub Actions + PyPI Trusted Publishing 自動發版。**不要手動 `twine upload`**，否則容易像 0.1.5 那次把殘缺 wheel 推到 PyPI。

## 標準流程

1. **改版本號**（兩個地方一定要同步，CI 會驗）
   - `pyproject.toml` 的 `version = "X.Y.Z"`
   - `arduino_cli_mcp/__init__.py` 的 `__version__ = "X.Y.Z"`

2. **提交版本 commit**
   ```bash
   git commit -am "release: X.Y.Z"
   git push
   ```

3. **打 tag 並推上去**
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

   推 tag 會觸發 `.github/workflows/release.yml`，自動跑：
   - 驗證 tag `vX.Y.Z` 與 `pyproject.toml` 的版本一致（不一致直接 fail）
   - `python -m build` 產生 sdist + wheel
   - 把 wheel 裝進臨時 venv，import `serve`/`main` 做 smoke test
   - 透過 OIDC trusted publishing 上傳到 PyPI

4. **驗證**
   ```bash
   pip install -U arduino-cli-mcp
   python -c "from arduino_cli_mcp.main import serve; print(serve)"
   ```

## 一次性設定（已完成，新增 maintainer 才需要重做）

### PyPI 端
- 到 <https://pypi.org/manage/project/arduino-cli-mcp/settings/publishing/> 新增 GitHub publisher：
  - Owner: `Oliver0804`
  - Repository: `arduino-cli-mcp`
  - Workflow: `release.yml`
  - Environment: `pypi`

### GitHub 端
- Settings → Environments → 建立名為 `pypi` 的 environment（可加保護規則例如 required reviewer）

## Troubleshooting

| 症狀 | 原因 | 處理 |
|---|---|---|
| `Tag vX.Y.Z does not match pyproject.toml version` | tag 跟 `pyproject.toml` 對不上 | 改 `pyproject.toml` 重新 commit、刪 tag 重打 |
| `invalid-publisher: ... no corresponding publisher` | PyPI Trusted Publisher 沒設好 | 對齊上面「PyPI 端」四個欄位 |
| Build job 過但 Publish 跳過 | GitHub environment `pypi` 不存在 | 建環境後 `gh run rerun --failed <id>` |
| 已存在版號 | 同一版號不能上傳兩次 | bump 到下個 patch 版重發 |

## 緊急 fallback（避免使用）

如果 GitHub Actions 整個壞掉、又急著發版，**且你清楚目前 `arduino_cli_mcp/main.py` 是完整可運作的版本**：

```bash
rm -rf dist build
uv build
twine upload dist/*
```

發完務必：
1. 在本機跑 `pip install --force-reinstall arduino-cli-mcp==X.Y.Z` 驗證 import
2. 補回 GitHub Actions、確認下次能走正規流程
