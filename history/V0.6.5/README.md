# FlipClock

鐵路式上下翻牌時鐘，以 Python/Tkinter 製作的小型桌面工具。畫面保持黑底白字、無標題列、置頂顯示，適合放在桌面角落當作乾淨醒目的時間提示。

## 特色

- 四位數字獨立上下翻牌，只在分鐘變化時翻動需要更新的數字。
- 黑底白字與中央水平分隔線，呈現鐵路翻牌鐘的視覺節奏。
- 無標題列視窗，可用滑鼠拖曳移動，預設出現在螢幕右上角。
- Windows 版使用原生 Win32 系統匣，不依賴 Pillow、pystray 或其他第三方 tray 套件。
- 右上角 X、Esc 會隱藏到系統匣；系統匣左鍵/雙擊切換顯示，右鍵選單可結束程式。
- `.pyw` 直接執行與 Nuitka EXE 都會優先使用同資料夾的自訂 ICO。
- Windows 會隱藏工作列與 Alt+Tab 圖示，只保留系統匣入口。
- macOS/Linux 保留基本置頂時鐘視窗，不啟用 Windows-only 系統匣流程。

## 目前版本

V0.6.5

本版重點：

- 系統匣優先載入同資料夾 `FlipClock_V0.6.5.ico`，不存在時才回退到 EXE embedded icon 或系統預設圖示。
- 釋放由 `LoadImageW`/`ExtractIconExW` 取得的 icon handle，避免 tray 結束時留下資源。
- 非 Windows 平台不再啟動 Win32 tray thread，維持基本時鐘視窗。
- 同步 `.py`、`.pyw`、Nuitka build scripts 與版本資訊。

## 執行

需要 Python 3.10 以上，Windows 建議 Python 3.13 64-bit。

```bash
python FlipClock_V0.6.5.py
```

Windows 若要無 console 執行，可直接雙擊：

```text
FlipClock_V0.6.5.pyw
```

## 建置 Windows EXE

建議先測 standalone，確認可啟動後再建 onefile。

```bat
Build_FlipClock_V0.6.5_Standalone.bat
Build_FlipClock_V0.6.5_Onefile.bat
```

Build script 會安裝/更新 Nuitka、ordered-set、zstandard，並使用 `FlipClock_V0.6.5.ico` 作為 EXE 圖示。

## 檔案

- `FlipClock_V0.6.5.py`: 主程式。
- `FlipClock_V0.6.5.pyw`: Windows 無 console 執行入口。
- `FlipClock_V0.6.5.ico`: Windows EXE 與系統匣圖示。
- `Build_FlipClock_V0.6.5_Standalone.bat`: Nuitka standalone 建置。
- `Build_FlipClock_V0.6.5_Onefile.bat`: Nuitka onefile 建置。
- `CODEX_HANDOFF.md`: 版本交接與驗收重點。

## 驗收重點

- `.pyw` 雙擊能顯示時鐘。
- Windows 工作列沒有 FlipClock 圖示，系統匣有 FlipClock 圖示。
- 自訂 ICO 存在時，系統匣使用同資料夾 ICO。
- X / Esc 只隱藏到系統匣，不直接結束。
- 系統匣右鍵選單可以結束程式。
- 每分鐘翻牌正常，且只翻動變化的數字。
