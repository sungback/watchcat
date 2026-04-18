import os
import subprocess
import threading
import time

import flet as ft
from watchdog.observers import Observer

from .monitor import NFCConverterHandler
from .path_fixer import run_bulk_fix
from .picker import pick_folder_mac_native
from .platform import IS_MACOS, IS_WINDOWS


def main(page: ft.Page):
    page.title = "K-Fixer: 한글 자소 분리 해결사"
    page.window.width = 600
    page.window.height = 550
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 30

    state = {"observer": None, "is_running": False}

    log_list = ft.ListView(expand=True, spacing=5, padding=10)

    def append_log(message):
        timestamp = time.strftime("%H:%M:%S")
        log_list.controls.append(
            ft.Text(f"[{timestamp}] {message}", size=12, font_family="monospace")
        )
        page.update()

    def on_path_change(e):
        has_path = bool(selected_path_input.value.strip())
        start_btn.disabled = not has_path
        bulk_btn.disabled = not has_path
        page.update()

    def set_selected_path(path):
        selected_path_input.value = os.path.normpath(path)
        has_path = bool(selected_path_input.value.strip())
        start_btn.disabled = not has_path
        bulk_btn.disabled = not has_path
        page.update()

    selected_path_input = ft.TextField(
        label="감시할 폴더 경로",
        hint_text="직접 입력하거나 좌측 아이콘을 클릭하세요.",
        expand=True,
        text_size=13,
        on_change=on_path_change,
    )

    async def pick_folder(e):
        selected_path = None

        if IS_MACOS:
            try:
                selected_path = pick_folder_mac_native()
            except subprocess.CalledProcessError:
                return
            except (FileNotFoundError, OSError):
                selected_path = None

        if selected_path is None:
            try:
                selected_path = await ft.FilePicker().get_directory_path(
                    dialog_title="감시할 폴더를 선택하세요"
                )
            except Exception as ex:
                append_log(f"❌ 폴더 선택창을 열지 못했습니다: {ex}")
                return

        if selected_path:
            set_selected_path(selected_path)

    def set_controls_busy(busy):
        """일괄 변환 중에는 경로 입력/버튼을 잠근다."""
        path_btn.disabled = busy
        selected_path_input.disabled = busy
        bulk_btn.disabled = busy
        page.update()

    def on_bulk_done(scanned, fixed):
        append_log(f"📊 일괄 변환 완료: {scanned}건 스캔 / {fixed}건 교정")
        set_controls_busy(False)
        start_btn.disabled = not bool(selected_path_input.value.strip())
        bulk_btn.disabled = not bool(selected_path_input.value.strip())
        page.update()

    def start_bulk_fix(e):
        path = selected_path_input.value.strip()
        if not os.path.isdir(path):
            append_log("❌ 유효한 폴더 경로를 입력해주세요.")
            return
        append_log(f"🔍 일괄 변환 시작: {path}")
        set_controls_busy(True)
        start_btn.disabled = True
        threading.Thread(
            target=run_bulk_fix,
            args=(path, append_log, on_bulk_done),
            daemon=True,
        ).start()

    def toggle_monitoring(e):
        if not state["is_running"]:
            path = selected_path_input.value.strip()
            if not os.path.isdir(path):
                append_log("❌ 유효한 폴더 경로를 입력해주세요.")
                return

            handler = NFCConverterHandler(append_log)
            state["observer"] = Observer()
            state["observer"].schedule(handler, path, recursive=True)

            try:
                state["observer"].start()
            except Exception as ex:
                state["observer"] = None
                append_log(f"❌ 감시를 시작하지 못했습니다: {ex}")
                page.update()
                return

            state["is_running"] = True
            start_btn.text = "감시 중지"
            start_btn.icon = ft.Icons.STOP_CIRCLE
            start_btn.color = ft.Colors.RED
            path_btn.disabled = True
            selected_path_input.disabled = True
            bulk_btn.disabled = True
            append_log(f"🚀 감시 시작: {path}")
        else:
            if state["observer"]:
                state["observer"].stop()
                state["observer"].join()
                state["observer"] = None

            state["is_running"] = False
            start_btn.text = "감시 시작"
            start_btn.icon = ft.Icons.PLAY_ARROW_ROUNDED
            start_btn.color = ft.Colors.BLUE
            path_btn.disabled = False
            selected_path_input.disabled = False
            bulk_btn.disabled = False
            append_log("🛑 감시가 중지되었습니다.")

        page.update()

    path_btn = ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN_ROUNDED,
        icon_color=ft.Colors.BLUE_GREY_700,
        on_click=pick_folder,
        tooltip="폴더 선택" if IS_WINDOWS else "폴더 선택",
    )

    start_btn = ft.Button(
        "감시 시작",
        icon=ft.Icons.PLAY_ARROW_ROUNDED,
        on_click=toggle_monitoring,
        disabled=True,
    )

    bulk_btn = ft.Button(
        "일괄 변환",
        icon=ft.Icons.AUTO_FIX_HIGH_ROUNDED,
        on_click=start_bulk_fix,
        disabled=True,
        color=ft.Colors.GREEN_700,
        tooltip="선택한 폴더의 기존 파일명을 모두 NFC로 교정합니다.",
    )

    page.add(
        ft.Column(
            [
                ft.Text("K-Fixer", size=32, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "맥-윈도우 한글 자소 분리 문제를 실시간으로 해결합니다.",
                    size=14,
                    color=ft.Colors.GREY_600,
                ),
                ft.Divider(height=20, thickness=1),
                ft.Row(
                    [path_btn, selected_path_input],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=10),
                ft.Row([start_btn, ft.Container(width=10), bulk_btn]),
                ft.Container(height=20),
                ft.Text("작업 로그", weight=ft.FontWeight.W_600),
                ft.Container(
                    content=log_list,
                    bgcolor=ft.Colors.GREY_50,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    expand=True,
                ),
            ],
            expand=True,
        )
    )
