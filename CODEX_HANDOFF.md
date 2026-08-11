# FlipClock V0.6.5 - Codex Handoff

## 專案定位

FlipClock 是 Python/Tkinter 製作的鐵路式上下翻牌時鐘。Windows 版使用原生 Win32 系統匣，維持零第三方 tray 依賴；macOS/Linux 則保留基本置頂時鐘視窗。

## 本版完成

1. 由 V0.6.4 升級到 V0.6.5。
2. `.py` / `.pyw` / BAT / Nuitka metadata / ICO 檔名同步進版。
3. Windows tray icon 優先載入程式同資料夾的 `FlipClock_V0.6.5.ico`。
4. 若同資料夾 ICO 不存在，fallback 到 `sys.executable` embedded icon，再 fallback 到 Windows 預設應用程式圖示。
5. 由 `LoadImageW` 或 `ExtractIconExW` 建立的 icon handle 會在 tray 關閉時釋放。
6. 非 Windows 平台不再啟動 Win32 tray thread，避免基本視窗被 tray 失敗流程關閉。
7. 更新 GitHub README，按程式特色重新整理 repo 簡介、功能、執行與建置方式。

## 仍需在 Windows 實機驗收

- `.pyw` 雙擊能顯示時鐘。
- Windows 工作列沒有 FlipClock 圖示。
- Windows 系統匣有 FlipClock 圖示。
- 自訂 ICO 存在時，系統匣使用該圖示。
- X / Esc 僅隱藏，不直接結束。
- 系統匣右鍵可以結束程式。
- 每分鐘翻牌正常。
- Standalone 可啟動。
- Onefile 若建置，啟動後不得只剩背景程序。

## 建置建議

優先用 Python 3.13 64-bit：

```bat
py -3.13 -m pip install --upgrade Nuitka ordered-set zstandard
Build_FlipClock_V0.6.5_Standalone.bat
Build_FlipClock_V0.6.5_Onefile.bat
```
