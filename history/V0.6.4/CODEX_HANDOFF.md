# FlipClock V0.6.4 — Codex Handoff

## 專案目標
這是一個 Python/Tkinter 的鐵路式上下翻牌時鐘。視窗黑底白字、每分鐘翻牌、無標題列、最上層顯示，並在 Windows 使用原生系統匣。

## 目前版本
- 版本：V0.6.4
- 主程式：`FlipClock_V0.6.4.py`
- 無 console 執行：`FlipClock_V0.6.4.pyw`
- Windows 圖示：`FlipClock_V0.6.4.ico`
- Nuitka Onefile：`Build_FlipClock_V0.6.4_Onefile.bat`
- Nuitka Standalone：`Build_FlipClock_V0.6.4_Standalone.bat`

## 已完成功能
1. 鐵路式上下翻牌時鐘，四個數字獨立翻動。
2. 每張數字牌中央固定水平分隔線。
3. 每分鐘只翻動有變化的數字。
4. 黑色背景、白色文字；Windows 使用 Microsoft JhengHei。
5. 視窗無標題列，可拖曳移動。
6. 視窗保持最上層。
7. Windows 使用原生 Win32 系統匣，不依賴 pystray 或 Pillow。
8. 右上角 X / Esc：隱藏到系統匣。
9. 系統匣：左鍵/雙擊切換顯示，右鍵選單可顯示/隱藏或結束。
10. 隱藏 Tk 根視窗，時鐘使用 Toplevel，避免工作列圖示。
11. Nuitka 可建 standalone / onefile。

## 重要限制 / 歷史問題
- V0.6.x 曾遇到 Nuitka EXE 只在背景執行、視窗不顯示，因此不要輕易改回根視窗直接 `overrideredirect(True)` 的架構。
- V0.6.3 使用 pystray/Pillow，因缺套件失敗；V0.6.4 已改為純 Win32 原生系統匣，請維持零第三方系統匣依賴。
- Nuitka 建議使用 Python 3.13 64-bit。Python 3.14 + Nuitka 4.1.3 曾出現實驗性支援警告。
- Onefile 容易被防毒軟體誤判；Standalone 通常較穩定。

## 下一步待辦（最新需求）
### A. `.pyw` 執行時支援自訂圖示
目前原生系統匣會從 `sys.executable` 抽取圖示。請改成：
1. 優先尋找主程式同資料夾的 `FlipClock_V0.6.4.ico`（進版後檔名同步）。
2. 若存在，使用 Win32 `LoadImageW(..., IMAGE_ICON, ..., LR_LOADFROMFILE | LR_DEFAULTSIZE)` 載入。
3. 若不存在，再 fallback 到 `sys.executable` 的 embedded icon。
4. `.pyw` 直接執行與 Nuitka EXE 都要正常。
5. 不新增 Pillow、pystray 等外部依賴。

### B. 版本規則
- 目前基準 V0.6.4。
- 一般修正 / 小功能：增加第三碼，例如 V0.6.5、V0.6.6。
- 不要無故跳大版本。
- 檔名、視窗內 VERSION、Nuitka metadata、BAT 輸出檔名需同步進版。

## Nuitka 建置要求
優先用 Python 3.13：
```bat
py -3.13 -m pip install --upgrade Nuitka ordered-set zstandard
```
Standalone 先測，成功後再 Onefile。

### Standalone
```bat
py -3.13 -m nuitka ^
  --mode=standalone ^
  --enable-plugin=tk-inter ^
  --windows-console-mode=disable ^
  --output-dir=build_standalone ^
  --output-filename=FlipClock_V0.6.4.exe ^
  --windows-icon-from-ico=FlipClock_V0.6.4.ico ^
  FlipClock_V0.6.4.py
```

### Onefile
```bat
py -3.13 -m nuitka ^
  --mode=onefile ^
  --enable-plugin=tk-inter ^
  --windows-console-mode=disable ^
  --output-dir=build ^
  --output-filename=FlipClock_V0.6.4.exe ^
  --windows-icon-from-ico=FlipClock_V0.6.4.ico ^
  FlipClock_V0.6.4.py
```

## 驗收重點
修改後至少檢查：
- `.pyw` 雙擊能顯示時鐘。
- Windows 工作列沒有 FlipClock 圖示。
- Windows 系統匣有 FlipClock 圖示。
- 自訂 ICO 存在時，系統匣使用該圖示。
- X / Esc 僅隱藏，不直接結束。
- 系統匣右鍵可以結束程式。
- 每分鐘翻牌正常。
- Standalone 可啟動。
- Onefile 若建置，啟動後不得只剩背景程序。

## 給 Codex 的工作方式
先閱讀 `FlipClock_V0.6.4.py`，盡量局部修改，不要重寫整個 UI/動畫架構。每次修改後做 Python 語法檢查，並同步更新 `.py` / `.pyw` / BAT / 版本資訊。
