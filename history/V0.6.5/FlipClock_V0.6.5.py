# -*- coding: utf-8 -*-
"""
鐵路翻牌時鐘 FlipClock V0.6.5

Windows Nuitka 專案參數：
直接執行「python -m nuitka FlipClock_V0.6.5.py」即可產生單一 EXE。
"""

# Nuitka project options：僅在 Windows 建立單一 GUI 執行檔。
# nuitka-project-if: {OS} == "Windows":
#    nuitka-project: --mode=onefile
#    nuitka-project: --enable-plugin=tk-inter
#    nuitka-project: --windows-console-mode=disable
#    nuitka-project: --output-dir={MAIN_DIRECTORY}/build
#    nuitka-project: --output-filename=FlipClock_V0.6.5.exe
#    nuitka-project: --remove-output
#    nuitka-project: --assume-yes-for-downloads
#    nuitka-project: --python-flag=no_docstrings
#    nuitka-project: --file-version=0.6.5.0
#    nuitka-project: --product-version=0.6.5.0
#    nuitka-project: --product-name=FlipClock
#    nuitka-project: --file-description=Railway Flip Clock
#    nuitka-project: --report={MAIN_DIRECTORY}/build/FlipClock_V0.6.5_compilation-report.xml
#    nuitka-project: --force-stdout-spec={PROGRAM_BASE}.out.txt
#    nuitka-project: --force-stderr-spec={PROGRAM_BASE}.err.txt

from __future__ import annotations

import ctypes
import os
import queue
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path


APP_NAME = "鐵路翻牌時鐘"
VERSION = "V0.6.5"
ICON_FILENAME = "FlipClock_V0.6.5.ico"

WINDOW_WIDTH_PT = 100
WINDOW_HEIGHT_PT = 50

WINDOW_BG = "#000000"
CARD_BORDER = "#1B1B1B"
TOP_BG = "#101010"
BOTTOM_BG = "#080808"
FLAP_DARK = "#050505"
TEXT_COLOR = "#FFFFFF"
DIM_TEXT_COLOR = "#9A9A9A"
CENTER_LINE_TOP = "#2A2A2A"
CENTER_LINE_BOTTOM = "#000000"
CLOSE_IDLE = "#686868"

ANIMATION_STEPS = 8
ANIMATION_DELAY_MS = 32
MAC_TOPMOST_INTERVAL_MS = 5000



def preferred_font() -> str:
    """依作業系統選擇正黑體風格字型。"""
    if sys.platform == "darwin":
        return "PingFang TC"
    if sys.platform.startswith("win"):
        return "Microsoft JhengHei"
    return "Noto Sans CJK TC"


FONT_NAME = preferred_font()



def enable_dpi_awareness() -> None:
    """啟用 Windows DPI 感知；其他平台不處理。"""
    if not sys.platform.startswith("win"):
        return

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass



def executable_directory() -> Path:
    """取得原始腳本或 Nuitka 單檔 EXE 所在資料夾。"""
    try:
        compiled = globals()["__compiled__"]
        return Path(compiled.containing_dir).resolve()
    except (KeyError, AttributeError, TypeError):
        pass

    try:
        return Path(__file__).resolve().parent
    except (NameError, OSError, RuntimeError):
        pass

    try:
        return Path(sys.argv[0]).resolve().parent
    except (OSError, RuntimeError):
        return Path.cwd()



def write_error_log(error_text: str):
    """優先寫在程式旁；無權限時改寫入系統暫存資料夾。"""
    import tempfile
    from pathlib import Path
    candidates = (
        executable_directory() / "FlipClock_error.log",
        Path(tempfile.gettempdir()) / "FlipClock_error.log",
    )

    for path in candidates:
        try:
            path.write_text(error_text, encoding="utf-8")
            return path
        except OSError:
            continue
    return None


class FlipCell(tk.Frame):
    """單一鐵路式上下翻牌數字。"""

    def __init__(
        self,
        master: tk.Misc,
        width: int,
        height: int,
        font_size: int,
        initial: str = "0",
    ) -> None:
        super().__init__(
            master,
            width=width,
            height=height,
            bg=CARD_BORDER,
            bd=0,
            highlightthickness=0,
        )
        self.pack_propagate(False)

        self.inner_width = max(4, width - 2)
        self.inner_height = max(6, height - 2)
        self.half_height = self.inner_height // 2
        self.bottom_height = self.inner_height - self.half_height
        self.font = (FONT_NAME, font_size, "bold")
        self.value = initial
        self.animation_job: str | None = None

        self.top_canvas = self._make_canvas(TOP_BG)
        self.top_canvas.place(x=1, y=1, width=self.inner_width, height=self.half_height)

        self.bottom_canvas = self._make_canvas(BOTTOM_BG)
        self.bottom_canvas.place(
            x=1,
            y=1 + self.half_height,
            width=self.inner_width,
            height=self.bottom_height,
        )

        self.top_text = self.top_canvas.create_text(
            self.inner_width / 2,
            self.half_height,
            text=initial,
            fill=TEXT_COLOR,
            font=self.font,
            anchor="center",
        )
        self.bottom_text = self.bottom_canvas.create_text(
            self.inner_width / 2,
            0,
            text=initial,
            fill=TEXT_COLOR,
            font=self.font,
            anchor="center",
        )

        self.line_top = tk.Frame(self, bg=CENTER_LINE_TOP, bd=0)
        self.line_top.place(x=1, y=self.half_height, width=self.inner_width, height=1)

        self.line_bottom = tk.Frame(self, bg=CENTER_LINE_BOTTOM, bd=0)
        self.line_bottom.place(
            x=1,
            y=self.half_height + 1,
            width=self.inner_width,
            height=1,
        )

        self.flip_top = self._make_canvas(TOP_BG)
        self.flip_bottom = self._make_canvas(BOTTOM_BG)
        self.flip_top_text = self.flip_top.create_text(
            0,
            0,
            text=initial,
            fill=TEXT_COLOR,
            font=self.font,
            anchor="center",
        )
        self.flip_bottom_text = self.flip_bottom.create_text(
            0,
            0,
            text=initial,
            fill=TEXT_COLOR,
            font=self.font,
            anchor="center",
        )

    def _make_canvas(self, background: str) -> tk.Canvas:
        return tk.Canvas(
            self,
            bg=background,
            bd=0,
            highlightthickness=0,
        )

    def cancel_animation(self) -> None:
        if self.animation_job is not None:
            try:
                self.after_cancel(self.animation_job)
            except tk.TclError:
                pass
            self.animation_job = None

        self.flip_top.place_forget()
        self.flip_bottom.place_forget()

    def _set_static_top(self, value: str) -> None:
        self.top_canvas.itemconfigure(self.top_text, text=value, fill=TEXT_COLOR)

    def _set_static_bottom(self, value: str) -> None:
        self.bottom_canvas.itemconfigure(self.bottom_text, text=value, fill=TEXT_COLOR)

    def set_value(self, value: str) -> None:
        self.cancel_animation()
        self.value = value
        self._set_static_top(value)
        self._set_static_bottom(value)

    def flip_to(self, new_value: str) -> None:
        if new_value == self.value:
            return

        self.cancel_animation()
        old_value = self.value

        # 新字的上半部先藏在舊翻片後方；舊下半部保持不變。
        self._set_static_top(new_value)
        self._set_static_bottom(old_value)
        self._collapse_old_top(step=0, old_value=old_value, new_value=new_value)

    def _raise_center_seam(self) -> None:
        self.line_top.lift()
        self.line_bottom.lift()

    def _collapse_old_top(self, step: int, old_value: str, new_value: str) -> None:
        if step > ANIMATION_STEPS:
            self.flip_top.place_forget()
            self._expand_new_bottom(step=0, new_value=new_value)
            return

        ratio = 1.0 - (step / ANIMATION_STEPS)
        visible_height = max(1, round(self.half_height * ratio))
        y_pos = 1 + self.half_height - visible_height
        is_dim = ratio < 0.42

        self.flip_top.configure(bg=FLAP_DARK if ratio < 0.45 else TOP_BG)
        self.flip_top.place(
            x=1,
            y=y_pos,
            width=self.inner_width,
            height=visible_height,
        )
        self.flip_top.coords(
            self.flip_top_text,
            self.inner_width / 2,
            visible_height,
        )
        self.flip_top.itemconfigure(
            self.flip_top_text,
            text=old_value,
            fill=DIM_TEXT_COLOR if is_dim else TEXT_COLOR,
        )
        self._raise_center_seam()

        self.animation_job = self.after(
            ANIMATION_DELAY_MS,
            self._collapse_old_top,
            step + 1,
            old_value,
            new_value,
        )

    def _expand_new_bottom(self, step: int, new_value: str) -> None:
        if step > ANIMATION_STEPS:
            self.flip_bottom.place_forget()
            self.value = new_value
            self._set_static_top(new_value)
            self._set_static_bottom(new_value)
            self._raise_center_seam()
            self.animation_job = None
            return

        ratio = step / ANIMATION_STEPS
        visible_height = max(1, round(self.bottom_height * ratio))
        is_dim = ratio < 0.42

        self.flip_bottom.configure(bg=FLAP_DARK if ratio < 0.45 else BOTTOM_BG)
        self.flip_bottom.place(
            x=1,
            y=1 + self.half_height,
            width=self.inner_width,
            height=visible_height,
        )
        self.flip_bottom.coords(
            self.flip_bottom_text,
            self.inner_width / 2,
            0,
        )
        self.flip_bottom.itemconfigure(
            self.flip_bottom_text,
            text=new_value,
            fill=DIM_TEXT_COLOR if is_dim else TEXT_COLOR,
        )
        self._raise_center_seam()

        self.animation_job = self.after(
            ANIMATION_DELAY_MS,
            self._expand_new_bottom,
            step + 1,
            new_value,
        )




class NativeWindowsTray:
    """Windows 原生系統匣；不依賴 pystray 或 Pillow。"""

    WM_APP = 0x8000
    WM_TRAYICON = WM_APP + 1
    WM_UPDATE_TIP = WM_APP + 2

    WM_COMMAND = 0x0111
    WM_CLOSE = 0x0010
    WM_DESTROY = 0x0002
    WM_NULL = 0x0000
    WM_LBUTTONUP = 0x0202
    WM_LBUTTONDBLCLK = 0x0203
    WM_RBUTTONUP = 0x0205
    WM_CONTEXTMENU = 0x007B

    CMD_TOGGLE = 1001
    CMD_EXIT = 1002

    NIM_ADD = 0
    NIM_MODIFY = 1
    NIM_DELETE = 2

    NIF_MESSAGE = 0x00000001
    NIF_ICON = 0x00000002
    NIF_TIP = 0x00000004

    MF_STRING = 0x00000000
    MF_SEPARATOR = 0x00000800
    TPM_RIGHTBUTTON = 0x0002
    TPM_RETURNCMD = 0x0100
    IDI_APPLICATION = 32512
    IMAGE_ICON = 1
    LR_LOADFROMFILE = 0x00000010
    LR_DEFAULTSIZE = 0x00000040

    def __init__(self, command_queue: queue.Queue[str], tooltip: str) -> None:
        self.command_queue = command_queue
        self.tooltip = tooltip[:127]

        self.ready_event = threading.Event()
        self.failed_event = threading.Event()
        self.error_text = ""

        self.thread: threading.Thread | None = None
        self.hwnd = 0
        self._post_message = None
        self._notify_data = None
        self._wndproc_ref = None
        self._tray_icon = 0
        self._owns_tray_icon = False

    def start(self) -> None:
        self.thread = threading.Thread(
            target=self._thread_main,
            name="FlipClockNativeTray",
            daemon=True,
        )
        self.thread.start()

    def stop(self) -> None:
        if self.hwnd and self._post_message is not None:
            try:
                self._post_message(self.hwnd, self.WM_CLOSE, 0, 0)
            except Exception:
                pass

    def update_tooltip(self, text: str) -> None:
        self.tooltip = text[:127]
        if self.hwnd and self._post_message is not None:
            try:
                self._post_message(self.hwnd, self.WM_UPDATE_TIP, 0, 0)
            except Exception:
                pass

    def _thread_main(self) -> None:
        if not sys.platform.startswith("win"):
            self.error_text = "原生系統匣只支援 Windows。"
            self.failed_event.set()
            self.ready_event.set()
            return

        try:
            self._run_windows()
        except Exception as exc:
            self.error_text = f"{type(exc).__name__}: {exc}"
            self.failed_event.set()
            self.ready_event.set()

    def _run_windows(self) -> None:
        from ctypes import wintypes

        LRESULT = ctypes.c_ssize_t
        WNDPROC = ctypes.WINFUNCTYPE(
            LRESULT,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )

        class POINT(ctypes.Structure):
            _fields_ = [
                ("x", wintypes.LONG),
                ("y", wintypes.LONG),
            ]

        class MSG(ctypes.Structure):
            _fields_ = [
                ("hwnd", wintypes.HWND),
                ("message", wintypes.UINT),
                ("wParam", wintypes.WPARAM),
                ("lParam", wintypes.LPARAM),
                ("time", wintypes.DWORD),
                ("pt", POINT),
                ("lPrivate", wintypes.DWORD),
            ]

        class WNDCLASSEXW(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.UINT),
                ("style", wintypes.UINT),
                ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE),
                ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
                ("hIconSm", wintypes.HICON),
            ]

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", ctypes.c_ubyte * 8),
            ]

        class NOTIFYICONDATAW(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("hWnd", wintypes.HWND),
                ("uID", wintypes.UINT),
                ("uFlags", wintypes.UINT),
                ("uCallbackMessage", wintypes.UINT),
                ("hIcon", wintypes.HICON),
                ("szTip", wintypes.WCHAR * 128),
                ("dwState", wintypes.DWORD),
                ("dwStateMask", wintypes.DWORD),
                ("szInfo", wintypes.WCHAR * 256),
                ("uTimeoutOrVersion", wintypes.UINT),
                ("szInfoTitle", wintypes.WCHAR * 64),
                ("dwInfoFlags", wintypes.DWORD),
                ("guidItem", GUID),
                ("hBalloonIcon", wintypes.HICON),
            ]

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        shell32 = ctypes.WinDLL("shell32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        kernel32.GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE

        user32.RegisterClassExW.argtypes = (ctypes.POINTER(WNDCLASSEXW),)
        user32.RegisterClassExW.restype = wintypes.ATOM

        user32.CreateWindowExW.argtypes = (
            wintypes.DWORD,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.DWORD,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.HWND,
            wintypes.HMENU,
            wintypes.HINSTANCE,
            wintypes.LPVOID,
        )
        user32.CreateWindowExW.restype = wintypes.HWND

        user32.DefWindowProcW.argtypes = (
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )
        user32.DefWindowProcW.restype = LRESULT

        user32.DestroyWindow.argtypes = (wintypes.HWND,)
        user32.DestroyWindow.restype = wintypes.BOOL
        user32.PostQuitMessage.argtypes = (ctypes.c_int,)
        user32.PostQuitMessage.restype = None

        user32.GetMessageW.argtypes = (
            ctypes.POINTER(MSG),
            wintypes.HWND,
            wintypes.UINT,
            wintypes.UINT,
        )
        user32.GetMessageW.restype = ctypes.c_int
        user32.TranslateMessage.argtypes = (ctypes.POINTER(MSG),)
        user32.TranslateMessage.restype = wintypes.BOOL
        user32.DispatchMessageW.argtypes = (ctypes.POINTER(MSG),)
        user32.DispatchMessageW.restype = LRESULT

        user32.PostMessageW.argtypes = (
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )
        user32.PostMessageW.restype = wintypes.BOOL
        self._post_message = user32.PostMessageW

        user32.CreatePopupMenu.argtypes = ()
        user32.CreatePopupMenu.restype = wintypes.HMENU
        user32.AppendMenuW.argtypes = (
            wintypes.HMENU,
            wintypes.UINT,
            ctypes.c_size_t,
            wintypes.LPCWSTR,
        )
        user32.AppendMenuW.restype = wintypes.BOOL
        user32.TrackPopupMenu.argtypes = (
            wintypes.HMENU,
            wintypes.UINT,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.HWND,
            ctypes.c_void_p,
        )
        user32.TrackPopupMenu.restype = wintypes.UINT
        user32.DestroyMenu.argtypes = (wintypes.HMENU,)
        user32.DestroyMenu.restype = wintypes.BOOL
        user32.GetCursorPos.argtypes = (ctypes.POINTER(POINT),)
        user32.GetCursorPos.restype = wintypes.BOOL
        user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
        user32.SetForegroundWindow.restype = wintypes.BOOL

        user32.LoadIconW.argtypes = (wintypes.HINSTANCE, ctypes.c_void_p)
        user32.LoadIconW.restype = wintypes.HICON
        user32.LoadImageW.argtypes = (
            wintypes.HINSTANCE,
            wintypes.LPCWSTR,
            wintypes.UINT,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        )
        user32.LoadImageW.restype = wintypes.HANDLE
        user32.DestroyIcon.argtypes = (wintypes.HICON,)
        user32.DestroyIcon.restype = wintypes.BOOL

        shell32.ExtractIconExW.argtypes = (
            wintypes.LPCWSTR,
            ctypes.c_int,
            ctypes.POINTER(wintypes.HICON),
            ctypes.POINTER(wintypes.HICON),
            wintypes.UINT,
        )
        shell32.ExtractIconExW.restype = wintypes.UINT

        shell32.Shell_NotifyIconW.argtypes = (
            wintypes.DWORD,
            ctypes.POINTER(NOTIFYICONDATAW),
        )
        shell32.Shell_NotifyIconW.restype = wintypes.BOOL

        hinstance = kernel32.GetModuleHandleW(None)
        class_name = f"FlipClockNativeTray_{os.getpid()}_{id(self):x}"

        def icon_handle_value(icon) -> int:
            return int(getattr(icon, "value", icon) or 0)

        def default_icon() -> tuple[int, bool]:
            return (
                icon_handle_value(
                    user32.LoadIconW(None, ctypes.c_void_p(self.IDI_APPLICATION))
                ),
                False,
            )

        def load_tray_icon() -> tuple[int, bool]:
            icon_path = executable_directory() / ICON_FILENAME
            if icon_path.is_file():
                icon = user32.LoadImageW(
                    None,
                    str(icon_path),
                    self.IMAGE_ICON,
                    0,
                    0,
                    self.LR_LOADFROMFILE | self.LR_DEFAULTSIZE,
                )
                if icon:
                    return icon_handle_value(icon), True

            large_icon = wintypes.HICON()
            small_icon = wintypes.HICON()
            extracted = shell32.ExtractIconExW(
                sys.executable,
                0,
                ctypes.byref(large_icon),
                ctypes.byref(small_icon),
                1,
            )

            if extracted and (small_icon or large_icon):
                hicon = icon_handle_value(small_icon if small_icon else large_icon)
                unused_icon = large_icon if small_icon else small_icon
                if unused_icon:
                    user32.DestroyIcon(unused_icon)
                return hicon, True

            return default_icon()

        def show_menu(hwnd: int) -> None:
            menu = user32.CreatePopupMenu()
            if not menu:
                return

            try:
                user32.AppendMenuW(
                    menu,
                    self.MF_STRING,
                    self.CMD_TOGGLE,
                    "顯示／隱藏時鐘",
                )
                user32.AppendMenuW(menu, self.MF_SEPARATOR, 0, None)
                user32.AppendMenuW(
                    menu,
                    self.MF_STRING,
                    self.CMD_EXIT,
                    "結束程式",
                )

                point = POINT()
                user32.GetCursorPos(ctypes.byref(point))
                user32.SetForegroundWindow(hwnd)

                command = user32.TrackPopupMenu(
                    menu,
                    self.TPM_RIGHTBUTTON | self.TPM_RETURNCMD,
                    point.x,
                    point.y,
                    0,
                    hwnd,
                    None,
                )
                if command == self.CMD_TOGGLE:
                    self.command_queue.put("toggle")
                elif command == self.CMD_EXIT:
                    self.command_queue.put("exit")

                user32.PostMessageW(hwnd, self.WM_NULL, 0, 0)
            finally:
                user32.DestroyMenu(menu)

        notify_data = NOTIFYICONDATAW()

        @WNDPROC
        def wndproc(hwnd, message, wparam, lparam):
            if message == self.WM_TRAYICON:
                tray_event = int(lparam) & 0xFFFF

                if tray_event in (self.WM_LBUTTONUP, self.WM_LBUTTONDBLCLK):
                    self.command_queue.put("toggle")
                    return 0

                if tray_event in (self.WM_RBUTTONUP, self.WM_CONTEXTMENU):
                    show_menu(hwnd)
                    return 0

            if message == self.WM_UPDATE_TIP:
                notify_data.uFlags = self.NIF_TIP
                notify_data.szTip = self.tooltip
                shell32.Shell_NotifyIconW(
                    self.NIM_MODIFY,
                    ctypes.byref(notify_data),
                )
                return 0

            if message == self.WM_CLOSE:
                shell32.Shell_NotifyIconW(
                    self.NIM_DELETE,
                    ctypes.byref(notify_data),
                )
                if self._tray_icon and self._owns_tray_icon:
                    user32.DestroyIcon(wintypes.HICON(self._tray_icon))
                    self._tray_icon = 0
                    self._owns_tray_icon = False
                user32.DestroyWindow(hwnd)
                return 0

            if message == self.WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0

            return user32.DefWindowProcW(hwnd, message, wparam, lparam)

        self._wndproc_ref = wndproc

        window_class = WNDCLASSEXW()
        window_class.cbSize = ctypes.sizeof(WNDCLASSEXW)
        window_class.lpfnWndProc = wndproc
        window_class.hInstance = hinstance
        window_class.lpszClassName = class_name

        if not user32.RegisterClassExW(ctypes.byref(window_class)):
            raise ctypes.WinError(ctypes.get_last_error())

        hwnd = user32.CreateWindowExW(
            0,
            class_name,
            class_name,
            0,
            0,
            0,
            0,
            0,
            None,
            None,
            hinstance,
            None,
        )
        if not hwnd:
            raise ctypes.WinError(ctypes.get_last_error())

        self.hwnd = int(hwnd)

        hicon, owns_icon = load_tray_icon()
        self._tray_icon = hicon
        self._owns_tray_icon = owns_icon

        notify_data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        notify_data.hWnd = hwnd
        notify_data.uID = 1
        notify_data.uFlags = self.NIF_MESSAGE | self.NIF_ICON | self.NIF_TIP
        notify_data.uCallbackMessage = self.WM_TRAYICON
        notify_data.hIcon = wintypes.HICON(hicon)
        notify_data.szTip = self.tooltip
        self._notify_data = notify_data

        if not shell32.Shell_NotifyIconW(
            self.NIM_ADD,
            ctypes.byref(notify_data),
        ):
            raise ctypes.WinError(ctypes.get_last_error())

        self.ready_event.set()

        message = MSG()
        while True:
            result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
            if result == 0:
                break
            if result == -1:
                raise ctypes.WinError(ctypes.get_last_error())
            user32.TranslateMessage(ctypes.byref(message))
            user32.DispatchMessageW(ctypes.byref(message))


class RailwayFlipClock(tk.Toplevel):
    """
    獨立的時鐘視窗。

    Tk 根視窗永久隱藏，只負責事件迴圈；時鐘使用 Toplevel。
    這樣 Windows 不會替隱藏根視窗建立工作列圖示。
    """

    TRAY_START_TIMEOUT_MS = 8000
    TRAY_POLL_MS = 50

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)

        self.master_root = master
        self.is_windows = sys.platform.startswith("win")
        self.is_macos = sys.platform == "darwin"

        self.withdraw()
        self.title(f"{APP_NAME} {VERSION}")
        self.configure(bg=WINDOW_BG)
        self.resizable(False, False)
        self.overrideredirect(True)

        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.clock_job: str | None = None
        self.topmost_job: str | None = None
        self.tray_poll_job: str | None = None
        self.command_poll_job: str | None = None

        self.tray_commands: queue.Queue[str] = queue.Queue()
        self.tray: NativeWindowsTray | None = None

        self.tray_available = False
        self.clock_visible = True
        self.is_closing = False
        self._tray_wait_elapsed = 0

        startup_time = datetime.now()
        self._configure_dimensions()
        self._build_clock(startup_time.strftime("%H%M"))
        self._bind_window_events()
        self.last_minute_key = startup_time.strftime("%Y%m%d%H%M")

        self.update_idletasks()

        # Windows 使用工具視窗樣式，確保不出現在工作列與 Alt+Tab。
        if self.is_windows:
            try:
                self.attributes("-toolwindow", True)
            except tk.TclError:
                pass
            self._apply_windows_toolwindow_style()
        else:
            self._configure_platform_window()

        self._schedule_next_minute()
        if self.is_windows:
            self.tray = NativeWindowsTray(
                self.tray_commands,
                f"{APP_NAME} {VERSION}",
            )
            self.tray.start()
            self._poll_tray_start()
            self._poll_tray_commands()
        else:
            self.tray_available = False
            self.show_from_tray()

        if self.is_macos:
            self.topmost_job = self.after(
                MAC_TOPMOST_INTERVAL_MS,
                self._maintain_macos_topmost,
            )

    def _configure_dimensions(self) -> None:
        pixels_per_inch = self.winfo_fpixels("1i")
        self.window_width = max(110, round(WINDOW_WIDTH_PT * pixels_per_inch / 72))
        self.window_height = max(56, round(WINDOW_HEIGHT_PT * pixels_per_inch / 72))

        screen_width = max(self.window_width, self.winfo_screenwidth())
        screen_height = max(self.window_height, self.winfo_screenheight())

        self.start_x = max(0, screen_width - self.window_width - 24)
        self.start_y = max(0, min(24, screen_height - self.window_height))
        self.geometry(
            f"{self.window_width}x{self.window_height}"
            f"+{self.start_x}+{self.start_y}"
        )

    def _build_clock(self, now_digits: str) -> None:
        margin_x = max(4, round(self.window_width * 0.035))
        top_margin = max(5, round(self.window_height * 0.09))
        bottom_margin = max(4, round(self.window_height * 0.07))
        gap = max(2, round(self.window_width * 0.014))
        colon_width = max(7, round(self.window_width * 0.055))

        card_height = self.window_height - top_margin - bottom_margin
        available_width = (
            self.window_width - (margin_x * 2) - colon_width - (gap * 4)
        )
        card_width = max(18, available_width // 4)
        content_width = card_width * 4 + colon_width + gap * 4
        x = (self.window_width - content_width) // 2
        font_size = max(15, round(card_height * 0.48))

        self.cells: list[FlipCell] = []

        for index, digit in enumerate(now_digits):
            if index == 2:
                colon = tk.Label(
                    self,
                    text=":",
                    bg=WINDOW_BG,
                    fg=TEXT_COLOR,
                    font=(FONT_NAME, max(12, round(font_size * 0.78)), "bold"),
                    bd=0,
                    highlightthickness=0,
                )
                colon.place(x=x, y=top_margin, width=colon_width, height=card_height)
                self._bind_drag(colon)
                x += colon_width + gap

            cell = FlipCell(
                self,
                width=card_width,
                height=card_height,
                font_size=font_size,
                initial=digit,
            )
            cell.place(x=x, y=top_margin, width=card_width, height=card_height)
            self.cells.append(cell)
            self._bind_drag_recursive(cell)
            x += card_width + gap

        close_size = max(8, round(self.window_height * 0.16))
        self.close_button = tk.Label(
            self,
            text="×",
            bg=WINDOW_BG,
            fg=CLOSE_IDLE,
            font=(FONT_NAME, close_size, "bold"),
            cursor="hand2",
            bd=0,
            highlightthickness=0,
        )
        self.close_button.place(
            relx=1.0,
            x=-2,
            y=0,
            anchor="ne",
            width=max(12, round(self.window_width * 0.1)),
            height=max(12, round(self.window_height * 0.25)),
        )
        self.close_button.bind("<Button-1>", lambda _event: self.hide_to_tray())
        self.close_button.bind(
            "<Enter>",
            lambda _event: self.close_button.configure(fg=TEXT_COLOR),
        )
        self.close_button.bind(
            "<Leave>",
            lambda _event: self.close_button.configure(fg=CLOSE_IDLE),
        )

    def _bind_window_events(self) -> None:
        self._bind_drag(self)
        self.bind("<Escape>", lambda _event: self.hide_to_tray())
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        if self.is_windows:
            self.bind("<FocusIn>", self._restore_window_state, add="+")
        else:
            self.bind("<Map>", self._restore_window_state, add="+")
            self.bind("<Visibility>", self._restore_window_state, add="+")
            self.bind("<FocusIn>", self._restore_window_state, add="+")

    def _windows_api(self):
        if not self.is_windows:
            return None

        try:
            from ctypes import wintypes

            user32 = ctypes.WinDLL("user32", use_last_error=True)

            user32.GetAncestor.argtypes = (wintypes.HWND, wintypes.UINT)
            user32.GetAncestor.restype = wintypes.HWND

            user32.GetWindowLongW.argtypes = (wintypes.HWND, ctypes.c_int)
            user32.GetWindowLongW.restype = ctypes.c_long

            user32.SetWindowLongW.argtypes = (
                wintypes.HWND,
                ctypes.c_int,
                ctypes.c_long,
            )
            user32.SetWindowLongW.restype = ctypes.c_long

            user32.SetWindowPos.argtypes = (
                wintypes.HWND,
                wintypes.HWND,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                wintypes.UINT,
            )
            user32.SetWindowPos.restype = wintypes.BOOL

            user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
            user32.ShowWindow.restype = wintypes.BOOL

            user32.BringWindowToTop.argtypes = (wintypes.HWND,)
            user32.BringWindowToTop.restype = wintypes.BOOL
            return user32
        except (AttributeError, OSError):
            return None

    def _windows_root_hwnd(self) -> int:
        if not self.is_windows:
            return 0

        try:
            child_hwnd = int(self.winfo_id())
            user32 = self._windows_api()
            if user32 is None:
                return child_hwnd

            outer_hwnd = int(user32.GetAncestor(child_hwnd, 2))
            return outer_hwnd or child_hwnd
        except (OSError, ValueError, tk.TclError):
            return 0

    def _apply_windows_toolwindow_style(self) -> None:
        """
        將時鐘視窗設定為工具視窗。

        隱藏根視窗不會出現在工作列；時鐘 Toplevel 再加上
        WS_EX_TOOLWINDOW 並移除 WS_EX_APPWINDOW，雙重避免工作列圖示。
        """
        hwnd = self._windows_root_hwnd()
        if not hwnd:
            return

        GWL_EXSTYLE = -20
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_APPWINDOW = 0x00040000

        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_NOZORDER = 0x0004
        SWP_NOACTIVATE = 0x0010
        SWP_FRAMECHANGED = 0x0020

        user32 = self._windows_api()
        if user32 is None:
            return

        try:
            style = int(user32.GetWindowLongW(hwnd, GWL_EXSTYLE))
            style = (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            user32.SetWindowPos(
                hwnd,
                0,
                0,
                0,
                0,
                0,
                SWP_NOSIZE
                | SWP_NOMOVE
                | SWP_NOZORDER
                | SWP_NOACTIVATE
                | SWP_FRAMECHANGED,
            )
        except (OSError, ValueError):
            pass

    def _force_windows_visible(self) -> None:
        hwnd = self._windows_root_hwnd()
        if not hwnd:
            return

        SW_SHOWNORMAL = 1
        HWND_TOPMOST = -1
        flags = 0x0001 | 0x0002 | 0x0010 | 0x0020 | 0x0040

        user32 = self._windows_api()
        if user32 is None:
            return

        try:
            user32.ShowWindow(hwnd, SW_SHOWNORMAL)
            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags)
            user32.BringWindowToTop(hwnd)
        except (OSError, ValueError):
            pass

    def _configure_platform_window(self) -> None:
        if not self.is_macos:
            return

        try:
            self.tk.call(
                "::tk::unsupported::MacWindowStyle",
                "style",
                self._w,
                "floating",
                "noTitleBar",
            )
        except tk.TclError:
            try:
                self.tk.call(
                    "::tk::unsupported::MacWindowStyle",
                    "style",
                    self._w,
                    "help",
                    "",
                )
            except tk.TclError:
                pass

    def _apply_always_on_top(self) -> None:
        if self.is_closing or not self.winfo_exists() or not self.clock_visible:
            return

        try:
            self.attributes("-topmost", True)
            self.lift()
        except tk.TclError:
            return

        if self.is_macos:
            try:
                self.tk.call("wm", "attributes", self._w, "-topmost", 1)
            except tk.TclError:
                pass

    def _restore_window_state(self, _event: tk.Event | None = None) -> None:
        if self.is_closing or not self.clock_visible:
            return

        if self.is_windows:
            self.after_idle(self._apply_windows_toolwindow_style)
            self.after_idle(self._force_windows_visible)
        else:
            self.after_idle(self._apply_always_on_top)

        self.after_idle(self._sync_time_immediately)

    def _maintain_macos_topmost(self) -> None:
        if self.is_closing:
            return
        self._apply_always_on_top()
        self.topmost_job = self.after(
            MAC_TOPMOST_INTERVAL_MS,
            self._maintain_macos_topmost,
        )

    def _poll_tray_start(self) -> None:
        if self.is_closing:
            return
        if self.tray is None:
            return

        if self.tray.ready_event.is_set():
            if self.tray.failed_event.is_set() or not self.tray.hwnd:
                message = (
                    "Windows 原生系統匣圖示建立失敗，"
                    "程式不會只留在背景執行。\n\n"
                    f"錯誤：{self.tray.error_text or '未知錯誤'}"
                )
                write_error_log(message)
                from tkinter import messagebox

                messagebox.showerror(
                    f"{APP_NAME} 系統匣失敗",
                    message,
                    parent=self.master_root,
                )
                self.close()
                return

            self.tray_available = True
            self._apply_windows_toolwindow_style()
            self.show_from_tray()
            return

        self._tray_wait_elapsed += self.TRAY_POLL_MS
        if self._tray_wait_elapsed >= self.TRAY_START_TIMEOUT_MS:
            message = (
                "Windows 原生系統匣圖示建立逾時，"
                "程式已停止，避免只留在背景。"
            )
            write_error_log(message)
            from tkinter import messagebox

            messagebox.showerror(
                f"{APP_NAME} 系統匣逾時",
                message,
                parent=self.master_root,
            )
            self.close()
            return

        self.tray_poll_job = self.after(
            self.TRAY_POLL_MS,
            self._poll_tray_start,
        )

    def _poll_tray_commands(self) -> None:
        if self.is_closing:
            return
        if self.tray is None:
            return

        try:
            while True:
                command = self.tray_commands.get_nowait()
                if command == "toggle":
                    self.toggle_clock_visibility()
                elif command == "exit":
                    self.close()
        except queue.Empty:
            pass

        self.command_poll_job = self.after(100, self._poll_tray_commands)

    def toggle_clock_visibility(self) -> None:
        if self.clock_visible:
            self.hide_to_tray()
        else:
            self.show_from_tray()

    def hide_to_tray(self) -> None:
        if self.is_closing:
            return

        if not self.tray_available:
            self.close()
            return

        self.clock_visible = False
        try:
            self.withdraw()
        except tk.TclError:
            pass

    def show_from_tray(self) -> None:
        if self.is_closing:
            return
        if self.is_windows and not self.tray_available:
            return

        self.clock_visible = True
        try:
            self.deiconify()
            self.state("normal")
            self.attributes("-topmost", True)
            self.lift()
            self.update_idletasks()
        except tk.TclError:
            return

        if self.is_windows:
            self._apply_windows_toolwindow_style()
            self._force_windows_visible()
        else:
            self._apply_always_on_top()

        self._sync_time_immediately()

    def _bind_drag(self, widget: tk.Misc) -> None:
        widget.bind("<ButtonPress-1>", self._start_drag, add="+")
        widget.bind("<B1-Motion>", self._drag_window, add="+")

    def _bind_drag_recursive(self, widget: tk.Misc) -> None:
        self._bind_drag(widget)
        for child in widget.winfo_children():
            self._bind_drag_recursive(child)

    def _start_drag(self, event: tk.Event) -> None:
        if event.widget == self.close_button:
            return
        self.drag_offset_x = event.x_root - self.winfo_x()
        self.drag_offset_y = event.y_root - self.winfo_y()

    def _drag_window(self, event: tk.Event) -> None:
        if event.widget == self.close_button:
            return
        self.geometry(
            f"+{event.x_root - self.drag_offset_x}"
            f"+{event.y_root - self.drag_offset_y}"
        )

    def _schedule_next_minute(self) -> None:
        if self.is_closing:
            return

        if self.clock_job is not None:
            try:
                self.after_cancel(self.clock_job)
            except tk.TclError:
                pass

        now = datetime.now()
        elapsed_ms = now.second * 1000 + now.microsecond // 1000
        delay_ms = max(50, 60_000 - elapsed_ms + 25)
        self.clock_job = self.after(delay_ms, self._minute_tick)

    def _minute_tick(self) -> None:
        self.clock_job = None
        self._sync_time_immediately()
        self._schedule_next_minute()

    def _sync_time_immediately(self) -> None:
        now = datetime.now()
        minute_key = now.strftime("%Y%m%d%H%M")
        if minute_key == self.last_minute_key:
            return

        self.last_minute_key = minute_key
        time_text = now.strftime("%H:%M")

        if self.tray_available and self.tray is not None:
            self.tray.update_tooltip(f"{APP_NAME} {time_text}")

        for cell, digit in zip(self.cells, now.strftime("%H%M")):
            cell.flip_to(digit)

    def close(self) -> None:
        if self.is_closing:
            return

        self.is_closing = True

        for job in (
            self.clock_job,
            self.topmost_job,
            self.tray_poll_job,
            self.command_poll_job,
        ):
            if job is not None:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass

        if self.tray is not None:
            self.tray.stop()

        for cell in self.cells:
            cell.cancel_animation()

        try:
            self.destroy()
        except tk.TclError:
            pass

        try:
            self.master_root.destroy()
        except tk.TclError:
            pass


def main() -> None:
    enable_dpi_awareness()

    root = tk.Tk()
    root.withdraw()

    RailwayFlipClock(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        import traceback
        from tkinter import messagebox

        error_text = traceback.format_exc()
        log_path = write_error_log(error_text)

        try:
            error_root = tk.Tk()
            error_root.withdraw()
            location_text = f"\n\n錯誤紀錄：{log_path}" if log_path else ""
            messagebox.showerror(
                f"{APP_NAME} 啟動失敗",
                f"程式無法啟動：\n{exc}{location_text}",
                parent=error_root,
            )
            error_root.destroy()
        except Exception:
            pass
